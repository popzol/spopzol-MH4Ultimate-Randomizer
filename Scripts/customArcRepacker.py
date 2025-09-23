#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import re

# Global: filename for the quest order DB (best practice: single global constant)
ORDER_FILENAME = "QuestOrderDataBase.json"

# Añadir lib al inicio para forzar imports desde tools/lib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

# Importar util y ARC explícitamente
from util import *            # readFile, writeFile, enable_log, ...
import arc as arc_mod         # importamos el módulo para inspección
from arc import ARC           # clase ARC (la esperada)

# Debug: mostrar qué archivo de módulo 'arc' se cargó
print("DEBUG: módulo 'arc' cargado desde:", getattr(arc_mod, '__file__', '<desconocido>'))

# Comprobación mínima de argumentos
if len(sys.argv) < 4:
    print("Uso: python customArcRepacker.py c <arc_salida> <carpeta_entrada>")
    sys.exit(1)

modo = sys.argv[1]  # 'c' para compilar
arc_salida = sys.argv[2]
carpeta_entrada = sys.argv[3]

# MH4U versión por defecto
VERSION = 19

enable_log(True)

if modo != 'c':
    print("Solo se soporta modo 'c' para compilar")
    sys.exit(1)


# ----------------------
# File collection helpers
# ----------------------
def collect_files(input_folder):
    """
    Collect all file paths inside the given input folder.
    Returns a sorted list of absolute file paths for reproducibility.
    """
    input_abs = os.path.abspath(input_folder)
    file_list = []
    for root, dirs, files in os.walk(input_abs):
        for fname in files:
            full_path = os.path.join(root, fname)
            file_list.append(full_path)
    file_list.sort()
    return file_list


# ----------------------
# ARC add helper
# ----------------------
def add_files_to_arc(arc, input_folder, file_list=None):
    """
    Add the given files into the ARC object.
    If file_list is None, the files will be collected automatically from input_folder.

    For files named like m<ID>.<8hex> (e.g. m10101.1BBFD18E) we:
      - parse the 8-hex string -> 4 bytes
      - reverse bytes to little-endian as observed needed
      - convert to ASCII hex string and pass as bytes to arc.add_file (e.g. b'8ed1bf1b')

    If no valid 8-hex suffix is present, '00000000' (as ASCII bytes) is used.
    """
    if file_list is None:
        file_list = collect_files(input_folder)

    base_dir = os.path.abspath(input_folder)
    base_parent = os.path.dirname(base_dir)  # relativize against this parent

    use_add_file = hasattr(arc, 'add_file')

    for fpath in file_list:
        rel_path = os.path.relpath(fpath, start=base_parent).replace('/', '\\')

        # read data
        data = readFile(fpath)

        # parse possible .<8hex> suffix
        base = os.path.basename(fpath)
        name_part, ext_part = os.path.splitext(base)

        ext_bin = None
        if ext_part:
            candidate = ext_part.lstrip('.').lower()
            if len(candidate) == 8 and all(c in '0123456789abcdef' for c in candidate):
                try:
                    be = bytes.fromhex(candidate)   # big-endian bytes from hex string
                    ext_bin = be[::-1]             # reverse -> little-endian bytes as required
                except Exception:
                    ext_bin = None

        # default -> 4 zero bytes
        if ext_bin is None:
            ext_bin = b'\x00\x00\x00\x00'

        # prepare the argument expected by arc.add_file: ASCII hex bytes (lowercase)
        ext_arg = ext_bin.hex().encode('ascii')   # e.g. b'8ed1bf1b' or b'00000000'

        # strip the .XXXXXXXX from stored filename when appropriate
        if ext_part and ext_bin != b'\x00\x00\x00\x00':
            dir_part = os.path.dirname(rel_path)
            if dir_part and dir_part != '.':
                rel_stored = os.path.join(dir_part, name_part).replace('/', '\\')
            else:
                rel_stored = name_part
        else:
            rel_stored = rel_path

        # Add to ARC using the signature expected by lib/arc.py
        if use_add_file:
            # pass ASCII-encoded hex (bytes), matching what arc.add_file decodes
            arc.add_file(rel_stored, data, ext_arg)
        else:
            # fallback: store raw_ext as the ASCII hex string (lowercase)
            f = {
                'file': rel_stored.replace('\\', '/'),
                'raw_ext': ext_arg.decode('ascii').lower(),   # e.g. '8ed1bf1b'
                'data': bytearray(data)
            }
            if not hasattr(arc, 'file_list') or arc.file_list is None:
                arc.file_list = []
            arc.file_list.append(f)

# ----------------------
# Order JSON helpers (uses ORDER_FILENAME in lib)
# ----------------------
def get_order_file_path():
    """
    Return the preferred path for the order JSON:
      1) script_dir/lib/ORDER_FILENAME
      2) input_folder/ORDER_FILENAME
      3) script_dir/ORDER_FILENAME
    Returns path or None.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 1) lib inside script dir
    lib_path = os.path.join(script_dir, 'lib', ORDER_FILENAME)
    if os.path.isfile(lib_path):
        return lib_path

    # 2) inside input folder (in case user put it there)
    candidate = os.path.join(os.path.abspath(carpeta_entrada), ORDER_FILENAME)
    if os.path.isfile(candidate):
        return candidate

    # 3) script dir fallback
    candidate2 = os.path.join(script_dir, ORDER_FILENAME)
    if os.path.isfile(candidate2):
        return candidate2

    return None


def extract_json_object_by_key(text, key):
    """
    Given text that may contain other junk, extract the JSON object starting at the
    key (e.g. "questOrderInMemory") by finding the opening '{' after the key and
    matching braces. Returns the substring or raises ValueError.
    """
    idx = text.find(key)
    if idx == -1:
        raise ValueError("key not found in text")
    # find the first '{' after the key
    brace_idx = text.find('{', idx)
    if brace_idx == -1:
        raise ValueError("opening brace not found after key")
    depth = 0
    for i in range(brace_idx, len(text)):
        c = text[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return text[brace_idx:i+1]
    raise ValueError("matching closing brace not found")


def load_order_map_from_file(path):
    """
    Load the mapping questOrderInMemory -> {id: order} from a JSON file.
    Tries robust parsing if the file contains extra objects/comments.
    Returns a dict mapping strings (IDs) -> int (order).
    """
    with open(path, 'r', encoding='utf-8') as fh:
        txt = fh.read()

    # 1) Try direct JSON load
    try:
        j = json.loads(txt)
        if isinstance(j, dict):
            if 'questOrderInMemory' in j and isinstance(j['questOrderInMemory'], dict):
                return {str(k): int(v) for k, v in j['questOrderInMemory'].items()}
            # maybe file contains only mapping directly
            if all(isinstance(v, int) for v in j.values()):
                return {str(k): int(v) for k, v in j.items()}
    except json.JSONDecodeError:
        pass

    # 2) Try to extract questOrderInMemory object textually
    if 'questOrderInMemory' in txt:
        try:
            obj_text = extract_json_object_by_key(txt, 'questOrderInMemory')
            parsed = json.loads(obj_text)
            if isinstance(parsed, dict):
                return {str(k): int(v) for k, v in parsed.items()}
        except Exception as e:
            print("Warning: could not extract questOrderInMemory via robust method:", e)

    # 3) Final heuristic: load first dict-like object and try to find nested mapping
    m = re.search(r'\{[\s\S]{10,}\}', txt)
    if m:
        try:
            parsed = json.loads(m.group(0))
            if isinstance(parsed, dict):
                for v in parsed.values():
                    if isinstance(v, dict):
                        # assume this nested dict is the mapping
                        return {str(k): int(val) for k, val in v.items()}
                if all(isinstance(v, int) for v in parsed.values()):
                    return {str(k): int(v) for k, v in parsed.items()}
        except Exception:
            pass

    raise ValueError(f"Could not parse order mapping from {path}")


def sort_files_by_order(file_list, input_folder, order_map):
    """
    Given a list of absolute file paths, return a new list sorted according to order_map.
    The file name format expected: m<id>.<8hex> (e.g. m10101.1BBFD18E).
    order_map maps id-string -> integer index (0..N).
    Files whose ID is not present in order_map will be placed after mapped files,
    sorted alphabetically (stable).
    """
    base_dir = os.path.abspath(input_folder)
    base_parent = os.path.dirname(base_dir)

    def extract_id_from_path(path):
        # basename like 'm10101.1BBFD18E' or 'm10101' (with or without ext)
        b = os.path.basename(path)
        name_part, _ = os.path.splitext(b)
        m = re.match(r'^m(\d+)$', name_part, re.IGNORECASE)
        if m:
            return m.group(1)
        m2 = re.match(r'^m(\d+)', b, re.IGNORECASE)
        if m2:
            return m2.group(1)
        return None

    LARGE = 10**6

    def sort_key(path):
        rel = os.path.relpath(path, start=base_parent).replace('/', '\\')
        id_ = extract_id_from_path(path)
        if id_ is not None and str(id_) in order_map:
            return (int(order_map[str(id_)]), rel)
        else:
            return (LARGE, rel)

    return sorted(file_list, key=sort_key)


# ----------------------
# Main flow
# ----------------------
# Normalize and check input folder
base_dir = os.path.abspath(carpeta_entrada)
print("Base dir usada:", base_dir)
if not os.path.isdir(base_dir):
    print(f"Error: carpeta de entrada '{carpeta_entrada}' no existe")
    sys.exit(1)

# Create ARC
arc = ARC()
arc.version = VERSION

# Debug: check add_file method
has_add_file = hasattr(arc, 'add_file')
print("ARC tiene add_file():", has_add_file)

# Collect files under carpeta_entrada
file_list = collect_files(carpeta_entrada)

# Find order JSON (prefer lib/ORDER_FILENAME)
order_path = get_order_file_path()
order_map = None
if order_path:
    try:
        print("Order JSON found at:", order_path)
        order_map = load_order_map_from_file(order_path)
        print("Loaded order mapping entries:", len(order_map))
        if order_map:
            file_list = sort_files_by_order(file_list, carpeta_entrada, order_map)
            print("Files sorted according to order mapping.")
    except Exception as e:
        print("Warning: could not load/parse order JSON:", e)
        print("Proceeding without custom ordering.")
else:
    print(f"No order JSON found at lib/{ORDER_FILENAME} or common fallbacks. Proceeding without custom ordering.")

# Add files into ARC in the (possibly reordered) sequence
add_files_to_arc(arc, carpeta_entrada, file_list)

# Save ARC
try:
    written = arc.export_arc()
    writeFile(arc_salida, written)
    print(f"ARC creado correctamente: {arc_salida}")
except Exception as e:
    print("Error al exportar/guardar ARC:", e)
    raise
