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

def reset_quest_files():
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

def random_hex(a:int , b:int):
    value = random.randint(a, b)
    return f"{value:02X}"



def build_large_monster_index_list(parsedMib: dict):
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

# Versión corregida de editMapData
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
    index_list = build_large_monster_index_list(parsedMib)
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
        # supongo que setArea_large(path, table_index, monster_index, area) es la firma correcta
        try:
            QuestEditor.setArea_large(questFilePath, table_index, monster_index, newArea)
        except Exception as e:
            print(f"[ERROR] setArea_large falló para table {table_index} idx {monster_index}: {e}")
            continue

        # setear coords (x,z) usando la función que añadiste
        try:
            QuestEditor.set_large_monster_position_by_indices(questFilePath, table_index, monster_index, newCoords[0], newCoords[1])
        except Exception as e:
            print(f"[ERROR] set_large_monster_position... falló para table {table_index} idx {monster_index}: {e}")
            continue

    print(f"[INFO] editMapData_fixed: aplicado map {newMap} en {count} monstruos.")

#region Helper functions
def get_map_for_unique_monster_id(unique_monster_id: int) -> int:
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

def _check_musical_monsters(monster_list: list) -> bool:
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

def _get_possible_maps(monster_count: int) -> list:
    """
    Get a list of possible maps based on settings and monster count.
    Handles arena restrictions for 2-monster quests.
    """
    if settingNoMoreThanOneInArena and monster_count == 2:
        arena_maps = VariousLists.getArenaMapsList()
        return [m for m in AVAILABLE_MAPS if m not in arena_maps]
    return AVAILABLE_MAPS.copy()

def _handle_gogmazios(questFilePath: str):
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
                    print(f"[INFO] setArea_large: placed monster 89 at table {table_idx} idx {mon_idx} area 3")
                    found = True
                except Exception as e:
                    print(f"[ERROR] setArea_large falló: {e}")
                break
        if found:
            break
            
    if not found:
        print("[WARN] No se encontró monster_id 89 en large_monster_table — no se aplica área especial")

def _reorder_unique_monster_to_end(questFilePath: str, unique_monster_id: int):
    """
    Reorders the unique monster to be the last monster in the quest.
    This is useful for quests with 3 or more monsters where the unique monster should appear last.
    
    Args:
        questFilePath: Path to the quest file
        unique_monster_id: ID of the unique monster to reorder
    """
    parsed = QuestEditor.parse_mib(questFilePath)
    monster_count = 0
    
    # Count total monsters
    for table in parsed.get('large_monster_table', []):
        monster_count += len(table)
    
    if monster_count < 3:
        # No need to reorder if there are fewer than 3 monsters
        return
    
    # Reorder the monster to be the last one (position = monster_count - 1)
    try:
        QuestEditor.swap_large_monsters_order(questFilePath, unique_monster_id, monster_count - 1)
        print(f"[INFO] Reordered unique monster {unique_monster_id} to be the last monster")
    except Exception as e:
        print(f"[ERROR] Failed to reorder unique monster: {e}")

def _select_map_for_regular_monsters(possible_maps: list, all_musical: bool) -> int:
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

def _select_tier1_or_tier2_monster():
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
#endregion



def randomizeMap(questFilePath: str, newMonstersList: list):
    """
    Randomize the map for a quest based on its monster list.
    
    This function:
    1. Identifies unique monsters in the quest
    2. Selects appropriate maps based on monster types and settings
    3. Handles special cases for unique monsters
    4. Applies the map change to the quest file
    5. Reorders unique monsters to appear last in quests with 3+ monsters
    6. Special handling for 2-monster quests with 1 unique monster
    """
    # Identify unique monsters
    uniqueMonsList = VariousLists.uniqueMonstersList()
    unique_monsters = [i for i in newMonstersList if i in uniqueMonsList]
    uniqueMonsCounter = len(unique_monsters)
    
    # Check if all monsters are musical (for music settings)
    allAreMusicalMonsters = _check_musical_monsters(newMonstersList)
    
    # Get possible maps based on settings
    possible_maps = _get_possible_maps(len(newMonstersList))
    
    # If there are multiple unique monsters, restart randomization
    if uniqueMonsCounter > 1:
        randomizeQuest(questFilePath)
        return
    
    # Handle case with exactly one unique monster
    if uniqueMonsCounter == 1:
        unique_monster_id = unique_monsters[0]
        
        # Special handling based on monster count
        monster_count = len(newMonstersList)
        
        # Case 1: Single monster quest - use the unique monster's specific map
        if monster_count == 1:
            newMap = get_map_for_unique_monster_id(unique_monster_id)
        
        # Case 2: Two monster quest - special handling for second monster
        elif monster_count == 2:
            newMap = get_map_for_unique_monster_id(unique_monster_id)
            
            # If settingNoMoreThanOneInArena is true, replace the non-unique monster
            # with a random monster from tier 1 or 2
            global settingNoMoreThanOneInArena
            if 'settingNoMoreThanOneInArena' in globals() and settingNoMoreThanOneInArena:
                # Find the index of the non-unique monster
                non_unique_idx = 1 - newMonstersList.index(unique_monster_id)
                
                # Select a random monster from tier 1 or 2
                new_second_monster = _select_tier1_or_tier2_monster()
                
                # Replace the monster in the quest file
                try:
                    QuestEditor.find_and_replace_monster_individual(
                        questFilePath, 
                        newMonstersList[non_unique_idx], 
                        new_second_monster, 
                        False
                    )
                    print(f"[INFO] Replaced second monster with tier 1/2 monster: {new_second_monster}")
                    # Update the monster list for map editing
                    newMonstersList[non_unique_idx] = new_second_monster
                except Exception as e:
                    print(f"[ERROR] Failed to replace second monster: {e}")
        
        # Case 3: Three or more monsters
        else:
            newMap = random.choice(possible_maps)
            
        # Apply map change
        editMapData(questFilePath, newMonstersList, newMap)
        
        # Special handling for Gogmazios
        if unique_monster_id == 89:
            _handle_gogmazios(questFilePath)
            
        # If there are 3 or more monsters, reorder the unique monster to be last
        if monster_count >= 3:
            _reorder_unique_monster_to_end(questFilePath, unique_monster_id)
    
    # Handle regular monsters (no unique monsters)
    else:
        newMap = _select_map_for_regular_monsters(possible_maps, allAreMusicalMonsters)
        editMapData(questFilePath, newMonstersList, newMap)
    
    return

def adjustStatsForSolo(stats : dict) -> dict:
    # adjustment: decrease health and attack by 20%
    adjusted_stats = stats.copy()
    if 'hp' in adjusted_stats:
        adjusted_stats['hp'] = int(adjusted_stats['hp'] * 0.8)
    if 'atk' in adjusted_stats:
        adjusted_stats['atk'] = int(adjusted_stats['atk'] * 0.8)
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

    if settingRandomMap:
        # Re-parse only if you know the file has changed
        parsedMib = QuestEditor.parse_mib(full_path)
        monstersIDs = getLargeMonstersIDs(parsedMib)
        randomizeMap(full_path, monstersIDs)


def randomizeQuest(full_path: str):
    if os.path.isfile(full_path):
        parsedMib = QuestEditor.parse_mib(full_path)
        monstersIDs = getLargeMonstersIDs(parsedMib)

        if settingProgresion:
            progresionRandomizer(full_path)
        else:
            monCount = 0
            largeIDList = VariousLists.getLargeList()
            for i in monstersIDs:
                newMon = random.choice(largeIDList)
                QuestEditor.find_and_replace_monster_individual(full_path, i, newMon, False)
                monCount += 1
            monCount = 0

            if settingRandomMap:
                # Only re-parse if you know the file has changed
                parsedMib = QuestEditor.parse_mib(full_path)
                monstersIDs = getLargeMonstersIDs(parsedMib)
                randomizeMap(full_path, monstersIDs)

                

def main():
    for file in os.listdir(folder):
        print('\n')
        print(file)
        full_path = os.path.join(folder, file)
        randomizeQuest(full_path)
         
        
    
def mainTests():
    for file in os.listdir(folder):
        full_path = os.path.join(folder, file)
        if file=="m11011.1BBFD18E":
            QuestEditor.pretty_print_quest_summary(full_path)
            parsedmib= QuestEditor.parse_mib(full_path)
            print(parsedmib['objectives'])

def pack_quest_arc(output_arc_name="quest01.arc"):
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

folder=getQuestFolder()
if True:
    reset_quest_files()
    sed= input("Enter a seed"'\n')
    setSeed(sed)
    main()
    # Pack the quest files into an ARC file after randomization
    pack_quest_arc()
else:
    mainTests()

#QuestEditor.expand_large_monster_table(full_path,0,1)