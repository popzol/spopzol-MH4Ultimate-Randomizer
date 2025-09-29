#THIS IS BASED OF DASDING'S CQ EDITOR, TRANSLATED INTO PYTHON BY CHATGPT I DO NOT UNDERSTAND SHIT ABOUT WHAT IS GOING ON, SO DON'T ASK ME
#ALL CREDIT ABOUT THIS CODE OBVIOUSLY GOES TO DASDING
import VariousLists
import os
import struct
import math
from pathlib import Path

MONSTER_STRUCT_SIZE = 0x28 # 40 bytes

def getQuestFolder():
    # Get the absolute path of the current script
    script_path = os.path.abspath(__file__)
    # Get the directory where the script is located
    base_folder = os.path.dirname(script_path)
    # Build the path to loc/quest
    target_folder = os.path.join(base_folder, "loc", "quest")
    return target_folder






# --- helper: count monsters inside large_monster_table ---
def count_large_monsters(questFilePath: str, safety_limit: int = 200):
    """
    Returns (table_addresses, counts_per_table, total_count).
    Each entry in table_addresses is an absolute address. counts_per_table is list of ints.
    """
    base_ptr_list_addr = read_dword(questFilePath, 0x28)
    table_addresses = read_dword_array_until_zero(questFilePath, base_ptr_list_addr)
    counts = []
    total = 0
    for a in table_addresses:
        cnt = 0
        idx = 0
        while True:
            off = a + idx * 0x28
            mid = read_dword(questFilePath, off)
            # termination: -1 / 0xFFFFFFFF
            if mid == 0xFFFFFFFF:
                break
            cnt += 1
            idx += 1
            if cnt >= safety_limit:
                # safety break to avoid infinite loop on corrupt files
                break
        counts.append(cnt)
        total += cnt
    return table_addresses, counts, total


def _read_bytes(path: str, offset: int, length: int) -> bytes:
    with open(path, "rb") as f:
        f.seek(offset)
        return f.read(length)

def read_byte(path: str, offset: int) -> int:
    return struct.unpack_from("<B", _read_bytes(path, offset, 1))[0]

def read_word(path: str, offset: int) -> int:
    return struct.unpack_from("<H", _read_bytes(path, offset, 2))[0]

def read_dword(path: str, offset: int) -> int:
    return struct.unpack_from("<I", _read_bytes(path, offset, 4))[0]

def read_float(path: str, offset: int) -> float:
    return struct.unpack_from("<f", _read_bytes(path, offset, 4))[0]

def read_dword_array_until_zero(path: str, offset: int):
    """Return Python list of dwords starting at offset until 0x00000000 encountered."""
    arr = []
    pos = offset
    while True:
        val = read_dword(path, pos)
        if val == 0:
            break
        arr.append(val)
        pos += 4
    return arr

def read_word_array(path: str, offset: int, count: int):
    arr = []
    pos = offset
    for i in range(count):
        arr.append(read_word(path, pos))
        pos += 2
    return arr

def read_string_utf16le_pair(path: str, offset: int) -> str:
    """Read string encoded as pairs of bytes (UTF-16LE-like), terminated by 0x0000 pair."""
    s = []
    pos = offset
    while True:
        two = _read_bytes(path, pos, 2)
        if len(two) < 2:
            break
        if two == b'\x00\x00':
            break
        # interpret as little-endian uint16 -> code point
        cp = struct.unpack_from("<H", two)[0]
        s.append(chr(cp))
        pos += 2
    return "".join(s)

# ----- header / dynamic header helpers -----
def get_header_addr(questFilePath: str) -> int:
    """Return the absolute header pointer stored at 0x00."""
    return read_dword(questFilePath, 0x00)

def get_dynamic_absolute_offset(questFilePath: str, code_relative_offset: int) -> int:
    """
    The JS code computes: header_offset = read_dword(0x0) - 0xA0
    and then reads at (header_offset + N) in their code.
    That resolves to absolute: header_addr + (N - 0xA0).
    So given an N (the same N used in their code), this returns the real absolute offset.
    """
    header_addr = get_header_addr(questFilePath)
    return header_addr + (code_relative_offset - 0xA0)

# Convenience wrappers to write primitive types into the file using your existing safe writer
def write_byte_at(path: str, offset: int, value: int):
    changeByteAtOffset_For_In(offset, bytes([value & 0xFF]), path)

def write_word_at(path: str, offset: int, value: int):
    b = struct.pack("<H", value & 0xFFFF)
    changeByteAtOffset_For_In(offset, b, path)

def write_dword_at(path: str, offset: int, value: int):
    b = struct.pack("<I", value & 0xFFFFFFFF)
    changeByteAtOffset_For_In(offset, b, path)

def write_float_at(path: str, offset: int, value: float):
    b = struct.pack("<f", float(value))
    changeByteAtOffset_For_In(offset, b, path)

# ----- High-level header editors (dynamic) -----
def set_quest_type(questFilePath: str, quest_type: int):
    """Set quest_type (JS used header_offset + 0xA0)."""
    abs_off = get_dynamic_absolute_offset(questFilePath, 0xA0)
    write_byte_at(questFilePath, abs_off, quest_type)

def set_header_flag_bit(questFilePath: str, code_relative_offset: int, bit_index: int, value: bool):
    """
    Set/clear a bit in one of the header bit fields.
    code_relative_offset: the same constant used in the JS code (e.g. 0xA1 or 0xA2 or 0xA3)
    """
    abs_off = get_dynamic_absolute_offset(questFilePath, code_relative_offset)
    cur = read_byte(questFilePath, abs_off)
    if value:
        cur = cur | (1 << bit_index)
    else:
        cur = cur & ~(1 << bit_index)
    write_byte_at(questFilePath, abs_off, cur)

def set_fee(questFilePath: str, fee_value: int):
    abs_off = get_dynamic_absolute_offset(questFilePath, 0xA4)
    write_dword_at(questFilePath, abs_off, fee_value)

def set_reward_main(questFilePath: str, reward_value: int):
    abs_off = get_dynamic_absolute_offset(questFilePath, 0xA8)
    write_dword_at(questFilePath, abs_off, reward_value)

def set_time_limit(questFilePath: str, seconds: int):
    abs_off = get_dynamic_absolute_offset(questFilePath, 0xB4)
    write_dword_at(questFilePath, abs_off, seconds)

def set_map_id_dynamic(questFilePath: str, map_id: int):
    """Set map id using the dynamic header offset (JS used header_offset + 0xC4)"""
    abs_off = get_dynamic_absolute_offset(questFilePath, 0xC4)
    write_byte_at(questFilePath, abs_off, map_id)

def set_quest_id(questFilePath: str, quest_id: int):
    abs_off = get_dynamic_absolute_offset(questFilePath, 0xC0)
    write_word_at(questFilePath, abs_off, quest_id)

def set_objective_qty(questFilePath: str, objective_index: int, qty: int):
    """
    objective_index: 0,1 or 'sub' (if you want objective_sub use 'sub' or index 2)
    The JS code stores objectives at header_offset + 0xCC (obj0), +0xD4 (obj1), +0xDC (obj_sub).
    We'll accept index 0/1/2 mapping to those offsets.
    """
    mapping = {0: 0xCC, 1: 0xD4, 2: 0xDC}
    if objective_index not in mapping:
        raise ValueError("objective_index must be 0,1 or 2")
    base_off = get_dynamic_absolute_offset(questFilePath, mapping[objective_index])
    # qty is a word inside objective struct at offset +6 in parse_objective
    write_word_at(questFilePath, base_off + 6, qty)


    # ----- Objective helpers (añadir en py, en la zona de header helpers) -----
_OBJECTIVE_BASES = {0: 0xCC, 1: 0xD4, 2: 0xDC}

def get_header_offset_dynamic(questFilePath: str) -> int:
    header_addr = read_dword(questFilePath, 0x00)
    return header_addr - 0xA0

def set_objective(questFilePath: str, index: int, type_val: int, target_id: int, qty: int):
    if index not in _OBJECTIVE_BASES:
        raise IndexError("set_objective: index must be 0,1 or 2")
    header_off = get_header_offset_dynamic(questFilePath)
    base = header_off + _OBJECTIVE_BASES[index]
    size = os.path.getsize(questFilePath)
    if base < 0 or base + 8 > size:
        raise EOFError(f"set_objective: header objective {index} outside file bounds (off 0x{base:X}, size 0x{size:X})")
    # type = dword, target_id = word, qty = word
    write_dword_at(questFilePath, base, int(type_val) & 0xFFFFFFFF)
    write_word_at(questFilePath, base + 4, int(target_id) & 0xFFFF)
    write_word_at(questFilePath, base + 6, int(qty) & 0xFFFF)

def get_objective(questFilePath: str, index: int):
    if index not in _OBJECTIVE_BASES:
        raise IndexError("get_objective: index must be 0,1 or 2")
    header_off = get_header_offset_dynamic(questFilePath)
    base = header_off + _OBJECTIVE_BASES[index]
    size = os.path.getsize(questFilePath)
    if base < 0 or base + 8 > size:
        raise EOFError("get_objective: fuera de fichero")
    t = read_dword(questFilePath, base)
    targ = read_word(questFilePath, base + 4)
    q = read_word(questFilePath, base + 6)
    return {'type': t, 'target_id': targ, 'qty': q}

def set_objective_amount(questFilePath: str, amount: int):
    if not (0 <= amount <= 0xFF):
        raise ValueError("set_objective_amount: amount must be 0..255")
    header_off = get_header_offset_dynamic(questFilePath)
    off = header_off + 0xCB
    size = os.path.getsize(questFilePath)
    if off < 0 or off + 1 > size:
        raise EOFError("set_objective_amount: fuera de fichero")
    write_byte_at(questFilePath, off, amount)

# ----- Refills (absolute offsets in JS: 0x0C + 8*i) -----
def set_refill_entry(questFilePath: str, index: int, box: int, condition: int, monster: int, qty: int):
    """
    index: 0 or 1
    layout (JS parse_refills): box @ 0x0C + 8*i, condition @ 0x0D + 8*i, monster @ 0x0E + 8*i, qty @ 0x10 + 8*i
    """
    assert index in (0, 1)
    base = 0x0C + 8 * index
    write_byte_at(questFilePath, base + 0, box)
    write_byte_at(questFilePath, base + 1, condition)
    write_byte_at(questFilePath, base + 2, monster)
    write_byte_at(questFilePath, base + 4, qty)

# ----- Small monster conditions (absolute base 0x64, two entries) -----
def set_small_monster_condition(questFilePath: str, which: int, type_val: int = None, target: int = None, qty: int = None, group: int = None):
    """
    which: 0 or 1
    structure per parse_small_monster_conditions:
      type = byte at base + 0 + 8*i
      target = word at base + 4 + 8*i
      qty = byte at base + 6 + 8*i
      group = byte at base + 7 + 8*i
    """
    assert which in (0, 1)
    base = 0x64 + 8 * which
    if type_val is not None:
        write_byte_at(questFilePath, base + 0, type_val)
    if target is not None:
        write_word_at(questFilePath, base + 4, target)
    if qty is not None:
        write_byte_at(questFilePath, base + 6, qty)
    if group is not None:
        write_byte_at(questFilePath, base + 7, group)

# ----- Monster struct write helper (monster struct size = 0x28) -----
def pack_monster_struct(monster: dict) -> bytes:
    """
    monster dict fields:
      monster_id (int), qty (int),
      condition (int), area (int), crashflag (int), special (int),
      unk2 (int), unk3 (int), unk4 (int), infection (int),
      x (float), y (float), z (float),
      x_rot (int), y_rot (int), z_rot (int)
    Returns packed 40-byte struct (<II8B3f3I)
    """
    # default missing values to 0
    monster_id = int(monster.get("monster_id", 0))
    qty = int(monster.get("qty", 0))
    b = [int(monster.get(k, 0)) for k in ("condition", "area", "crashflag", "special", "unk2", "unk3", "unk4", "infection")]
    x = float(monster.get("x", 0.0))
    y = float(monster.get("y", 0.0))
    z = float(monster.get("z", 0.0))
    x_rot = int(monster.get("x_rot", 0))
    y_rot = int(monster.get("y_rot", 0))
    z_rot = int(monster.get("z_rot", 0))
    fmt = "<II8BfffIII"
    return struct.pack(fmt, monster_id, qty, *b, x, y, z, x_rot, y_rot, z_rot)

def write_monster_struct_at(questFilePath: str, absolute_offset: int, monster: dict):
    """Write a monster struct (40 bytes) at absolute offset."""
    data = pack_monster_struct(monster)
    changeByteAtOffset_For_In(absolute_offset, data, questFilePath)

# ----- High-level: write monster into large monster table by indices -----
def write_monster_in_large_table(questFilePath: str, table_index: int, monster_index: int, monster: dict):
    """
    table_index: which top-array entry (0-based) read from pointer at 0x28
    monster_index: index inside that monster array (0-based)
    This uses the structure: base = read_dword(0x28) -> read_dword_array_until_zero(base) -> pick entry
    """
    base_ptr_list_addr = read_dword(questFilePath, 0x28)
    table_addresses = read_dword_array_until_zero(questFilePath, base_ptr_list_addr)
    if table_index >= len(table_addresses):
        raise IndexError("table_index out of range")
    monster_array_addr = table_addresses[table_index]
    absolute_offset = monster_array_addr + monster_index * 0x28
    write_monster_struct_at(questFilePath, absolute_offset, monster)

# ----- Small monster table / unstable table helpers (read addresses) -----
def get_large_monster_table_addresses(questFilePath: str):
    base_ptr_list_addr = read_dword(questFilePath, 0x28)
    return read_dword_array_until_zero(questFilePath, base_ptr_list_addr)

def get_small_monster_table_addresses(questFilePath: str):
    base_ptr_list_addr = read_dword(questFilePath, 0x2C)
    return read_dword_array_until_zero(questFilePath, base_ptr_list_addr)

def get_unstable_monster_table_base(questFilePath: str):
    return read_dword(questFilePath, 0x30)

# ----- Loot pointer setters (pointers stored at absolute offsets 0x1C,0x20,0x24) -----
def set_loot_table_pointer(questFilePath: str, which: str, pointer_addr: int):
    """
    which: 'a'|'b'|'c'
    pointer_addr: absolute file offset where the loot top-table begins
    """
    mapping = {'a': 0x1C, 'b': 0x20, 'c': 0x24}
    if which not in mapping:
        raise ValueError("which must be 'a','b' or 'c'")
    write_dword_at(questFilePath, mapping[which], pointer_addr)

# ----- Meta table writers -----
def write_meta_entry(questFilePath: str, idx: int, size: int = None, size_var: int = None, hp: int = None,
                     atk: int = None, break_res: int = None, stamina: int = None, status_res: int = None):
    """
    Write one entry to meta_table at base 0x34 + idx*8
    fields: size (word), size_var (byte at +2), hp (+3), atk(+4), break_res(+5), stamina(+6), status_res(+7)
    """
    base = 0x34 + idx * 8
    if size is not None:
        write_word_at(questFilePath, base, size)
    if size_var is not None:
        write_byte_at(questFilePath, base + 2, size_var)
    if hp is not None:
        write_byte_at(questFilePath, base + 3, hp)
    if atk is not None:
        write_byte_at(questFilePath, base + 4, atk)
    if break_res is not None:
        write_byte_at(questFilePath, base + 5, break_res)
    if stamina is not None:
        write_byte_at(questFilePath, base + 6, stamina)
    if status_res is not None:
        write_byte_at(questFilePath, base + 7, status_res)

# ----- Small meta writer (base 0x5C) -----
def write_small_meta(questFilePath: str, size: int = None, unk0: int = None, hp: int = None, atk: int = None,
                     break_res: int = None, stamina: int = None, unk2: int = None):
    base = 0x5C
    if size is not None:
        write_word_at(questFilePath, base, size)
    if unk0 is not None:
        write_byte_at(questFilePath, base + 1, unk0)
    if hp is not None:
        write_byte_at(questFilePath, base + 3, hp)
    if atk is not None:
        write_byte_at(questFilePath, base + 4, atk)
    if break_res is not None:
        write_byte_at(questFilePath, base + 5, break_res)
    if stamina is not None:
        write_byte_at(questFilePath, base + 6, stamina)
    if unk2 is not None:
        write_byte_at(questFilePath, base + 7, unk2)


# ---------------------------
# Additional editor helpers:
# write_loot_table, write_supplies, pretty_print_quest_summary,
# find_and_replace_monster, verify_tables
# ---------------------------


def append_aligned(path: str, data: bytes, align: int = 0x10) -> int:
    """Append data to file aligned to `align`. Return absolute address where data was written."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "r+b") as f:
        f.seek(0, 2)
        length = f.tell()
        pad = (align - (length % align)) % align
        if pad:
            f.write(b'\x00' * pad)
        addr = f.tell()
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    print(f"[DEBUG] Appended {len(data)} bytes at 0x{addr:X} (pad {pad} bytes)")
    return addr

# ---------- WRITE LOOT TABLE ----------
def write_loot_table(questFilePath: str, which: str, loot_top: list):
    """
    Write a loot table to the file and update pointer at offsets:
      which: 'a' -> 0x1C, 'b' -> 0x20, 'c' -> 0x24
    loot_top: list of { 'flag': int, 'items': [ {'chance': int, 'item_id': int, 'qty': int}, ... ] }
    The function will append the necessary item tables and a top-table at EOF (aligned), then store pointer.
    """
    mapping = {'a': 0x1C, 'b': 0x20, 'c': 0x24}
    if which not in mapping:
        raise ValueError("which must be 'a','b' or 'c'")

    # 1) Build item tables and register their addresses
    item_table_addrs = []
    item_table_bytes_all = b''
    for table in loot_top:
        items = table.get('items', [])
        b = bytearray()
        for it in items:
            chance = int(it.get('chance', 0)) & 0xFFFF
            item_id = int(it.get('item_id', 0)) & 0xFFFF
            qty = int(it.get('qty', 0)) & 0xFFFF
            b += struct.pack("<HHH", chance, item_id, qty)
        # terminator for item table: chance == 0xFFFF (word)
        b += struct.pack("<H", 0xFFFF)
        # append aligned and record address
        addr = append_aligned(questFilePath, bytes(b))
        item_table_addrs.append(addr)

    # 2) Build top-table: each entry = dword(flag) + dword(item_table_addr)
    top_bytes = bytearray()
    for idx, table in enumerate(loot_top):
        flag = int(table.get('flag', 0)) & 0xFFFFFFFF
        top_bytes += struct.pack("<I", flag)
        top_bytes += struct.pack("<I", item_table_addrs[idx] & 0xFFFFFFFF)
    # append terminator dword 0x00000000
    top_bytes += struct.pack("<I", 0)
    top_addr = append_aligned(questFilePath, bytes(top_bytes))

    # 3) write pointer into appropriate offset (dword)
    write_dword_at(questFilePath, mapping[which], top_addr)
    print(f"[INFO] Wrote loot table '{which}' top at 0x{top_addr:X} with {len(loot_top)} entries")
    return top_addr

# ---------- WRITE SUPPLIES ----------
def write_supplies(questFilePath: str, supplies_top: list):
    """
    supplies_top: list of lists. Each inner list is list of {'item_id': int, 'qty': int}
    The function will append each item list, then a top-table (8-byte entries) and write a dword pointer at 0x08.
    Top entry layout (8 bytes):
      byte 0 = table_idx (we'll use sequential index),
      byte 1 = length (num items),
      word 2 = filler (0),
      dword 4 = addr (pointer to item_table)
    The item_table entries each are word(item_id) + word(qty). End item_table with word 0 (item_id==0).
    """
    item_table_addrs = []
    for table in supplies_top:
        b = bytearray()
        for it in table:
            item_id = int(it.get('item_id', 0)) & 0xFFFF
            qty = int(it.get('qty', 0)) & 0xFFFF
            b += struct.pack("<HH", item_id, qty)
        # terminator item_id == 0
        b += struct.pack("<H", 0)
        addr = append_aligned(questFilePath, bytes(b))
        item_table_addrs.append((len(table), addr))

    # build top_table
    top = bytearray()
    for idx, (length, addr) in enumerate(item_table_addrs):
        # pack as: B (idx), B (length), H (0 filler), I (addr)
        top += struct.pack("<BBHI", idx & 0xFF, length & 0xFF, 0, addr & 0xFFFFFFFF)
    # add a final 0xFF byte like the JS did (not strictly necessary, but harmless)
    top += b'\xFF'
    top_addr = append_aligned(questFilePath, bytes(top))

    # write pointer (dword) to 0x08
    write_dword_at(questFilePath, 0x08, top_addr)
    print(f"[INFO] Wrote supplies top at 0x{top_addr:X} with {len(item_table_addrs)} tables")
    return top_addr

# === START: standalone parse_mib + pretty_print_quest_summary ===


def _load_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

# low-level readers working on a bytes buffer
def _read_byte(buf: bytes, offset: int) -> int:
    return struct.unpack_from("<B", buf, offset)[0]

def _read_word(buf: bytes, offset: int) -> int:
    return struct.unpack_from("<H", buf, offset)[0]

import os, struct

def _read_dword(path: str, offset: int) -> int:
    """Safe read of 4 bytes dword from file path at offset. Raises informative EOFError if out-of-bounds."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"read_dword: file not found: {path}")
    size = os.path.getsize(path)
    if offset < 0 or offset + 4 > size:
        raise EOFError(f"read_dword: attempt to read 4 bytes at offset 0x{offset:X} but file size is 0x{size:X}")
    with open(path, "rb") as f:
        f.seek(offset)
        b = f.read(4)
        if len(b) < 4:
            raise EOFError(f"read_dword: short read at 0x{offset:X}")
        return struct.unpack_from("<I", b, 0)[0]

def _read_float(buf: bytes, offset: int) -> float:
    return struct.unpack_from("<f", buf, offset)[0]

def _read_bytes(buf: bytes, offset: int, length: int) -> bytes:
    return buf[offset:offset+length]

def _read_word_array(buf: bytes, offset: int, count: int):
    return [_read_word(buf, offset + i*2) for i in range(count)]

def _read_bytes(path: str, offset: int, length: int) -> bytes:
    """
    Minimal file-reader used by read_* helpers.
    Accepts a file path and returns `length` bytes starting at `offset`.
    This must exist and accept (path, offset, length) — the TypeError shows it was
    shadowed or removed, so re-instate it in the module global scope.
    """
    with open(path, "rb") as f:
        f.seek(offset)
        return f.read(length)

def _read_dword_array_until_zero(buf: bytes, offset: int):
    arr = []
    pos = offset
    size = len(buf)
    while pos + 4 <= size:
        v = _read_dword(buf, pos)
        if v == 0:
            break
        arr.append(v)
        pos += 4
    return arr


def unpack_monster_struct(monster_bytes: bytes) -> dict:
    """Desempaqueta una estructura de monstruo de 0x28 bytes a un diccionario."""
    if len(monster_bytes) != 0x28:
        raise ValueError(f"Monster struct must be 0x28 bytes, got {len(monster_bytes)}")
    monster = {}
    monster['monster_id'] = struct.unpack_from("<I", monster_bytes, 0x00)[0]
    monster['qty'] = struct.unpack_from("<I", monster_bytes, 0x04)[0]
    monster['condition'] = monster_bytes[0x08]
    monster['area'] = monster_bytes[0x09]
    monster['crashflag'] = monster_bytes[0x0A]
    monster['special'] = monster_bytes[0x0B]
    monster['unk2'] = monster_bytes[0x0C]
    monster['unk3'] = monster_bytes[0x0D]
    monster['unk4'] = monster_bytes[0x0E]
    monster['infection'] = monster_bytes[0x0F]
    monster['x'] = struct.unpack_from("<f", monster_bytes, 0x10)[0]
    monster['y'] = struct.unpack_from("<f", monster_bytes, 0x14)[0]
    monster['z'] = struct.unpack_from("<f", monster_bytes, 0x18)[0]
    monster['x_rot'] = struct.unpack_from("<I", monster_bytes, 0x1C)[0]
    monster['y_rot'] = struct.unpack_from("<I", monster_bytes, 0x20)[0]
    monster['z_rot'] = struct.unpack_from("<I", monster_bytes, 0x24)[0]

    return monster

# ----------------------------
# Map / Area getters & setters
# ----------------------------
def getMap(questFilePath: str) -> int:
    """
    Devuelve el map id (byte) leído desde el header dinámico (offset code-relative 0xC4).
    Resultado en decimal (0..255).
    """
    abs_off = get_dynamic_absolute_offset(questFilePath, 0xC4)
    size = os.path.getsize(questFilePath)
    if abs_off < 0 or abs_off + 1 > size:
        raise EOFError(f"getMap: offset 0x{abs_off:X} fuera de rango (size 0x{size:X})")
    return read_byte(questFilePath, abs_off)


def setMap(questFilePath: str, map_id: int):
    """
    Escribe el map id (0..255) en el header dinámico (code-relative 0xC4).
    map_id debe ser un int decimal.
    """
    if not (0 <= map_id <= 0xFF):
        raise ValueError("setMap: map_id debe estar entre 0 y 255")
    abs_off = get_dynamic_absolute_offset(questFilePath, 0xC4)
    size = os.path.getsize(questFilePath)
    if abs_off < 0 or abs_off + 1 > size:
        raise EOFError(f"setMap: offset 0x{abs_off:X} fuera de rango (size 0x{size:X})")
    write_byte_at(questFilePath, abs_off, map_id)


# Helper genérico: devuelve/pon el byte 'area' dentro de una struct de monstruo absoluta
def _get_area_at_monster_struct_offset(questFilePath: str, monster_struct_abs_off: int) -> int:
    size = os.path.getsize(questFilePath)
    area_byte_off = monster_struct_abs_off + 0x09  # offset dentro de struct
    if monster_struct_abs_off < 0 or area_byte_off + 1 > size:
        raise EOFError(f"_get_area_at_monster_struct_offset: offset 0x{monster_struct_abs_off:X} fuera de rango (size 0x{size:X})")
    return read_byte(questFilePath, area_byte_off)

def _set_area_at_monster_struct_offset(questFilePath: str, monster_struct_abs_off: int, area: int):
    if not (0 <= area <= 0xFF):
        raise ValueError("_set_area_at_monster_struct_offset: area debe estar entre 0 y 255")
    size = os.path.getsize(questFilePath)
    area_byte_off = monster_struct_abs_off + 0x09
    if monster_struct_abs_off < 0 or area_byte_off + 1 > size:
        raise EOFError(f"_set_area_at_monster_struct_offset: offset 0x{monster_struct_abs_off:X} fuera de rango (size 0x{size:X})")
    write_byte_at(questFilePath, area_byte_off, area)


# Large monsters: acceso por (table_index, monster_index)
def getArea_large(questFilePath: str, table_index: int, monster_index: int) -> int:
    """
    Devuelve la 'area' (subzona) del monstruo en la tabla grande:
      table_index: índice de la tabla top (0-based)
      monster_index: índice dentro de esa tabla (0-based)
    Resultado en decimal.
    """
    size = os.path.getsize(questFilePath)
    base_ptr_list_addr = read_dword(questFilePath, 0x28)
    if base_ptr_list_addr == 0:
        raise ValueError("getArea_large: large table pointer (0x28) == 0")
    tables = read_dword_array_until_zero(questFilePath, base_ptr_list_addr)
    if table_index < 0 or table_index >= len(tables):
        raise IndexError("getArea_large: table_index fuera de rango")
    table_addr = tables[table_index]
    monster_off = table_addr + monster_index * 0x28
    # comprobar terminador y bounds
    if monster_off + 4 > size:
        raise EOFError("getArea_large: monster offset fuera de fichero")
    mid = read_dword(questFilePath, monster_off)
    if mid == 0xFFFFFFFF:
        raise ValueError("getArea_large: monster_index apunta al terminador (0xFFFFFFFF)")
    return _get_area_at_monster_struct_offset(questFilePath, monster_off)


def setArea_large(questFilePath: str, table_index: int, monster_index: int, area: int):
    """
    Escribe la 'area' (0..255) para un monstruo de la tabla large.
    """
    size = os.path.getsize(questFilePath)
    base_ptr_list_addr = read_dword(questFilePath, 0x28)
    if base_ptr_list_addr == 0:
        raise ValueError("setArea_large: large table pointer (0x28) == 0")
    tables = read_dword_array_until_zero(questFilePath, base_ptr_list_addr)
    if table_index < 0 or table_index >= len(tables):
        raise IndexError("setArea_large: table_index fuera de rango")
    table_addr = tables[table_index]
    monster_off = table_addr + monster_index * 0x28
    if monster_off + 4 > size:
        raise EOFError("setArea_large: monster offset fuera de fichero")
    mid = read_dword(questFilePath, monster_off)
    if mid == 0xFFFFFFFF:
        raise ValueError("setArea_large: monster_index apunta al terminador (0xFFFFFFFF)")
    _set_area_at_monster_struct_offset(questFilePath, monster_off, area)


# Small monsters: acceso por (top_index, sub_index, monster_index)
def getArea_small(questFilePath: str, top_index: int, sub_index: int, monster_index: int) -> int:
    """
    Devuelve la 'area' para un monstruo en small table.
      top_index: índice en la top-list (0-based)
      sub_index: índice en la sub-list dentro del top (0-based)
      monster_index: índice dentro de esa sub-list (0-based)
    """
    base_small_ptr = read_dword(questFilePath, 0x2C)
    if base_small_ptr == 0:
        raise ValueError("getArea_small: small table pointer (0x2C) == 0")
    tops = read_dword_array_until_zero(questFilePath, base_small_ptr)
    if top_index < 0 or top_index >= len(tops):
        raise IndexError("getArea_small: top_index fuera de rango")
    top_addr = tops[top_index]
    subs = read_dword_array_until_zero(questFilePath, top_addr)
    if sub_index < 0 or sub_index >= len(subs):
        raise IndexError("getArea_small: sub_index fuera de rango")
    sub_addr = subs[sub_index]
    monster_off = sub_addr + monster_index * 0x28
    size = os.path.getsize(questFilePath)
    if monster_off + 4 > size:
        raise EOFError("getArea_small: monster offset fuera de fichero")
    mid = read_dword(questFilePath, monster_off)
    if mid == 0xFFFFFFFF:
        raise ValueError("getArea_small: monster_index apunta al terminador (0xFFFFFFFF)")
    return _get_area_at_monster_struct_offset(questFilePath, monster_off)


def setArea_small(questFilePath: str, top_index: int, sub_index: int, monster_index: int, area: int):
    """
    Escribe la 'area' para un monstruo en small table.
    """
    base_small_ptr = read_dword(questFilePath, 0x2C)
    if base_small_ptr == 0:
        raise ValueError("setArea_small: small table pointer (0x2C) == 0")
    tops = read_dword_array_until_zero(questFilePath, base_small_ptr)
    if top_index < 0 or top_index >= len(tops):
        raise IndexError("setArea_small: top_index fuera de rango")
    top_addr = tops[top_index]
    subs = read_dword_array_until_zero(questFilePath, top_addr)
    if sub_index < 0 or sub_index >= len(subs):
        raise IndexError("setArea_small: sub_index fuera de rango")
    sub_addr = subs[sub_index]
    monster_off = sub_addr + monster_index * 0x28
    size = os.path.getsize(questFilePath)
    if monster_off + 4 > size:
        raise EOFError("setArea_small: monster offset fuera de fichero")
    mid = read_dword(questFilePath, monster_off)
    if mid == 0xFFFFFFFF:
        raise ValueError("setArea_small: monster_index apunta al terminador (0xFFFFFFFF)")
    _set_area_at_monster_struct_offset(questFilePath, monster_off, area)


# Unstable table: acceso por índice (0-based)
def getArea_unstable(questFilePath: str, unstable_index: int) -> int:
    """
    Devuelve la 'area' del monstruo en unstable table por índice.
    """
    base_unstable = read_dword(questFilePath, 0x30)
    if base_unstable == 0:
        raise ValueError("getArea_unstable: unstable table pointer (0x30) == 0")
    entry_off = base_unstable + unstable_index * 0x2C
    size = os.path.getsize(questFilePath)
    if entry_off + 4 > size:
        raise EOFError("getArea_unstable: entrada fuera de fichero")
    chance = read_word(questFilePath, entry_off)
    if chance == 0xFFFF:
        raise ValueError("getArea_unstable: entrada terminadora (0xFFFF)")
    monster_off = entry_off + 4
    if monster_off + 4 > size:
        raise EOFError("getArea_unstable: monster struct fuera de fichero")
    return _get_area_at_monster_struct_offset(questFilePath, monster_off)


def setArea_unstable(questFilePath: str, unstable_index: int, area: int):
    """
    Escribe la 'area' en unstable table por índice.
    """
    base_unstable = read_dword(questFilePath, 0x30)
    if base_unstable == 0:
        raise ValueError("setArea_unstable: unstable table pointer (0x30) == 0")
    entry_off = base_unstable + unstable_index * 0x2C
    size = os.path.getsize(questFilePath)
    if entry_off + 4 > size:
        raise EOFError("setArea_unstable: entrada fuera de fichero")
    chance = read_word(questFilePath, entry_off)
    if chance == 0xFFFF:
        raise ValueError("setArea_unstable: entrada terminadora (0xFFFF)")
    monster_off = entry_off + 4
    if monster_off + 4 > size:
        raise EOFError("setArea_unstable: monster struct fuera de fichero")
    _set_area_at_monster_struct_offset(questFilePath, monster_off, area)




def expand_large_monster_table(questFilePath: str, table_index: int = 0, new_monster_id: int = 1):
    if not os.path.exists(questFilePath):
        raise FileNotFoundError(f"File not found: {questFilePath}")
    # 1. Obtener las direcciones de las tablas de monstruos grandes
    base_ptr_list_addr = read_dword(questFilePath, 0x28)
    table_addresses = read_dword_array_until_zero(questFilePath, base_ptr_list_addr)
    if table_index >= len(table_addresses):
        raise IndexError(f"Table index {table_index} out of range. Available tables: {len(table_addresses)}")
    current_table_addr = table_addresses[table_index]
    # 2. Leer todos los monstruos de la tabla actual (hasta encontrar 0xFFFFFFFF)
    monsters = []
    idx = 0
    while True:
        offset = current_table_addr + idx * 0x28
        monster_id = read_dword(questFilePath, offset)
        if monster_id == 0xFFFFFFFF:
            break
        # Leer la estructura completa del monstruo
        monster_data = _read_bytes(questFilePath, offset, 0x28)
        monsters.append(monster_data)
        idx += 1
        # Límite de seguridad
        if idx > 1000:
            break
    if len(monsters) == 0:
        raise ValueError("No monsters found in the specified table")
    # 3. Crear nuevo monstruo copiando el primero pero con nueva ID
    first_monster = monsters[0]
    # Desempaquetar la estructura para modificar el monster_id
    monster_dict = unpack_monster_struct(first_monster)
    monster_dict['monster_id'] = new_monster_id
    # 4. Crear el nuevo array de monstruos
    new_table_data = b''
    # Añadir todos los monstruos originales
    for monster in monsters:
        new_table_data += monster
    # Añadir el nuevo monstruo
    new_table_data += pack_monster_struct(monster_dict)
    # Añadir terminador
    new_table_data += struct.pack("<I", 0xFFFFFFFF)
    # 5. Escribir la nueva tabla al final del archivo (alineado)
    new_table_addr = append_aligned(questFilePath, new_table_data)
    # 6. Actualizar el puntero en la top-table
    # La top-table está en base_ptr_list_addr, y cada entrada son 4 bytes
    pointer_offset = base_ptr_list_addr + table_index * 4
    write_dword_at(questFilePath, pointer_offset, new_table_addr)
    print(f"[SUCCESS] Expanded large monster table {table_index}")
    print(f"          Original table at: 0x{current_table_addr:X}")
    print(f"          New table at: 0x{new_table_addr:X}")
    print(f"          Added monster with ID: 0x{new_monster_id:X}")
    print(f"          Total monsters in table: {len(monsters) + 1}")
    return new_table_addr
# parse helpers for structures
def _parse_monster_from_buf(buf: bytes, offset: int):
    m = {}
    m['monster_id'] = _read_dword(buf, offset + 0x00)
    m['qty'] = _read_dword(buf, offset + 0x04)
    m['condition'] = _read_byte(buf, offset + 0x08)
    m['area'] = _read_byte(buf, offset + 0x09)
    m['crashflag'] = _read_byte(buf, offset + 0x0A)
    m['special'] = _read_byte(buf, offset + 0x0B)
    m['unk2'] = _read_byte(buf, offset + 0x0C)
    m['unk3'] = _read_byte(buf, offset + 0x0D)
    m['unk4'] = _read_byte(buf, offset + 0x0E)
    m['infection'] = _read_byte(buf, offset + 0x0F)
    m['x'] = _read_float(buf, offset + 0x10)
    m['y'] = _read_float(buf, offset + 0x14)
    m['z'] = _read_float(buf, offset + 0x18)
    m['x_rot'] = _read_dword(buf, offset + 0x1C)
    m['y_rot'] = _read_dword(buf, offset + 0x20)
    m['z_rot'] = _read_dword(buf, offset + 0x24)
    return m


# ----------------------------
# Find instances + get positions
# ----------------------------
def find_monster_instances(path: str, monster_id: int):
    """
    Busca todas las apariciones del monster_id en:
      - large tables (top-list en 0x28 -> array de punteros a arrays de structs)
      - small tables (top-list en 0x2C -> array de punteros a tops -> punteros a arrays de structs)
      - unstable table (puntero en 0x30, stride 0x2C)
    Devuelve lista de dicts con:
      { 'type': 'large'|'small'|'unstable',
        'table_index': int or None,
        'sub_index': int or None,
        'monster_index': int,
        'struct_offset': absolute_offset,
        'x': float, 'y': float, 'z': float }
    """
    size = os.path.getsize(path)
    results = []

    # --- large tables ---
    try:
        lbase = read_dword(path, 0x28)
    except Exception:
        lbase = 0
    if lbase != 0 and 0 <= lbase < size:
        top_addrs = read_dword_array_until_zero(path, lbase)
        for t_idx, table_addr in enumerate(top_addrs):
            if table_addr == 0 or table_addr >= size:
                continue
            idx = 0
            while True:
                off = table_addr + idx * 0x28
                if off + 4 > size:
                    # fin por archivo
                    break
                mid = read_dword(path, off)
                if mid == 0xFFFFFFFF:
                    break
                if mid == monster_id:
                    # leer coords
                    x = read_float(path, off + 0x10)
                    y = read_float(path, off + 0x14)
                    z = read_float(path, off + 0x18)
                    results.append({
                        'type': 'large',
                        'table_index': t_idx,
                        'sub_index': None,
                        'monster_index': idx,
                        'struct_offset': off,
                        'x': x, 'y': y, 'z': z
                    })
                idx += 1
                if idx > 2000:
                    break

    # --- small tables (dos niveles) ---
    try:
        sbase = read_dword(path, 0x2C)
    except Exception:
        sbase = 0
    if sbase != 0 and 0 <= sbase < size:
        top_ptrs = read_dword_array_until_zero(path, sbase)
        for top_idx, top_addr in enumerate(top_ptrs):
            if top_addr == 0 or top_addr >= size:
                continue
            sub_ptrs = read_dword_array_until_zero(path, top_addr)
            for sub_idx, sub_addr in enumerate(sub_ptrs):
                if sub_addr == 0 or sub_addr >= size:
                    continue
                idx = 0
                while True:
                    off = sub_addr + idx * 0x28
                    if off + 4 > size:
                        break
                    mid = read_dword(path, off)
                    if mid == 0xFFFFFFFF:
                        break
                    if mid == monster_id:
                        x = read_float(path, off + 0x10)
                        y = read_float(path, off + 0x14)
                        z = read_float(path, off + 0x18)
                        results.append({
                            'type': 'small',
                            'table_index': top_idx,
                            'sub_index': sub_idx,
                            'monster_index': idx,
                            'struct_offset': off,
                            'x': x, 'y': y, 'z': z
                        })
                    idx += 1
                    if idx > 2000:
                        break

    # --- unstable table ---
    try:
        ubase = read_dword(path, 0x30)
    except Exception:
        ubase = 0
    if ubase != 0 and 0 <= ubase < size:
        idx = 0
        while True:
            entry_off = ubase + idx * 0x2C
            if entry_off + 2 > size:
                break
            chance = read_word(path, entry_off)
            if chance == 0xFFFF:
                break
            monster_off = entry_off + 4
            if monster_off + 4 > size:
                break
            mid = read_dword(path, monster_off)
            if mid == monster_id:
                x = read_float(path, monster_off + 0x10)
                y = read_float(path, monster_off + 0x14)
                z = read_float(path, monster_off + 0x18)
                results.append({
                    'type': 'unstable',
                    'table_index': None,
                    'sub_index': idx,
                    'monster_index': None,
                    'struct_offset': monster_off,
                    'x': x, 'y': y, 'z': z
                })
            idx += 1
            if idx > 2000:
                break

    return results

def set_monster_position_by_id(path: str, monster_id: int, new_x=None, new_z=None, apply_to='all'):
    """
    Cambia la posición X/Z de las apariciones del monster_id.
    - new_x, new_z: float o None (None = no tocar esa coordenada).
    - apply_to: 'all' para cambiar todas las apariciones, 'first' para sólo la primera encontrada.
    Devuelve número de posiciones modificadas.
    """
    if new_x is None and new_z is None:
        return 0
    inst = find_monster_instances(path, monster_id)
    if not inst:
        print(f"[INFO] No se encontraron apariciones de monster_id {monster_id}")
        return 0

    updated = 0
    for entry in inst:
        off = entry['struct_offset']
        # seguridad: comprobar que tenemos espacio para escribir floats
        size = os.path.getsize(path)
        if off + 0x18 + 4 > size:  # z float at off+0x18
            print(f"[WARN] struct en 0x{off:X} demasiado cerca del EOF, salto")
            continue
        if new_x is not None:
            write_float_at(path, off + 0x10, float(new_x))
        if new_z is not None:
            write_float_at(path, off + 0x18, float(new_z))
        updated += 1
        print(f"[WRITE] updated {entry['type']} at 0x{off:X} -> x={new_x if new_x is not None else entry['x']}, z={new_z if new_z is not None else entry['z']}")
        if apply_to == 'first':
            break

    print(f"[INFO] posiciones actualizadas: {updated}")
    return updated

# ----------------------------
# OBJECTIVE HELPERS (INSERT INTO QuestEditor.py)
# ----------------------------
# Dependencies: get_dynamic_absolute_offset, read_byte, read_word, read_dword,
# write_byte_at, write_word_at, write_dword_at, os.path.getsize


def _objective_slot_abs_off(path: str, slot_index: int) -> int:
    """
    Return absolute offset of objective slot.
    slot_index: 0 -> header code-relative 0xCC
                1 -> header code-relative 0xD4
    Each objective struct layout (8 bytes): type:dword @ +0, target:word @ +4, qty:word @ +6
    """
    if slot_index not in (0, 1):
        raise IndexError("slot_index must be 0 or 1")
    code_rel = 0xCC + (slot_index * 0x08)
    return get_dynamic_absolute_offset(path, code_rel)


def read_objective_slot(path: str, slot_index: int) -> dict:
    """
    Read objective slot and return dict {'type': int, 'target': int, 'qty': int}.
    Raises EOFError when header area is out of file bounds.
    """
    abs_off = _objective_slot_abs_off(path, slot_index)
    size = os.path.getsize(path)
    if abs_off < 0 or abs_off + 8 > size:
        raise EOFError(f"read_objective_slot: offset 0x{abs_off:X} out of range (size 0x{size:X})")
    type_v = read_dword(path, abs_off)
    target = read_word(path, abs_off + 4)
    qty = read_word(path, abs_off + 6)
    return {'type': type_v, 'target': target, 'qty': qty}


def write_objective_slot(path: str, slot_index: int, type_val: int, target_id: int, qty: int):
    """
    Write objective struct (type:dword, target:word, qty:word) into slot 0 or 1.
    """
    abs_off = _objective_slot_abs_off(path, slot_index)
    size = os.path.getsize(path)
    if abs_off < 0 or abs_off + 8 > size:
        raise EOFError(f"write_objective_slot: offset 0x{abs_off:X} out of range (size 0x{size:X})")
    write_dword_at(path, abs_off, int(type_val) & 0xFFFFFFFF)
    write_word_at(path, abs_off + 4, int(target_id) & 0xFFFF)
    write_word_at(path, abs_off + 6, int(qty) & 0xFFFF)


def clear_objective_slot(path: str, slot_index: int):
    """Clear objective slot (type=0,target=0,qty=0)."""
    write_objective_slot(path, slot_index, 0, 0, 0)


def get_objective_amount(path: str) -> int:
    """Read objective_amount byte at header_offset + 0xCB and return decimal."""
    abs_off = get_dynamic_absolute_offset(path, 0xCB)
    size = os.path.getsize(path)
    if abs_off < 0 or abs_off + 1 > size:
        raise EOFError(f"get_objective_amount: offset 0x{abs_off:X} out of range (size 0x{size:X})")
    return read_byte(path, abs_off)


def set_objective_amount(path: str, amount: int):
    """Write objective_amount byte (0..255)."""
    if amount < 0 or amount > 255:
        raise ValueError("amount out of range")
    abs_off = get_dynamic_absolute_offset(path, 0xCB)
    size = os.path.getsize(path)
    if abs_off < 0 or abs_off + 1 > size:
        raise EOFError(f"set_objective_amount: offset 0x{abs_off:X} out of range (size 0x{size:X})")
    write_byte_at(path, abs_off, int(amount) & 0xFF)


def push_objective_recent(path: str, monster_id: int, type_val: int = 1, qty: int = 1,
                          duplicate_policy: str = "increment_if_same"):
    """
    Push-style objective updater. Call this for each monster while iterating.

    Behavior:
      - If no objectives yet -> write monster into slot0 (objective_count=1).
      - If only slot0 exists:
           * if same monster: increment slot0.qty by `qty`.
           * else: place incoming monster into slot1 (objective_count=2).
      - If both slots exist:
           * if incoming == slot1.target -> increment slot1.qty by `qty`.
           * elif incoming == slot0.target -> increment slot0.qty by `qty`.
           * else -> shift: slot0 := old slot1, slot1 := incoming (qty as provided).
    Parameters:
      path            : quest file path
      monster_id      : monster id (int)
      type_val        : objective type (dword) to use for newly created slots (existing slot types are preserved on increment)
      qty             : integer to add for the objective quantity (usually 1)
      duplicate_policy: "increment_if_same" (default) -> when incoming equals an existing slot, increment that slot.
                        "ignore_if_same_as_last" -> ignore incoming if equals current slot1.
                        "no_duplicates" -> avoid having same monster in both slots; if would happen, merge into one slot.
    Returns:
      (new_amount, info)
      info is a tuple ((slot0_target, slot0_qty), (slot1_target, slot1_qty))
    """
    # safety normalize inputs
    monster_id = int(monster_id) & 0xFFFF
    add_qty = max(0, int(qty))

    # clamp helper for word range
    def _clamp_word(v):
        if v < 0:
            return 0
        if v > 0xFFFF:
            return 0xFFFF
        return int(v)

    # read current objective state
    cur0 = read_objective_slot(path, 0)
    cur1 = read_objective_slot(path, 1)
    old0_id = int(cur0.get('target', 0))
    old0_qty = int(cur0.get('qty', 0))
    old1_id = int(cur1.get('target', 0))
    old1_qty = int(cur1.get('qty', 0))

    # policy: ignore if same as last (slot1)
    if duplicate_policy == "ignore_if_same_as_last" and monster_id == old1_id:
        return (get_objective_amount(path), ((old0_id, old0_qty), (old1_id, old1_qty)))

    # CASE: no objectives => place in slot0
    if old0_id == 0 and old1_id == 0:
        write_objective_slot(path, 0, type_val, monster_id, _clamp_word(add_qty))
        clear_objective_slot(path, 1)
        set_objective_amount(path, 1)
        return (1, ((monster_id, _clamp_word(add_qty)), (0, 0)))

    # CASE: only slot0 exists
    if old0_id != 0 and old1_id == 0:
        if monster_id == old0_id:
            # same monster -> increment slot0 qty
            new_qty = _clamp_word(old0_qty + add_qty)
            write_objective_slot(path, 0, cur0.get('type', type_val), old0_id, new_qty)
            set_objective_amount(path, 1)
            return (1, ((old0_id, new_qty), (0, 0)))
        else:
            # different -> place in slot1
            write_objective_slot(path, 1, type_val, monster_id, _clamp_word(add_qty))
            set_objective_amount(path, 2)
            return (2, ((old0_id, old0_qty), (monster_id, _clamp_word(add_qty))))

    # CASE: both slots exist
    # If incoming equals slot1 -> increment slot1
    if monster_id == old1_id:
        new_qty = _clamp_word(old1_qty + add_qty)
        write_objective_slot(path, 1, cur1.get('type', type_val), old1_id, new_qty)
        set_objective_amount(path, 2)
        return (2, ((old0_id, old0_qty), (old1_id, new_qty)))

    # If incoming equals slot0 -> increment slot0 (don't disturb slot1)
    if monster_id == old0_id:
        new_qty = _clamp_word(old0_qty + add_qty)
        write_objective_slot(path, 0, cur0.get('type', type_val), old0_id, new_qty)
        set_objective_amount(path, 2)
        return (2, ((old0_id, new_qty), (old1_id, old1_qty)))

    # Otherwise shift: new slot0 = old slot1, new slot1 = incoming
    # preserve old1 type/qty
    write_objective_slot(path, 0, cur1.get('type', type_val), old1_id, _clamp_word(old1_qty))
    write_objective_slot(path, 1, type_val, monster_id, _clamp_word(add_qty))
    set_objective_amount(path, 2)
    return (2, ((old1_id, old1_qty), (monster_id, _clamp_word(add_qty))))

def clear_all_objectives(path: str):
    """
    Reset quest objectives: clears both slots and sets amount=0.
    """
    clear_objective_slot(path, 0)
    clear_objective_slot(path, 1)
    set_objective_amount(path, 0)

# top-level parse_mib
def parse_mib(path: str) -> dict:
    import struct, os
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    with open(path, "rb") as f:
        buf = f.read()
    size = len(buf)

    def _is_valid_ptr(addr: int) -> bool:
        return addr != 0 and 0 <= addr < size

    MONSTER_STRUCT_SIZE = 0x28
    UNSTABLE_ENTRY_STRIDE = 0x2C

    # safe readers over buf (return 0 / 0.0 on OOB)
    def read_b(off: int) -> int:
        if off + 1 > size: return 0
        return struct.unpack_from("<B", buf, off)[0]
    def read_w(off: int) -> int:
        if off + 2 > size: return 0
        return struct.unpack_from("<H", buf, off)[0]
    def read_dw(off: int) -> int:
        if off + 4 > size: return 0
        return struct.unpack_from("<I", buf, off)[0]
    def read_f(off: int) -> float:
        if off + 4 > size: return 0.0
        return struct.unpack_from("<f", buf, off)[0]
    def read_bytes_local(off: int, ln: int) -> bytes:
        if off + ln > size:
            return buf[off: size]
        return buf[off: off+ln]

    def read_dword_array_until_zero_local(off: int):
        arr = []
        pos = off
        while pos + 4 <= size:
            v = read_dw(pos)
            if v == 0:
                break
            arr.append(v)
            pos += 4
        return arr

    def read_string_utf16_pairs_local(off: int):
        s = []
        pos = off
        while pos + 2 <= size:
            w = read_w(pos)
            if w == 0:
                break
            s.append(chr(w))
            pos += 2
        return "".join(s)
    

    def parse_monster_local(off: int):
        # ensure full monster struct is inside buffer
        if off + MONSTER_STRUCT_SIZE > size:
            return None
        m = {}
        m['monster_id'] = read_dw(off + 0x00)
        m['qty'] = read_dw(off + 0x04)
        m['condition'] = read_b(off + 0x08)
        m['area'] = read_b(off + 0x09)
        m['crashflag'] = read_b(off + 0x0A)
        m['special'] = read_b(off + 0x0B)
        m['unk2'] = read_b(off + 0x0C)
        m['unk3'] = read_b(off + 0x0D)
        m['unk4'] = read_b(off + 0x0E)
        m['infection'] = read_b(off + 0x0F)
        m['x'] = read_f(off + 0x10)
        m['y'] = read_f(off + 0x14)
        m['z'] = read_f(off + 0x18)
        m['x_rot'] = read_dw(off + 0x1C)
        m['y_rot'] = read_dw(off + 0x20)
        m['z_rot'] = read_dw(off + 0x24)
        return m

    q = {}
    # static header
    q['header_addr'] = read_dw(0x00)
    q['version_bytes'] = read_bytes_local(0x04, 4)
    q['supplies_ptr'] = read_dw(0x08)

    # some absolute fields
    q['hrp'] = read_dw(0x74)
    q['hrp_reduction'] = read_dw(0x78)
    q['hrp_sub'] = read_dw(0x7C)
    q['intruder_timer'] = read_b(0x80)
    q['intruder_chance'] = read_b(0x82)
    q['gather_rank'] = read_b(0x89)
    q['carve_rank'] = read_b(0x8A)
    q['monster_ai'] = read_b(0x8B)
    q['spawn_area'] = read_b(0x8C)

    header_addr = q['header_addr']
    header_offset = header_addr - 0xA0

    # dynamic fields (read safely)
    q['quest_type'] = read_b(header_offset + 0xA0)
    a1 = read_b(header_offset + 0xA1)
    q['huntathon_flag'] = bool(a1 & 1)
    q['intruder_flag'] = bool(a1 & 2)
    q['repel_flag'] = bool(a1 & 4)
    a2 = read_b(header_offset + 0xA2)
    q['harvest_flag'] = bool(a2 & 2)
    q['sub_flag'] = bool(a2 & (1 << 6))

    q['fee'] = read_dw(header_offset + 0xA4)
    q['reward_main'] = read_dw(header_offset + 0xA8)
    q['reward_reduction'] = read_dw(header_offset + 0xAC)
    q['reward_sub'] = read_dw(header_offset + 0xB0)
    q['time'] = read_dw(header_offset + 0xB4)
    q['intruder_chance2'] = read_dw(header_offset + 0xB8)

    # parse text
    text_top_ptr = read_dw(header_offset + 0xBC)
    q['text'] = []
    if text_top_ptr != 0 and _is_valid_ptr(text_top_ptr):
        for i in range(5):
            addr = read_dw(text_top_ptr + i*4)
            if addr == 0:
                break
            if not _is_valid_ptr(addr):
                break
            lang = []
            for j in range(7):
                saddr = read_dw(addr + j*4)
                if saddr == 0:
                    break
                if not _is_valid_ptr(saddr):
                    break
                lang.append(read_string_utf16_pairs_local(saddr))
            q['text'].append(lang)

    q['quest_id'] = read_w(header_offset + 0xC0)
    q['quest_rank'] = read_w(header_offset + 0xC2)
    q['map_id'] = read_b(header_offset + 0xC4)
    q['requirements'] = [read_b(header_offset + 0xC5), read_b(header_offset + 0xC6)]
    q['objective_amount'] = read_b(header_offset + 0xCB)

    def parse_objective_at(off):
        return {'type': read_dw(off), 'target_id': read_w(off + 4), 'qty': read_w(off + 6)}

    q['objectives'] = [parse_objective_at(header_offset + 0xCC), parse_objective_at(header_offset + 0xD4)]
    q['objective_sub'] = parse_objective_at(header_offset + 0xDC)
    q['pictures'] = [read_w(header_offset + 0xE8 + i*2) for i in range(5)]

    # supplies (safe)
    def parse_supplies_local():
        base_addr = read_dw(0x08)
        out = []
        if base_addr == 0 or not _is_valid_ptr(base_addr):
            return out
        idx = 0
        while True:
            entry_off = base_addr + idx*8
            if entry_off + 8 > size:
                break
            item_table_idx = read_b(entry_off)
            if item_table_idx == 0xFF:
                break
            length = read_b(entry_off + 1)
            addr = read_dw(entry_off + 4)
            if not _is_valid_ptr(addr):
                break
            items = []
            for i in range(length):
                if addr + i*4 + 4 > size:
                    break
                iid = read_w(addr + i*4)
                qty = read_w(addr + i*4 + 2)
                if iid == 0:
                    break
                items.append({'item_id': iid, 'qty': qty})
            out.append(items)
            idx += 1
            if idx > 200:
                break
        return out

    q['supplies'] = parse_supplies_local()

    # refills (safe)
    q['refills'] = []
    for i in range(2):
        base = 0x0C + 8*i
        if base + 8 > size: break
        q['refills'].append({
            'box': read_b(base + 0),
            'condition': read_b(base + 1),
            'monster': read_b(base + 2),
            'qty': read_b(base + 4)
        })

    # loot parser (safe)
    def parse_loot_local(offset):
        base = read_dw(offset)
        out = []
        if base == 0 or not _is_valid_ptr(base):
            return out
        idx = 0
        while True:
            if base + idx*8 + 4 > size:
                break
            val = read_dw(base + idx*8)
            if val == 0 or val == 0xFFFF:
                break
            addr = read_dw(base + idx*8 + 4)
            if not _is_valid_ptr(addr):
                break
            items = []
            j = 0
            while True:
                if addr + j*6 + 2 > size:
                    break
                chance = read_w(addr + j*6)
                if chance == 0xFFFF:
                    break
                item_id = read_w(addr + j*6 + 2)
                qty = read_w(addr + j*6 + 4)
                items.append({'chance': chance, 'item_id': item_id, 'qty': qty})
                j += 1
                if j > 500:
                    break
            out.append({'flag': val, 'items': items})
            idx += 1
            if idx > 500:
                break
        return out

    q['loot_a'] = parse_loot_local(0x1C)
    q['loot_b'] = parse_loot_local(0x20)
    q['loot_c'] = parse_loot_local(0x24)

    # small monster conditions
    conds = []
    base_cond = 0x64
    for i in range(2):
        if base_cond + 8*i + 8 > size:
            conds.append({'type':0,'target':0,'qty':0,'group':0})
            continue
        conds.append({
            'type': read_b(base_cond + 0 + 8*i),
            'target': read_w(base_cond + 4 + 8*i),
            'qty': read_b(base_cond + 6 + 8*i),
            'group': read_b(base_cond + 7 + 8*i)
        })
    q['small_monster_conditions'] = conds

    # --- IMPORTANT: initialize top-table address lists safely ---
    lbase = read_dw(0x28)
    if lbase != 0 and _is_valid_ptr(lbase):
        q['large_monster_table_addresses'] = read_dword_array_until_zero_local(lbase)
    else:
        q['large_monster_table_addresses'] = []

    sbase = read_dw(0x2C)
    if sbase != 0 and _is_valid_ptr(sbase):
        q['small_monster_table_addresses'] = read_dword_array_until_zero_local(sbase)
    else:
        q['small_monster_table_addresses'] = []

    # large monster table (safe bounded parse)
    q['large_monster_table'] = []
    for addr in q['large_monster_table_addresses']:
        if not _is_valid_ptr(addr):
            q['large_monster_table'].append([])
            continue
        arr = []
        for i in range(0, 200):
            off = addr + i * MONSTER_STRUCT_SIZE
            if off + MONSTER_STRUCT_SIZE > size:
                break
            mid = read_dw(off)
            if mid == 0xFFFFFFFF:
                break
            mon = parse_monster_local(off)
            if mon is None:
                break
            monID = mon['monster_id']
            if not monID in VariousLists.getLargeList():
                if not monID in VariousLists.getSmallList():
                    break
        
            arr.append(mon)
        q['large_monster_table'].append(arr)

    # small monster table (nested) - uses small_monster_table_addresses for top
    q['small_monster_table'] = []
    if sbase != 0 and _is_valid_ptr(sbase):
        top_ptrs = read_dword_array_until_zero_local(sbase)
        for top_addr in top_ptrs:
            if not _is_valid_ptr(top_addr):
                q['small_monster_table'].append([])
                continue
            sublist = []
            sub_ptrs = read_dword_array_until_zero_local(top_addr)
            for sub_ptr in sub_ptrs:
                if not _is_valid_ptr(sub_ptr):
                    continue
                monsters = []
                for i in range(0, 200):
                    off = sub_ptr + i * MONSTER_STRUCT_SIZE
                    if off + MONSTER_STRUCT_SIZE > size:
                        break
                    mid = read_dw(off)
                    if mid == 0xFFFFFFFF:
                        break
                    mon = parse_monster_local(off)
                    if mon is None:
                        break
                    monsters.append(mon)
                sublist.append(monsters)
            q['small_monster_table'].append(sublist)
    else:
        q['small_monster_table'] = []

    # unstable
    q['unstable_monster_table'] = []
    ubase = read_dw(0x30)
    if ubase != 0 and _is_valid_ptr(ubase):
        for idx in range(0, 200):
            entry_off = ubase + idx * UNSTABLE_ENTRY_STRIDE
            if entry_off + 2 > size:
                break
            chance = read_w(entry_off)
            if chance == 0xFFFF:
                break
            monster_off = entry_off + 4
            if monster_off + MONSTER_STRUCT_SIZE > size:
                break
            monster = parse_monster_local(monster_off)
            if monster is None:
                break
            q['unstable_monster_table'].append({'chance': chance, 'monster': monster})

    q['large_monsters_per_table'] = [len(t) for t in q['large_monster_table']]
    q['large_monsters_total'] = sum(q['large_monsters_per_table'])

    return q



def pretty_print_quest_summary(path: str):
    """Pretty print using the self-contained parse_mib above."""
    try:
        q = parse_mib(path)
    except Exception as e:
        print("[ERROR] parse_mib failed:", e)
        return

    print("=== QUEST SUMMARY ===")
    print(f"file: {path}")
    print(f"quest_id: {q.get('quest_id')}  rank: {q.get('quest_rank')}  map_id: {q.get('map_id')}")
    print(f"quest_type: {q.get('quest_type')}  time: {q.get('time')}")
    print(f"HRP: {q.get('hrp')}  reward_main: 0x{q.get('reward_main'):X}")
    print(f"large monster arrays: {len(q.get('large_monster_table_addresses', []))}")
    print(f"large monsters per table: {q.get('large_monsters_per_table')} -> total: {q.get('large_monsters_total')}")
    # large monster IDs
    freq = {}
    for table in q.get('large_monster_table', []):
        for m in table:
            freq[m['monster_id']] = freq.get(m['monster_id'], 0) + 1
    if freq:
        print("Large monster IDs (id:count):", ", ".join([f"{hex(k)}:{v}" for k,v in freq.items()]))
    print("loot A:", "empty" if not q.get('loot_a') else f"{len(q['loot_a'])} entries")
    print("supplies tables:", len(q.get('supplies', [])))
    print("=====================")

# === END: standalone parse_mib + pretty_print_quest_summary ===
def find_and_replace_monster_individual(path: str, old_monster_id: int, new_monster_id: int, dry_run: bool = False):
    """
    Versión CORREGIDA: Reemplaza solo UN monstruo a la vez, PERO busca en TODAS las tablas.
    """
    replaced = 0
    size = os.path.getsize(path)
    found_and_replaced = False  # Bandera para controlar si ya reemplazamos uno

    # --- large monsters ---
    base_list = get_large_monster_table_addresses(path)
    for table_idx, a in enumerate(base_list):
        if a == 0 or a < 0 or a >= size:
            continue
        idx = 0
        while True:
            off = a + idx * 0x28
            if off + 4 > size:
                break
            mid = read_dword(path, off)
            if mid == 0xFFFFFFFF:
                break
            if mid == old_monster_id and not found_and_replaced:  # Solo si no hemos reemplazado aún
                if dry_run:
                    print(f"[DRY] would replace large at 0x{off:X} ({hex(mid)}) -> {hex(new_monster_id)}")
                else:
                    write_dword_at(path, off, new_monster_id)
                    print(f"[WRITE] replaced large at 0x{off:X} {hex(old_monster_id)} -> {hex(new_monster_id)}")
                    replaced += 1
                    found_and_replaced = True  # Marcamos que ya reemplazamos uno
                    # NO hacemos return aquí, continuamos buscando en otras tablas
                # Si ya reemplazamos, salimos de este bucle while pero continuamos con otras tablas
                if found_and_replaced:
                    break
            idx += 1
            if idx > 1000:
                break
        if found_and_replaced:
            break  # Salimos del bucle de tablas grandes

    # Si ya reemplazamos, no buscamos en small monsters
    if not found_and_replaced:
        # --- small monsters: nested tables ---
        base_small_ptr = read_dword(path, 0x2C)
        if base_small_ptr != 0:
            top_ptrs = read_dword_array_until_zero(path, base_small_ptr)
            for top_idx, top in enumerate(top_ptrs):
                if top == 0 or top < 0 or top >= size:
                    continue
                sub_ptrs = read_dword_array_until_zero(path, top)
                for sub_idx, addr in enumerate(sub_ptrs):
                    if addr == 0 or addr < 0 or addr >= size:
                        continue
                    idx = 0
                    while True:
                        off = addr + idx * 0x28
                        if off + 4 > size:
                            break
                        mid = read_dword(path, off)
                        if mid == 0xFFFFFFFF:
                            break
                        if mid == old_monster_id and not found_and_replaced:
                            if dry_run:
                                print(f"[DRY] would replace small at 0x{off:X} ({hex(mid)})")
                            else:
                                write_dword_at(path, off, new_monster_id)
                                print(f"[WRITE] replaced small at 0x{off:X} {hex(old_monster_id)} -> {hex(new_monster_id)}")
                                replaced += 1
                                found_and_replaced = True
                            if found_and_replaced:
                                break
                        idx += 1
                        if idx > 1000:
                            break
                    if found_and_replaced:
                        break
                if found_and_replaced:
                    break

    # Si ya reemplazamos, no buscamos en unstable
    if not found_and_replaced:
        # --- unstable table ---
        base_unstable = read_dword(path, 0x30)
        if base_unstable != 0:
            idx = 0
            while True:
                entry_off = base_unstable + idx * 0x2C
                if entry_off + 2 > size:
                    break
                chance = read_word(path, entry_off)
                if chance == 0xFFFF:
                    break
                off = entry_off + 4
                if off + 4 > size:
                    break
                mid = read_dword(path, off)
                if mid == old_monster_id and not found_and_replaced:
                    if dry_run:
                        print(f"[DRY] would replace unstable at 0x{off:X} ({hex(mid)})")
                    else:
                        write_dword_at(path, off, new_monster_id)
                        print(f"[WRITE] replaced unstable at 0x{off:X} {hex(old_monster_id)} -> {hex(new_monster_id)}")
                        replaced += 1
                        found_and_replaced = True
                    if found_and_replaced:
                        break
                idx += 1
                if idx > 1000:
                    break

    print(f"[INFO] Replacements done: {replaced} (dry_run={dry_run})")
    return replaced

# ---------- FIND AND REPLACE MONSTER ----------
def find_and_replace_monster(path: str, old_monster_id: int, new_monster_id: int, dry_run: bool = False):
    """
    Versión robusta: evita lecturas fuera de fichero y salta tablas/punteros inválidos.
    """
    replaced = 0
    size = os.path.getsize(path)

    def safe_read_dword_at(off):
        if off < 0 or off + 4 > size:
            # fuera de rango
            print(f"[WARN] safe_read_dword_at: off 0x{off:X} fuera de rango (filesize 0x{size:X})")
            return None
        return read_dword(path, off)

    # --- large monsters ---
    base_list = get_large_monster_table_addresses(path)
    for table_idx, a in enumerate(base_list):
        if a == 0 or a < 0 or a >= size:
            print(f"[WARN] large table pointer #{table_idx} inválido: 0x{a:X}")
            continue
        idx = 0
        while True:
            off = a + idx * 0x28
            if off + 4 > size:
                print(f"[WARN] large[{table_idx}] off 0x{off:X} supera filesize 0x{size:X} -> stop")
                break
            mid = read_dword(path, off)
            if mid == 0xFFFFFFFF:
                break
            if mid == old_monster_id:
                if dry_run:
                    print(f"[DRY] would replace large at 0x{off:X} ({hex(mid)}) -> {hex(new_monster_id)}")
                else:
                    write_dword_at(path, off, new_monster_id)
                    print(f"[WRITE] replaced large at 0x{off:X} {hex(old_monster_id)} -> {hex(new_monster_id)}")
                replaced += 1
            idx += 1
            if idx > 1000:
                print(f"[WARN] large[{table_idx}] demasiadas iteraciones, abortando (safety limit)")
                break

    # --- small monsters: nested tables ---
    base_small_ptr = read_dword(path, 0x2C)
    if base_small_ptr != 0:
        top_ptrs = read_dword_array_until_zero(path, base_small_ptr)
        for top_idx, top in enumerate(top_ptrs):
            if top == 0 or top < 0 or top >= size:
                print(f"[WARN] small top pointer #{top_idx} inválido: 0x{top:X}")
                continue
            sub_ptrs = read_dword_array_until_zero(path, top)
            for sub_idx, addr in enumerate(sub_ptrs):
                if addr == 0 or addr < 0 or addr >= size:
                    print(f"[WARN] small sub pointer idx {sub_idx} inválido: 0x{addr:X}")
                    continue
                idx = 0
                while True:
                    off = addr + idx * 0x28
                    if off + 4 > size:
                        print(f"[WARN] small[{top_idx}][{sub_idx}] off 0x{off:X} fuera de rango -> stop")
                        break
                    mid = read_dword(path, off)
                    if mid == 0xFFFFFFFF:
                        break
                    if mid == old_monster_id:
                        if dry_run:
                            print(f"[DRY] would replace small at 0x{off:X} ({hex(mid)})")
                        else:
                            write_dword_at(path, off, new_monster_id)
                            print(f"[WRITE] replaced small at 0x{off:X} {hex(old_monster_id)} -> {hex(new_monster_id)}")
                        replaced += 1
                    idx += 1
                    if idx > 1000:
                        print(f"[WARN] small[{top_idx}][{sub_idx}] safety limit hit, break")
                        break

    # --- unstable table ---
    base_unstable = read_dword(path, 0x30)
    if base_unstable != 0:
        idx = 0
        while True:
            entry_off = base_unstable + idx * 0x2C
            if entry_off + 2 > size:
                print(f"[WARN] unstable entry_off 0x{entry_off:X} fuera de rango -> stop")
                break
            chance = read_word(path, entry_off)
            if chance == 0xFFFF:
                break
            off = entry_off + 4
            if off + 4 > size:
                print(f"[WARN] unstable monster struct at 0x{off:X} fuera de rango -> stop")
                break
            mid = read_dword(path, off)
            if mid == old_monster_id:
                if dry_run:
                    print(f"[DRY] would replace unstable at 0x{off:X} ({hex(mid)})")
                else:
                    write_dword_at(path, off, new_monster_id)
                    print(f"[WRITE] replaced unstable at 0x{off:X} {hex(old_monster_id)} -> {hex(new_monster_id)}")
                replaced += 1
            idx += 1
            if idx > 1000:
                print("[WARN] unstable safety limit reached")
                break

    print(f"[INFO] Replacements done: {replaced} (dry_run={dry_run})")
    return replaced


# ----- Objective getters / setters -----
def _objective_code_offset_for_index(objective_index: int) -> int:
    """Map objective_index 0/1/2 -> code-relative offset used in the original JS (0xCC,0xD4,0xDC)."""
    mapping = {0: 0xCC, 1: 0xD4, 2: 0xDC}
    if objective_index not in mapping:
        raise ValueError("objective_index must be 0,1 or 2")
    return mapping[objective_index]

def get_objective(questFilePath: str, objective_index: int) -> dict:
    """
    Read a full objective from the dynamic header.
    objective_index: 0,1 or 2 (2 == sub objective)
    Returns dict: {'type': int, 'target_id': int, 'qty': int}
    """
    if objective_index not in (0,1,2):
        raise ValueError("objective_index must be 0,1 or 2")
    rel = _objective_code_offset_for_index(objective_index)
    abs_off = get_dynamic_absolute_offset(questFilePath, rel)
    # layout: dword at off+0 = type, word at +4 = target_id, word at +6 = qty
    t = read_dword(questFilePath, abs_off + 0)
    target = read_word(questFilePath, abs_off + 4)
    qty = read_word(questFilePath, abs_off + 6)
    return {'type': t, 'target_id': target, 'qty': qty}

def get_all_objectives(questFilePath: str) -> dict:
    """Return objectives 0,1 and sub as a dict {'obj0':..., 'obj1':..., 'sub':...}"""
    return {
        'obj0': get_objective(questFilePath, 0),
        'obj1': get_objective(questFilePath, 1),
        'sub':  get_objective(questFilePath, 2)
    }

def set_objective(questFilePath: str, objective_index: int, type_val: int = None, target_id: int = None, qty: int = None):
    """
    Write one or more fields for an objective.
    Pass None for fields you don't want to change.
    objective_index: 0,1 or 2
    type_val: 32-bit int, target_id: word (0..65535), qty: word (0..65535)
    """
    if objective_index not in (0,1,2):
        raise ValueError("objective_index must be 0,1 or 2")
    rel = _objective_code_offset_for_index(objective_index)
    abs_off = get_dynamic_absolute_offset(questFilePath, rel)

    # write type (dword)
    if type_val is not None:
        # ensure 32-bit range
        if not (0 <= int(type_val) <= 0xFFFFFFFF):
            raise ValueError("type_val out of range 0..0xFFFFFFFF")
        write_dword_at(questFilePath, abs_off + 0, int(type_val))

    # write target_id (word)
    if target_id is not None:
        if not (0 <= int(target_id) <= 0xFFFF):
            raise ValueError("target_id out of range 0..65535")
        write_word_at(questFilePath, abs_off + 4, int(target_id))

    # write qty (word)
    if qty is not None:
        if not (0 <= int(qty) <= 0xFFFF):
            raise ValueError("qty out of range 0..65535")
        write_word_at(questFilePath, abs_off + 6, int(qty))
# --- helper seguro para objetivos ---
def _safe_set_objective(path: str, obj_index: int, type_id: int, target_id: int, qty: int):
    """
    Wrapper que asegura que index esté en 0..2 y captura errores para no corromper el fichero.
    Llama a set_objective(path, index, type, target, qty)
    """
    try:
        if obj_index < 0:
            obj_index = 0
        if obj_index > 2:
            # nunca escribir fuera de los 3 slots válidos
            raise IndexError("objective_index fuera de rango (solo 0,1,2 permitidos)")
        set_objective(path, obj_index, type_id, target_id, qty)
    except Exception as e:
        # no lanzamos para evitar abortar el randomizer entero; logueamos para debug
        print(f"[ERROR] _safe_set_objective: no pude escribir objective idx={obj_index} -> {e}")

def clear_all_objectives(path: str):
    """Pone a cero los tres slots de objectives (tipo=0,target=0,qty=0)."""
    for idx in range(3):
        _safe_set_objective(path, idx, 0, 0, 0)

def write_objectives_for_monsters(path: str, monster_ids: list, prefer_type_for_single:int = 1):
    """
    monster_ids: lista de monster_id presentes en la quest (ordenados como quieras).
    prefer_type_for_single: tipo a usar cuando escribimos objetivos individuales (p.ej. 1 para matar).
    Reglas:
      - Si len(monster_ids) <= 3 -> escribe cada uno en su slot (0..len-1) con type=prefer_type_for_single y qty=1.
      - Si len(monster_ids) > 3 -> escribe un único objetivo type=8 (hunt all) en slot 0 y limpia los otros dos.
    """
    if monster_ids is None:
        monster_ids = []

    total = len(monster_ids)
    if total == 0:
        clear_all_objectives(path)
        return

    if total <= 3:
        # escribir uno por slot
        clear_all_objectives(path)  # opcional: limpiar antes
        for i in range(total):
            mid = int(monster_ids[i])  # target normalmente el monster id
            _safe_set_objective(path, i, prefer_type_for_single, mid, 1)
        # si había slots libres, asegurarse de que están a 0
        for j in range(total, 3):
            _safe_set_objective(path, j, 0, 0, 0)
    else:
        # más de 3 monstruos: poner objetivo tipo 8 (hunt all) en slot 0
        # target_id para type 8 normalmente no hace falta (depende), usar 0 para seguridad
        _safe_set_objective(path, 0, 8, 0, 0)   # qty/target ignorados por tipo 8 en muchos juegos
        # limpiar los demás slots
        _safe_set_objective(path, 1, 0, 0, 0)
        _safe_set_objective(path, 2, 0, 0, 0)

# ---------- VERIFY TABLES ----------
def verify_tables(path: str, verbose: bool = True):
    """
    Run basic integrity checks:
     - pointer fields are within file bounds
     - dword-array top tables end with 0x00000000
     - monster arrays have 0xFFFFFFFF terminator within a sane limit
    Returns list of issues found (empty if good).
    """
    issues = []
    size = os.path.getsize(path)

    def check_ptr(offset, name):
        try:
            p = read_dword(path, offset)
        except Exception as e:
            issues.append(f"{name}: cannot read pointer at 0x{offset:X}: {e}")
            return None
        if p != 0 and (p < 0 or p >= size):
            issues.append(f"{name}: pointer 0x{p:X} out of file bounds (size 0x{size:X})")
        return p

    # pointers to check
    ptrs = {
        "supplies_ptr": 0x08,
        "loot_a_ptr": 0x1C,
        "loot_b_ptr": 0x20,
        "loot_c_ptr": 0x24,
        "large_monster_ptr": 0x28,
        "small_monster_ptr": 0x2C,
        "unstable_monster_ptr": 0x30,
    }
    ptr_vals = {}
    for name, off in ptrs.items():
        ptr_vals[name] = check_ptr(off, name)

    # verify top dword-arrays end with zero (read first 256 dwords or until zero)
    def verify_dword_array(addr, name):
        if addr is None or addr == 0:
            return
        max_count = 1024
        pos = addr
        count = 0
        while True:
            if pos + 4 > size:
                issues.append(f"{name}: dword-array at 0x{addr:X} overruns file")
                break
            v = read_dword(path, pos)
            count += 1
            pos += 4
            if v == 0:
                break
            if count > max_count:
                issues.append(f"{name}: no terminator found within {max_count} entries")
                break

    verify_dword_array(ptr_vals['large_monster_ptr'], 'large_monster_top')
    verify_dword_array(ptr_vals['small_monster_ptr'], 'small_monster_top')

    # verify monster arrays have 0xFFFFFFFF terminator somewhere
    def verify_monster_array(addr, name):
        if addr is None or addr == 0:
            return
        max_mon = 500
        i = 0
        while True:
            off = addr + i * 0x28
            if off + 4 > size:
                issues.append(f"{name}: monster array at 0x{addr:X} overruns file")
                break
            mid = read_dword(path, off)
            if mid == 0xFFFFFFFF:
                break
            i += 1
            if i > max_mon:
                issues.append(f"{name}: no monster terminator within {max_mon} entries at 0x{addr:X}")
                break

    # iterate large monster tables
    lbase = ptr_vals['large_monster_ptr']
    if lbase and lbase != 0:
        top_addrs = read_dword_array_until_zero(path, lbase)
        for idx, a in enumerate(top_addrs):
            verify_monster_array(a, f"large[{idx}]")

    # small monster tables: nested
    sbase = ptr_vals['small_monster_ptr']
    if sbase and sbase != 0:
        tops = read_dword_array_until_zero(path, sbase)
        for t in tops:
            subs = read_dword_array_until_zero(path, t)
            for addr in subs:
                verify_monster_array(addr, f"small at 0x{addr:X}")

    if verbose:
        if issues:
            print("[VERIFY] Issues found:")
            for it in issues:
                print(" -", it)
        else:
            print("[VERIFY] No obvious issues found.")
    return issues


# ----- Utility examples / usage -----
# Example: set map id dynamically:
#   set_map_id_dynamic("loc/quest/m10111.1BBFD18E", 3)
#
# Example: set a header flag bit (e.g. set intruder_flag bit1 at code-relative 0xA1):
#   set_header_flag_bit("path.mib", 0xA1, 1, True)
#
# Example: change the first monster in large table 0 to Rathalos (monster id 0x1):
#   write_monster_in_large_table("path.mib", table_index=0, monster_index=0,
#       monster={"monster_id": 0x1, "qty":1, "area":1, "x":0.0, "y":0.0, "z":0.0})
#
# Example: set refill 0:
#   set_refill_entry("path.mib", 0, box=1, condition=0, monster=5, qty=3)
#
# Example: set small monster condition 0 target to monster id 0x20 and qty 5:
#   set_small_monster_condition("path.mib", 0, type_val=1, target=0x20, qty=5, group=0)
#

import os

# ----------------------------
# Helpers internos
# ----------------------------
MONSTER_STRUCT_SIZE = 0x28  # 40 bytes

def _is_valid_ptr_in_file(path: str, addr: int) -> bool:
    if addr == 0:
        return False
    size = os.path.getsize(path)
    return 0 <= addr < size

# ----------------------------
# Large table: get / set by indices
# ----------------------------
def get_large_monster_by_indices(path: str, top_index: int, monster_index: int):
    """
    Devuelve dict con info del monster struct apuntado por:
      base = read_dword(path, 0x28)  # top-list
      table_addr = top_list[top_index]
      struct_offset = table_addr + monster_index * 0x28

    Si inválido o fuera de rango devuelve None.
    Resultado:
      {
        'table_addr': int,
        'struct_offset': int,
        'monster_id': int,
        'x': float, 'y': float, 'z': float,
        'monster_index': int, 'top_index': int
      }
    """
    size = os.path.getsize(path)
    # leer base top-list
    try:
        lbase = read_dword(path, 0x28)
    except Exception as e:
        return None
    if not _is_valid_ptr_in_file(path, lbase):
        return None

    # leer array de punteros hasta cero
    top_ptrs = read_dword_array_until_zero(path, lbase)
    if top_index < 0 or top_index >= len(top_ptrs):
        return None
    table_addr = top_ptrs[top_index]
    if not _is_valid_ptr_in_file(path, table_addr):
        return None

    struct_off = table_addr + monster_index * MONSTER_STRUCT_SIZE
    # comprobaciones de seguridad
    if struct_off + 4 > size:
        return None
    mid = read_dword(path, struct_off)
    if mid == 0xFFFFFFFF:
        return None

    # asegurar que todo el struct está dentro
    if struct_off + MONSTER_STRUCT_SIZE > size:
        return None

    x = read_float(path, struct_off + 0x10)
    y = read_float(path, struct_off + 0x14)
    z = read_float(path, struct_off + 0x18)

    return {
        'table_addr': table_addr,
        'struct_offset': struct_off,
        'monster_id': mid,
        'x': x, 'y': y, 'z': z,
        'monster_index': monster_index,
        'top_index': top_index
    }

def set_large_monster_position_by_indices(path: str, top_index: int, monster_index: int, new_x=None, new_z=None):
    """
    Escribe new_x/new_z (floats) en el struct indicado. Devuelve True si escribió al menos 1 valor.
    Si new_x o new_z es None, esa coordenada no se modifica.
    """
    info = get_large_monster_by_indices(path, top_index, monster_index)
    if info is None:
        print(f"[WARN] get_large_monster_by_indices devolvió None para top={top_index} idx={monster_index}")
        return False

    off = info['struct_offset']
    size = os.path.getsize(path)
    # seguridad: comprobar espacio para escribir floats (x en off+0x10, z en off+0x18)
    if off + 0x18 + 4 > size:
        print(f"[WARN] struct en 0x{off:X} demasiado cerca del EOF, no se escribe")
        return False

    if new_x is not None:
        write_float_at(path, off + 0x10, float(new_x))
    if new_z is not None:
        write_float_at(path, off + 0x18, float(new_z))
    print(f"[WRITE] Large(top={top_index},idx={monster_index}) @0x{off:X} -> x={new_x if new_x is not None else info['x']}, z={new_z if new_z is not None else info['z']}")
    return True

# ----------------------------
# Small table (nested): get / set by indices
# ----------------------------
def get_small_monster_by_indices(path: str, top_index: int, sub_index: int, monster_index: int):
    """
    Acceso a small tables:
      base = read_dword(path, 0x2C)  # top-list
      top_addr = top_list[top_index]
      sub_ptrs = read_dword_array_until_zero(path, top_addr)
      table_addr = sub_ptrs[sub_index]
      struct_offset = table_addr + monster_index * 0x28

    Devuelve dict (similar al de get_large_monster_by_indices) o None si inválido.
    """
    size = os.path.getsize(path)
    try:
        sbase = read_dword(path, 0x2C)
    except Exception:
        return None
    if not _is_valid_ptr_in_file(path, sbase):
        return None

    top_ptrs = read_dword_array_until_zero(path, sbase)
    if top_index < 0 or top_index >= len(top_ptrs):
        return None
    top_addr = top_ptrs[top_index]
    if not _is_valid_ptr_in_file(path, top_addr):
        return None

    sub_ptrs = read_dword_array_until_zero(path, top_addr)
    if sub_index < 0 or sub_index >= len(sub_ptrs):
        return None
    table_addr = sub_ptrs[sub_index]
    if not _is_valid_ptr_in_file(path, table_addr):
        return None

    struct_off = table_addr + monster_index * MONSTER_STRUCT_SIZE
    if struct_off + 4 > size:
        return None
    mid = read_dword(path, struct_off)
    if mid == 0xFFFFFFFF:
        return None
    if struct_off + MONSTER_STRUCT_SIZE > size:
        return None

    x = read_float(path, struct_off + 0x10)
    y = read_float(path, struct_off + 0x14)
    z = read_float(path, struct_off + 0x18)

    return {
        'top_addr': top_addr,
        'table_addr': table_addr,
        'struct_offset': struct_off,
        'monster_id': mid,
        'x': x, 'y': y, 'z': z,
        'monster_index': monster_index,
        'top_index': top_index,
        'sub_index': sub_index
    }

def set_small_monster_position_by_indices(path: str, top_index: int, sub_index: int, monster_index: int, new_x=None, new_z=None):
    """
    Escribe new_x/new_z en un monstruo de la tabla small identificada por (top_index, sub_index, monster_index).
    Devuelve True si escribió correctamente.
    """
    info = get_small_monster_by_indices(path, top_index, sub_index, monster_index)
    if info is None:
        print(f"[WARN] get_small_monster_by_indices devolvió None para top={top_index}, sub={sub_index}, idx={monster_index}")
        return False

    off = info['struct_offset']
    size = os.path.getsize(path)
    if off + 0x18 + 4 > size:
        print(f"[WARN] struct en 0x{off:X} demasiado cerca del EOF, no se escribe")
        return False

    if new_x is not None:
        write_float_at(path, off + 0x10, float(new_x))
    if new_z is not None:
        write_float_at(path, off + 0x18, float(new_z))
    print(f"[WRITE] Small(top={top_index},sub={sub_index},idx={monster_index}) @0x{off:X} -> x={new_x if new_x is not None else info['x']}, z={new_z if new_z is not None else info['z']}")
    return True

def is_large_monster_not_first_and_table_has_three(parsedMib: dict, monster_id: int) -> bool:
    """
    Returns True if the monster_id is in a large monster table,
    is NOT the first in that table, and that table has at least 3 monsters.
    Returns False otherwise.
    """
    large_tables = parsedMib.get('large_monster_table', [])
    for table in large_tables:
        if len(table) >= 3:
            for idx, mon in enumerate(table):
                if mon.get('monster_id') == monster_id and idx > 0:
                    return True
    return False



def changeByteAtOffset_For_In(offset: int, new_value: bytes, questFilePath: str):
    """
    Change the byte(s) at a given offset in the file.
    """
    if not os.path.exists(questFilePath):
        raise FileNotFoundError(f"File not found: {questFilePath}")
    size = os.path.getsize(questFilePath)
    if offset < 0 or offset + len(new_value) > size:
        raise ValueError(f"Write outside file bounds: offset=0x{offset:X}, len={len(new_value)}, size=0x{size:X}")
    
    with open(questFilePath, "r+b") as f:   # read+write in binary mode
        f.seek(offset)
        f.write(new_value)
        f.flush()
        os.fsync(f.fileno())
    print(f"[DEBUG] Successfully wrote {new_value.hex().upper()} at offset 0x{offset:X}")

def last_byte_pos(path: str) -> int:
    """Return the index of the last byte in the file (size-1)."""
    size = Path(path).stat().st_size
    if size == 0:
        raise ValueError("file is empty")
    return size - 1

def getSpawnByte(filePath: str) -> int:
    """Given the last-byte index (e.g. 0x177F) return the spawn offset (first column) using -0x90 rule."""
    lastByteIndex = last_byte_pos(filePath)

    base_row = (lastByteIndex // 0x10) * 0x10   # HxD row base (col 00)
    spawn = base_row - 0x90
    if spawn < 0:
        raise ValueError("calculated spawn offset is negative")
    return spawn

def replaceMonsterWith_In(oldMonsterStr: str,newMonsterStr: str, questFileName: str):
    
    questFolder = getQuestFolder()

    questFilePath = os.path.join(questFolder, questFileName)
    if not os.path.exists(questFilePath):
        raise FileNotFoundError(f"File not found: {questFilePath}")
    
    oldMonster = bytes.fromhex(oldMonsterStr)
    newMonster = bytes.fromhex(newMonsterStr)
    print(f"[DEBUG] oldMonster = {oldMonster.hex().upper()}, newMonster = {newMonster.hex().upper()}")


    changeByteAtOffset_For_In(0xD0 , newMonster, questFilePath)
    changeByteAtOffset_For_In(0xE0 , newMonster, questFilePath)
   

    spawnByte= getSpawnByte(questFilePath)

    print(f"[DEBUG] Calculated spawnByte offset = 0x{spawnByte:X}")
    changeByteAtOffset_For_In(spawnByte, newMonster, questFilePath)
    print(f"[INFO] Patched {questFileName} at 0x{spawnByte:X} (and 0xD0, 0xE0) with {newMonsterStr.upper()}")

def replaceZoneWith_In(zoneIDStr: str, questFileName: str):
    questFolder = getQuestFolder()
    questFilePath = os.path.join(questFolder, questFileName)
    if not os.path.exists(questFilePath):
        raise FileNotFoundError(f"File not found: {questFilePath}")
    newZoneID = bytes.fromhex(zoneIDStr)
    changeByteAtOffset_For_In(0xC4, newZoneID,questFilePath)
    
def replaceSubzone_In(subzoneIDStr: str, questFileName: str):
    questFolder = getQuestFolder()
    questFilePath = os.path.join(questFolder, questFileName)
    spawnZoneByte= getSpawnByte(questFilePath) + 0x09
    newZoneID = bytes.fromhex(subzoneIDStr)
    changeByteAtOffset_For_In(spawnZoneByte, newZoneID, questFilePath)


questFolder= getQuestFolder()
if __name__ == "__main__":
    # ensure questFolder exists (keeps your convention)
    questFolder = getQuestFolder()
    print(f"[DEBUG] questFolder = {questFolder}")

    print("Enter quest filename (inside loc/quest):")
    questFileName = input("> ").strip()

    print("Enter new monster hex (e.g. DEADBEEF or DE AD BE EF):")
    newMonsterHex = input("> ").strip().replace(" ", "").replace("0x", "").upper()
    # ensure even-length hex
    if len(newMonsterHex) % 2 == 1:
        newMonsterHex = "0" + newMonsterHex
        print(f"[DEBUG] questFileName = {questFileName}, newMonsterHex = {newMonsterHex}")

    try:
        # we pass the same hex as old and new so length check passes
        replaceMonsterWith_In(newMonsterHex, newMonsterHex, questFileName)
    except Exception as e:
        print("Error:", e)
