#THIS IS BASED OF DASDING'S CQ EDITOR, TRANSLATED INTO PYTHON BY CHATGPT I DO NOT UNDERSTAND SHIT ABOUT WHAT IS GOING ON, SO DON'T ASK ME
#THIS JUST WORKS AND DOESN'T EXPLODE A PC
#ALL CREDIT ABOUT THIS CODE OBVIOUSLY GOES TO DASDING
#Just vibe-coded all this, dont blame me too hard, it is my first mod, programming project 
import os
import struct
from pathlib import Path

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
import struct
import math

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
import struct
import os

def _load_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

# low-level readers working on a bytes buffer
def _read_byte(buf: bytes, offset: int) -> int:
    return struct.unpack_from("<B", buf, offset)[0]

def _read_word(buf: bytes, offset: int) -> int:
    return struct.unpack_from("<H", buf, offset)[0]

def _read_dword(buf: bytes, offset: int) -> int:
    return struct.unpack_from("<I", buf, offset)[0]

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

def _read_string_utf16le_pairs(buf: bytes, offset: int):
    """Read string encoded as 2-byte words until 0x0000 terminator. Each word is a codepoint."""
    s = []
    pos = offset
    size = len(buf)
    while pos + 2 <= size:
        w = _read_word(buf, pos)
        if w == 0:
            break
        s.append(chr(w))
        pos += 2
    return "".join(s)

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

# top-level parse_mib
def parse_mib(path: str) -> dict:
    """
    Self-contained parse_mib that reads the file into memory and parses structures.
    Uses local helper functions to avoid colliding with other module-level names.
    """
    import struct
    import os

    if not os.path.exists(path):
        raise FileNotFoundError(path)

    with open(path, "rb") as f:
        buf = f.read()
    size = len(buf)

    # --- local readers (buffer-based) ---
    def read_b(off: int) -> int:
        return struct.unpack_from("<B", buf, off)[0]

    def read_w(off: int) -> int:
        return struct.unpack_from("<H", buf, off)[0]

    def read_dw(off: int) -> int:
        return struct.unpack_from("<I", buf, off)[0]

    def read_f(off: int) -> float:
        return struct.unpack_from("<f", buf, off)[0]

    def read_bytes_local(off: int, ln: int) -> bytes:
        return buf[off:off+ln]

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

    # --- start parse ---
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

    # dynamic header base
    header_addr = q['header_addr']
    header_offset = header_addr - 0xA0

    # dynamic fields
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

    # parse text (similar logic to JS)
    text_top_ptr = read_dw(header_offset + 0xBC)
    q['text'] = []
    if text_top_ptr != 0:
        for i in range(5):
            addr = read_dw(text_top_ptr + i*4)
            if addr == 0:
                break
            lang = []
            for j in range(7):
                saddr = read_dw(addr + j*4)
                if saddr == 0:
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
    # pictures
    q['pictures'] = [read_w(header_offset + 0xE8 + i*2) for i in range(5)]

    # supplies
    def parse_supplies_local():
        base_addr = read_dw(0x08)
        out = []
        if base_addr == 0:
            return out
        idx = 0
        while True:
            entry_off = base_addr + idx*8
            if entry_off + 1 >= size:
                break
            item_table_idx = read_b(entry_off)
            if item_table_idx == 0xFF:
                break
            length = read_b(entry_off + 1)
            addr = read_dw(entry_off + 4)
            items = []
            for i in range(length):
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

    # refills
    q['refills'] = []
    for i in range(2):
        base = 0x0C + 8*i
        q['refills'].append({
            'box': read_b(base + 0),
            'condition': read_b(base + 1),
            'monster': read_b(base + 2),
            'qty': read_b(base + 4)
        })

    # loot parser helper
    def parse_loot_local(offset):
        base = read_dw(offset)
        out = []
        if base == 0:
            return out
        idx = 0
        while True:
            val = read_dw(base + idx*8)
            if val == 0 or val == 0xFFFF:
                break
            addr = read_dw(base + idx*8 + 4)
            items = []
            j = 0
            while True:
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
        conds.append({
            'type': read_b(base_cond + 0 + 8*i),
            'target': read_w(base_cond + 4 + 8*i),
            'qty': read_b(base_cond + 6 + 8*i),
            'group': read_b(base_cond + 7 + 8*i)
        })
    q['small_monster_conditions'] = conds

    # large monster table
    lbase = read_dw(0x28)
    q['large_monster_table_addresses'] = read_dword_array_until_zero_local(lbase) if lbase != 0 else []
    q['large_monster_table'] = []
    for addr in q['large_monster_table_addresses']:
        arr = []
        for i in range(0, 200):
            off = addr + i*0x28
            if off + 4 > size:
                break
            mid = read_dw(off)
            if mid == 0xFFFFFFFF:
                break
            arr.append(parse_monster_local(off))
        q['large_monster_table'].append(arr)

    # small monster table
    sbase = read_dw(0x2C)
    q['small_monster_table_addresses'] = read_dword_array_until_zero_local(sbase) if sbase != 0 else []
    q['small_monster_table'] = []
    for top_addr in q['small_monster_table_addresses']:
        sublist = []
        for sub_ptr in read_dword_array_until_zero_local(top_addr):
            monsters = []
            for i in range(0, 200):
                off = sub_ptr + i*0x28
                if off + 4 > size:
                    break
                mid = read_dw(off)
                if mid == 0xFFFFFFFF:
                    break
                monsters.append(parse_monster_local(off))
            sublist.append(monsters)
        q['small_monster_table'].append(sublist)

    # unstable
    ubase = read_dw(0x30)
    q['unstable_monster_table'] = []
    if ubase != 0:
        for idx in range(0, 200):
            chance = read_w(ubase + idx*0x2C)
            if chance == 0xFFFF:
                break
            monster = parse_monster_local(ubase + idx*0x2C + 4)
            q['unstable_monster_table'].append({'chance': chance, 'monster': monster})

    # meta tables
    q['large_meta_table'] = []
    for idx in range(5):
        off = 0x34 + idx*8
        q['large_meta_table'].append({
            'size': read_w(off),
            'size_var': read_b(off+2),
            'hp': read_b(off+3),
            'atk': read_b(off+4),
            'break_res': read_b(off+5),
            'stamina': read_b(off+6),
            'status_res': read_b(off+7)
        })
    q['small_meta'] = {
        'size': read_w(0x5C),
        'unk0': read_b(0x5D),
        'hp': read_b(0x5F),
        'atk': read_b(0x60),
        'break_res': read_b(0x61),
        'stamina': read_b(0x62),
        'unk2': read_b(0x63)
    }

    # convenience counts
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

# ---------- FIND AND REPLACE MONSTER ----------
def find_and_replace_monster(path: str, old_monster_id: int, new_monster_id: int, dry_run: bool = False):
    """
    Search through large, small and unstable monster tables and replace monster_id occurrences.
    Returns count of replacements.
    If dry_run True -> only report what would be changed.
    """
    replaced = 0
    # large
    base_list = get_large_monster_table_addresses(path)
    for table_idx, a in enumerate(base_list):
        idx = 0
        while True:
            off = a + idx * 0x28
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

    # small (two-level)
    base_small_ptr = read_dword(path, 0x2C)
    if base_small_ptr != 0:
        top_ptrs = read_dword_array_until_zero(path, base_small_ptr)
        for top in top_ptrs:
            sub_ptrs = read_dword_array_until_zero(path, top)
            for addr in sub_ptrs:
                idx = 0
                while True:
                    off = addr + idx * 0x28
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

    # unstable
    base_unstable = read_dword(path, 0x30)
    if base_unstable != 0:
        idx = 0
        while True:
            chance = read_word(path, base_unstable + idx * 0x2C)
            if chance == 0xFFFF:
                break
            off = base_unstable + idx * 0x2C + 4
            mid = read_dword(path, off)
            if mid == old_monster_id:
                if dry_run:
                    print(f"[DRY] would replace unstable at 0x{off:X} ({hex(mid)})")
                else:
                    write_dword_at(path, off, new_monster_id)
                    print(f"[WRITE] replaced unstable at 0x{off:X} {hex(old_monster_id)} -> {hex(new_monster_id)}")
                replaced += 1
            idx += 1

    print(f"[INFO] Replacements done: {replaced} (dry_run={dry_run})")
    return replaced

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
# Example: change the first monster in large table 0 to Rathalos (monster id 0x12345678):
#   write_monster_in_large_table("path.mib", table_index=0, monster_index=0,
#       monster={"monster_id": 0x12345678, "qty":1, "area":1, "x":0.0, "y":0.0, "z":0.0})
#
# Example: set refill 0:
#   set_refill_entry("path.mib", 0, box=1, condition=0, monster=5, qty=3)
#
# Example: set small monster condition 0 target to monster id 0x20 and qty 5:
#   set_small_monster_condition("path.mib", 0, type_val=1, target=0x20, qty=5, group=0)
#
# === END: add this to QuestEditor.py ===





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


