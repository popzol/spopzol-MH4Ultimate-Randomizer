# diagnostic_dump_quiet_failures.py
import pytest
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
    """Print buffered lines directly to the original stdout.

    This function writes directly to the saved original stdout so it's
    guaranteed to appear even if the global stdout is currently redirected.
    It joins lines with newline separators to ensure proper formatting.
    """
    if not buf:
        return
    # Join with explicit newline to guarantee correct line breaks and spacing
    text = "".join(buf) + ""
    try:
        _original_stdout.write(text)
        _original_stdout.flush()
    except Exception:
        # Fallback: write lines individually
        for line in buf:
            try:
                _original_stdout.write(line + "")
            except Exception:
                pass

def test_mainTests():

    """
    Comprehensive test function that randomizes quest files and validates
    unique monster placement, arena restrictions, and reports errors.

    Behavior:
      - Fully silent unless a quest fails. On failure the quest buffer is printed
        immediately and silence resumes.
      - Final summary is always printed at the end and printing remains enabled.
      - All stdout/stderr produced by the called functions is captured per-quest
        and printed if that quest fails (so you can see internal diagnostic prints).
      - "No monsters found after randomization" is treated as a special case, not an error.
    """
    # Start fully silent
    _disable_print()

    # Reset quest files to original state
    Randomizer.resetQuestFiles()

    # Set a test seed for reproducible results
    seed = random.randint(0, 1000000)
    Randomizer.setSeed(seed)

    # Get quest folder
    quest_folder = Randomizer.getQuestFolder()

    # Process up to 120 quest files for testing
    quest_files = [f for f in os.listdir(quest_folder) if f.endswith('.1BBFD18E')][:120]

    # Statistics tracking
    total_quests = len(quest_files)
    successful_quests = 0
    error_count = 0
    validation_errors = 0
    special_cases = 0
    failedCases = []

    for quest_idx, quest_file in enumerate(quest_files, 1):
        # Buffer for this quest's messages — only printed if this quest fails.
        buf = []
        buf.append('=' * 80)
        buf.append(f'[TESTING] Quest {quest_idx}/{total_quests}: {quest_file}')
        buf.append('=' * 80)

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

                buf.append('[ORIGINAL] Monsters before randomization:')
                if original_monsters:
                    for wave_idx, wave in enumerate(original_parsed.get('large_monster_table', [])):
                        if wave:
                            buf.append(f'  Wave {wave_idx + 1}:')
                            for pos_idx, monster in enumerate(wave):
                                monster_id = monster.get('monster_id', 0)
                                monster_name = VariousLists.getMonsterName(monster_id)
                                buf.append(f'    Position {pos_idx + 1}: {monster_name} ({monster_id})')
                        else:
                            buf.append(f'  Wave {wave_idx + 1}: Empty')
                else:
                    buf.append('  No large monsters found')

                # Randomize the quest
                Randomizer.randomizeQuest(full_path)
                print('[INTERNAL] randomizeQuest() returned (captured)')

                # Parse quest after randomization to get new monster info
                randomized_parsed = QuestEditor.parse_mib(full_path)
                randomized_monsters = Randomizer.getLargeMonstersIDs(randomized_parsed)
                print('[INTERNAL] Completed parse of randomized quest (captured)')

                buf.append('[RANDOMIZED] Monsters after randomization (Wave Format):')
                if randomized_monsters:
                    unique_monsters_list = VariousLists.uniqueMonstersList()
                    arena_maps = VariousLists.getArenaMapsList()

                    try:
                        quest_map_id = QuestEditor.get_map_id(full_path)
                        is_arena_map = quest_map_id in arena_maps
                        buf.append(f'[MAP] Quest map ID: {quest_map_id} {"(ARENA)" if is_arena_map else ""}')
                    except Exception as e:
                        buf.append(f'[ERROR] Could not get map ID: {e}')
                        quest_map_id = None
                        is_arena_map = False

                    # Check each wave
                    for wave_idx, wave in enumerate(randomized_parsed.get('large_monster_table', [])):
                        if wave:
                            buf.append(f'  Wave {wave_idx + 1}: {len(wave)} monster(s)')

                            # Check for multiple monsters in arena
                            if is_arena_map and len(wave) > 1 and Randomizer.settingNoMoreThanOneInArena:
                                error_msg = f'VIOLATION: Wave {wave_idx + 1} has {len(wave)} monsters in arena map {quest_map_id}'
                                current_errors.append(error_msg)
                                failedCases.append(error_msg)
                                buf.append(f'    [ERROR] {error_msg}')
                                quest_passed = False

                            for pos_idx, monster in enumerate(wave):
                                monster_id = monster.get('monster_id', 0)
                                monster_name = VariousLists.getMonsterName(monster_id)
                                is_unique = monster_id in unique_monsters_list

                                # Check if unique monster is in first wave
                                if is_unique and wave_idx == 0:
                                    total_monsters = sum(len(w) for w in randomized_parsed.get('large_monster_table', []))
                                    if total_monsters > 1:
                                        error_msg = f'VIOLATION: Unique monster {monster_name} ({monster_id}) in Wave 1'
                                        current_errors.append(error_msg)
                                        failedCases.append(error_msg)
                                        buf.append(f'    Position {pos_idx + 1}: {monster_name} ({monster_id}) [UNIQUE] [ERROR: Should not be in Wave 1]')
                                        quest_passed = False
                                    else:
                                        special_msg = f'Single monster quest with unique {monster_name} ({monster_id}) in Wave 1'
                                        current_special_cases.append(special_msg)
                                        buf.append(f'    Position {pos_idx + 1}: {monster_name} ({monster_id}) [UNIQUE] [SPECIAL: Single monster quest]')
                                else:
                                    unique_tag = ' [UNIQUE]' if is_unique else ''
                                    buf.append(f'    Position {pos_idx + 1}: {monster_name} ({monster_id}){unique_tag}')
                        else:
                            buf.append(f'  Wave {wave_idx + 1}: Empty')

                    # Display monsters in a single line format
                    monster_display = ", ".join([f"{VariousLists.getMonsterName(mid)} ({mid})" for mid in randomized_monsters])
                    buf.append(f'[SUMMARY] Quest monsters: {monster_display}')

                    # Check for multiple Dah'ren Mohran
                    dahren_count = randomized_monsters.count(46)
                    if dahren_count > 1:
                        error_msg = f"VIOLATION: Multiple Dah'ren Mohran found ({dahren_count} instances)"
                        current_errors.append(error_msg)
                        failedCases.append(error_msg)
                        buf.append(f'[ERROR] {error_msg}')
                        quest_passed = False
                    elif dahren_count == 1:
                        # Record as a special case
                        current_special_cases.append(f"Quest contains Dah'ren Mohran (ID 46)")

                else:
                    # No monsters found after randomization — NOT considered a failure
                    buf.append('  No large monsters found after randomization')
                    current_special_cases.append('No monsters found after randomization')
                    # quest_passed remains True
                    pass

            # End of captured block

            # Retrieve captured stdout/stderr from the functions we invoked
            captured_output = capture_io.getvalue()
            if captured_output:
                buf.append('[CAPTURED OUTPUT BEGIN]')
                for line in captured_output.rstrip().splitlines():
                    buf.append('  ' + line)
                buf.append('[CAPTURED OUTPUT END]')

            # Collect special cases counts
            if current_special_cases:
                special_cases += len(current_special_cases)
                for sc in current_special_cases:
                    buf.append(f'[SPECIAL] {sc}')

            # Decide whether to flush the buffer for this quest: only if it failed
            if not quest_passed or current_errors:
                # This quest failed: enable printing, flush this quest buffer, then go silent again
                _enable_print()
                buf.append('[RESULT] FAIL Quest validation FAILED')
                validation_errors += 1
                _flush_buffer(buf)
                _disable_print()
            else:
                successful_quests += 1

        except Exception as e:
            # Ensure we still have captured output available after an exception
            captured_output = capture_io.getvalue()
            if captured_output:
                buf.append('[CAPTURED OUTPUT BEGIN]')
                for line in captured_output.rstrip().splitlines():
                    buf.append('  ' + line)
                buf.append('[CAPTURED OUTPUT END]')

            # Quest processing raised — enable printing and show details immediately
            buf.append(f'[ERROR] Failed to process quest {quest_file}: {e}')
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
