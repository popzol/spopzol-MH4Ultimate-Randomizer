import QuestEditor
import os
import tempfile

def make_dummy_file(size=0x1000):
    fd, path = tempfile.mkstemp(suffix=".mib")
    with os.fdopen(fd, "wb") as f:
        f.write(b"\x00" * size)
    return path

def test_all():
    path = make_dummy_file()
    try:
        # Write header pointer
        QuestEditor.write_dword_at(path, 0x00, 0x200)
        # Write large monster table pointer
        QuestEditor.write_dword_at(path, 0x28, 0x300)
        # Write a top-table with one table pointer
        QuestEditor.write_dword_at(path, 0x300, 0x400)
        QuestEditor.write_dword_at(path, 0x304, 0x0)
        # Write a monster struct with id=1 at 0x400
        QuestEditor.write_dword_at(path, 0x400, 1)
        QuestEditor.write_dword_at(path, 0x404, 1)
        QuestEditor.write_byte_at(path, 0x409, 5) # area
        QuestEditor.write_float_at(path, 0x410, 1.23)
        QuestEditor.write_float_at(path, 0x418, 4.56)
        QuestEditor.write_dword_at(path, 0x400 + 0x28, 0xFFFFFFFF) # terminator

        # Test header/dynamic setters
        QuestEditor.set_quest_type(path, 2)
        assert QuestEditor.read_byte(path, QuestEditor.get_dynamic_absolute_offset(path, 0xA0)) == 2

        QuestEditor.set_header_flag_bit(path, 0xA1, 1, True)
        val = QuestEditor.read_byte(path, QuestEditor.get_dynamic_absolute_offset(path, 0xA1))
        assert (val & (1 << 1)) != 0

        QuestEditor.set_fee(path, 5000)
        assert QuestEditor.read_dword(path, QuestEditor.get_dynamic_absolute_offset(path, 0xA4)) == 5000

        QuestEditor.set_reward_main(path, 10000)
        assert QuestEditor.read_dword(path, QuestEditor.get_dynamic_absolute_offset(path, 0xA8)) == 10000

        QuestEditor.set_time_limit(path, 1800)
        assert QuestEditor.read_dword(path, QuestEditor.get_dynamic_absolute_offset(path, 0xB4)) == 1800

        QuestEditor.set_map_id_dynamic(path, 3)
        assert QuestEditor.read_byte(path, QuestEditor.get_dynamic_absolute_offset(path, 0xC4)) == 3

        QuestEditor.set_quest_id(path, 1234)
        assert QuestEditor.read_word(path, QuestEditor.get_dynamic_absolute_offset(path, 0xC0)) == 1234

        QuestEditor.set_objective_qty(path, 0, 2)
        assert QuestEditor.read_word(path, QuestEditor.get_dynamic_absolute_offset(path, 0xCC) + 6) == 2

        # Test monster struct write/read
        monster = {
            "monster_id": 2, "qty": 1, "area": 7, "x": 2.2, "y": 3.3, "z": 4.4,
            "condition": 0, "crashflag": 0, "special": 0, "unk2": 0, "unk3": 0, "unk4": 0, "infection": 0,
            "x_rot": 0, "y_rot": 0, "z_rot": 0
        }
        QuestEditor.write_monster_struct_at(path, 0x400, monster)
        m = QuestEditor.unpack_monster_struct(QuestEditor._read_bytes(path, 0x400, 0x28))
        assert m['monster_id'] == 2 and m['area'] == 7 and abs(m['x'] - 2.2) < 0.01

        # Test large monster table functions
        QuestEditor.write_monster_in_large_table(path, 0, 0, monster)
        addr, counts, total = QuestEditor.count_large_monsters(path)
        assert addr[0] == 0x400 and counts[0] == 1 and total == 1

        # Test meta table
        QuestEditor.write_meta_entry(path, 0, size=100, hp=200)
        assert QuestEditor.read_word(path, 0x34) == 100
        assert QuestEditor.read_byte(path, 0x34 + 3) == 200

        QuestEditor.write_small_meta(path, size=50, hp=100)
        assert QuestEditor.read_word(path, 0x5C) == 50
        assert QuestEditor.read_byte(path, 0x5C + 3) == 100

        # Test loot table
        loot = [{'flag': 1, 'items': [{'chance': 100, 'item_id': 2, 'qty': 1}]}]
        loot_addr = QuestEditor.write_loot_table(path, 'a', loot)
        assert QuestEditor.read_dword(path, 0x1C) == loot_addr

        # Test supplies
        supplies = [[{'item_id': 1, 'qty': 2}, {'item_id': 2, 'qty': 3}]]
        supplies_addr = QuestEditor.write_supplies(path, supplies)
        assert QuestEditor.read_dword(path, 0x08) == supplies_addr

        # Test objective helpers
        QuestEditor.set_objective(path, 0, 1, 2, 3)
        obj = QuestEditor.get_objective(path, 0)
        assert obj['type'] == 1 and obj['target_id'] == 2 and obj['qty'] == 3

        QuestEditor.set_objective_amount(path, 2)
        amt = QuestEditor.get_objective_amount(path)
        assert amt == 2

        QuestEditor.clear_all_objectives(path)
        obj0 = QuestEditor.get_objective(path, 0)
        obj1 = QuestEditor.get_objective(path, 1)
        obj2 = QuestEditor.get_objective(path, 2)
        assert obj0['type'] == 0 and obj1['type'] == 0 and obj2['type'] == 0

        # Test position setters
        QuestEditor.set_large_monster_position_by_indices(path, 0, 0, new_x=9.9, new_z=8.8)
        info = QuestEditor.get_large_monster_by_indices(path, 0, 0)
        assert abs(info['x'] - 9.9) < 0.01 and abs(info['z'] - 8.8) < 0.01

        # Test find/replace monster
        QuestEditor.write_monster_struct_at(path, 0x400, {"monster_id": 2, "qty": 1, "area": 1, "x": 1.0, "y": 2.0, "z": 3.0})
        QuestEditor.find_and_replace_monster(path, 2, 3, dry_run=False)
        m = QuestEditor.unpack_monster_struct(QuestEditor._read_bytes(path, 0x400, 0x28))
        assert m['monster_id'] == 3

        QuestEditor.write_monster_struct_at(path, 0x400, {"monster_id": 4, "qty": 1, "area": 1, "x": 1.0, "y": 2.0, "z": 3.0})
        QuestEditor.find_and_replace_monster_individual(path, 4, 5, dry_run=False)
        m = QuestEditor.unpack_monster_struct(QuestEditor._read_bytes(path, 0x400, 0x28))
        assert m['monster_id'] == 5

        # Test verify_tables
        issues = QuestEditor.verify_tables(path, verbose=True)
        assert isinstance(issues, list)

        # Test pretty print
        QuestEditor.pretty_print_quest_summary(path)

        # Test pack/unpack monster struct
        packed = QuestEditor.pack_monster_struct(monster)
        unpacked = QuestEditor.unpack_monster_struct(packed)
        for k in ['monster_id', 'qty', 'area']:
            assert unpacked[k] == monster[k]

        # Test append_aligned
        data = b"hello"
        addr = QuestEditor.append_aligned(path, data, align=0x10)
        with open(path, "rb") as f:
            f.seek(addr)
            assert f.read(len(data)) == data

        # Test changeByteAtOffset_For_In
        QuestEditor.changeByteAtOffset_For_In(0x10, b"\xAA\xBB", path)
        with open(path, "rb") as f:
            f.seek(0x10)
            assert f.read(2) == b"\xAA\xBB"

        # Test last_byte_pos
        last = QuestEditor.last_byte_pos(path)
        assert last == os.path.getsize(path) - 1

        print("All expanded tests completed and passed.")

        # Test monster stats adjustment (like adjustStatsForSolo)
        QuestEditor.write_stats_from_dict(path, 0, {
            'size': 100,
            'size_var': 1,
            'hp': 200,
            'atk': 150,
            'break_res': 10,
            'stamina': 50,
            'status_res': 5
        })
        stats = QuestEditor.read_meta_entry(path, 0)
        assert stats['hp'] == 200
        assert stats['atk'] == 150

        # Adjust stats (reduce hp and atk by 20%)
        adjusted_stats = stats.copy()
        adjusted_stats['hp'] = int(stats['hp'] * 0.8)
        adjusted_stats['atk'] = int(stats['atk'] * 0.8)
        QuestEditor.write_stats_from_dict(path, 0, adjusted_stats)
        stats2 = QuestEditor.read_meta_entry(path, 0)
        assert stats2['hp'] == int(200 * 0.8)
        assert stats2['atk'] == int(150 * 0.8)

    finally:
        os.remove(path)

if __name__ == "__main__":
    test_all()
