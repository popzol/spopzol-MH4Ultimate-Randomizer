# diagnostic_dump_quiet_failures.py
#THIS DOES NOT USE PYTEST
#THIS DOES NOT USE PYTEST
#THIS DOES NOT USE PYTEST
#THIS DOES NOT USE PYTEST
#THIS DOES NOT USE PYTEST
#THIS DOES NOT USE PYTEST
import random
import Randomizer
import VariousLists
import QuestEditor
import os
import sys
import io
import contextlib

# This version runs completely silent (suppresses stdout/stderr) until a failure occurs.
# It captures all stdout/stderr produced by the called functions (per-quest) and
# stores that captured output. If a quest fails, the stored output for that quest
# is printed together with the buffered diagnostic messages. After printing the
# failure details, the runner returns to silent mode and proceeds. At the end of
# the run the final summary is printed and printing remains enabled.

# Keep original stdout/stderr so we can restore and write directly to them.
_original_stdout = sys.stdout
_original_stderr = sys.stderr
ntest = 250

# Helper functions to enable/disable global printing
def _disable_print():
    """Redirect stdout/stderr to a dummy buffer to silence all prints."""
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

def _enable_print():
    """Restore stdout/stderr to the originals so prints show up again."""
    sys.stdout = _original_stdout
    sys.stderr = _original_stderr

def _flush_buffer(buf):
    """Print buffered lines directly to the original stdout."""
    if not buf:
        return
    text = "".join(buf)
    try:
        _original_stdout.write(text)
        _original_stdout.flush()
    except Exception:
        # Fallback: write lines individually
        for line in buf:
            try:
                _original_stdout.write(line)
            except Exception:
                pass

def test_mainTests():
    """
    Comprehensive test function that randomizes quest files and validates:
      - unique monster placement (must be in last non-empty wave, with Akantor/Ukanlos exceptions)
      - arena multi-monster restrictions
      - multiple Dah'ren Mohran detection

    Behavior:
      - Fully silent unless a quest fails. On failure the quest buffer is printed
        immediately and silence resumes.
      - Final summary is always printed at the end and printing remains enabled.
      - "No monsters found after randomization" is a special case (not a failure).
    """
    # Start fully silent
    _disable_print()

    # Reset quest files to original state
    Randomizer.resetQuestFiles()

    # Set a test seed for reproducible-ish results
    seed = random.randint(0, 1000000)
    Randomizer.setSeed(seed)

    # Get quest folder
    quest_folder = Randomizer.getQuestFolder()

    # Process up to ntest quest files for testing
    quest_files = [f for f in os.listdir(quest_folder) if f.endswith('.1BBFD18E')][:ntest]

    # Statistics tracking
    total_quests = len(quest_files)
    successful_quests = 0
    error_count = 0
    validation_errors = 0
    special_cases = 0
    failedCases = []

    # Precompute special unique mapping for Akantor/Ukanlos
    akantor_ukanlos_list = VariousLists.akantorAndUkanlos() if hasattr(VariousLists, 'akantorAndUkanlos') else [33, 116]
    special_map_for = {33: 9, 116: 20}

    for quest_idx, quest_file in enumerate(quest_files, 1):
        # Buffer for this quest's messages — only printed if this quest fails.
        buf = []
        buf.append('=' * 80 + '\n')
        buf.append(f'[TESTING] Quest {quest_idx}/{total_quests}: {quest_file}\n')
        buf.append('=' * 80 + '\n')

        full_path = os.path.join(quest_folder, quest_file)
        quest_passed = True
        current_errors = []
        current_special_cases = []

        # Prepare a per-quest capture buffer to collect everything functions print
        capture_io = io.StringIO()

        try:
            # All operations that may print will be executed with stdout/stderr
            # redirected to capture_io so we can keep their output even while
            # the test runner is globally silent.
            with contextlib.redirect_stdout(capture_io), contextlib.redirect_stderr(capture_io):
                # Parse original quest to get monster info before randomization
                original_parsed = QuestEditor.parse_mib(full_path)
                original_monsters = Randomizer.getLargeMonstersIDs(original_parsed)

                print('[INTERNAL] Completed parse of original quest (captured)')

                buf.append('[ORIGINAL] Monsters before randomization:\n')
                # Count monsters before randomization
                orig_waves = original_parsed.get('large_monster_table', [])
                total_original_monsters = sum(len(w) for w in orig_waves)
                if original_monsters:
                    for wave_idx, wave in enumerate(original_parsed.get('large_monster_table', [])):
                        if wave:
                            buf.append(f'  Wave {wave_idx + 1}:\n')
                            for pos_idx, monster in enumerate(wave):
                                monster_id = monster.get('monster_id', 0)
                                monster_name = VariousLists.getMonsterName(monster_id)
                                buf.append(f'    Position {pos_idx + 1}: {monster_name} ({monster_id})\n')
                        else:
                            buf.append(f'  Wave {wave_idx + 1}: Empty\n')
                else:
                    buf.append('  No large monsters found\n')
                buf.append(f'[COUNT] Monsters before: {total_original_monsters}\n')

                # Randomize the quest
                Randomizer.randomizeQuest(full_path)
                print('[INTERNAL] randomizeQuest() returned (captured)')

                # Parse quest after randomization to get new monster info
                randomized_parsed = QuestEditor.parse_mib(full_path)
                randomized_monsters = Randomizer.getLargeMonstersIDs(randomized_parsed)
                print('[INTERNAL] Completed parse of randomized quest (captured)')

                buf.append('[RANDOMIZED] Monsters after randomization (Wave Format):\n')
                if randomized_monsters:
                    unique_monsters_list = VariousLists.uniqueMonstersList()
                    arena_maps = VariousLists.getArenaMapsList()
                    # Dalamadur/Shah head to tail mapping
                    dalamadur_heads = {24: 83, 110: 111}

                    try:
                        quest_map_id = QuestEditor.get_map_id(full_path)
                        is_arena_map = quest_map_id in arena_maps
                        buf.append(f'[MAP] Quest map ID: {quest_map_id} {"(ARENA)" if is_arena_map else ""}\n')
                    except Exception as e:
                        buf.append(f'[ERROR] Could not get map ID: {e}\n')
                        quest_map_id = None
                        is_arena_map = False

                    # Count total monsters and find last non-empty wave index
                    waves = randomized_parsed.get('large_monster_table', [])
                    total_after_monsters = sum(len(w) for w in waves)
                    last_non_empty_wave_idx = -1
                    for idx in range(len(waves) - 1, -1, -1):
                        if len(waves[idx]) > 0:
                            last_non_empty_wave_idx = idx
                            break
                    buf.append(f'[COUNT] Monsters after: {total_after_monsters}\n')

                    # Validation: no empty wave may appear before the last non-empty wave
                    # Examples:
                    # - [1],[3],[] is valid (empty only after last non-empty)
                    # - [1],[],[3] is a violation (empty between non-empty waves)
                    try:
                        if last_non_empty_wave_idx != -1:
                            for idx in range(0, last_non_empty_wave_idx + 1):
                                if len(waves[idx]) == 0:
                                    error_msg = (
                                        f'VIOLATION: Empty wave {idx + 1} before last non-empty wave '
                                        f'{last_non_empty_wave_idx + 1}'
                                    )
                                    current_errors.append(error_msg)
                                    failedCases.append(error_msg)
                                    buf.append(f'    [ERROR] {error_msg}\n')
                                    quest_passed = False
                                    break
                    except Exception as e:
                        buf.append(f"    [WARN] Empty-wave ordering validation skipped due to error: {e}\n")

                    # Validation: if a unique monster appears in wave 1, it must be alone and on its required map
                    # Exception: Dalamadur/Shah heads (24/110) are valid in wave 1 if their tail (83/111) is also present
                    try:
                        first_wave = waves[0] if waves else []
                        if first_wave:
                            ids_first_wave = [m.get('monster_id', 0) for m in first_wave]
                            unique_in_first = [mid for mid in ids_first_wave if mid in unique_monsters_list]
                            if unique_in_first:
                                # Allow head+tail pair in wave 1 for Dalamadur/Shah
                                has_valid_dalamadur_pair = (
                                    (24 in ids_first_wave and 83 in ids_first_wave) or
                                    (110 in ids_first_wave and 111 in ids_first_wave)
                                )
                                # Must be alone in wave 1
                                if not has_valid_dalamadur_pair and len(first_wave) != 1:
                                    error_msg = (
                                        f"VIOLATION: Unique monster in wave 1 must be alone; "
                                        f"wave 1 has {len(first_wave)} monsters"
                                    )
                                    current_errors.append(error_msg)
                                    failedCases.append(error_msg)
                                    buf.append(f'    [ERROR] {error_msg}\n')
                                    quest_passed = False

                                # Must be on the unique monster's required map
                                for mid in unique_in_first:
                                    required_map = Randomizer.getMapForUniqueMonster(mid)
                                    if quest_map_id is None or quest_map_id != required_map:
                                        mname = VariousLists.getMonsterName(mid)
                                        error_msg = (
                                            f"VIOLATION: Unique {mname} ({mid}) in wave 1 on map {quest_map_id} "
                                            f"(required {required_map})"
                                        )
                                        current_errors.append(error_msg)
                                        failedCases.append(error_msg)
                                        buf.append(f'    [ERROR] {error_msg}\n')
                                        quest_passed = False
                    except Exception as e:
                        # Do not break the run; record diagnostic and continue
                        buf.append(f"    [WARN] Wave-1 unique validation skipped due to error: {e}\n")

                    # New verification: no wave may contain 3 or more monsters
                    for wave_idx, wave in enumerate(waves):
                        if len(wave) >= 3:
                            error_msg = f'VIOLATION: Wave {wave_idx + 1} has {len(wave)} monsters (max 2 allowed)'
                            current_errors.append(error_msg)
                            failedCases.append(error_msg)
                            buf.append(f'    [ERROR] {error_msg}\n')
                            quest_passed = False

                    # Validation: counts must match unless Dalamadur/Shah head+tail present in same wave
                    if total_after_monsters != total_original_monsters:
                        allowed_exception = False
                        if total_after_monsters == total_original_monsters + 1:
                            # Check for head+tail pair in the same wave (normal or Shah)
                            dalamadur_heads = {24: 83, 110: 111}
                            for w in waves:
                                ids_in_wave = {m.get('monster_id', 0) for m in w}
                                for head_id, tail_id in dalamadur_heads.items():
                                    if head_id in ids_in_wave and tail_id in ids_in_wave:
                                        allowed_exception = True
                                        break
                                if allowed_exception:
                                    break
                        if not allowed_exception:
                            error_msg = (f"VIOLATION: Monster count changed from {total_original_monsters} to "
                                         f"{total_after_monsters} without valid Dalamadur head+tail exception")
                            current_errors.append(error_msg)
                            failedCases.append(error_msg)
                            buf.append(f'    [ERROR] {error_msg}\n')
                            quest_passed = False

                    # New validation: no quests may contain more than one distinct unique monster
                    distinct_unique_ids = set()
                    for w in waves:
                        for m in w:
                            mid = m.get('monster_id', 0)
                            if mid in unique_monsters_list:
                                distinct_unique_ids.add(mid)
                    if len(distinct_unique_ids) > 1:
                        error_msg = f"VIOLATION: Multiple distinct unique monsters present: {sorted(list(distinct_unique_ids))}"
                        current_errors.append(error_msg)
                        failedCases.append(error_msg)
                        buf.append(f'    [ERROR] {error_msg}\n')
                        quest_passed = False

                    # Check each wave
                    for wave_idx, wave in enumerate(waves):
                        if wave:
                            buf.append(f'  Wave {wave_idx + 1}: {len(wave)} monster(s)\n')

                            # Arena rule: only single-monster waves are allowed, except a head+tail pair in the same wave
                            if is_arena_map and Randomizer.settingNoMoreThanOneInArena:
                                ids_in_wave = [m.get('monster_id', 0) for m in wave]
                                allowed_pair = False
                                # Head+tail allowed as the only 2 monsters in the wave
                                if len(wave) == 2:
                                    for head_id, tail_id in dalamadur_heads.items():
                                        if (head_id in ids_in_wave) and (tail_id in ids_in_wave):
                                            allowed_pair = True
                                            break
                                if not allowed_pair and len(wave) > 1:
                                    error_msg = f'VIOLATION: Wave {wave_idx + 1} has {len(wave)} monsters in arena map {quest_map_id} (only solo allowed; head+tail pair is exception)'
                                    current_errors.append(error_msg)
                                    failedCases.append(error_msg)
                                    buf.append(f'    [ERROR] {error_msg}\n')
                                    quest_passed = False

                            for pos_idx, monster in enumerate(wave):
                                monster_id = monster.get('monster_id', 0)
                                monster_name = VariousLists.getMonsterName(monster_id)
                                is_unique = monster_id in unique_monsters_list

                                # Special handling for Akantor/Ukanlos
                                if monster_id in akantor_ukanlos_list:
                                    # Allowed anywhere if on their special map; otherwise treat like unique
                                    special_allowed = (special_map_for.get(monster_id) == quest_map_id)
                                    if special_allowed:
                                        buf.append(f'    Position {pos_idx + 1}: {monster_name} ({monster_id}) [SPECIAL-ALLOWED]\n')
                                        continue
                                    else:
                                        is_unique = True  # treat as unique for placement rule

                                # New rule: unique monsters (including Dalamadur/Shah head) must be in the last non-empty wave
                                if is_unique:
                                    if last_non_empty_wave_idx == -1:
                                        # weird: no non-empty waves? shouldn't happen if we have monsters
                                        pass
                                    elif wave_idx != last_non_empty_wave_idx:
                                        # If there's only one monster in total, it's allowed anywhere.
                                        if total_after_monsters > 1:
                                            error_msg = (f'VIOLATION: Unique monster {monster_name} ({monster_id}) '
                                                         f'in wave {wave_idx + 1} but last non-empty wave is {last_non_empty_wave_idx + 1}')
                                            current_errors.append(error_msg)
                                            failedCases.append(error_msg)
                                            buf.append(f'    Position {pos_idx + 1}: {monster_name} ({monster_id}) [UNIQUE] [ERROR: Should be in last non-empty wave]\n')
                                            quest_passed = False
                                        else:
                                            special_msg = f'Single monster quest with unique {monster_name} ({monster_id})'
                                            current_special_cases.append(special_msg)
                                            buf.append(f'    Position {pos_idx + 1}: {monster_name} ({monster_id}) [UNIQUE] [SPECIAL: Single monster quest]\n')
                                    else:
                                        buf.append(f'    Position {pos_idx + 1}: {monster_name} ({monster_id}) [UNIQUE]\n')
                                else:
                                    buf.append(f'    Position {pos_idx + 1}: {monster_name} ({monster_id})\n')
                        else:
                            buf.append(f'  Wave {wave_idx + 1}: Empty\n')

                    # Dalamadur/Shah verification
                    # Dalamadur/Shah verification and map rules
                    # Heads must have their tails in the same wave and be in the last wave
                    # If a head appears in the FIRST wave, map must be 8. Otherwise, map must be in allowed maps.
                    # Also enforce allowed maps for Shah variants via getDalamadurMapsList.
                    # Note: tail alone should not trigger map restrictions.
                    # Map checks done here ensure Randomizer logic conforms to requested constraints.
                    dalamadur_heads = {24: 83, 110: 111}
                    head_instances = []
                    for w_idx, w in enumerate(waves):
                        for m in w:
                            mid = m.get('monster_id', 0)
                            if mid in dalamadur_heads:
                                head_instances.append((mid, w_idx))
                    if head_instances:
                        try:
                            allowed_maps = VariousLists.getDalamadurMapsList()
                        except Exception:
                            allowed_maps = [8, 9, 10]
                        # First-wave head forces map 8
                        first_wave_head = any(w_idx == 0 for _, w_idx in head_instances)
                        if first_wave_head and quest_map_id != 8:
                            error_msg = f'VIOLATION: Dalamadur/Shah head in first wave but map is {quest_map_id} (must be 8)'
                            current_errors.append(error_msg)
                            failedCases.append(error_msg)
                            buf.append(f'    [ERROR] {error_msg}\n')
                            quest_passed = False
                        # If no head in first wave, map must be in allowed maps
                        if not first_wave_head and quest_map_id not in allowed_maps:
                            error_msg = f'VIOLATION: Dalamadur/Shah on disallowed map {quest_map_id} (allowed: {allowed_maps})'
                            current_errors.append(error_msg)
                            failedCases.append(error_msg)
                            buf.append(f'    [ERROR] {error_msg}\n')
                            quest_passed = False
                        for head_id, w_idx in head_instances:
                            tail_id = dalamadur_heads[head_id]
                            tail_in_same = any(m.get('monster_id', 0) == tail_id for m in waves[w_idx])
                            if not tail_in_same:
                                error_msg = f'VIOLATION: Head {head_id} without tail {tail_id} in same wave'
                                current_errors.append(error_msg)
                                failedCases.append(error_msg)
                                buf.append(f'    [ERROR] {error_msg}\n')
                                quest_passed = False
                            if w_idx != last_non_empty_wave_idx:
                                error_msg = f'VIOLATION: Dalamadur/Shah not in last wave (wave {w_idx + 1} vs {last_non_empty_wave_idx + 1})'
                                current_errors.append(error_msg)
                                failedCases.append(error_msg)
                                buf.append(f'    [ERROR] {error_msg}\n')
                                quest_passed = False



                    # Display monsters in a single line format
                    monster_display = ", ".join([f"{VariousLists.getMonsterName(mid)} ({mid})" for mid in randomized_monsters])
                    buf.append(f'[SUMMARY] Quest monsters: {monster_display}\n')

                    # Check for multiple Dah'ren Mohran
                    dahren_count = randomized_monsters.count(46)
                    if dahren_count > 1:
                        error_msg = f"VIOLATION: Multiple Dah'ren Mohran found ({dahren_count} instances)"
                        current_errors.append(error_msg)
                        failedCases.append(error_msg)
                        buf.append(f'[ERROR] {error_msg}\n')
                        quest_passed = False
                    elif dahren_count == 1:
                        # Record as a special case
                        current_special_cases.append(f"Quest contains Dah'ren Mohran (ID 46)")

                else:
                    # No monsters found after randomization — NOT considered a failure
                    buf.append('  No large monsters found after randomization\n')
                    current_special_cases.append('No monsters found after randomization')
                    # quest_passed remains True

            # End of captured block

            # Retrieve captured stdout/stderr from the functions we invoked
            captured_output = capture_io.getvalue()
            if captured_output:
                buf.append('[CAPTURED OUTPUT BEGIN]\n')
                for line in captured_output.rstrip().splitlines():
                    buf.append('  ' + line + '\n')
                buf.append('[CAPTURED OUTPUT END]\n')

            # Collect special cases counts
            if current_special_cases:
                special_cases += len(current_special_cases)
                for sc in current_special_cases:
                    buf.append(f'[SPECIAL] {sc}\n')

            # Decide whether to flush the buffer for this quest: only if it failed
            if not quest_passed or current_errors:
                # This quest failed: enable printing, flush this quest buffer, then go silent again
                _enable_print()
                buf.append('[RESULT] FAIL Quest validation FAILED\n')
                validation_errors += 1
                _flush_buffer(buf)
                _disable_print()
            else:
                successful_quests += 1

        except Exception as e:
            # Ensure we still have captured output available after an exception
            captured_output = capture_io.getvalue()
            if captured_output:
                buf.append('[CAPTURED OUTPUT BEGIN]\n')
                for line in captured_output.rstrip().splitlines():
                    buf.append('  ' + line + '\n')
                buf.append('[CAPTURED OUTPUT END]\n')

            # Quest processing raised — enable printing and show details immediately
            buf.append(f'[ERROR] Failed to process quest {quest_file}: {e}\n')
            _enable_print()
            _flush_buffer(buf)
            _disable_print()
            error_count += 1
            failedCases.append(str(e))
            continue

    # End of loop: enable printing and show final summary (leave printing enabled afterwards)
    _enable_print()

    print()
    print('=' * 80)
    print('[FINAL SUMMARY] Quest randomization tests completed!')
    print('=' * 80)
    print(f'Total quests tested: {total_quests}')
    print(f'Successfully processed: {successful_quests}')
    print(f'Validation errors: {validation_errors}')
    print(f'Processing errors: {error_count}')
    print(f'Special cases detected: {special_cases}')
    success_rate = (successful_quests / total_quests) * 100 if total_quests else 0.0
    print(f'Success rate: {success_rate:.1f}%')

    print()
    print('-' * 40)
    print(f'Failed cases: {len(failedCases)}')
    for case in failedCases:
        print(f'  - {case}')

    # Repack the quest archive (no print here)
    Randomizer.packQuestArc()

if __name__ == "__main__":
    test_mainTests()
