# test_questeditor_main.py
import os
import shutil
import sys
from pathlib import Path
import QuestEditor

def resolve_path(user_input: str) -> str:
    path = user_input.strip()
    if not path:
        raise SystemExit("No file provided.")
    if os.path.isabs(path):
        return path
    # if not absolute, assume inside loc/quest using your convention
    qf = QuestEditor.getQuestFolder()
    return os.path.join(qf, path)

def backup_file(path: str) -> str:
    bak = path + ".bak"
    shutil.copy2(path, bak)
    print(f"[INFO] Backup created: {bak}")
    return bak

def restore_backup(path: str, bak: str):
    shutil.copy2(bak, path)
    os.remove(bak)
    print(f"[INFO] Restored original from backup and removed {bak}")

def safe_read(func, *args):
    try:
        return func(*args)
    except Exception as e:
        print(f"[ERROR] {func.__name__} failed: {e}")
        return None

def main():
    print("Enter path to quest file (absolute) or filename inside loc/quest:")
    user = input("> ").strip()
    try:
        quest_path = resolve_path(user)
    except Exception as e:
        print("Error resolving path:", e)
        return

    if not os.path.exists(quest_path):
        print("File not found:", quest_path)
        return

    print(f"[INFO] Testing file: {quest_path}")
    bak = backup_file(quest_path)

    try:
        # ----- READS (non-destructive) -----
        print("\n=== READ TESTS ===")
        header_addr = safe_read(QuestEditor.get_header_addr, quest_path)
        if header_addr is not None:
            print(f"header_addr = 0x{header_addr:X}")

        # dynamic offsets helper
        dyn = lambda rel: QuestEditor.get_dynamic_absolute_offset(quest_path, rel)

        # read quest_type (dynamic 0xA0)
        qt = safe_read(QuestEditor.read_byte, quest_path, dyn(0xA0))
        print(f"quest_type (dynamic 0xA0) = {qt}")

        # map id (dynamic 0xC4)
        map_id = safe_read(QuestEditor.read_byte, quest_path, dyn(0xC4))
        print(f"map_id (dynamic 0xC4) = {map_id}")

        # quest id (dynamic 0xC0)
        qid = safe_read(QuestEditor.read_word, quest_path, dyn(0xC0))
        print(f"quest_id (dynamic 0xC0) = {qid}")

        # hrp values (absolute)
        hrp = safe_read(QuestEditor.read_dword, quest_path, 0x74)
        hrp_red = safe_read(QuestEditor.read_dword, quest_path, 0x78)
        hrp_sub = safe_read(QuestEditor.read_dword, quest_path, 0x7C)
        print(f"hrp={hrp}, hrp_reduction={hrp_red}, hrp_sub={hrp_sub}")

        # loot pointers
        loot_a = safe_read(QuestEditor.read_dword, quest_path, 0x1C)
        loot_b = safe_read(QuestEditor.read_dword, quest_path, 0x20)
        loot_c = safe_read(QuestEditor.read_dword, quest_path, 0x24)
        print(f"loot pointers: A=0x{loot_a:X} B=0x{loot_b:X} C=0x{loot_c:X}")

        # large monster table addresses
        large_addrs = QuestEditor.get_large_monster_table_addresses(quest_path)
        table_addresses, counts, total = QuestEditor.count_large_monsters(quest_path)
        print(f"large_monster_table top entries: {len(table_addresses)} (addresses: {table_addresses})")
        print(f"monsters per table: {counts} -> total large monsters = {total}")
        # optionally print which table holds >1 monsters
        for i, c in enumerate(counts):
            if c > 1:
                print(f" note: table[{i}] at 0x{table_addresses[i]:X} contains {c} monsters")

        # small monster table addresses
        small_addrs = safe_read(QuestEditor.get_small_monster_table_addresses, quest_path)
        if small_addrs is not None:
            print(f"small_monster_table has {len(small_addrs)} entries, first addrs: {small_addrs[:5]}")

        # ----- WRITES (will be reverted at the end) -----
        print("\n=== WRITE TESTS (will be reverted) ===")

        # 1) Toggle map id (write then read)
        try:
            if map_id is None:
                raise RuntimeError("cannot read original map_id")
            new_map = (map_id ^ 1) & 0xFF
            QuestEditor.set_map_id_dynamic(quest_path, new_map)
            readback = QuestEditor.read_byte(quest_path, dyn(0xC4))
            print(f"[WRITE] set_map_id_dynamic -> wrote {new_map}, readback {readback}")
        except Exception as e:
            print(f"[ERROR] set_map_id_dynamic failed: {e}")

        # 2) Toggle quest_type bit (flip low bit)
        try:
            if qt is None:
                raise RuntimeError("cannot read original quest_type")
            new_qt = qt ^ 1
            QuestEditor.set_quest_type(quest_path, new_qt)
            rb = QuestEditor.read_byte(quest_path, dyn(0xA0))
            print(f"[WRITE] set_quest_type -> wrote {new_qt}, readback {rb}")
        except Exception as e:
            print(f"[ERROR] set_quest_type failed: {e}")

        # 3) Set a refill entry (index 0)
        try:
            QuestEditor.set_refill_entry(quest_path, 0, box=1, condition=0, monster=2, qty=3)
            box = QuestEditor.read_byte(quest_path, 0x0C + 8 * 0 + 0)
            cond = QuestEditor.read_byte(quest_path, 0x0C + 8 * 0 + 1)
            mon = QuestEditor.read_byte(quest_path, 0x0C + 8 * 0 + 2)
            qty = QuestEditor.read_byte(quest_path, 0x0C + 8 * 0 + 4)
            print(f"[WRITE] set_refill_entry(0) -> box={box}, cond={cond}, mon={mon}, qty={qty}")
        except Exception as e:
            print(f"[ERROR] set_refill_entry failed: {e}")

        # 4) Set small monster condition 0
        try:
            QuestEditor.set_small_monster_condition(quest_path, 0, type_val=1, target=0x20, qty=5, group=0)
            t = QuestEditor.read_byte(quest_path, 0x64 + 8*0 + 0)
            targ = QuestEditor.read_word(quest_path, 0x64 + 8*0 + 4)
            qv = QuestEditor.read_byte(quest_path, 0x64 + 8*0 + 6)
            print(f"[WRITE] set_small_monster_condition(0) -> type={t}, target=0x{targ:X}, qty={qv}")
        except Exception as e:
            print(f"[ERROR] set_small_monster_condition failed: {e}")

        # 5) Write meta entry 0 (size) and read back
        try:
            QuestEditor.write_meta_entry(quest_path, 0, size=0x1234)
            size0 = QuestEditor.read_word(quest_path, 0x34 + 0*8)
            print(f"[WRITE] write_meta_entry idx0 size -> read {hex(size0)}")
        except Exception as e:
            print(f"[ERROR] write_meta_entry failed: {e}")

        # 6) Write small_meta (example) and read back
        try:
            QuestEditor.write_small_meta(quest_path, size=0x2222, hp=77)
            s = QuestEditor.read_word(quest_path, 0x5C)
            hp = QuestEditor.read_byte(quest_path, 0x5C + 3)
            print(f"[WRITE] write_small_meta -> size=0x{s:X}, hp={hp}")
        except Exception as e:
            print(f"[ERROR] write_small_meta failed: {e}")

        # 7) If large table present, write first monster struct (non-destructive values)
        try:
            if large_addrs and len(large_addrs) > 0:
                mbase = large_addrs[0]
                # read original first monster_id if exists
                orig_id = QuestEditor.read_dword(quest_path, mbase + 0x00)
                print(f"[INFO] original first monster_id at 0x{mbase:X} = 0x{orig_id:X}")
                # write same id back but with different coords so we test pack/write/read
                monster = {"monster_id": orig_id, "qty": 1, "area": 1, "x": 1.234, "y": 2.345, "z": 3.456}
                QuestEditor.write_monster_in_large_table(quest_path, table_index=0, monster_index=0, monster=monster)
                read_id = QuestEditor.read_dword(quest_path, mbase + 0x00)
                print(f"[WRITE] write_monster_in_large_table -> wrote monster_id 0x{read_id:X}")
            else:
                print("[SKIP] no large monster table addresses found")
        except Exception as e:
            print(f"[ERROR] write_monster_in_large_table failed: {e}")

        # 8) Set loot pointer A to itself (test writer)
        try:
            if loot_a is not None:
                QuestEditor.set_loot_table_pointer(quest_path, 'a', loot_a)
                ptr = QuestEditor.read_dword(quest_path, 0x1C)
                print(f"[WRITE] set_loot_table_pointer('a') -> pointer at 0x1C = 0x{ptr:X}")
            else:
                print("[SKIP] no loot_a pointer read")
        except Exception as e:
            print(f"[ERROR] set_loot_table_pointer failed: {e}")

        print("\n[INFO] All tests executed. Restoring original file from backup...")

        from QuestEditor import pretty_print_quest_summary, parse_mib
        print("\n\n\n")
        pretty_print_quest_summary("loc/quest/m11037.1BBFD18E")
    finally:
        # restore original file from backup to leave filesystem unchanged
        try:
            restore_backup(quest_path, bak)
            print("[DONE] Backup restored. Tests completed.")
        except Exception as e:
            print("[FATAL] Could not restore backup:", e)
            print("Your file may have been modified. Backup located at:", bak)

if __name__ == "__main__":
    main()