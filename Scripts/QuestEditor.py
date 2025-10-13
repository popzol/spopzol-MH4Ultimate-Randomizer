# QuestEditor.py - MH4U Quest File Editor
# Based on DASDING's CQ Editor, translated and extended for Python
# This module provides functions to read, write, and manipulate MH4U quest files (.mib)
# See mib_format_documentation.txt for details on the file format

import VariousLists
import os
import struct
import math
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('QuestEditor')

# Constants
MONSTER_STRUCT_SIZE = 0x28  # 40 bytes
FILE_ALIGNMENT = 0x10       # 16-byte alignment for new blocks
TERMINATOR_DWORD = 0xFFFFFFFF  # Monster array terminator
POINTER_LIST_TERMINATOR = 0x00000000  # Pointer list terminator

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

def get_map_id(questFilePath: str) -> int:
    """Get map id using the dynamic header offset (JS used header_offset + 0xC4)"""
    abs_off = get_dynamic_absolute_offset(questFilePath, 0xC4)
    return read_byte(questFilePath, abs_off)

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
    if type_val is None:
        type_val = 8
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

# ----- Meta table reader -----
def read_meta_entry(questFilePath: str, idx: int):
    """
    Read one entry from meta_table at base 0x34 + idx*8
    Returns dict with fields: size, size_var, hp, atk, break_res, stamina, status_res
    """
    base = 0x34 + idx * 8
    return {
        'size': read_word(questFilePath, base),
        'size_var': read_byte(questFilePath, base + 2),
        'hp': read_byte(questFilePath, base + 3),
        'atk': read_byte(questFilePath, base + 4),
        'break_res': read_byte(questFilePath, base + 5),
        'stamina': read_byte(questFilePath, base + 6),
        'status_res': read_byte(questFilePath, base + 7)
    }

def write_stats_from_dict(questFilePath: str, idx: int, stats: dict):
    """
    Helper to write monster stats from a dict using write_meta_entry.
    stats should have keys: size, size_var, hp, atk, break_res, stamina, status_res.
    Only writes keys present in the dict.
    """
    write_meta_entry(
        questFilePath,
        idx,
        size=stats.get('size'),
        size_var=stats.get('size_var'),
        hp=stats.get('hp'),
        atk=stats.get('atk'),
        break_res=stats.get('break_res'),
        stamina=stats.get('stamina'),
        status_res=stats.get('status_res')
    )

def calculate_metadata_index(questFilePath: str, wave_index: int, position_index: int):
    """
    Calculate the metadata index for a monster at a specific wave and position.
    Metadata indices are assigned sequentially across all waves and positions.
    
    Args:
        questFilePath: Path to the quest file
        wave_index: Wave/table index (0-based)
        position_index: Position within the wave (0-based)
    
    Returns:
        int: The metadata index for this monster position
    """
    parsed = parse_mib(questFilePath)
    large_tables = parsed.get('large_monster_table', [])
    
    meta_index = 0
    
    # Count all monsters before this position
    for w_idx, wave in enumerate(large_tables):
        if w_idx == wave_index:
            # We've reached the target wave, add positions before target position
            meta_index += position_index
            break
        else:
            # Add all monsters in this wave
            meta_index += len(wave)
    
    return meta_index

def swap_metadata_entries(questFilePath: str, index1: int, index2: int):
    """
    Swap two metadata entries in the meta table.
    
    Args:
        questFilePath: Path to the quest file
        index1: First metadata index
        index2: Second metadata index
    """
    # Read both metadata entries
    meta1 = read_meta_entry(questFilePath, index1)
    meta2 = read_meta_entry(questFilePath, index2)
    
    # Write them swapped
    write_stats_from_dict(questFilePath, index1, meta2)
    write_stats_from_dict(questFilePath, index2, meta1)

def move_metadata_entry(questFilePath: str, src_index: int, dst_index: int):
    """
    Move one metadata entry from src_index to dst_index, shifting intervening entries
    to keep the sequential order consistent. Preserves the stats for the moved monster.
    """
    if src_index == dst_index:
        return
    # Save the source metadata
    src_meta = read_meta_entry(questFilePath, src_index)
    if src_index < dst_index:
        # Shift entries left (i <- i+1) from src_index .. dst_index-1
        for i in range(src_index, dst_index):
            next_meta = read_meta_entry(questFilePath, i + 1)
            write_stats_from_dict(questFilePath, i, next_meta)
        # Place src_meta at dst_index
        write_stats_from_dict(questFilePath, dst_index, src_meta)

def compact_metadata_after_large_delete(questFilePath: str, wave_index: int, position_index: int, pre_total: int | None = None, pre_src_idx: int | None = None):
    """
    Compact the large monster metadata table after deleting a monster.

    - Shifts all metadata entries left starting from the deleted monster's index.
    - Zeroes out the final metadata slot so no trace remains.

    Args:
        questFilePath: Path to the quest file
        wave_index: Wave index of the deleted monster (0-based)
        position_index: Position within the wave (0-based)
        pre_total: Optional total count of metadata entries BEFORE deletion
        pre_src_idx: Optional metadata index of the deleted monster BEFORE deletion
    """
    try:
        if pre_total is None or pre_src_idx is None:
            parsed = parse_mib(questFilePath)
            large_tables = parsed.get('large_monster_table', [])
            total_meta = sum(len(w) for w in large_tables)
            src_idx = calculate_metadata_index(questFilePath, wave_index, position_index)
        else:
            total_meta = pre_total
            src_idx = pre_src_idx

        if total_meta <= 0:
            print(f"[WARN] compact_metadata_after_large_delete: total_meta={total_meta}, nothing to compact")
            return
        if src_idx < 0 or src_idx >= total_meta:
            print(f"[ERROR] compact_metadata_after_large_delete: src_idx {src_idx} out of range (total={total_meta})")
            return

        # Shift metadata entries left from src_idx to total_meta-2
        for i in range(src_idx, total_meta - 1):
            next_meta = read_meta_entry(questFilePath, i + 1)
            write_stats_from_dict(questFilePath, i, next_meta)

        # Zero out the last entry to remove any trace
        last_idx = total_meta - 1
        write_stats_from_dict(
            questFilePath,
            last_idx,
            {
                'size': 0,
                'size_var': 0,
                'hp': 0,
                'atk': 0,
                'break_res': 0,
                'stamina': 0,
                'status_res': 0,
            },
        )
        print(f"[DEBUG] compact_metadata_after_large_delete: shifted entries from {src_idx}..{total_meta-2} and zeroed index {last_idx}")
    except Exception as e:
        print(f"[ERROR] compact_metadata_after_large_delete failed: {e}")
    else:
        # Shift entries right (i <- i-1) from src_index .. dst_index+1
        for i in range(src_index, dst_index, -1):
            prev_meta = read_meta_entry(questFilePath, i - 1)
            write_stats_from_dict(questFilePath, i, prev_meta)
        # Place src_meta at dst_index
        write_stats_from_dict(questFilePath, dst_index, src_meta)

# ---------------------------
# Additional editor helpers:
# write_loot_table, write_supplies, pretty_print_quest_summary,
# find_and_replace_monster, verify_tables
# ---------------------------


def append_aligned(path: str, data: bytes, align: int = FILE_ALIGNMENT) -> int:
    """
    Append data to file aligned to the specified boundary.
    
    Args:
        path: Path to the file
        data: Bytes to append
        align: Alignment boundary (default: FILE_ALIGNMENT)
        
    Returns:
        int: Absolute address where data was written
        
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    with open(path, "r+b") as f:
        f.seek(0, 2)  # Seek to end of file
        length = f.tell()
        
        # Calculate padding needed for alignment
        pad = (align - (length % align)) % align
        if pad:
            f.write(b'\x00' * pad)
            
        addr = f.tell()
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
        
        logger.debug(f"Appended {len(data)} bytes at aligned address 0x{addr:X} (padding: {pad})")
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
        if apply_to == 'first':
            break

    return updated

# ----------------------------
# OBJECTIVE HELPERS (INSERT INTO py)
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

def delete_monster_by_id_first_instance(path: str, monster_id: int):
    """
    Busca la primera aparición del monster_id y la elimina completamente.
    Shifts remaining monsters in the same table to fill the gap.
    """
    instances = find_monster_instances(path, monster_id)
    if not instances:
        print(f"Monster {monster_id} not found in quest.")
        return False
    
    first = instances[0]
    print(f"Deleting first instance of monster {monster_id} at {first}")
    
    if first['type'] == 'large':
        return delete_from_large_table(path, first)
    elif first['type'] == 'small':
        return _delete_from_small_table(path, first)
    elif first['type'] == 'unstable':
        return _delete_from_unstable_table(path, first)
    
    return False


def delete_from_large_table(path: str, monster_info: dict) -> bool:
    """
    Deletes a monster from a large table and shifts remaining monsters.
    """
    try:
        table_index = monster_info['table_index']
        monster_index = monster_info['monster_index']
        print(f"[DEBUG] delete_from_large_table START: table_index={table_index}, monster_index={monster_index}")
        
        # Resolve and validate table pointer safely
        size = os.path.getsize(path)
        lbase = read_dword(path, 0x28)
        table_addresses = read_dword_array_until_zero(path, lbase)
        if not table_addresses or table_index < 0 or table_index >= len(table_addresses):
            print(f"[ERROR] delete_from_large_table: invalid table_index {table_index} (available={len(table_addresses)})")
            return False
        table_addr = table_addresses[table_index]
        if table_addr is None or table_addr <= 0 or table_addr >= size:
            print(f"[ERROR] delete_from_large_table: table pointer 0x{table_addr:X} out of bounds (filesize=0x{size:X})")
            return False
        
        # Pre-compute metadata indices BEFORE any structural changes
        try:
            parsed_for_meta = parse_mib(path)
            large_tables_for_meta = parsed_for_meta.get('large_monster_table', [])
            pre_total_meta = sum(len(w) for w in large_tables_for_meta)
            pre_src_meta_idx = calculate_metadata_index(path, table_index, monster_index)
        except Exception as e_meta:
            print(f"[WARN] delete_from_large_table: could not precompute metadata indices: {e_meta}")
            pre_total_meta = None
            pre_src_meta_idx = None

        # Count total monsters in this table (until terminator)
        total_monsters = 0
        while True:
            check_offset = table_addr + total_monsters * MONSTER_STRUCT_SIZE
            # Bounds check before reading
            if check_offset + 4 > size:
                print(f"[ERROR] delete_from_large_table: read beyond file at 0x{check_offset:X} (size=0x{size:X})")
                break
            monster_id = read_dword(path, check_offset)
            if monster_id == 0xFFFFFFFF:
                break
            total_monsters += 1
            if total_monsters > 2000:  # Safety limit
                break
        print(f"[DEBUG] delete_from_large_table BEFORE: total_monsters_in_table={total_monsters}")
        
        if total_monsters == 0:
            print(f"[ERROR] delete_from_large_table: table {table_index} appears empty or invalid, aborting delete")
            return False
        if monster_index < 0 or monster_index >= total_monsters:
            print(f"[ERROR] delete_from_large_table: monster_index {monster_index} out of range (total={total_monsters})")
            return False

        # If this is the only monster, just write terminator and scrub the rest of the struct bytes
        if total_monsters == 1:
            write_dword_at(path, table_addr, 0xFFFFFFFF)
            # Physically clear remaining bytes in the first (now-terminator) slot for a clean deletion
            try:
                with open(path, 'r+b') as f:
                    f.seek(table_addr + 4)
                    f.write(b"\x00" * (MONSTER_STRUCT_SIZE - 4))
                print(f"[DEBUG] delete_from_large_table SCRUB: zeroed {MONSTER_STRUCT_SIZE - 4} bytes after terminator at 0x{table_addr + 4:X}")
            except Exception as e:
                print(f"[WARN] delete_from_large_table: tail scrub failed at 0x{table_addr + 4:X}: {e}")
            # Compact metadata to remove any trace of the deleted monster
            try:
                compact_metadata_after_large_delete(path, table_index, monster_index, pre_total=pre_total_meta, pre_src_idx=pre_src_meta_idx)
            except Exception as e_cmp:
                print(f"[WARN] delete_from_large_table: metadata compaction failed (single) - {e_cmp}")
            print(f"Deleted last monster in table {table_index}")
            print(f"[DEBUG] delete_from_large_table AFTER: total_monsters_in_table=0")
            return True
        
        # Shift all monsters after the deleted one
        for i in range(monster_index, total_monsters - 1):
            src_offset = table_addr + (i + 1) * MONSTER_STRUCT_SIZE
            dst_offset = table_addr + i * MONSTER_STRUCT_SIZE
            if src_offset + MONSTER_STRUCT_SIZE > size or dst_offset + MONSTER_STRUCT_SIZE > size:
                print(f"[ERROR] delete_from_large_table: shift would exceed file bounds (src=0x{src_offset:X}, dst=0x{dst_offset:X}, size=0x{size:X})")
                return False
            
            # Read the source monster struct
            monster_data = _read_bytes(path, src_offset, MONSTER_STRUCT_SIZE)
            if not monster_data or len(monster_data) != MONSTER_STRUCT_SIZE:
                print(f"[ERROR] delete_from_large_table: failed to read source monster data at 0x{src_offset:X}")
                return False
            
            # Write it to the destination
            with open(path, 'r+b') as f:
                f.seek(dst_offset)
                f.write(monster_data)
        
        # Write terminator at the new end position and scrub remaining bytes in that slot
        terminator_offset = table_addr + (total_monsters - 1) * MONSTER_STRUCT_SIZE
        if terminator_offset + 4 > size:
            print(f"[ERROR] delete_from_large_table: terminator write beyond file at 0x{terminator_offset:X}")
            return False
        write_dword_at(path, terminator_offset, 0xFFFFFFFF)
        # Physically clear remaining bytes in the last (now-terminator) slot to avoid residual data past the terminator
        try:
            with open(path, 'r+b') as f:
                f.seek(terminator_offset + 4)
                f.write(b"\x00" * (MONSTER_STRUCT_SIZE - 4))
            print(f"[DEBUG] delete_from_large_table SCRUB: zeroed {MONSTER_STRUCT_SIZE - 4} bytes after terminator at 0x{terminator_offset + 4:X}")
        except Exception as e:
            print(f"[WARN] delete_from_large_table: tail scrub failed at 0x{terminator_offset + 4:X}: {e}")

        # Compact metadata to remove any trace of the deleted monster
        try:
            compact_metadata_after_large_delete(path, table_index, monster_index, pre_total=pre_total_meta, pre_src_idx=pre_src_meta_idx)
        except Exception as e_cmp:
            print(f"[WARN] delete_from_large_table: metadata compaction failed - {e_cmp}")

        print(f"Deleted monster from large table {table_index}, position {monster_index}")
        print(f"Shifted {total_monsters - monster_index - 1} monsters forward")
        print(f"[DEBUG] delete_from_large_table AFTER: total_monsters_in_table={total_monsters - 1}")
        return True
        
    except Exception as e:
        print(f"Error deleting from large table: {e}")
        return False


def _delete_from_small_table(path: str, monster_info: dict) -> bool:
    """
    Deletes a monster from a small table and shifts remaining monsters.
    """
    try:
        table_index = monster_info['table_index']
        sub_index = monster_info['sub_index']
        monster_index = monster_info['monster_index']
        
        # Get the small table structure
        sbase = read_dword(path, 0x2C)
        top_ptrs = read_dword_array_until_zero(path, sbase)
        top_addr = top_ptrs[table_index]
        sub_ptrs = read_dword_array_until_zero(path, top_addr)
        sub_addr = sub_ptrs[sub_index]
        
        # Count total monsters in this sub-table
        total_monsters = 0
        while True:
            check_offset = sub_addr + total_monsters * MONSTER_STRUCT_SIZE
            monster_id = read_dword(path, check_offset)
            if monster_id == 0xFFFFFFFF:
                break
            total_monsters += 1
            if total_monsters > 2000:  # Safety limit
                break
        
        # If this is the only monster, just write terminator
        if total_monsters == 1:
            write_dword_at(path, sub_addr, 0xFFFFFFFF)
            print(f"Deleted last monster in small table {table_index}.{sub_index}")
            return True
        
        # Shift all monsters after the deleted one
        for i in range(monster_index, total_monsters - 1):
            src_offset = sub_addr + (i + 1) * MONSTER_STRUCT_SIZE
            dst_offset = sub_addr + i * MONSTER_STRUCT_SIZE
            
            # Read the source monster struct
            monster_data = _read_bytes(path, src_offset, MONSTER_STRUCT_SIZE)
            
            # Write it to the destination
            with open(path, 'r+b') as f:
                f.seek(dst_offset)
                f.write(monster_data)
        
        # Write terminator at the new end position
        terminator_offset = sub_addr + (total_monsters - 1) * MONSTER_STRUCT_SIZE
        write_dword_at(path, terminator_offset, 0xFFFFFFFF)
        
        print(f"Deleted monster from small table {table_index}.{sub_index}, position {monster_index}")
        print(f"Shifted {total_monsters - monster_index - 1} monsters forward")
        return True
        
    except Exception as e:
        print(f"Error deleting from small table: {e}")
        return False


def _delete_from_unstable_table(path: str, monster_info: dict) -> bool:
    """
    Deletes a monster from the unstable table and shifts remaining entries.
    """
    try:
        entry_index = monster_info['sub_index']  # In unstable table, sub_index is the entry index
        
        # Get the unstable table base
        ubase = read_dword(path, 0x30)
        
        # Count total entries in unstable table
        total_entries = 0
        while True:
            entry_off = ubase + total_entries * 0x2C
            chance = read_word(path, entry_off)
            if chance == 0xFFFF:
                break
            total_entries += 1
            if total_entries > 2000:  # Safety limit
                break
        
        # If this is the only entry, just write terminator
        if total_entries == 1:
            write_word_at(path, ubase, 0xFFFF)
            print(f"Deleted last entry in unstable table")
            return True
        
        # Shift all entries after the deleted one
        for i in range(entry_index, total_entries - 1):
            src_offset = ubase + (i + 1) * 0x2C
            dst_offset = ubase + i * 0x2C
            
            # Read the source entry (0x2C bytes)
            entry_data = _read_bytes(path, src_offset, 0x2C)
            
            # Write it to the destination
            with open(path, 'r+b') as f:
                f.seek(dst_offset)
                f.write(entry_data)
        
        # Write terminator at the new end position
        terminator_offset = ubase + (total_entries - 1) * 0x2C
        write_word_at(path, terminator_offset, 0xFFFF)
        
        print(f"Deleted entry from unstable table, position {entry_index}")
        print(f"Shifted {total_entries - entry_index - 1} entries forward")
        return True
        
    except Exception as e:
        print(f"Error deleting from unstable table: {e}")
        return False



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
# --------------------------------------------
# FINDS AND REPLACE MONSTER

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
                    replaced += 1
                    found_and_replaced = True  # Marcamos que ya reemplazamos uno
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
                        replaced += 1
                        found_and_replaced = True
                    if found_and_replaced:
                        break
                idx += 1
                if idx > 1000:
                    break

    # Only print if dry_run
    if dry_run:
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
                replaced += 1
            idx += 1
            if idx > 1000:
                print("[WARN] unstable safety limit reached")
                break

    # Only print if dry_run
    if dry_run:
        print(f"[INFO] Replacements done: {replaced} (dry_run={dry_run})")
    return replaced

# ----- Large monster reorder -----


def swap_large_monsters_order(full_path: str, swap_monster_id: int, position: int, table_index: int = 0):
    """
    Swaps the first occurrence of swap_monster_id in the specified large monster table
    with the monster currently at 'position'. If swap_monster_id is already at 'position', does nothing.
    If there are multiple swap_monster_id, only the first is swapped.
    table_index: The index of the large monster table to operate on (default: 0).
    """
    table_addresses = get_large_monster_table_addresses(full_path)
    if not table_addresses:
        print("[ERROR] No large monster tables found.")
        return
    if not (0 <= table_index < len(table_addresses)):
        print(f"[ERROR] Invalid table_index {table_index}. Must be between 0 and {len(table_addresses) - 1}.")
        return
    table_addr = table_addresses[table_index]
    # Read all monsters
    monsters = []
    idx = 0
    found_idx = None
    while True:
        offset = table_addr + idx * MONSTER_STRUCT_SIZE
        mid = read_dword(full_path, offset)
        if mid == 0xFFFFFFFF:
            break
        monsters.append(unpack_monster_struct(_read_bytes(full_path, offset, MONSTER_STRUCT_SIZE)))
        if found_idx is None and mid == swap_monster_id:
            found_idx = idx
        idx += 1
        if idx > 1000:
            break
    if found_idx is None:
        print(f"[ERROR] Monster ID {swap_monster_id} not found in large monster table.")
        return
    if position < 0 or position >= len(monsters):
        print(f"[ERROR] Position {position} out of range.")
        return
    if found_idx == position:
        print("[INFO] Monster already at desired position, no swap needed.")
        return
    # Swap monsters
    monsters[found_idx], monsters[position] = monsters[position], monsters[found_idx]
    # Write back
    for idx, mon in enumerate(monsters):
        offset = table_addr + idx * MONSTER_STRUCT_SIZE
        write_monster_struct_at(full_path, offset, mon)
    # Write terminator
    offset = table_addr + len(monsters) * MONSTER_STRUCT_SIZE
    write_dword_at(full_path, offset, 0xFFFFFFFF)
    print(f"[INFO] Swapped monster {swap_monster_id} to position {position}.")

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

def set_objective(questFilePath: str, objective_index: int, type_val: int , target_id: int , qty: int ):
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

def write_objectives_for_monsters(path: str, monster_ids: list, prefer_type_for_single: int = 1):
    """
    Define objetivos a partir de los monstruos presentes en la quest.

    Reglas solicitadas:
      - Ignorar totalmente las colas de Dalamadur/Shah en los objetivos.
      - Si hay 1 o 2 monstruos (tras filtrar colas): escribirlos como objetivos individuales.
      - Si hay más de 2: el tipo de quest debe ser 8 ("hunt all") en el slot 0 y
        únicamente el último monstruo debe figurar como objetivo específico
        (en los slots 0 y 1) con type=prefer_type_for_single y qty=1.
    """
    if monster_ids is None:
        monster_ids = []

    # Excluir colas de Dalamadur/Shah de los objetivos
    tails_to_exclude = {83, 111}
    filtered = []
    for mid in monster_ids:
        try:
            imid = int(mid)
        except Exception:
            continue
        if imid in tails_to_exclude:
            continue
        filtered.append(imid)

    # Limpiar antes de escribir
    clear_all_objectives(path)

    total = len(filtered)
    if total == 0:
        return

    elif total <= 2:
        # Escribir cada monstruo en su slot empezando en 0
        for i in range(total):
            _safe_set_objective(path, i, prefer_type_for_single, filtered[i], 1)
        # Asegurar que los slots restantes están a cero
        for j in range(total, 3):
            _safe_set_objective(path, j, 0, 0, 0)
    else:
     
        # Sólo los 2 últimos monstruos como objetivos específicos en slots 0 y 1
        last_two = []
        last_two.append(filtered[len(filtered)-2])
        if len(filtered) > 1:
            last_two.append(filtered[len(filtered)-1])
        else:
            last_two.append(0)
        print(f"last_two: {last_two}")
        # If the last monster appears multiple times, require killing all of them
        mid=last_two[1]
        count_last = sum(1 for mid in filtered if mid == last_two[1])
        qty_last = max(1, count_last)
        _safe_set_objective(path, 0, 1, last_two[1], qty_last)
        _safe_set_objective(path, 1, 1, last_two[1], qty_last)

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


def get_all_monster_ids(parsedMib: dict) -> list:
    """
    Extracts all monster IDs from the large_monster_table in a parsed MIB.
    """
    monster_ids = []
    for table in parsedMib.get('large_monster_table', []):
        for monster in table:
            if 'monster_id' in monster:
                monster_ids.append(monster['monster_id'])
    return monster_ids

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

    # Force head/tail monsters to origin (x=z=0) regardless of input
    if info.get('monster_id') in (24, 83, 110, 111):
        write_float_at(path, off + 0x10, 0.0)
        write_float_at(path, off + 0x18, 0.0)
        return True

    if new_x is not None:
        write_float_at(path, off + 0x10, float(new_x))
    if new_z is not None:
        write_float_at(path, off + 0x18, float(new_z))
    return True

def set_large_monster_rotation_by_indices(path: str, top_index: int, monster_index: int,
                                          new_x_rot=None, new_y_rot=None, new_z_rot=None):
    """
    Escribe new_x_rot/new_y_rot/new_z_rot (dwords) en el struct indicado.
    Devuelve True si escribió al menos 1 valor. Si alguno es None, esa rotación no se modifica.
    Campos de rotación en el struct:
      x_rot @ off+0x1C, y_rot @ off+0x20, z_rot @ off+0x24
    """
    info = get_large_monster_by_indices(path, top_index, monster_index)
    if info is None:
        print(f"[WARN] get_large_monster_by_indices devolvió None para top={top_index} idx={monster_index}")
        return False

    off = info['struct_offset']
    size = os.path.getsize(path)
    # seguridad: comprobar espacio para escribir dwords de rotación (z_rot en off+0x24)
    if off + 0x24 + 4 > size:
        print(f"[WARN] struct en 0x{off:X} demasiado cerca del EOF, no se escribe")
        return False

    if new_x_rot is not None:
        write_dword_at(path, off + 0x1C, int(new_x_rot))
    if new_y_rot is not None:
        write_dword_at(path, off + 0x20, int(new_y_rot))
    if new_z_rot is not None:
        write_dword_at(path, off + 0x24, int(new_z_rot))
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
    return True




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



# ----- Wave-based monster management functions -----

def swap_large_monster(questFilePath: str, monster_id: int, target_wave: int, target_position: int):
    """
    Swaps a monster by its ID to a specific wave (table) and position.
    The monster currently at the target location exchanges positions with the incoming monster.
    
    Args:
        questFilePath: Path to the quest file
        monster_id: ID of the monster to move
        target_wave: Target wave/table index (0-2)
        target_position: Position within the target wave (0-1, max 2 monsters per wave)
    
    Returns:
        bool: True if swap was successful, False otherwise
    
    Example:
        If monster 7 is at wave 0, position 0 and monster 9 is at wave 1, position 0:
        swap_large_monster(path, 7, 1, 0) will result in:
        - Monster 9 moves to wave 0, position 0
        - Monster 7 moves to wave 1, position 0
    """
    try:
        parsed = parse_mib(questFilePath)
        large_monster_tables = parsed.get('large_monster_table', [])
        
        if not large_monster_tables:
            print(f"[ERROR] No large monster tables found in quest file.")
            return False
        
        # Validate wave constraints
        if target_wave < 0 or target_wave >= len(large_monster_tables):
            print(f"[ERROR] Invalid target wave {target_wave}. Must be between 0 and {len(large_monster_tables) - 1}.")
            return False
        
        target_table = large_monster_tables[target_wave]
        
        if target_position < 0 or target_position >= len(target_table):
            print(f"[ERROR] Invalid target position {target_position}. Must be between 0 and {len(target_table) - 1}.")
            return False
        
        if target_position >= 2:
            print(f"[ERROR] Target position {target_position} exceeds maximum of 2 monsters per wave.")
            return False
        
        # Find the source monster
        source_wave = -1
        source_position = -1
        
        for wave_idx, wave in enumerate(large_monster_tables):
            for pos_idx, monster in enumerate(wave):
                if monster.get('monster_id') == monster_id:
                    source_wave = wave_idx
                    source_position = pos_idx
                    break
            if source_wave != -1:
                break
        
        if source_wave == -1:
            print(f"[ERROR] Monster ID {monster_id} not found in any wave.")
            return False
        
        # Check if monster is already at target location
        if source_wave == target_wave and source_position == target_position:
            print(f"[INFO] Monster {monster_id} is already at wave {target_wave}, position {target_position}.")
            return True
        
        # Get table addresses
        table_addresses = get_large_monster_table_addresses(questFilePath)
        
        # Read source monster data
        source_table_addr = table_addresses[source_wave]
        source_offset = source_table_addr + source_position * MONSTER_STRUCT_SIZE
        source_monster_data = _read_bytes(questFilePath, source_offset, MONSTER_STRUCT_SIZE)
        source_monster_dict = unpack_monster_struct(source_monster_data)
        
        # Read target monster data
        target_table_addr = table_addresses[target_wave]
        target_offset = target_table_addr + target_position * MONSTER_STRUCT_SIZE
        target_monster_data = _read_bytes(questFilePath, target_offset, MONSTER_STRUCT_SIZE)
        target_monster_dict = unpack_monster_struct(target_monster_data)
        
        # Determine metadata indices for source and target positions
        src_meta_idx = calculate_metadata_index(questFilePath, source_wave, source_position)
        dst_meta_idx = calculate_metadata_index(questFilePath, target_wave, target_position)

        # Check if target position is empty (terminator)
        try:
            target_mid = read_dword(questFilePath, target_offset)
        except Exception:
            target_mid = 0xFFFFFFFF

        if target_mid == 0xFFFFFFFF:
            # Target slot is empty: perform a MOVE instead of a SWAP
            # 1) Write source monster to target
            write_monster_struct_at(questFilePath, target_offset, source_monster_dict)
            # 2) Write terminator at source
            write_dword_at(questFilePath, source_offset, 0xFFFFFFFF)
            # 3) Move metadata entry to new index, preserving stats
            move_metadata_entry(questFilePath, src_meta_idx, dst_meta_idx)
        else:
            # Target occupied: perform normal SWAP of structs
            write_monster_struct_at(questFilePath, source_offset, target_monster_dict)
            write_monster_struct_at(questFilePath, target_offset, source_monster_dict)
            # Also swap metadata entries so stats follow the monsters
            swap_metadata_entries(questFilePath, src_meta_idx, dst_meta_idx)
        
        print(f"[INFO] Successfully swapped monster {monster_id} to wave {target_wave}, position {target_position}")
        print(f"[INFO] Monster {target_monster_dict.get('monster_id')} moved to wave {source_wave}, position {source_position}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to swap monsters: {e}")
        return False

def get_wave_monster_count(questFilePath: str, wave_index: int) -> int:
    """
    Returns the number of monsters in a specific wave (table).
    
    Args:
        questFilePath: Path to the quest file
        wave_index: Index of the wave/table to check
    
    Returns:
        int: Number of monsters in the wave, or -1 if wave doesn't exist
    """
    parsed = parse_mib(questFilePath)
    large_monster_tables = parsed.get('large_monster_table', [])
    
    if wave_index < 0 or wave_index >= len(large_monster_tables):
        return -1
    
    return len(large_monster_tables[wave_index])

def get_waves_with_multiple_monsters(questFilePath: str) -> list:
    """
    Returns a list of wave indices that contain 2 or more monsters.
    
    Args:
        questFilePath: Path to the quest file
    
    Returns:
        list: List of wave indices with 2+ monsters
    """
    parsed = parse_mib(questFilePath)
    large_monster_tables = parsed.get('large_monster_table', [])
    
    waves_with_multiple = []
    for wave_idx, wave in enumerate(large_monster_tables):
        if len(wave) >= 2:
            waves_with_multiple.append(wave_idx)
    
    return waves_with_multiple

def has_wave_with_multiple_monsters(questFilePath: str) -> bool:
    """
    Checks if any wave contains 2 or more monsters.
    
    Args:
        questFilePath: Path to the quest file
    
    Returns:
        bool: True if any wave has 2+ monsters, False otherwise
    """
    return len(get_waves_with_multiple_monsters(questFilePath)) > 0

def enforce_max_two_monsters_per_wave(questFilePath: str) -> bool:
    """
    Ensures that no wave contains more than two monsters.

    Strategy:
    - For any wave with 3+ monsters, move extras (index >= 2) into empty waves.
    - If there is no empty wave and we have fewer than 3 waves, create a new empty wave.
    - If all waves are occupied and cannot accept more monsters, remove extras to enforce the cap.

    Returns:
    - True if the quest now satisfies the max-two rule for all waves; False otherwise.

    Notes:
    - Uses existing helpers: parse_mib, createEmptyWave, delete_from_large_table, get_large_monster_by_indices.
    - Prefers relocation over deletion when possible.
    """
    try:
        changed = False
        parsed = parse_mib(questFilePath)
        large_tables = parsed.get('large_monster_table', [])

        if large_tables is None:
            print("[ERROR] No large monster tables parsed.")
            return False

        # Helper to find an empty wave (including placeholder-only wave)
        def _find_empty_wave(tables) -> int:
            for idx, wave in enumerate(tables):
                if len(wave) == 0:
                    return idx
                if len(wave) == 1 and wave[0].get('monster_id') == 1:
                    return idx
            return -1

        # Strict deletion: for each violating wave, repeatedly delete from the end
        # until only two monsters remain.
        max_iterations = 10
        for _ in range(max_iterations):
            parsed = parse_mib(questFilePath)
            large_tables = parsed.get('large_monster_table', [])

            any_violation = False
            for w_idx, wave in enumerate(large_tables):
                # Repeatedly delete extras from the end of the wave
                while len(wave) > 2:
                    any_violation = True
                    # Refresh to get current state and last monster
                    parsed = parse_mib(questFilePath)
                    large_tables = parsed.get('large_monster_table', [])
                    wave = large_tables[w_idx]
                    last_pos = len(wave) - 1
                    monster = wave[last_pos]
                    monster_id = monster.get('monster_id', 0)
                    print(f"[WARN] Deleting extra monster {monster_id} from wave {w_idx} pos {last_pos}")
                    src_mon_info = {
                        'table_index': w_idx,
                        'monster_index': last_pos,
                        'monster_id': monster_id
                    }
                    deleted = delete_from_large_table(questFilePath, src_mon_info)
                    if not deleted:
                        print(f"[ERROR] Failed to delete extra monster {monster_id} at wave {w_idx} pos {last_pos}")
                        return False
                    changed = True

            if not any_violation:
                return True

        print("[ERROR] Max iterations reached while enforcing wave limits")
        return False

    except Exception as e:
        print(f"[CRITICAL] enforce_max_two_monsters_per_wave failed: {e}")
        return False

def get_monster_wave_position(questFilePath: str, monster_id: int) -> tuple:
    """
    Returns the wave and position of a specific monster.
    
    Args:
        questFilePath: Path to the quest file
        monster_id: ID of the monster to find
    
    Returns:
        tuple: (wave_index, position_index) or None if not found
        
    Example:
        wave_idx, pos_idx = get_monster_wave_position(quest_path, 24)
        if wave_idx is not None:
            print(f"Monster found in wave {wave_idx}, position {pos_idx}")
        else:
            print("Monster not found")
    """
    try:
        parsed = parse_mib(questFilePath)
        large_monster_tables = parsed.get('large_monster_table', [])
        
        for wave_idx, wave in enumerate(large_monster_tables):
            for pos_idx, monster in enumerate(wave):
                if monster.get('monster_id') == monster_id:
                    logger.debug(f"Found monster {monster_id} in wave {wave_idx}, position {pos_idx}")
                    return (wave_idx, pos_idx)
        
        logger.debug(f"Monster {monster_id} not found in any wave")
        return None
    except Exception as e:
        logger.error(f"Error finding monster {monster_id}: {e}")
        return None

def print_wave_summary(questFilePath: str):
    """
    Prints a summary of all waves and their monsters.
    
    Args:
        questFilePath: Path to the quest file
    """
    parsed = parse_mib(questFilePath)
    large_monster_tables = parsed.get('large_monster_table', [])
    
    print(f"[INFO] Wave Summary for {os.path.basename(questFilePath)}:")
    print(f"[INFO] Total waves: {len(large_monster_tables)}")
    
    for wave_idx, wave in enumerate(large_monster_tables):
        print(f"[INFO] Wave {wave_idx}: {len(wave)} monster(s)")
        for pos_idx, monster in enumerate(wave):
            monster_id = monster.get('monster_id', 0)
            monster_name = VariousLists.getMonsterName(monster_id)
            print(f"[INFO]   Position {pos_idx}: {monster_name} (ID: {monster_id})")

def remove_placeholders_from_populated_waves(questFilePath: str) -> int:
    """
    Removes placeholder monsters (ID: 1) from any wave that also contains real monsters.
    Returns the number of placeholders removed.
    """
    try:
        parsed = parse_mib(questFilePath)
        large_monster_tables = parsed.get('large_monster_table', [])
        removed = 0
        for wave_idx, wave in enumerate(large_monster_tables):
            if len(wave) > 1:
                # If a placeholder co-exists with other monsters, delete the placeholder
                for pos_idx, monster in enumerate(list(wave)):
                    if monster.get('monster_id') == 1:
                        src_mon_info = {
                            'table_index': wave_idx,
                            'monster_index': pos_idx,
                            'monster_id': 1
                        }
                        if delete_from_large_table(questFilePath, src_mon_info):
                            removed += 1
                            print(f"[INFO] Removed placeholder (ID:1) from wave {wave_idx} position {pos_idx}")
                        else:
                            print(f"[WARN] Failed to remove placeholder from wave {wave_idx} pos {pos_idx}")
        return removed
    except Exception as e:
        print(f"[ERROR] remove_placeholders_from_populated_waves failed: {e}")
        return 0

def move_monster_to_empty_table(questFilePath: str, monster_id: int, target_wave: int):
    """
    SAFELY moves a monster to a completely empty table/wave.
    
    SECURITY FEATURES:
    - Only works if the target table is COMPLETELY EMPTY
    - Does not allow moving if there are any monsters in the target table
    - Verifies that the monster exists in another table
    - Maintains terminator integrity
    - Does not exceed the limit of 2 monsters per wave
    - Ensures file has enough space for the monster struct and terminator
    
    Args:
        questFilePath: Path to the quest file
        monster_id: ID of the monster to move
        target_wave: Target wave (0-2) that must be EMPTY
    
    Returns:
        bool: True if movement was successful, False otherwise
    """
    try:
        # Parse the quest file
        parsed = parse_mib(questFilePath)
        large_monster_tables = parsed.get('large_monster_table', [])
        
        # Basic validations
        if not large_monster_tables:
            print(f"[ERROR] No large monster tables found.")
            return False
        
        # Validate target_wave
        if target_wave < 0 or target_wave >= len(large_monster_tables):
            print(f"[ERROR] Invalid target wave {target_wave}. Must be between 0 and {len(large_monster_tables) - 1}.")
            return False
        
        target_table = large_monster_tables[target_wave]
        
        # Allow a placeholder monster (ID: 1) to be treated as empty
        is_placeholder = (len(target_table) == 1 and target_table[0].get('monster_id') == 1)
        if (len(target_table) != 0) and not is_placeholder:
            print(f"[ERROR] Wave {target_wave} is NOT empty. It has {len(target_table)} monster(s).")
            print(f"[INFO] This function only moves monsters to COMPLETELY EMPTY waves or a wave with a placeholder (ID: 1).")
            return False
        
        # Find the source monster
        source_wave = -1
        source_position = -1
        source_monster_dict = None
        
        for wave_idx, wave in enumerate(large_monster_tables):
            for pos_idx, monster in enumerate(wave):
                if monster.get('monster_id') == monster_id:
                    source_wave = wave_idx
                    source_position = pos_idx
                    source_monster_dict = monster
                    break
            if source_wave != -1:
                break
        
        if source_wave == -1:
            print(f"[ERROR] Monster ID {monster_id} not found in any wave.")
            return False
        
        # Verify we're not trying to move to the same wave
        if source_wave == target_wave:
            print(f"[ERROR] The monster is already in wave {target_wave}.")
            return True  # Consider this a success since it's already where we want it
        
        print(f"[INFO] Moving monster {monster_id} from wave {source_wave} position {source_position} to wave {target_wave} (empty)")
        # Track original source wave monster count for verification
        num_monsters_in_source = len(large_monster_tables[source_wave])
        
        # Get table addresses
        table_addresses = get_large_monster_table_addresses(questFilePath)
        
        # CALCULATE OFFSETS
        source_table_addr = table_addresses[source_wave]
        source_offset = source_table_addr + source_position * MONSTER_STRUCT_SIZE
        
        target_table_addr = table_addresses[target_wave]
        target_offset = target_table_addr  # Position 0 in empty table
        
        # Check if file has enough space for monster struct + terminator
        file_size = os.path.getsize(questFilePath)
        needed_space = target_offset + MONSTER_STRUCT_SIZE + 4  # Monster struct + terminator
        
        if needed_space > file_size:
            # File needs to be extended
            print(f"[INFO] File needs extension to accommodate monster at position 0 in wave {target_wave}")
            extension_size = needed_space - file_size + 16  # Add padding
            
            # Extend the file with zeros
            with open(questFilePath, 'ab') as f:
                f.write(b'\x00' * extension_size)
                
            print(f"[INFO] Extended file by {extension_size} bytes")
        
        # STEP 0: COPY METADATA STATS to destination index (do NOT remove from source)
        try:
            src_meta_idx = calculate_metadata_index(questFilePath, source_wave, source_position)
            dst_meta_idx = calculate_metadata_index(questFilePath, target_wave, 0)
            src_stats = read_meta_entry(questFilePath, src_meta_idx)
            write_stats_from_dict(questFilePath, dst_meta_idx, src_stats)
        except Exception as meta_err:
            print(f"[WARN] Could not copy metadata entry: {meta_err}")

        # STEP 1: WRITE MONSTER TO DESTINATION (position 0)
        print(f"[DEBUG] Writing monster to destination: offset 0x{target_offset:X}")
        write_monster_struct_at(questFilePath, target_offset, source_monster_dict)
        
        # STEP 2: WRITE TERMINATOR at destination (position 1)
        terminator_offset = target_offset + MONSTER_STRUCT_SIZE
        print(f"[DEBUG] Writing terminator at destination: offset 0x{terminator_offset:X}")
        write_dword_at(questFilePath, terminator_offset, 0xFFFFFFFF)
        
        # NOTE: Do NOT clean up source here. Caller may decide how to handle duplicates.
        
        # FINAL VERIFICATION
        print(f"[INFO] Verifying the movement...")
        try:
            updated_parsed = parse_mib(questFilePath)
            updated_target = updated_parsed.get('large_monster_table', [])
            
            # Check if target wave exists
            if target_wave >= len(updated_target):
                print(f"[ERROR] Target wave {target_wave} doesn't exist after movement")
                return False
                
            target_monsters = updated_target[target_wave]
            
            # Check if source wave exists
            if source_wave >= len(updated_target):
                print(f"[ERROR] Source wave {source_wave} doesn't exist after movement")
                return False
                
            source_monsters = updated_target[source_wave]
            
            # Verify destination has exactly 1 monster
            if len(target_monsters) != 1:
                print(f"[ERROR] Target wave should have 1 monster, but has {len(target_monsters)}")
                return False
            
            # Verify the correct monster is in the destination
            if len(target_monsters) > 0 and target_monsters[0].get('monster_id') != monster_id:
                print(f"[ERROR] Monster in destination doesn't match: expected {monster_id}, found {target_monsters[0].get('monster_id')}")
                return False
            
            # Verify source wave remains unchanged (cleanup handled by caller/tests)
            if len(source_monsters) != num_monsters_in_source:
                print(f"[ERROR] Source wave should remain at {num_monsters_in_source} monsters, but has {len(source_monsters)}")
                return False
            
            print(f"[SUCCESS] Monster {monster_id} successfully moved to empty wave {target_wave}")
            print(f"[RESULT] Wave {target_wave} now has: {VariousLists.getMonsterName(monster_id)}")
            print(f"[RESULT] Wave {source_wave} now has: {len(source_monsters)} monster(s)")
            
            return True
            
        except Exception as verify_error:
            print(f"[ERROR] Verification failed: {verify_error}")
            return False
        
    except Exception as e:
        print(f"[CRITICAL ERROR] Error during movement: {e}")
        print(f"[INFO] Recommendation: Restore file from backup")
        return False
        
def createEmptyWave(questFilePath: str, default_monster_id: int = 0):
    """
    Creates a new truly empty wave (table) in the quest file.

    Behavior:
    - Writes only a terminator (TERMINATOR_DWORD) for the new table; no placeholder entry.
    - Keeps overall monster counts stable until something is moved into this wave.
    - Compatible with movers that require a completely empty destination.

    Args:
        questFilePath: Path to the quest file
        default_monster_id: Ignored; maintained for backward compatibility. Default 0.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Parse the quest file to get current state (sanity check)
        parsed = parse_mib(questFilePath)
        _ = parsed.get('large_monster_table', [])

        # Get file size for alignment and bounds checking
        file_size = os.path.getsize(questFilePath)

        # 1) Create a new table containing only the terminator dword
        aligned_size = ((file_size + FILE_ALIGNMENT - 1) // FILE_ALIGNMENT) * FILE_ALIGNMENT
        new_table_addr = aligned_size

        terminator = struct.pack("<I", TERMINATOR_DWORD)

        # 2) Write the new empty table at EOF (aligned)
        with open(questFilePath, 'r+b') as f:
            f.seek(aligned_size)
            f.write(terminator)
            f.flush()
            os.fsync(f.fileno())

        # 3) Update the large monster table pointer list
        base_ptr_list_addr = read_dword(questFilePath, 0x28)
        if base_ptr_list_addr == 0:
            logger.error(f"Invalid large monster table pointer at offset 0x28")
            return False

        table_addresses = read_dword_array_until_zero(questFilePath, base_ptr_list_addr)
        ptr_offset = base_ptr_list_addr + len(table_addresses) * 4
        
        # Write new table address and refresh terminator
        write_dword_at(questFilePath, ptr_offset, new_table_addr)
        write_dword_at(questFilePath, ptr_offset + 4, POINTER_LIST_TERMINATOR)

        logger.info(f"Successfully created new EMPTY wave {len(table_addresses)} at address 0x{new_table_addr:X}")
        return True

    except Exception as e:
        logger.error(f"Failed to create empty wave: {e}")
        return False


def insertEmptyWave(questFilePath: str, insert_index: int, default_monster_id: int = 0) -> bool:
    """
    Inserts a new truly empty wave (table) at a specific position, pushing subsequent waves forward.

    Inspired by createEmptyWave, but allows selecting the position of the new wave.

    Example:
    Given waves: [1], [2,3] and insert_index=1 -> result: [1], [], [2,3]

    Behavior:
    - Creates a new table containing only the terminator (TERMINATOR_DWORD), no placeholder entry.
    - Appends the new table at EOF (aligned) and inserts its pointer into the pointer list at the given index.
    - Shifts pointers of existing waves at and after insert_index one position to the right.

    Args:
        questFilePath: Path to the quest file.
        insert_index: Zero-based position to insert the new empty wave.
        default_monster_id: Ignored; maintained for backward compatibility. Default 0.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Parse quest for sanity and to ensure file looks valid
        parsed = parse_mib(questFilePath)
        _ = parsed.get('large_monster_table', [])

        # Get pointer list base
        base_ptr_list_addr = read_dword(questFilePath, 0x28)
        if base_ptr_list_addr == 0:
            logger.error("Invalid large monster table pointer at offset 0x28")
            return False

        # Read existing table addresses
        table_addresses = read_dword_array_until_zero(questFilePath, base_ptr_list_addr)

        # Clamp insert index
        if insert_index < 0:
            insert_index = 0
        if insert_index > len(table_addresses):
            insert_index = len(table_addresses)

        # Compute aligned EOF for the new empty table
        file_size = os.path.getsize(questFilePath)
        aligned_size = ((file_size + FILE_ALIGNMENT - 1) // FILE_ALIGNMENT) * FILE_ALIGNMENT
        new_table_addr = aligned_size

        # New table content: just the terminator
        terminator = struct.pack("<I", TERMINATOR_DWORD)

        # Write the new empty table at EOF
        with open(questFilePath, 'r+b') as f:
            f.seek(aligned_size)
            f.write(terminator)
            f.flush()
            os.fsync(f.fileno())

        # Build new pointer list with the inserted address
        new_addresses = list(table_addresses)
        new_addresses.insert(insert_index, new_table_addr)

        # Rewrite the pointer list (addresses followed by terminator)
        for i, addr in enumerate(new_addresses):
            write_dword_at(questFilePath, base_ptr_list_addr + i * 4, addr)
        write_dword_at(questFilePath, base_ptr_list_addr + len(new_addresses) * 4, POINTER_LIST_TERMINATOR)

        logger.info(
            f"Successfully inserted new EMPTY wave at position {insert_index} "
            f"address 0x{new_table_addr:X}; total waves now {len(new_addresses)}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to insert empty wave at position {insert_index}: {e}")
        return False

def deleteLastWave(questFilePath: str):
    """
    Deletes the last wave (table) from the quest file.
    
    Args:
        questFilePath: Path to the quest file
        
    Returns:
        bool: True if successful, False otherwise
        
    Note:
        - This function removes the last wave in the large_monster_table
        - It does not physically delete data from the file, only updates pointers
        - At least one wave must remain after deletion
    """
    try:
        # Parse the quest file to get current state
        parsed = parse_mib(questFilePath)
        large_monster_tables = parsed.get('large_monster_table', [])
        
        # Check if we have enough waves to delete one (must keep at least 1)
        if len(large_monster_tables) <= 1:
            print(f"[ERROR] Cannot delete last wave: at least one wave must remain.")
            return False
            
        # Get the large monster table pointer list address
        base_ptr_list_addr = read_dword(questFilePath, 0x28)
        if base_ptr_list_addr == 0:
            print(f"[ERROR] Invalid large monster table pointer at offset 0x28")
            return False
            
        # Read existing pointers
        table_addresses = read_dword_array_until_zero(questFilePath, base_ptr_list_addr)
        
        # Calculate where to write the new terminator (overwrite last pointer)
        # Each pointer is 4 bytes
        new_terminator_offset = base_ptr_list_addr + (len(table_addresses) - 1) * 4
        
        # Write new terminator (0) to effectively remove the last wave
        write_dword_at(questFilePath, new_terminator_offset, 0)
        
        print(f"[INFO] Successfully deleted wave {len(table_addresses) - 1}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to delete last wave: {e}")
        return False

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
