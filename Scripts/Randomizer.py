from ast import List
from enum import unique
from operator import index, ne
from queue import Empty
import VariousLists
import QuestEditor
import os
import shutil
from pathlib import Path
import random

AVAILABLE_MAPS = [1,2,3,4,5,6,7,8,9,10,11,12,14,15,16,17,18,19,20,21]  # Avoid map 13

GVseed=""
settingRandomMap = True
settingProgresion = True
settingAlwaysMusic= True
settingNoMoreThanOneInArena= True
settingSoloBalance= True
settingAllowUniqueMonsters = True

def resetQuestFiles():
    """
    Resets the quest files by deleting the current loc folder and replacing it with
    a fresh copy from the og_loc folder.
    
    This function should be called at the start of the randomization process to ensure
    we're working with the original quest files.
    """
    try:
        # Define paths
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        loc_path = os.path.join(scripts_dir, "loc")
        og_loc_path = os.path.join(scripts_dir, "og_loc", "loc")
        
        # Delete the current loc folder if it exists
        if os.path.exists(loc_path):
            print(f"[INFO] Deleting existing loc folder: {loc_path}")
            shutil.rmtree(loc_path)
        
        # Copy the og_loc/loc folder to the scripts folder
        print(f"[INFO] Copying original quest files from: {og_loc_path}")
        shutil.copytree(og_loc_path, loc_path)
        print(f"[INFO] Quest files have been reset successfully")
        
    except Exception as e:
        print(f"[ERROR] Failed to reset quest files: {e}")
        raise

def setSeed(Seed: str):
    global GVseed
    GVseed = Seed
    random.seed(Seed)
def getSeed()->str:
    return GVseed

#region Helper functions
def getMonsterData(parsedMib: dict):
    data=[]

    for i in parsedMib['large_monster_table']:
        for k in i:
            data.append(k)
    return data

def getLargeMonstersIDs(parsedMib: dict)-> list:
    l= []
    monsterData=(getMonsterData(parsedMib))
    for i in monsterData:
        l.append(i['monster_id'])
    return l

def getQuestFolder():
    # Get the absolute path of the current script
    script_path = os.path.abspath(__file__)
    # Get the directory where the script is located
    base_folder = os.path.dirname(script_path)
    # Build the path to loc/quest
    target_folder = os.path.join(base_folder, "loc", "quest")
    return target_folder

def randomHex(a:int , b:int):
    value = random.randint(a, b)
    return f"{value:02X}"

def buildLargeMonsterIndexList(parsedMib: dict):
    """
    Devuelve lista de tuplas (table_index, monster_index, monster_id)
    recorriendo parsedMib['large_monster_table'] respetando la estructura.
    """
    out = []
    tables = parsedMib.get('large_monster_table', [])
    for ti, table in enumerate(tables):
        # table es lista de monster dicts
        for mi, monster in enumerate(table):
            mid = monster.get('monster_id')
            out.append((ti, mi, mid))
    return out

def editMapData(questFilePath: str, newMonstersList: list, newMap: int):
    """
    newMonstersList: lista de monster_ids (puede ser devuelta por getLargeMonstersIDs),
                     pero iteramos usando parsedMib para mapear índices reales.
    Esta versión:
      - selecciona areas/coords por monster en orden de tablas reales
      - respeta casos en los que no hay suficientes monsters
    """

    # setear map id primero
    QuestEditor.set_map_id_dynamic(questFilePath, newMap)

    # conseguir parsedMib actualizado (por si el cambio del map afecta a estructura)
    parsedMib = QuestEditor.parse_mib(questFilePath)

    # lista de areas válidas para ese mapa
    areaList = VariousLists.subMapsOf(newMap)
    if not areaList:
        print(f"[WARN] editMapData_fixed: no hay submaps para map {newMap}")
        return

    # construir lista con índices reales
    index_list = buildLargeMonsterIndexList(parsedMib)
    if not index_list:
        print("[WARN] editMapData_fixed: no hay monstruos grandes en parsedMib")
        return

    # Si newMonstersList tiene exactamente el mismo tamaño que index_list -> emparejamos 1:1
    # Si no, iteramos hasta min(len(index_list), len(newMonstersList)) y aplicamos aleatorio donde falte.
    count = min(len(index_list), len(newMonstersList))

    for idx in range(count):
        table_index, monster_index, _old_mid = index_list[idx]
        new_mid = newMonstersList[idx]  # asumes newMonstersList alineada; si no, podrías elegir aleatorio
        # elegir area y coords válidos
        newArea = random.choice(areaList)
        newCoords = VariousLists.getListOfCoords(newMap, newArea)
        if not newCoords or len(newCoords) < 2:
            print(f"[WARN] no coords para map {newMap} area {newArea}")
            continue
        
        # setear area (usa índices reales)
        # supongo que setAreaLarge(path, table_index, monster_index, area) es la firma correcta
        try:
            QuestEditor.setArea_large(questFilePath, table_index, monster_index, newArea)
        except Exception as e:
            print(f"[ERROR] setAreaLarge falló para table {table_index} idx {monster_index}: {e}")
            continue

        # setear coords (x,z) usando la función que añadiste
        try:
            QuestEditor.set_large_monster_position_by_indices(questFilePath, table_index, monster_index, newCoords[0], newCoords[1])
        except Exception as e:
            print(f"[ERROR] setLargeMonsterPosition... falló para table {table_index} idx {monster_index}: {e}")
            continue
    if(89 in newMonstersList and newMap == 19):
        handleGogmazios(questFilePath)

    print(f"[INFO] editMapData_fixed: aplicado map {newMap} en {count} monstruos.")


def getMapForUniqueMonsterID(unique_monster_id: int) -> int:
    """
    Returns the map id for a quest with a single unique monster (by id).
    """
    monster_map = {
        24: 8, 83: 8, 110: 8, 111: 8,      # Dalamadurs (Head/Tail/Shah)
        46: 6,                             # Dahren Mohran
        116: 20,                           # Ukanlos
        77: 10, 79: 10,                    # Black/White Fatalis
        78: 9, 117: 9, 33: 9,              # Crimson Fatalis (Super)/Akantor
        89: 19                             # Gogmazios
    }
    if unique_monster_id in monster_map:
        return monster_map[unique_monster_id]
    return random.choice(AVAILABLE_MAPS)

def checkMusicalMonsters(monster_list: list) -> bool:
    """
    Check if all monsters in the list are musical monsters.
    Returns True if all monsters are musical, False otherwise.
    """
    if not settingAlwaysMusic:
        return False
        
    for monster_id in monster_list:
        if monster_id not in VariousLists.getMusicalMonstersList():
            return False
    return True

def getPossibleMaps(newMonsterList: list ,allWaves: list,monsterList: list) -> list:
    """
    Get a list of possible maps based on settings and wave configuration.
    Handles arena restrictions when any wave has multiple monsters.
    """
    possible_maps = AVAILABLE_MAPS.copy()
    allAreMusical = checkMusicalMonsters(newMonsterList)
    
    if settingNoMoreThanOneInArena:
        # Check if any wave has multiple monsters
        has_multi_monster_wave = any(len(wave) > 1 for wave in allWaves)
        if has_multi_monster_wave:
            arena_maps = VariousLists.getArenaMapsList()
            possible_maps = [m for m in possible_maps if m not in arena_maps]
            print(f"[INFO] Excluding arena maps due to multi-monster waves: {arena_maps}")
    
    if not allAreMusical and settingAlwaysMusic:
        possible_maps = [m for m in possible_maps if m not in VariousLists.getNoMusicalMapsList()]
            
    return possible_maps

def handleGogmazios(questFilePath: str):
    """
    Special handling for Gogmazios (monster ID 89).
    Places it in area 3 of its map.
    """
    parsed = QuestEditor.parse_mib(questFilePath)
    found = False
    
    for table_idx, table in enumerate(parsed.get('large_monster_table', [])):
        for mon_idx, mon in enumerate(table):
            if mon.get('monster_id') == 89:
                try:
                    QuestEditor.setArea_large(questFilePath, table_idx, mon_idx, 3)
                    print(f"[INFO] setAreaLarge: placed monster 89 at table {table_idx} idx {mon_idx} area 3")
                    found = True
                except Exception as e:
                    print(f"[ERROR] setAreaLarge falló: {e}")
                break
        if found:
            break
            
    if not found:
        print("[WARN] No se encontró monster_id 89 en large_monster_table — no se aplica área especial")

def selectMapForRegularMonsters(possible_maps: list, all_musical: bool) -> int:
    """
    Select an appropriate map for regular monsters.
    Handles music settings if applicable.
    """
    new_map = random.choice(possible_maps)
    
    # If we need music and the map doesn't support it, keep trying
    while (settingAlwaysMusic and 
           new_map in VariousLists.getNoMusicalMapsList() and 
           not all_musical):
        new_map = random.choice(possible_maps)
        
    return new_map

def selectTier1or2Monster():
    """
    Selects a random monster from tier 1 or tier 2 with a 50/50 chance.
    Used for the second monster in 2-monster quests with 1 unique monster.
    
    Returns:
        int: Monster ID from tier 1 or tier 2
    """
    # 50/50 chance to select tier 1 or tier 2
    selected_tier = random.choice([1, 2])
    possible_monsters = VariousLists.monsterListFromTier(selected_tier)
    return random.choice(possible_monsters)

def hasDahrenMohran(questFilePath: str) -> bool:
    """
    Checks if a quest already contains a Dah'ren Mohran (ID 46).
    
    Args:
        questFilePath: Path to the quest file
        
    Returns:
        bool: True if quest contains Dah'ren Mohran, False otherwise
    """
    try:
        parsedMib = QuestEditor.parse_mib(questFilePath)
        monstersIDs = getLargeMonstersIDs(parsedMib)
        return 46 in monstersIDs
    except Exception as e:
        print(f"[ERROR] Failed to check for Dah'ren Mohran in quest: {e}")
        return False

def selectTier8MonsterNotUnique():
    """
    Selects a tier 8 monster, it is not unique

    
    Args:
        questFilePath: Path to the quest file
        
    Returns:
        int: Monster ID from tier 8, avoiding another unique monster
    """
    tier8_monsters = [m for m in VariousLists.monsterListFromTier(8) if m not in VariousLists.uniqueMonstersList()]
    return random.choice(tier8_monsters)


def randomizeMonstersNoProgression(monster_ids, quest_path):
    large_id_list = VariousLists.getLargeList()
    count = 0  # Initialize count variable
    if settingAllowUniqueMonsters:
        alreadyHasUnique = False
        for mid in monster_ids:
            if(alreadyHasUnique):
                new_mon=random.choice([m for m in large_id_list if m not in VariousLists.uniqueMonstersList()]) #Random and not unique
            else:
                new_mon=random.choice(large_id_list) #Random and unique
            if new_mon in VariousLists.uniqueMonstersList():
                alreadyHasUnique = True
            QuestEditor.find_and_replace_monster_individual(quest_path, mid, new_mon, False)
            count += 1
    
    return count


def packQuestArc(output_arc_name="quest01.arc"):
    """
    Packs the quest files into an ARC file using customArcRepacker.py.
    This function should be called after all randomization is complete.
    
    Args:
        output_arc_name: Name of the output ARC file (default: "quest01.arc")
    """
    import subprocess
    import os
    
    try:
        # Get the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Build paths
        repacker_path = os.path.join(script_dir, "customArcRepacker.py")
        output_arc_path = os.path.join(script_dir, output_arc_name)
        loc_dir = os.path.join(script_dir, "loc")
        
        # Build the command
        cmd = ["python", repacker_path, "c", output_arc_path, loc_dir]
        
        # Execute the command
        print(f"[INFO] Packing quest files into {output_arc_name}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check if successful
        if result.returncode == 0:
            print(f"[SUCCESS] Quest files packed successfully into {output_arc_name}")
            print(f"Output: {result.stdout}")
        else:
            print(f"[ERROR] Failed to pack quest files: {result.stderr}")
            
    except Exception as e:
        print(f"[ERROR] Exception while packing quest files: {e}")
#endregion

def randomizeMap(questFilePath: str, newMonstersList: list):
    """
    Randomize the map for a quest based on its monster list and wave configuration.
    
    This function:
    1. Identifies unique monsters in the quest
    2. Selects appropriate maps based on monster types, wave configuration, and settings
    3. Handles special cases for unique monsters
    4. Applies the map change to the quest file
    5. Reorders unique monsters to appear last in quests with 3+ monsters
    6. Special handling for 2-monster quests with 1 unique monster
    7. Applies arena restrictions based on wave configuration
    8. Manages waves properly for multi-monster quests
    """

    # All monsters in its waves - populate allWaves FIRST
    parsed_mib = QuestEditor.parse_mib(questFilePath)
    rawWaves=parsed_mib['large_monster_table']
    allWaves=[]
    uniqueMons=[]
    
    # Populate allWaves before calling getPossibleMaps
    for wave in rawWaves:
        idList=[]
        for m in wave:
            idList.append(m['monster_id'])
            if m['monster_id'] in VariousLists.uniqueMonstersList():
                uniqueMons.append(m['monster_id'])
        allWaves.append(idList)
    
    # Check if we have multi-monster waves for arena restriction
    has_multi_monster_wave = any(len(wave) > 1 for wave in allWaves)
    
    # Now get possible maps with properly populated allWaves
    possible_maps = getPossibleMaps(newMonstersList,allWaves,newMonstersList)
    newMap=random.choice(possible_maps)
    
    # Check for unique monsters in first wave that need specific maps
    # BUT respect arena restrictions if we have multi-monster waves
    allUniqueMons=VariousLists.uniqueMonstersList()
    wave0=allWaves[0] if allWaves else []
    for m in wave0:
        if m in allUniqueMons or m in VariousLists.akantorAndUkanlos():
            unique_map = getMapForUniqueMonsterID(m)
            # Only use the unique map if it doesn't violate arena restrictions
            if settingNoMoreThanOneInArena and has_multi_monster_wave:
                arena_maps = VariousLists.getArenaMapsList()
                if unique_map not in arena_maps:
                    newMap = unique_map
                    print(f"[INFO] Using specific map {unique_map} for unique monster {m}")
                else:
                    print(f"[INFO] Skipping arena map {unique_map} for unique monster {m} due to multi-monster waves")
            else:
                newMap = unique_map
                print(f"[INFO] Using specific map {unique_map} for unique monster {m}")
    
    editMapData(questFilePath,newMonstersList,newMap)
    if(settingNoMoreThanOneInArena and newMap in VariousLists.getArenaMapsList()):
        1==1
#AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
 #AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
 #AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
 #AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
 #AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
 #AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
 #AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
 
def adjustStatsForSolo(stats : dict) -> dict:
    # adjustment: decrease health and attack by 20%
    adjusted_stats = stats.copy()
    if 'hp' in adjusted_stats:
        adjusted_stats['hp'] = int(adjusted_stats['hp'] * 0.05)
    if 'atk' in adjusted_stats:
        adjusted_stats['atk'] = int(adjusted_stats['atk'] * 0.05)
    return adjusted_stats

def progresionRandomizer(full_path: str):
    parsedMib = QuestEditor.parse_mib(full_path)
    monstersIDs = getLargeMonstersIDs(parsedMib)
    if len(monstersIDs) > 0:
        QuestEditor.clear_all_objectives(full_path)

    rank = parsedMib['quest_rank']
    tierChances = VariousLists.tierChancesOfRank(rank)
    allTiers = [8, 7, 6, 5, 4, 3, 2, 1]
    monCount = 0
    newMonsters = []
    for i in monstersIDs:
        selectedTier = random.choices(allTiers, weights=tierChances, k=1)[0]
        possibleMons = VariousLists.monsterListFromTier(selectedTier)
        newMon = random.choice(possibleMons)
            
        newMonsters.append(newMon)
        QuestEditor.push_objective_recent(full_path, newMon, type_val=1, qty=1)
        QuestEditor.find_and_replace_monster_individual(full_path, i, newMon, False)

        if settingSoloBalance:
            stats = QuestEditor.read_meta_entry(full_path, monCount)
            newStats = adjustStatsForSolo(stats)
            QuestEditor.write_stats_from_dict(full_path, monCount, newStats)

        monCount += 1
    monCount = 0
    fixQuestMonsters(full_path)



def findNonUniqueMonsterInWavesAndNotInFirstWave(allWaves: list) -> list:
    """
    Search for the LAST non-unique monster that is NOT in the first wave (wave 0).

    Parameters:
      allWaves (list): list of waves, each wave is a list of monster IDs (ints).
                       Example: [[11,12],[21],[31,32]]

    Returns:
      [monster_id, wave_index, monster_position_in_wave] if found,
      otherwise [-1, -1, -1].
    """
    unique_set = set(VariousLists.uniqueMonstersList())

    # iterate waves from last to first, but skip wave 0
    for wave_index in range(len(allWaves) - 1, 0, -1):
        wave = allWaves[wave_index]
        # iterate positions from last to first to get the "last" monster in that wave
        for pos in range(len(wave) - 1, -1, -1):
            monster_id = wave[pos]
            if monster_id not in unique_set:
                return [monster_id, wave_index, pos]

    return [-1, -1, -1]


def fixExtremeCase1Unique1NormalInWave0(questFilePath: str, uniqueMonsterId: int):
    """
    Fix the extreme case where wave0 has [unique, normal] and total monsters == 2.
    Procedure:
      - create an empty wave (reparse to get its real index)
      - find the source (table, pos) of the unique
      - swap unique -> new_table_index pos 0
      - delete the placeholder that remained at the source position
    """
    # create new empty wave and reparse to get its index
    created = QuestEditor.createEmptyWave(questFilePath)
    if not created:
        print("[ERROR] createEmptyWave failed in fixExtremeCase1Unique1NormalInWave0")
        return False

    parsed = QuestEditor.parse_mib(questFilePath)
    tables = parsed.get('large_monster_table', [])
    new_table_index = len(tables) - 1
    if new_table_index < 0:
        print("[ERROR] no tables after createEmptyWave")
        return False

    # find the current instance (table, pos) of the unique monster BEFORE the swap
    src_table = -1
    src_pos = -1
    for ti, table in enumerate(tables):
        for mi, m in enumerate(table):
            if m.get('monster_id') == uniqueMonsterId:
                src_table = ti
                src_pos = mi
                break
        if src_table != -1:
            break

    if src_table == -1:
        print(f"[ERROR] unique monster {uniqueMonsterId} not found after createEmptyWave")
        return False

    # move unique to the new table (swap by monster id is safe: unique is unique)
    success = QuestEditor.swap_large_monster(questFilePath, uniqueMonsterId, new_table_index, 0)
    if not success:
        print(f"[ERROR] swap_large_monster failed for unique {uniqueMonsterId} -> table {new_table_index}")
        return False

    # delete the placeholder that now sits at the original source (it was swapped there)
    ok_del = QuestEditor.delete_from_large_table(questFilePath, {'table_index': src_table, 'monster_index': src_pos})
    if not ok_del:
        print("[ERROR] delete_from_large_table failed in extreme fix; file may be inconsistent")
        return False

    return True



def validateArenaAndMusicSettings(full_path: str):
    """
    Validates and fixes arena and music settings after map assignment.
    - If settingNoMoreThanOneInArena is active and quest is in arena map with multi-monster waves, fix it
    - If settingAlwaysMusic is active and quest is in non-musical arena without musical monsters, add one
    """
    try:
        parsed = QuestEditor.parse_mib(full_path)
        quest_map_id = QuestEditor.get_map_id(full_path)
        rawWaves = parsed.get('large_monster_table', [])
        
        arena_maps = VariousLists.getArenaMapsList()
        no_musical_maps = VariousLists.getNoMusicalMapsList()
        musical_monsters = VariousLists.getMusicalMonstersList()
        
        is_arena_map = quest_map_id in arena_maps
        is_no_musical_map = quest_map_id in no_musical_maps
        
        # Check arena restriction
        if settingNoMoreThanOneInArena and is_arena_map:
            # Find waves with multiple monsters
            for wave_idx, wave in enumerate(rawWaves):
                if len(wave) > 1:
                    print(f"[INFO] Arena map {quest_map_id} has multi-monster wave {wave_idx}, fixing...")
                    # Move all but first monster to later waves or create new waves
                    monsters_to_move = wave[1:]  # All except first
                    
                    # Remove extra monsters from current wave
                    for i in range(len(monsters_to_move) - 1, -1, -1):
                        QuestEditor.delete_from_large_table(full_path, {'table_index': wave_idx, 'monster_index': i + 1})
                    
                    # Add them to later waves or create new waves
                    for monster in monsters_to_move:
                        # Try to find an empty wave first
                        empty_wave_idx = -1
                        for w_idx, w in enumerate(rawWaves):
                            if w_idx > wave_idx and len(w) == 0:
                                empty_wave_idx = w_idx
                                break
                        
                        if empty_wave_idx != -1:
                            # Add to empty wave
                            QuestEditor.add_monster_to_wave(full_path, empty_wave_idx, monster['monster_id'])
                        else:
                            # Create new wave
                            QuestEditor.createEmptyWave(full_path)
                            # Reparse to get updated structure
                            parsed = QuestEditor.parse_mib(full_path)
                            new_wave_idx = len(parsed.get('large_monster_table', [])) - 1
                            QuestEditor.add_monster_to_wave(full_path, new_wave_idx, monster['monster_id'])
                    
                    # Reparse after changes
                    parsed = QuestEditor.parse_mib(full_path)
                    rawWaves = parsed.get('large_monster_table', [])
        
        # Check music requirement
        if settingAlwaysMusic and is_no_musical_map:
            # Check if any monster in the quest is musical
            has_musical_monster = False
            for wave in rawWaves:
                for monster in wave:
                    if monster.get('monster_id') in musical_monsters:
                        has_musical_monster = True
                        break
                if has_musical_monster:
                    break
            
            if not has_musical_monster:
                print(f"[INFO] Non-musical arena map {quest_map_id} needs a musical monster, adding one...")
                # Replace the first non-unique monster with a musical one
                for wave_idx, wave in enumerate(rawWaves):
                    for monster_idx, monster in enumerate(wave):
                        monster_id = monster.get('monster_id')
                        if monster_id not in VariousLists.uniqueMonstersList():
                            # Replace with a random musical monster
                            musical_replacement = random.choice(musical_monsters)
                            QuestEditor.find_and_replace_monster_individual(full_path, monster_id, musical_replacement, False)
                            print(f"[INFO] Replaced monster {monster_id} with musical monster {musical_replacement}")
                            return
                            
    except Exception as e:
        print(f"[ERROR] Failed to validate arena/music settings: {e}")

def fixQuestMonsters(full_path: str):
    """
    Fixes quest monsters to ensure proper unique monster placement and Akantor/Ukanlos handling.
    - Only one unique per quest (reroll until satisfied)
    - If a single unique exists and it's in wave0, move it to a non-first wave (prefer last or empty wave)
    - Handle Akantor/Ukanlos special placement rules
    """
    # parse and build helper lists
    parsed = QuestEditor.parse_mib(full_path)
    rawWaves = parsed.get('large_monster_table', [])
    quest_map_id = QuestEditor.get_map_id(full_path)
    akantor_ukanlos = VariousLists.akantorAndUkanlos()  # [33, 116]
    
    def build_lists_from_raw(raw):
        aw = []
        u = []
        mc = 0
        for w in raw:
            ids = []
            for m in w:
                ids.append(m['monster_id'])
                if m['monster_id'] in VariousLists.uniqueMonstersList():
                    u.append(m['monster_id'])
                mc += 1
            aw.append(ids)
        return aw, u, mc

    allWaves, uniqueMons, mcount = build_lists_from_raw(rawWaves)

    # If more than 1 unique -> reroll until <=1 (safe loop with attempt limit)
    attempts = 0
    while len(uniqueMons) > 1 and attempts < 99:
        randomizeQuest(full_path)  # reroll
        parsed = QuestEditor.parse_mib(full_path)
        rawWaves = parsed.get('large_monster_table', [])
        allWaves, uniqueMons, mcount = build_lists_from_raw(rawWaves)
        attempts += 1
    if len(uniqueMons) > 1:
        print("[WARNING] Could not reduce uniques to 1 after rerolls")
        # continue anyway

    # reparse state fresh (defensive)
    parsed = QuestEditor.parse_mib(full_path)
    rawWaves = parsed.get('large_monster_table', [])
    allWaves, uniqueMons, mcount = build_lists_from_raw(rawWaves)

    # handle single-unique cases
    if len(uniqueMons) == 1:
        uniqueMonsterId = uniqueMons[0]

        # if only 2 monsters total and both in wave0 -> extreme case
        if mcount == 2 and len(allWaves) >= 1 and len(allWaves[0]) == 2:
            fixExtremeCase1Unique1NormalInWave0(full_path, uniqueMonsterId)
            # reparse for safety
            parsed = QuestEditor.parse_mib(full_path)
            rawWaves = parsed.get('large_monster_table', [])
            allWaves, uniqueMons, mcount = build_lists_from_raw(rawWaves)
            return

        # if unique is in wave0 and there are more than two monsters total -> move it out
        if mcount > 1 and len(allWaves) >= 1 and uniqueMonsterId in allWaves[0]:
            # find unique position robustly
            try:
                uniquePos = allWaves[0].index(uniqueMonsterId)
            except ValueError:
                print("[ERROR] unique present in allWaves[0] but index() failed")
                return

            # helper: find first empty wave index (or -1)
            def first_empty_wave_index(aw):
                for idx, w in enumerate(aw):
                    if len(w) == 0:
                        return idx
                return -1

            empty_idx = first_empty_wave_index(allWaves)
            if empty_idx != -1:
                # move unique to empty wave
                success = QuestEditor.move_monster_to_empty_table(full_path, uniqueMonsterId, empty_idx)
                if success:
                    # after swap the placeholder is where unique used to be; delete it
                    ok_del = QuestEditor.delete_from_large_table(full_path, {'table_index': 0, 'monster_index': uniquePos})
                    if ok_del:
                        # update local representation
                        allWaves[empty_idx].append(uniqueMonsterId)
                        allWaves[0].pop(uniquePos)
                else:
                    print(f"[ERROR] swap to empty wave failed for unique {uniqueMonsterId}")
                return
            else:
                # no empty wave: choose replacement slot (the last non-unique outside wave0)
                replacement = findNonUniqueMonsterInWavesAndNotInFirstWave(allWaves)
                if replacement != [-1, -1, -1]:
                    # replacement = [monster_id, wave_idx, pos]
                    # move unique into that replacement's slot
                    rep_mid, rep_w, rep_pos = replacement
                    success = QuestEditor.swap_large_monster(full_path, uniqueMonsterId, rep_w, rep_pos)
                    if success:
                        # update local allWaves safely
                        allWaves[rep_w][rep_pos] = uniqueMonsterId
                        allWaves[0][uniquePos] = rep_mid
                    else:
                        print(f"[ERROR] swap_large_monster failed moving unique {uniqueMonsterId} -> wave {rep_w} pos {rep_pos}")
                    return
                else:
                    # fallback: try create new wave and move unique there
                    created = QuestEditor.createEmptyWave(full_path)
                    if not created:
                        print("[ERROR] createEmptyWave failed as final fallback")
                        return
                    parsed = QuestEditor.parse_mib(full_path)
                    new_idx = len(parsed.get('large_monster_table', [])) - 1
                    success = QuestEditor.swap_large_monster(full_path, uniqueMonsterId, new_idx, 0)
                    if success:
                        # delete placeholder at old spot
                        ok_del = QuestEditor.delete_from_large_table(full_path, {'table_index': 0, 'monster_index': uniquePos})
                        if ok_del:
                            # update local
                            allWaves.append([uniqueMonsterId])
                            allWaves[0].pop(uniquePos)
                    else:
                        print("[ERROR] final fallback swap failed")
                        return

    # Handle Akantor/Ukanlos special placement rules
    # If they are on their specific maps (Akantor: 9, Ukanlos: 20), they can't be in first wave
    # If they are on other maps, they must be in wave 2+ (randomly placed, not replacing uniques)
    for wave_idx, wave in enumerate(allWaves):
        for monster_id in wave:
            if monster_id in akantor_ukanlos:
                akantor_map = 9  # Ingle Isle
                ukanlos_map = 20  # Polar Field
                
                # Check if monster is on its specific map
                is_on_specific_map = (monster_id == 33 and quest_map_id == akantor_map) or \
                                   (monster_id == 116 and quest_map_id == ukanlos_map)
                
                # If on specific map and in first wave, move to later wave
                if is_on_specific_map and wave_idx == 0:
                    print(f"[INFO] Moving {VariousLists.getMonsterName(monster_id)} from wave 1 on its specific map")
                    # Find position in wave
                    try:
                        monster_pos = wave.index(monster_id)
                    except ValueError:
                        continue
                    
                    # Try to find empty wave or create one
                    empty_wave_idx = -1
                    for w_idx, w in enumerate(allWaves):
                        if w_idx > 0 and len(w) == 0:
                            empty_wave_idx = w_idx
                            break
                    
                    if empty_wave_idx != -1:
                        # Move to empty wave
                        success = QuestEditor.swap_large_monster(full_path, monster_id, empty_wave_idx, 0)
                        if success:
                            QuestEditor.delete_from_large_table(full_path, {'table_index': 0, 'monster_index': monster_pos})
                            allWaves[empty_wave_idx].append(monster_id)
                            allWaves[0].pop(monster_pos)
                    else:
                        # Create new wave
                        created = QuestEditor.createEmptyWave(full_path)
                        if created:
                            parsed = QuestEditor.parse_mib(full_path)
                            new_wave_idx = len(parsed.get('large_monster_table', [])) - 1
                            success = QuestEditor.swap_large_monster(full_path, monster_id, new_wave_idx, 0)
                            if success:
                                QuestEditor.delete_from_large_table(full_path, {'table_index': 0, 'monster_index': monster_pos})
                                allWaves.append([monster_id])
                                allWaves[0].pop(monster_pos)
                
                # If not on specific map, ensure it's in wave 2+ (but don't replace uniques)
                elif not is_on_specific_map and wave_idx == 0:
                    print(f"[INFO] Moving {VariousLists.getMonsterName(monster_id)} to wave 2+ on non-specific map")
                    # Similar logic as above but for non-specific maps
                    try:
                        monster_pos = wave.index(monster_id)
                    except ValueError:
                        continue
                    
                    # Find a suitable wave (not first, and not replacing uniques)
                    target_wave_idx = -1
                    for w_idx, w in enumerate(allWaves):
                        if w_idx > 0:
                            # Check if wave has room or is empty
                            has_unique = any(m_id in VariousLists.uniqueMonstersList() for m_id in w)
                            if not has_unique and len(w) == 0:
                                target_wave_idx = w_idx
                                break
                    
                    if target_wave_idx != -1:
                        success = QuestEditor.swap_large_monster(full_path, monster_id, target_wave_idx, 0)
                        if success:
                            QuestEditor.delete_from_large_table(full_path, {'table_index': 0, 'monster_index': monster_pos})
                            allWaves[target_wave_idx].append(monster_id)
                            allWaves[0].pop(monster_pos)
                    else:
                        # Create new wave for Akantor/Ukanlos
                        created = QuestEditor.createEmptyWave(full_path)
                        if created:
                            parsed = QuestEditor.parse_mib(full_path)
                            new_wave_idx = len(parsed.get('large_monster_table', [])) - 1
                            success = QuestEditor.swap_large_monster(full_path, monster_id, new_wave_idx, 0)
                            if success:
                                QuestEditor.delete_from_large_table(full_path, {'table_index': 0, 'monster_index': monster_pos})
                                allWaves.append([monster_id])
                                allWaves[0].pop(monster_pos)

    # if no unique or handled, done
    return

        
 


def randomizeQuest(full_path: str):
    if os.path.isfile(full_path):
        parsedMib = QuestEditor.parse_mib(full_path)
        monstersIDs = getLargeMonstersIDs(parsedMib)

        if settingProgresion:
            progresionRandomizer(full_path)
        else:
            randomizeMonstersNoProgression(monstersIDs, full_path)

        fixQuestMonsters(full_path)
        if settingRandomMap:            
            randomizeMap(full_path, monstersIDs)
        
        # Call the new arena and music validation after map assignment
        if settingNoMoreThanOneInArena or settingAlwaysMusic:
            validateArenaAndMusicSettings(full_path)
        
        # Always fix quest monsters to ensure unique monsters and Akantor/Ukanlos are in the correct waves
        fixQuestMonsters(full_path)

        

        

def main():
    for file in os.listdir(folder):
        print('\n')
        print(file)
        full_path = os.path.join(folder, file)
        randomizeQuest(full_path)
    
def packQuestArc(output_arc_name="quest01.arc"):
    """
    Packs the quest files into an ARC file using customArcRepacker.py.
    This function should be called after all randomization is complete.
    
    Args:
        output_arc_name: Name of the output ARC file (default: "quest01.arc")
    """
    import subprocess
    import os
    
    try:
        # Get the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Build paths
        repacker_path = os.path.join(script_dir, "customArcRepacker.py")
        output_arc_path = os.path.join(script_dir, output_arc_name)
        loc_dir = os.path.join(script_dir, "loc")
        
        # Build the command
        cmd = ["python", repacker_path, "c", output_arc_path, loc_dir]
        
        # Execute the command
        print(f"[INFO] Packing quest files into {output_arc_name}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check if successful
        if result.returncode == 0:
            print(f"[SUCCESS] Quest files packed successfully into {output_arc_name}")
            print(f"Output: {result.stdout}")
        else:
            print(f"[ERROR] Failed to pack quest files: {result.stderr}")
            
    except Exception as e:
        print(f"[ERROR] Exception while packing quest files: {e}")


if __name__ == "__main__":
    folder=getQuestFolder()
    resetQuestFiles()
    sed= input("Enter a seed"'\n')
    setSeed(sed)
    main()
    # Pack the quest files into an ARC file after randomization
    packQuestArc()
