# diagnostic_dump.py
import Randomizer
import VariousLists
import QuestEditor
import os

def mainTests():
    """
    Comprehensive test function that randomizes quest files and displays 
    monster information with wave format, validates unique monster placement,
    arena restrictions, and reports errors.
    """
    print("[INFO] Starting comprehensive quest randomization tests with wave format...")
    
    # Reset quest files to original state
    Randomizer.resetQuestFiles()
    
    # Set a test seed for reproducible results
    Randomizer.setSeed("TEST_SEED_123")
    
    # Get quest folder
    quest_folder = Randomizer.getQuestFolder()
    
    # Process exactly 120 quest files for testing
    quest_files = [f for f in os.listdir(quest_folder) if f.endswith('.1BBFD18E')][:120]
    
    # Statistics tracking
    total_quests = len(quest_files)
    successful_quests = 0
    error_count = 0
    validation_errors = 0
    special_cases = 0
    
    print(f"[INFO] Testing {total_quests} quest files...")
    
    for quest_idx, quest_file in enumerate(quest_files, 1):
        print(f"\n{'='*80}")
        print(f"[TESTING] Quest {quest_idx}/{total_quests}: {quest_file}")
        print(f"{'='*80}")
        
        full_path = os.path.join(quest_folder, quest_file)
        quest_passed = True
        current_errors = []
        current_special_cases = []
        
        try:
            # Parse original quest to get monster info before randomization
            original_parsed = QuestEditor.parse_mib(full_path)
            original_monsters = Randomizer.getLargeMonstersIDs(original_parsed)
            
            print(f"[ORIGINAL] Monsters before randomization:")
            if original_monsters:
                # Display original monsters by wave
                for wave_idx, wave in enumerate(original_parsed.get('large_monster_table', [])):
                    if wave:
                        print(f"  Wave {wave_idx + 1}:")
                        for pos_idx, monster in enumerate(wave):
                            monster_id = monster.get('monster_id', 0)
                            monster_name = VariousLists.getMonsterName(monster_id)
                            print(f"    Position {pos_idx + 1}: {monster_name} ({monster_id})")
                    else:
                        print(f"  Wave {wave_idx + 1}: Empty")
            else:
                print("  No large monsters found")
            
            # Randomize the quest
            Randomizer.randomizeQuest(full_path)
            
            # Parse quest after randomization to get new monster info
            randomized_parsed = QuestEditor.parse_mib(full_path)
            randomized_monsters = Randomizer.getLargeMonstersIDs(randomized_parsed)
            
            print(f"\n[RANDOMIZED] Monsters after randomization (Wave Format):")
            if randomized_monsters:
                # Display monsters by wave with validation
                unique_monsters_list = VariousLists.uniqueMonstersList()
                arena_maps = VariousLists.getArenaMapsList()
                
                try:
                    quest_map_id = QuestEditor.get_map_id(full_path)
                    is_arena_map = quest_map_id in arena_maps
                    print(f"[MAP] Quest map ID: {quest_map_id} {'(ARENA)' if is_arena_map else ''}")
                except Exception as e:
                    print(f"[ERROR] Could not get map ID: {e}")
                    quest_map_id = None
                    is_arena_map = False
                
                # Check each wave
                for wave_idx, wave in enumerate(randomized_parsed.get('large_monster_table', [])):
                    if wave:
                        print(f"  Wave {wave_idx + 1}: {len(wave)} monster(s)")
                        
                        # Check for multiple monsters in arena
                        if is_arena_map and len(wave) > 1 and Randomizer.settingNoMoreThanOneInArena:
                            error_msg = f"VIOLATION: Wave {wave_idx + 1} has {len(wave)} monsters in arena map {quest_map_id}"
                            current_errors.append(error_msg)
                            print(f"    [ERROR] {error_msg}")
                            quest_passed = False
                        
                        for pos_idx, monster in enumerate(wave):
                            monster_id = monster.get('monster_id', 0)
                            monster_name = VariousLists.getMonsterName(monster_id)
                            is_unique = monster_id in unique_monsters_list
                            
                            # Check if unique monster is in first wave
                            if is_unique and wave_idx == 0:
                                # Special case: single monster quests can have unique in first wave
                                total_monsters = sum(len(w) for w in randomized_parsed.get('large_monster_table', []))
                                if total_monsters > 1:
                                    error_msg = f"VIOLATION: Unique monster {monster_name} ({monster_id}) in Wave 1"
                                    current_errors.append(error_msg)
                                    print(f"    Position {pos_idx + 1}: {monster_name} ({monster_id}) [UNIQUE] [ERROR: Should not be in Wave 1]")
                                    quest_passed = False
                                else:
                                    special_msg = f"Single monster quest with unique {monster_name} ({monster_id}) in Wave 1"
                                    current_special_cases.append(special_msg)
                                    print(f"    Position {pos_idx + 1}: {monster_name} ({monster_id}) [UNIQUE] [SPECIAL: Single monster quest]")
                            else:
                                unique_tag = " [UNIQUE]" if is_unique else ""
                                print(f"    Position {pos_idx + 1}: {monster_name} ({monster_id}){unique_tag}")
                    else:
                        print(f"  Wave {wave_idx + 1}: Empty")
                
                # Display monsters in a single line format
                monster_display = ", ".join([f"{VariousLists.getMonsterName(mid)} ({mid})" for mid in randomized_monsters])
                print(f"\n[SUMMARY] Quest monsters: {monster_display}")
                
                # Check for multiple Dah'ren Mohran
                dahren_count = randomized_monsters.count(46)
                if dahren_count > 1:
                    error_msg = f"VIOLATION: Multiple Dah'ren Mohran found ({dahren_count} instances)"
                    current_errors.append(error_msg)
                    print(f"[ERROR] {error_msg}")
                    quest_passed = False
                elif dahren_count == 1:
                    special_msg = f"Quest contains Dah'ren Mohran (ID 46)"
                    current_special_cases.append(special_msg)
                    print(f"[SPECIAL] {special_msg}")
                
            else:
                print("  No large monsters found after randomization")
                error_msg = "No monsters found after randomization"
                current_errors.append(error_msg)
                print(f"[ERROR] {error_msg}")
                quest_passed = False
            
            # Report quest status
            if quest_passed and not current_errors:
                print(f"\n[RESULT] ✓ Quest validation PASSED")
                successful_quests += 1
            else:
                print(f"\n[RESULT] ✗ Quest validation FAILED")
                validation_errors += 1
            
            # Report special cases
            if current_special_cases:
                special_cases += len(current_special_cases)
                print(f"[SPECIAL CASES] {len(current_special_cases)} special case(s) detected:")
                for case in current_special_cases:
                    print(f"  - {case}")
            
            # Report errors
            if current_errors:
                print(f"[ERRORS] {len(current_errors)} error(s) detected:")
                for error in current_errors:
                    print(f"  - {error}")
                    
        except Exception as e:
            print(f"[ERROR] Failed to process quest {quest_file}: {e}")
            error_count += 1
            continue
    
    # Final summary
    print(f"\n{'='*80}")
    print("[FINAL SUMMARY] Quest randomization tests completed!")
    print(f"{'='*80}")
    print(f"Total quests tested: {total_quests}")
    print(f"Successfully processed: {successful_quests}")
    print(f"Validation errors: {validation_errors}")
    print(f"Processing errors: {error_count}")
    print(f"Special cases detected: {special_cases}")
    print(f"Success rate: {(successful_quests/total_quests)*100:.1f}%")
    
    if validation_errors > 0 or error_count > 0:
        print(f"\n[WARNING] {validation_errors + error_count} issues detected during testing!")
    else:
        print(f"\n[SUCCESS] All quests passed validation!")
    
    print(f"{'='*80}")
    Randomizer.packQuestArc()
    return

mainTests()