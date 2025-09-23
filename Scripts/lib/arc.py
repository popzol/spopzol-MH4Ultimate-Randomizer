# arc.py - versión compatible con util.py (Python 3)
import os
import zlib
import binascii

from util import *  # usamos read_block, read_word, read_dword, write_block, write_dword, alloc_block, writeFile, log_info

# mapping de signatures a extensiones (abreviado; puedes ampliarlo si quieres)
ext = {
    b"8ed1bf1b": ".mib",   # ejemplo de mapping (asegúrate que está en tu lista si lo necesitas)
    # ... (puedes pegar aquí el resto de tu diccionario si lo deseas)
}

# rev_ext no usado en este archivo pero lo puedes preparar si quieres
rev_ext = {}

class ARC:
    magic = b'ARC\x00'
    supported_versions = [7, 17, 19]

    def __init__(self, arc=None):
        if arc:
            self.import_arc(arc)
        else:
            self.default_meta()

    def default_meta(self):
        self.magic = ARC.magic
        self.version = 19
        self.file_list = []
        self.file_count = 0

    def import_arc(self, arc):
        # arc es bytes/bytearray
        self.parse_header(arc)
        self.parse_file_list(arc)
        self.parse_files(arc)

    def parse_header(self, arc):
        self.magic = read_block(arc, 0x00, 0x4)
        if self.magic != ARC.magic:
            error("Invalid Magic Identifier: {}".format(self.magic))

        self.version = read_word(arc, 0x04)

        if self.version not in ARC.supported_versions:
            error('Unsupported Version: {}'.format(self.version))

        self.file_count = read_word(arc, 0x06)

    def parse_file_list(self, arc):
        if self.version in (19, 17):
            file_table_offset = 0x0C
            file_table_length = 0x50
        elif self.version == 7:
            file_table_offset = 0x08
            file_table_length = 0x50
        else:
            error("Unsupported ARC version")

        file_list = []

        for idx in range(self.file_count):
            offset = file_table_offset + (idx * file_table_length)
            f = {}
            rawname = read_block(arc, offset + 0, 64)  # bytes
            extbytes = read_block(arc, offset + 64, 4)  # 4 bytes ext/typecode
            size = read_dword(arc, offset + 68)
            unc_size = read_dword(arc, offset + 72)
            off = read_dword(arc, offset + 76)

            # rawname: bytes -> decode and strip nulls, convert backslashes
            try:
                fname = rawname.split(b'\x00', 1)[0].decode('utf-8')
            except Exception:
                fname = rawname.split(b'\x00', 1)[0].decode('latin-1')
            fname = fname.replace("\\", "/")
            raw_ext_hex = binascii.hexlify(extbytes).decode('ascii').lower()

            f['file'] = fname  # ruta con / separador
            f['extension'] = ext.get(extbytes, None)
            if f['extension'] is None:
                # keep hex as extension if unknown
                f['extension'] = '.' + raw_ext_hex
            f['size'] = size
            f['unc_size'] = unc_size & 0xFFFFFF
            f['unk0'] = (unc_size & 0xFF000000) >> 24
            f['offset'] = off
            f['raw_ext'] = raw_ext_hex  # ascii hex string
            file_list.append(f)

        self.file_list = file_list

    def parse_files(self, arc):
        for f in self.file_list:
            # leer bloque comprimido y descomprimir
            cdata = read_block(arc, f['offset'], f['size'])
            try:
                f['data'] = zlib.decompress(cdata)
            except Exception as e:
                # si falla la descompresión, guardar los datos crudos
                log_info(f"Warning: zlib decompress failed for {f['file']}: {e}")
                f['data'] = bytes(cdata)

    def export_arc(self):
        arc = bytearray()
        self.write_header(arc)
        self.write_file_list(arc)
        return arc

    def write_header(self, arc):
        # reservar y escribir header (0x1C bytes)
        alloc_block(arc, 0x1C)
        write_block(arc, 0x0, self.magic)
        write_word(arc, 0x04, int(self.version))
        write_word(arc, 0x06, len(self.file_list))
        write_dword(arc, 0x08, 0)
        return arc

    def write_file_list(self, arc):
        if self.version in (19, 17):
            file_table_offset = 0x0C
            file_table_length = 0x50
        elif self.version == 7:
            file_table_offset = 0x08
            file_table_length = 0x50
        else:
            error("Unsupported ARC version")

        # reservar espacio para tabla
        _ = alloc_block(arc, file_table_length * len(self.file_list) + 4)

        for idx, f in enumerate(self.file_list):
            offset = file_table_offset + (idx * file_table_length)

            # datos sin comprimir (f['data'] puede ser bytes/bytearray)
            data_bytes = bytes(f['data']) if not isinstance(f['data'], bytes) else f['data']
            cdata = zlib.compress(data_bytes)
            data_addr = alloc_block(arc, len(cdata))

            # calcular unc_size (flag en MSB)
            # si extensión .mod usar A0, sino 20 (tal y como hacía la versión anterior)
            _, extension_part = os.path.splitext(f['file'])
            if extension_part == '.mod':
                unc_size = (0xA0 << 24) + len(data_bytes)
            else:
                unc_size = (0x20 << 24) + len(data_bytes)

            # raw_ext: puede ser string hex '1bbfd18e' o bytes
            raw_ext = f.get('raw_ext', None)
            if raw_ext is None:
                extension_bytes = b'\x00\x00\x00\x00'
            else:
                if isinstance(raw_ext, bytes):
                    raw_hex = raw_ext
                else:
                    raw_hex = str(raw_ext).encode('ascii')
                raw_hex = raw_hex.strip().lower()
                try:
                    extension_bytes = binascii.unhexlify(raw_hex)
                    if len(extension_bytes) != 4:
                        extension_bytes = b'\x00\x00\x00\x00'
                except Exception:
                    extension_bytes = b'\x00\x00\x00\x00'

            # escribir datos comprimidos
            write_block(arc, data_addr, cdata)

            # escribir filename (64 bytes area) - usar backslashes en TOC
            filename_bytes = f['file'].replace('/', '\\').encode('utf-8')
            if len(filename_bytes) > 64:
                filename_bytes = filename_bytes[:64]
            # llenar con nulls hasta 64
            filename_padded = filename_bytes + (b'\x00' * (64 - len(filename_bytes)))
            write_block(arc, offset + 0, filename_padded)

            # escribir extension (4 bytes)
            write_block(arc, offset + 64, extension_bytes)

            # escribir sizes y offset
            write_dword(arc, offset + 68, len(cdata))
            write_dword(arc, offset + 72, unc_size)
            write_dword(arc, offset + 76, data_addr)

        return arc

    def add_file(self, filename, data, ext):
        # filename: ruta con backslashes o slashes, guardamos con slashes
        f = {}
        f['file'] = filename.replace('\\', '/')
        # ext puede ser b'1bbfd18e' o '1BBFD18E' o '.mib', normalizamos a hex ascii
        if isinstance(ext, bytes):
            ext_val = ext.decode('ascii').lower()
        else:
            ext_val = str(ext).lstrip('.').lower()
        # si ext_val es una extensión real ".mib" que no es hex, intenta mantenerla como hex 00000000
        # se asume que el caller pasa hex si es necesario
        f['raw_ext'] = ext_val
        f['data'] = bytearray(data) if not isinstance(data, (bytes, bytearray)) else bytearray(data)
        if not hasattr(self, 'file_list') or self.file_list is None:
            self.file_list = []
        self.file_list.append(f)

    def __str__(self):
        info = f"ARC\nVersion : {self.version}\nfiles   : {len(self.file_list)}"
        return info