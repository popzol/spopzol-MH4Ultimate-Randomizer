# util.py - versión corregida para Python 3 (manejo de bytes/bytearray)
from struct import *
import os
import json
import sys

class ANSI:
    RESET   = ''
    RED     = ''
    GREEN   = ''
    YELLOW  = ''
    BLUE    = ''
    MAGENTA = ''
    CYAN    = ''
    WHITE   = ''
    UNDERLINE = ''

LOGGING = 0

def color(msg, color):
    return color + msg + ANSI.RESET

def find(path, pattern):
    for e in os.listdir(path):
        file = os.path.join(path, e)
        if os.path.isdir(file):
            for subfile in find(file, pattern):
                yield subfile
        elif file.find(pattern) > -1:
            yield file

def readFile(path):
    log_loading(path)
    try:
        with open(path, 'rb') as f:
            c = bytearray(f.read())
        return c
    except IOError:
        error('Loading ' + path)

def writeFile(path, c):
    log_saving(path)
    try:
        # asegurar que lo que escribimos es bytes/bytearray
        if isinstance(c, bytearray):
            data = bytes(c)
        elif isinstance(c, bytes):
            data = c
        else:
            # permitir escribir str (codificar)
            data = str(c).encode('utf-8')
        # crear directorio si hace falta
        d = os.path.dirname(path)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data)
    except IOError:
        error('Saving ' + path)

def readJSON(path):
    raw = readFile(path)
    try:
        return json.loads(raw.decode('utf-8'))
    except Exception:
        error('JSON Error')

def byteswap(data):
    s = bytearray()
    for x in range(0, len(data), 4):
        s += data[x:x+4][::-1]
    return s

def read_char(buf, offset):
    return chr(buf[offset])

def read_block(buf, offset, length):
    # devuelve bytes
    return bytes(buf[offset:offset + length])

def read_byte(buf, offset):
    return buf[offset]

def read_word(buf, offset):
    return unpack_from('<H', buf, offset=offset)[0]

def read_dword(buf, offset):
    return unpack_from('<I', buf, offset=offset)[0]

def read_dword_be(buf, offset):
    return unpack_from('>I', buf, offset=offset)[0]

def read_float(buf, offset):
    return unpack_from('<f', buf, offset=offset)[0]

def read_word_array(buf, offset, length):
    a = []
    for i in range(length):
        word = read_word(buf, offset)
        a.append(word)
        offset += 2
    return a

def read_dword_array(buf, offset, length):
    a = []
    for i in range(length):
        word = read_dword(buf, offset)
        a.append(word)
        offset += 4
    return a

def read_ascii_string(buf, offset, maxlength=-1):
    s = ''
    length = 0
    while length != maxlength:
        character = buf[offset + length]
        if character == 0x00:
            break
        s += chr(character)
        length += 1
    return s

def read_string(buf, offset, maxlength=-1):
    s = u''
    length = 0
    while length != maxlength:
        byte1 = read_char(buf, offset)
        byte2 = read_char(buf, offset + 1)
        if ord(byte1) == 0x00 and ord(byte2) == 0x00:
            break
        s += (byte1 + byte2).encode('latin-1').decode('utf-16le')
        offset += 2
        length += 1
    return s

def write_byte(buf, offset, value):
    buf[offset] = value

def write_word(buf, offset, value):
    buf[offset:offset + 2] = pack('<H', value)

def write_dword(buf, offset, value):
    buf[offset:offset + 4] = pack('<I', value)

def write_float(buf, offset, value):
    buf[offset:offset + 4] = pack('<f', value)

def write_block(buf, offset, value):
    # Acepta bytes, bytearray o str; si es str lo codifica en utf-8 automáticamente.
    if isinstance(value, str):
        value = value.encode('utf-8')
    if isinstance(value, bytearray):
        value = bytes(value)
    buf[offset:offset + len(value)] = value

def write_word_array(buf, offset, arr):
    for idx in range(len(arr)):
        write_word(buf, offset + idx * 2, arr[idx])
    return buf

def write_ascii_string(buf, s):
    if isinstance(s, str):
        b = s.encode('ascii') + b'\x00'
    else:
        b = bytes(s) + b'\x00'
    buf.extend(b)

def write_string(buf, offset, s):
    s = s.encode('utf-16le')
    buf[offset:offset+len(s)] = s

def alloc_block(buf, length, alignment=0):
    # buf es bytearray
    if not isinstance(buf, bytearray):
        raise TypeError("alloc_block expects bytearray buf")
    # align blockstart
    if alignment > 0:
        padding = (alignment - (len(buf) % alignment)) % alignment
        if padding:
            buf.extend(b'\x00' * padding)
    addr = len(buf)
    buf.extend(b'\x00' * length)
    return addr

def to_json(obj):
    return json.dumps(obj, default=lambda o: o.__dict__, sort_keys=True, indent=4)

def to_csv(arr, delim='\t'):
    s = ''
    for row in arr:
        line = ''
        if isinstance(row, list):
            line = delim.join(row)
        if isinstance(row, str):
            line = ''.join(row)
        s += line.replace('\n', '\\n').replace('\r', '\\r') + '\n'
    return s[:-1]  # trim trailing newline

def from_csv(string):
    table = []
    for row in string.split('\n'):
        row = row.replace('\\n', '\n')
        table.append(row)
    return table

def enable_log(level):
    global LOGGING
    LOGGING = level

def log(msg):
    if LOGGING > 0:
        print(msg)

def log_info(msg):
    if LOGGING > 1:
        print(msg)

def log_warn(msg):
    print(color("Warning:", ANSI.YELLOW) + msg)

def log_saving(fn):
    log(color('Saving ', ANSI.BLUE) + fn + '...')

def log_loading(fn):
    log(color('Loading ', ANSI.YELLOW) + fn + '...')

def error(msg):
    print(color('Error ', ANSI.RED) + msg)
    sys.exit(1)

def dump_obj(obj):
    s = ""
    for attr in obj.__dict__:
        value = obj.__dict__[attr]
        if type(value) == list:
            pass
        else:
            s += "{0:10}: {1}\n".format(attr, value)
    return s[:-1]