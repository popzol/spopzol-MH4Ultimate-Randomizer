# ============================================================================
# IMPORTS
# ============================================================================
import os
import shutil
import time
import random
import VariousLists
import QuestEditor

# ============================================================================
# CONFIG & SETTINGS
# ============================================================================
AVAILABLE_MAPS = [1,2,3,4,5,6,7,8,9,10,11,12,14,15,16,17,18,19,20,21]  # Avoid map 13

GVseed=""
settingRandomMap = True
settingProgresion = True
settingAlwaysMusic= True
settingNoMoreThanOneInArena= True
settingSoloBalance= True
settingAllowUniqueMonsters = True

# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def setSeed(Seed: str):
    global GVseed
    GVseed = Seed
    random.seed(Seed)

def getSeed() -> str:
    return GVseed

def resetQuestFiles():
    """Reset quest files by copying from og_loc backup."""
    try:
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        loc_path = os.path.join(scripts_dir, "loc")
        og_loc_path = os.path.join(scripts_dir, "og_loc", "loc")
        
        def _on_rm_error(func, path, exc_info):
            try:
                os.chmod(path, 0o777)
                if not os.path.isdir(path):
                    os.remove(path)
            except Exception:
                pass

        if os.path.exists(loc_path):
            print(f"[INFO] Deleting existing loc folder: {loc_path}")
            for attempt in range(5):
                try:
                    shutil.rmtree(loc_path, onerror=_on_rm_error)
                    break
                except Exception as e:
                    if attempt == 4:
                        raise e
                    time.sleep(0.5)
        
        print(f"[INFO] Copying original quest files from: {og_loc_path}")
        shutil.copytree(og_loc_path, loc_path, dirs_exist_ok=True)
        print(f"[INFO] Quest files have been reset successfully")
        
    except Exception as e:
        print(f"[ERROR] Failed to reset quest files: {e}")
        raise

def getQuestFolder():
    """Get the quest folder path."""
    script_path = os.path.abspath(__file__)
    base_folder = os.path.dirname(script_path)
    return os.path.join(base_folder, "loc", "quest")

def packQuestArc(output_arc_name="quest01.arc"):
    """Pack quest files into ARC after randomization."""
    import subprocess
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        repacker_path = os.path.join(script_dir, "customArcRepacker.py")
        output_arc_path = os.path.join(script_dir, output_arc_name)
        loc_dir = os.path.join(script_dir, "loc")
        
        cmd = ["python", repacker_path, "c", output_arc_path, loc_dir]
        print(f"[INFO] Packing quest files into {output_arc_name}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"[SUCCESS] Quest files packed successfully into {output_arc_name}")
        else:
            print(f"[ERROR] Failed to pack quest files: {result.stderr}")
            
    except Exception as e:
        print(f"[ERROR] Exception while packing quest files: {e}")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def getLargeMonstersIDs(parsedMib: dict) -> list:
    """Extract all monster IDs from the quest."""
    monster_ids = []
    for wave in parsedMib.get('large_monster_table', []):
        for monster in wave:
            monster_ids.append(monster.get('monster_id', 0))
    return monster_ids

def getMapForUniqueMonster(monster_id: int) -> int:
    """Get the required map for a unique monster."""
    monster_map = {
        24: 8, 83: 8, 110: 8, 111: 8,      # Dalamadurs (Head/Tail/Shah)
        46: 6,                             # Dahren Mohran
        116: 20,                           # Ukanlos
        77: 10, 79: 10,                    # Black/White Fatalis
        78: 9, 117: 9, 33: 9,              # Crimson Fatalis/Akantor
        89: 19                             # Gogmazios
    }
    return monster_map.get(monster_id, random.choice(AVAILABLE_MAPS))

def isArenaMap(map_id: int) -> bool:
    """Check if a map is an arena map."""
    return map_id in VariousLists.getArenaMapsList()

def isMusicalMonster(monster_id: int) -> bool:
    """Check if a monster is musical."""
    return monster_id in VariousLists.getMusicalMonstersList()

def isDalamadurHead(monster_id: int) -> bool:
    """Check if monster is a Dalamadur/Shah head."""
    return monster_id in [24, 110]

def getDalamadurTail(head_id: int) -> int:
    """Get the tail ID for a Dalamadur/Shah head."""
    return {24: 83, 110: 111}.get(head_id, 0)

def selectRandomMonster(tier: int = None, exclude_unique: bool = False) -> int:
    """Select a random monster, optionally from a specific tier."""
    if tier:
        possible_monsters = VariousLists.monsterListFromTier(tier)
    else:
        possible_monsters = VariousLists.getLargeList()
    
    if exclude_unique:
        unique_monsters = set(VariousLists.uniqueMonstersList())
        possible_monsters = [m for m in possible_monsters if m not in unique_monsters]
    
    return random.choice(possible_monsters)

# ============================================================================
# RANDOMIZATION LOGIC
# ============================================================================

def randomizeMonsters(quest_path: str, original_monsters: list) -> list:
    """Randomize monsters based on progression setting."""
    new_monsters = []
    
    if settingProgresion:
        # Progression-based randomization
        parsed = QuestEditor.parse_mib(quest_path)
        rank = parsed.get('quest_rank', 1)
        tier_chances = VariousLists.tierChancesOfRank(rank)
        all_tiers = [8, 7, 6, 5, 4, 3, 2, 1]
        
        has_unique = False
        for original_id in original_monsters:
            # Select tier based on rank
            selected_tier = random.choices(all_tiers, weights=tier_chances, k=1)[0]
            
            if settingAllowUniqueMonsters and not has_unique:
                # Allow unique monsters
                new_monster = selectRandomMonster(selected_tier)
                if new_monster in VariousLists.uniqueMonstersList():
                    has_unique = True
            else:
                # No more unique monsters allowed
                new_monster = selectRandomMonster(selected_tier, exclude_unique=True)
            
            new_monsters.append(new_monster)
            
            # Replace the monster in the quest
            QuestEditor.find_and_replace_monster_individual(quest_path, original_id, new_monster, False)
    else:
        # Simple randomization
        large_monsters = VariousLists.getLargeList()
        has_unique = False
        
        for original_id in original_monsters:
            if settingAllowUniqueMonsters and not has_unique:
                new_monster = random.choice(large_monsters)
                if new_monster in VariousLists.uniqueMonstersList():
                    has_unique = True
            else:
                # Exclude unique monsters
                non_unique = [m for m in large_monsters if m not in VariousLists.uniqueMonstersList()]
                new_monster = random.choice(non_unique)
            
            new_monsters.append(new_monster)
            QuestEditor.find_and_replace_monster_individual(quest_path, original_id, new_monster, False)
    
    return new_monsters

def selectAppropriateMap(quest_path: str, monsters: list) -> int:
    """Select an appropriate map based on monsters and settings."""
    # Check for unique monsters that require specific maps
    unique_monsters = [m for m in monsters if m in VariousLists.uniqueMonstersList()]
    
    # Handle Dalamadur/Shah special cases first
    if any(isDalamadurHead(mid) for mid in monsters):
        # Check if head is in first wave - if so, must use map 8
        parsed = QuestEditor.parse_mib(quest_path)
        waves = parsed.get('large_monster_table', [])
        if waves and len(waves[0]) > 0:
            first_wave_monsters = [m.get('monster_id', 0) for m in waves[0]]
            if any(isDalamadurHead(mid) for mid in first_wave_monsters):
                print(f"[INFO] Dalamadur/Shah head in first wave - forcing map 8")
                return 8
        
        # If not in first wave, use allowed Dalamadur maps
        # Tail is added after map selection; only head position matters here.
        # If head is not in the first wave, pick randomly among 8, 9, 10.
        selected_map = random.choice([8, 9, 10])
        print(f"[INFO] Selected Dalamadur map (head not in first wave): {selected_map}")
        return selected_map
    
    # Start with all available maps
    possible_maps = AVAILABLE_MAPS.copy()
    
    # Check arena restrictions FIRST - applies to all quests with multiple monsters
    if settingNoMoreThanOneInArena and len(monsters) > 1:
        # Only allow arena maps if we have an exact valid head+tail pair
        is_valid_dalamadur_pair = False
        if len(monsters) == 2:
            if (24 in monsters and 83 in monsters) or (110 in monsters and 111 in monsters):
                is_valid_dalamadur_pair = True
        
        if not is_valid_dalamadur_pair:
            arena_maps = VariousLists.getArenaMapsList()
            possible_maps = [m for m in possible_maps if m not in arena_maps]
            print(f"[INFO] Excluded arena maps for multi-monster quest: {arena_maps}")
    
    # Check music restrictions
    if settingAlwaysMusic:
        all_musical = all(isMusicalMonster(mid) for mid in monsters)
        if not all_musical:
            # Exclude non-musical maps
            no_musical_maps = VariousLists.getNoMusicalMapsList()
            possible_maps = [m for m in possible_maps if m not in no_musical_maps]
    
    # Handle other unique monsters
    if unique_monsters:
        required_map = getMapForUniqueMonster(unique_monsters[0])
        
        # For multi-monster quests, check if required map violates arena restrictions
        if len(monsters) > 1 and settingNoMoreThanOneInArena:
            is_valid_dalamadur_pair = False
            if len(monsters) == 2:
                if (24 in monsters and 83 in monsters) or (110 in monsters and 111 in monsters):
                    is_valid_dalamadur_pair = True
            
            # If it's not a valid Dalamadur pair and required map is arena, use non-arena alternative
            if (not is_valid_dalamadur_pair) and required_map in VariousLists.getArenaMapsList():
                if possible_maps:
                    selected_map = random.choice(possible_maps)
                    print(f"[INFO] Overrode unique map {required_map} (arena) with {selected_map} for multi-monster quest")
                    return selected_map
        
        return required_map
    
    return random.choice(possible_maps) if possible_maps else random.choice(AVAILABLE_MAPS)

def applyMapToQuest(quest_path: str, map_id: int, monsters: list):
    """Apply the selected map to the quest with proper area/coordinate assignment."""
    # Set the map ID
    QuestEditor.set_map_id_dynamic(quest_path, map_id)
    
    # Get valid areas for this map
    area_list = VariousLists.subMapsOf(map_id)
    if not area_list:
        print(f"[WARN] No areas available for map {map_id}")
        return
    
    # Apply areas and coordinates to monsters
    parsed = QuestEditor.parse_mib(quest_path)
    monster_count = 0
    
    for table_idx, table in enumerate(parsed.get('large_monster_table', [])):
        for monster_idx, monster in enumerate(table):
            if monster_count >= len(monsters):
                break
                
            # Select random area and coordinates
            area = random.choice(area_list)
            coords = VariousLists.getListOfCoords(map_id, area)
            
            if coords and len(coords) >= 2:
                try:
                    QuestEditor.setArea_large(quest_path, table_idx, monster_idx, area)
                    QuestEditor.set_large_monster_position_by_indices(
                        quest_path, table_idx, monster_idx, coords[0], coords[1]
                    )
                    QuestEditor.set_large_monster_rotation_by_indices(quest_path, table_idx, monster_idx, 0,None,None)
                except Exception as e:
                    print(f"[WARN] Failed to set area/coords for monster {monster_count}: {e}")
            
            monster_count += 1
    
    # Special handling for Gogmazios
    if 89 in monsters and map_id == 19:
        try:
            for table_idx, table in enumerate(parsed.get('large_monster_table', [])):
                for monster_idx, monster in enumerate(table):
                    if monster.get('monster_id') == 89:
                        QuestEditor.setArea_large(quest_path, table_idx, monster_idx, 3)
                        print(f"[INFO] Placed Gogmazios in area 3")
                        break
        except Exception as e:
            print(f"[WARN] Failed to place Gogmazios: {e}")
    
    print(f"[INFO] Applied map {map_id} to quest with {len(monsters)} monsters")

def ensureDalamadurPairing(quest_path: str):
    """Ensure Dalamadur/Shah heads have their tails in the same wave."""
    try:
        parsed = QuestEditor.parse_mib(quest_path)
        waves = parsed.get('large_monster_table', [])

        # First, enforce that any Dalamadur/Shah head resides in the LAST non-empty wave
        last_nonempty_idx = -1
        for i in range(len(waves) - 1, -1, -1):
            if len(waves[i]) > 0:
                last_nonempty_idx = i
                break
        if last_nonempty_idx != -1:
            for wi, wave in enumerate(waves):
                if wi == last_nonempty_idx:
                    continue
                for m in wave:
                    mid = m.get('monster_id', 0)
                    if isDalamadurHead(mid):
                        try:
                            print(f"[INFO] Moving Dalamadur/Shah head {mid} to last wave {last_nonempty_idx}")
                            QuestEditor.swap_large_monster(quest_path, mid, last_nonempty_idx, 0)
                            print(f"[SUCCESS] Head {mid} relocated to last wave {last_nonempty_idx}")
                        except Exception as e:
                            print(f"[WARN] Failed to move head {mid} to last wave: {e}")
                        break  # only process one head per wave

        for wave_idx, wave in enumerate(waves):
            monster_ids = [m.get('monster_id', 0) for m in wave]
            
            # Check for heads without tails
            for monster_id in monster_ids:
                if isDalamadurHead(monster_id):
                    tail_id = getDalamadurTail(monster_id)
                    
                    if tail_id not in monster_ids:
                        print(f"[INFO] Found Dalamadur head {monster_id} without tail {tail_id} in wave {wave_idx}")
                        
                        # First, try to find and move the tail from another wave
                        tail_moved = False
                        for other_wave_idx, other_wave in enumerate(waves):
                            if other_wave_idx == wave_idx:
                                continue
                            
                            other_ids = [m.get('monster_id', 0) for m in other_wave]
                            if tail_id in other_ids:
                                # Move tail to head's wave
                                try:
                                    if len(wave) < 2:  # Only if there's space
                                        QuestEditor.swap_large_monster(quest_path, tail_id, wave_idx, len(wave))
                                        print(f"[INFO] Moved tail {tail_id} to pair with head {monster_id}")
                                        tail_moved = True
                                        break
                                    else:
                                        # Preserve the head: replace the other slot with the tail
                                        head_pos = next((idx for idx, mid in enumerate(monster_ids) if isDalamadurHead(mid)), 0)
                                        replace_pos = 1 if head_pos == 0 else 0
                                        QuestEditor.swap_large_monster(quest_path, tail_id, wave_idx, replace_pos)
                                        print(f"[INFO] Replaced monster in wave {wave_idx} pos {replace_pos} with tail {tail_id}")
                                        tail_moved = True
                                        break
                                except Exception as e:
                                    print(f"[WARN] Failed to move tail {tail_id}: {e}")
                        
                        # If tail wasn't found or couldn't be moved, add it to the wave
                        if not tail_moved:
                            try:
                                if len(wave) < 2:
                                    QuestEditor.expand_large_monster_table(quest_path, wave_idx, tail_id)
                                    print(f"[INFO] Added tail {tail_id} to pair with head {monster_id}")
                                else:
                                    # Preserve the head: replace the other slot with the tail
                                    head_pos = next((idx for idx, mid in enumerate(monster_ids) if isDalamadurHead(mid)), 0)
                                    replace_pos = 1 if head_pos == 0 else 0
                                    mon_copy = dict(wave[replace_pos])
                                    mon_copy['monster_id'] = tail_id
                                    QuestEditor.write_monster_in_large_table(quest_path, wave_idx, replace_pos, mon_copy)
                                    print(f"[INFO] Replaced wave {wave_idx} pos {replace_pos} with tail {tail_id}")
                            except Exception as e:
                                print(f"[WARN] Failed to add tail {tail_id}: {e}")
                                
    except Exception as e:
        print(f"[WARN] Dalamadur pairing failed: {e}")

def moveUniqueToLastWave(quest_path: str):
    """Move unique monsters to the last non-empty wave."""
    parsed = QuestEditor.parse_mib(quest_path)
    waves = parsed.get('large_monster_table', [])
    unique_monsters = set(VariousLists.uniqueMonstersList())
    # Note: this function strictly moves uniques to the last non-empty wave.
    # Any isolation/new-wave logic belongs in isolateMonstersWhenUniquePresent.

    # Find last non-empty wave (for reference)
    last_wave_idx = -1
    for idx in range(len(waves) - 1, -1, -1):
        if len(waves[idx]) > 0:
            last_wave_idx = idx
            break
        
    if last_wave_idx == -1:
        return  # No waves with monsters
        
    # Count total monsters to determine if this is a single-monster quest
    total_monsters = sum(len(wave) for wave in waves)
        
    # Find unique monsters not in the last wave
    unique_to_move = []
    for wave_idx, wave in enumerate(waves):
        if wave_idx == last_wave_idx:
            continue
        for monster in wave:
            monster_id = monster.get('monster_id', 0)
            if monster_id in unique_monsters:
                unique_to_move.append((monster_id, wave_idx))
        
    # Only move unique monsters if there are multiple monsters total
    # Single-monster quests are exempt from this rule
    if total_monsters > 1:
        for monster_id, source_wave_idx in unique_to_move:
            # Always swap into position 0 of the last wave to avoid invalid index errors
            p_last = QuestEditor.parse_mib(quest_path)
            last_wave_now = p_last.get('large_monster_table', [])[last_wave_idx]
            target_pos = 0

            if isDalamadurHead(monster_id):
                # If tail exists in the same source wave, try swapping it into last wave position 0 first
                p_src = QuestEditor.parse_mib(quest_path)
                src_wave = p_src.get('large_monster_table', [])[source_wave_idx]
                src_ids = [m.get('monster_id', 0) for m in src_wave]
                tail_id = getDalamadurTail(monster_id)
                if tail_id in src_ids:
                    QuestEditor.swap_large_monster(quest_path, tail_id, last_wave_idx, 0)
                # Move head into the last wave via swap (position 0)
                QuestEditor.swap_large_monster(quest_path, monster_id, last_wave_idx, 0)
            else:
                # Regular unique: swap into the last non-empty wave at position 0
                QuestEditor.swap_large_monster(quest_path, monster_id, last_wave_idx, target_pos)
    # For single-monster quests, unique placement does not apply

"""
Assumptions:
- QuestEditor and VariousLists are available in scope
- Helper functions isDalamadurHead, getDalamadurTail, getLargeMonstersIDs exist
- Dalamadur/Shah id pairs are kept as constants below; update if your project uses different ids
"""

def isolateMonstersWhenUniquePresent(quest_path: str):
    parsedMib=QuestEditor.parse_mib(quest_path)
    rawWaves=parsedMib.get('large_monster_table', [])
    allmons=[]
    allWaves= []
    for w in rawWaves:
        wave=[]
        for n in w:
            wave.append(n.get('monster_id', 0))
            allmons.append(n.get('monster_id', 0))
        allWaves.append(wave)
    # Special case: exactly two monsters total, both in wave 1.
    # If a non-Dalamadur unique is present in wave 1, isolate it to a new wave.
    try:
        total_monsters = sum(len(w) for w in rawWaves)
        if total_monsters == 2 and len(allWaves) > 0 and len(allWaves[0]) == 2:
            unique_list = VariousLists.uniqueMonstersList()
            first_wave_ids = allWaves[0]
            unique_in_first = [mid for mid in first_wave_ids if (mid in unique_list) and (not isDalamadurHead(mid))]
            if unique_in_first:
                unique_id = unique_in_first[0]
                # Insert an empty wave after the first wave
                QuestEditor.insertEmptyWave(quest_path, 1)
                # Move the unique monster into the new empty wave
                moved = QuestEditor.move_monster_to_empty_table(quest_path, unique_id, 1)
                # Delete the original instance from wave 1 using fresh indices after structural change
                try:
                    post = QuestEditor.parse_mib(quest_path)
                    waves_now = post.get('large_monster_table', [])
                    wave0_ids = [m.get('monster_id', 0) for m in (waves_now[0] if waves_now else [])]
                    if unique_id in wave0_ids:
                        idx0 = wave0_ids.index(unique_id)
                        QuestEditor.delete_from_large_table(quest_path, {'table_index': 0, 'monster_index': idx0})
                except Exception as de:
                    print(f"[WARN] Fallback delete by id due to error: {de}")
                    QuestEditor.delete_monster_by_id_first_instance(quest_path, unique_id)
                # Update local tracking
                allWaves.insert(1, [unique_id])
                allWaves[0] = [mid for mid in allWaves[0] if mid != unique_id]
    except Exception as e:
        print(f"[WARN] Isolation special-case failed: {e}")
    if 24 in allmons or 110 in allmons or 46 in allmons:
        currentWave=0
        for w in allWaves:
            if(len(w)==2 and w[0]!=24 and w[0]!=110 and w[1]!=24 and w[1]!=110):
                # Insert an empty wave right after the current wave
                QuestEditor.insertEmptyWave(quest_path, currentWave+1)
                # Move one instance into the new empty wave. This function copies, so source remains.
                QuestEditor.move_monster_to_empty_table(quest_path, w[1], currentWave+1)
                # Explicitly delete the SECOND slot from the source wave to ensure only 1 remains.
                # This handles duplicate IDs correctly by always removing position 1.
                QuestEditor.delete_from_large_table(quest_path, {'table_index': currentWave, 'monster_index': 1})
                # Update local tracking
                allWaves.insert(currentWave+1, [w[1]])
                allWaves[currentWave] = [w[0]]
            currentWave+=1

def enforceArenaWave1Solo(quest_path: str):
    """
    Ensure wave 1 in arena maps has at most one monster, except the 110/111 head-tail pair.
    If two monsters exist in wave 1 and it's not the head-tail pair, move the second to a new empty wave.
    """
    parsed = QuestEditor.parse_mib(quest_path)
    large = parsed.get('large_monster_table', [])
    if not large or len(large) < 1:
        return
    wave0 = large[0]
    if len(wave0) < 2:
        return
    ids = [m.get('monster_id', 0) for m in wave0]
    # Allow exact head-tail pair in any order
    if set(ids) == {110, 111}:
        return
    # Otherwise, isolate the second monster into a new wave after wave 1
    QuestEditor.insertEmptyWave(quest_path, 1)
    # Copy the second slot into the empty wave
    QuestEditor.move_monster_to_empty_table(quest_path, ids[1], 1)
    # Delete the second slot from wave 1 to leave one monster
    QuestEditor.delete_from_large_table(quest_path, {'table_index': 0, 'monster_index': 1})

def getAllWaves(quest_path: str)->list:
    """Return a flattened list of all monster IDs present in the quest."""
    parsed = QuestEditor.parse_mib(quest_path)
    waves = parsed.get('large_monster_table', []) if parsed else []

    allWaves=[]
    for wave in waves:
        currentWave=[]
        for m in wave:
            currentWave.append(m.get('monster_id', 0))
        allWaves.append(currentWave)
    return allWaves

def updateQuestObjectives(quest_path: str):
    """Update quest objectives to match all large monsters currently present in the quest.

    Builds a flat list of monster IDs from the quest's large_monster_table and writes
    objectives accordingly:
      - If up to 3 monsters: each gets its own objective (type 1, qty 1).
      - If more than 3 monsters: write a single objective type 8 (hunt all).
    """
    try:
        parsed = QuestEditor.parse_mib(quest_path)
        waves = parsed.get('large_monster_table', []) if parsed else []

        # Flatten all monster IDs present in the quest
        monster_ids = []
        for wave in waves:
            for m in wave:
                mid = m.get('monster_id', 0)
                if mid:
                    monster_ids.append(mid)

        # Write objectives based on current monsters
        QuestEditor.write_objectives_for_monsters(quest_path, monster_ids, prefer_type_for_single=1)
    except Exception as e:
        print(f"[WARN] Failed to update objectives: {e}")

def adjustStatsForSolo(quest_path: str, monster_count: int):
    """Adjust monster stats if solo balance is enabled."""
    if not settingSoloBalance:
        return
        
    try:
        # Always use the actual current monster count from the quest,
        # so tails added during pairing are included.
        parsed = QuestEditor.parse_mib(quest_path)
        waves = parsed.get('large_monster_table', []) if parsed else []
        actual_count = sum(len(w) for w in waves)
        for i in range(actual_count):
            stats = QuestEditor.read_meta_entry(quest_path, i)
            if 'hp' in stats:
                stats['hp'] = int(stats['hp'] * 0.05)  # Reduce HP by 20%
            if 'atk' in stats:
                stats['atk'] = int(stats['atk'] * 0.05)  # Reduce attack by 20%
            QuestEditor.write_stats_from_dict(quest_path, i, stats)
    except Exception as e:
        print(f"[WARN] Failed to adjust stats: {e}")

# ============================================================================
# MAIN RANDOMIZATION FUNCTION
# ============================================================================

def randomizeQuest(full_path: str):
    """
    Main quest randomization function - clean and predictable.
    
    This function:
    1. Parses the original quest
    2. Randomizes monsters while preserving count
    3. Selects appropriate map
    4. Applies map with proper areas/coordinates
    5. Ensures Dalamadur/Shah pairing
    6. Updates objectives
    7. Adjusts stats if needed
    
    Monster counts are NEVER changed - only monster types are randomized.
    """
    if not os.path.isfile(full_path):
        print(f"[ERROR] Quest file not found: {full_path}")
        return
    
    try:
        # 1. Parse original quest
        print(f"[INFO] Randomizing quest: {os.path.basename(full_path)}")
        original_parsed = QuestEditor.parse_mib(full_path)
        original_monsters = getLargeMonstersIDs(original_parsed)
        original_count = len(original_monsters)
        
        # Skip quests with no monsters
        if original_count == 0:
            print("[INFO] Skipping quest with no large monsters")
            return
        
        print(f"[INFO] Original monsters: {original_count}")
        
        # 2. Randomize monsters (preserves count)
        new_monsters = randomizeMonsters(full_path, original_monsters)
        print(f"[INFO] New monsters: {new_monsters}")
        
        # 3. Select appropriate map
        if settingRandomMap:
            selected_map = selectAppropriateMap(full_path, new_monsters)
            print(f"[INFO] Selected map: {selected_map}")
            
        # 4. Apply map with areas/coordinates
        applyMapToQuest(full_path, selected_map, new_monsters)
        
        # 4.5 Isolate unique monsters special-cases regardless of map to enforce rules
        isolateMonstersWhenUniquePresent(full_path)
        # 4.6 Enforce arena wave 1 solo rule (except head+tail)
        if selected_map in VariousLists.getArenaMapsList():
            enforceArenaWave1Solo(full_path)

        # 5. Move unique monsters to last wave first (before pairing)
        moveUniqueToLastWave(full_path)


        
        # 6. Ensure Dalamadur/Shah pairing
        ensureDalamadurPairing(full_path)
        
        # 7. Update objectives
        updateQuestObjectives(full_path)
        
        # 8. Adjust stats if needed
        parsed_for_stats = QuestEditor.parse_mib(full_path)
        count_for_stats = sum(len(w) for w in (parsed_for_stats.get('large_monster_table', []) if parsed_for_stats else []))
        adjustStatsForSolo(full_path, count_for_stats)
        
        # 9. Verify final count
        final_parsed = QuestEditor.parse_mib(full_path)
        final_monsters = getLargeMonstersIDs(final_parsed)
        final_count = len(final_monsters)
        
        if final_count != original_count:
            # Only allow +1 for valid Dalamadur head+tail pairing
            if final_count == original_count + 1:
                # Check if we have a valid head+tail pair
                waves = final_parsed.get('large_monster_table', [])
                valid_pairing = False
                for wave in waves:
                    ids = [m.get('monster_id', 0) for m in wave]
                    if (24 in ids and 83 in ids) or (110 in ids and 111 in ids):
                        valid_pairing = True
                        break
                
                if valid_pairing:
                    print(f"[INFO] Final monster count increased by 1 due to Dalamadur/Shah pairing")
                else:
                    print(f"[WARN] Final monster count {final_count} differs from original {original_count}")
            else:
                print(f"[WARN] Final monster count {final_count} differs from original {original_count}")
        
        print(f"[SUCCESS] Quest randomized: {os.path.basename(full_path)}")
    except Exception as e:
        print(f"[ERROR] Failed to randomize quest: {e}")



# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Process all quest files in the quest folder."""
    folder = getQuestFolder()
    for file in os.listdir(folder):
        if file.endswith('.1BBFD18E'):
            print('\n' + '='*50)
            print ("before: ",QuestEditor.parse_mib(os.path.join(folder, file))['large_monster_table']) 
            full_path = os.path.join(folder, file)
            randomizeQuest(full_path)
            print ("after: ",QuestEditor.parse_mib(full_path)['large_monster_table']) 

if __name__ == "__main__":
    folder = getQuestFolder()
    resetQuestFiles()
    seed = input("Enter a seed: ")
    setSeed(seed)
    main()
    packQuestArc()
