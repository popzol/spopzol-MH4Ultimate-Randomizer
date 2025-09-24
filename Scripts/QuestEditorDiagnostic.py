# diagnostic_dump.py
import QuestEditor
import struct
import os

def dump_dword(addr):
    return hex(addr)

def read_dword_local(path, offset):
    return QuestEditor.read_dword(path, offset)

def dump_large_monster_tables(path):
    print("---- Large monster table (top) ----")
    base_ptr_list_addr = QuestEditor.read_dword(path, 0x28)
    print(f"pointer list @ 0x28 -> 0x{base_ptr_list_addr:X}")
    addrs = QuestEditor.read_dword_array_until_zero(path, base_ptr_list_addr)
    print(f"top-table entries: {len(addrs)}")
    for ti, a in enumerate(addrs):
        print(f" table[{ti}] addr = 0x{a:X}")
        # iterate monsters in this array
        idx = 0
        monsters = []
        while True:
            off = a + idx*0x28
            mid = QuestEditor.read_dword(path, off)
            if mid == 0xFFFFFFFF or mid == 0xFFFFFFFF:  # termination convention in JS = -1
                break
            monsters.append(mid)
            idx += 1
            if idx > 200:
                print("  > too many entries (safety break)")
                break
        print(f"  -> monsters count = {len(monsters)}  ids: {[hex(m) for m in monsters]}")
    return addrs

def dump_small_monster_top_ptrs(path):
    print("---- Small monster table (top pointers) ----")
    base_ptr = QuestEditor.read_dword(path, 0x2C)
    print(f"pointer to top array @ 0x2C = 0x{base_ptr:X}")
    raw = []
    pos = base_ptr
    # read 20 dwords max (stop at 0)
    for i in range(0, 40):
        try:
            val = QuestEditor.read_dword(path, pos + i*4)
        except Exception:
            break
        raw.append(val)
        if val == 0:
            break
    print("raw dwords from top (until 0):", [hex(x) for x in raw])
    return raw

def dump_unstable_table(path):
    print("---- Unstable monster table ----")
    base = QuestEditor.read_dword(path, 0x30)
    print(f"base = 0x{base:X}")
    idx = 0
    entries = []
    while True:
        chance = QuestEditor.read_word(path, base + idx*0x2C)
        if chance == 0xFFFF:
            break
        # monster struct at base + idx*0x2C + 4
        mid = QuestEditor.read_dword(path, base + idx*0x2C + 4)
        entries.append((idx, chance, mid))
        idx += 1
        if idx > 200:
            break
    print("entries (idx, chance, monster_id):", [(e[0], hex(e[1]), hex(e[2])) for e in entries])
    return entries

def dump_monster_struct_at(path, absolute_offset):
    # return a dict like parse_monster
    monster = {}
    monster['monster_id'] = QuestEditor.read_dword(path, absolute_offset + 0x00)
    monster['qty']        = QuestEditor.read_dword(path, absolute_offset + 0x04)
    monster['condition']  = QuestEditor.read_byte(path, absolute_offset + 0x08)
    monster['area']       = QuestEditor.read_byte(path, absolute_offset + 0x09)
    monster['x']          = QuestEditor.read_float(path, absolute_offset + 0x10)
    monster['y']          = QuestEditor.read_float(path, absolute_offset + 0x14)
    monster['z']          = QuestEditor.read_float(path, absolute_offset + 0x18)
    return monster

def raw_hex_dump(path, addr, length=64):
    with open(path, "rb") as f:
        f.seek(addr)
        data = f.read(length)
    print(f"Raw @ 0x{addr:X} (len {len(data)}):", data.hex())

def main():
    print("Enter filename or full path:")
    p = input("> ").strip()
    if not os.path.isabs(p):
        p = os.path.join(QuestEditor.getQuestFolder(), p)
    if not os.path.exists(p):
        print("File not found:", p); return
    print("DEBUG file:", p)

    large_addrs = dump_large_monster_tables(p)
    raw_small_ptrs = dump_small_monster_top_ptrs(p)
    unstable = dump_unstable_table(p)

    # If large_addrs exist, dump the first few monster structs bytes
    if large_addrs:
        for i,a in enumerate(large_addrs):
            print(f"\n-- dump monsters in large array {i} at 0x{a:X} --")
            for mi in range(0, 8):
                off = a + mi*0x28
                mid = QuestEditor.read_dword(p, off)
                if mid == 0xFFFFFFFF:
                    print(f"  entry {mi}: TERMINATOR (0xFFFFFFFF)")
                    break
                mon = dump_monster_struct_at(p, off)
                print(f"  entry {mi}: id=0x{mon['monster_id']:X} qty={mon['qty']} area={mon['area']} pos=({mon['x']:.3f},{mon['y']:.3f},{mon['z']:.3f})")

    # dump raw around first large addr, and around base pointers
    if large_addrs:
        raw_hex_dump(p, large_addrs[0], 128)
    if raw_small_ptrs:
        if raw_small_ptrs[0] != 0:
            raw_hex_dump(p, raw_small_ptrs[0], 128)

if __name__ == "__main__":
    main()