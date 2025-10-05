from ast import List
from operator import ne
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

def getPossibleMaps(questFilePath: str) -> list:
    """
    Get a list of possible maps based on settings and wave configuration.
    Handles arena restrictions when any wave has multiple monsters.
    """
    if settingNoMoreThanOneInArena:
        # Check if any wave has multiple monsters
        if QuestEditor.has_wave_with_multiple_monsters(questFilePath):
            arena_maps = VariousLists.getArenaMapsList()
            return [m for m in AVAILABLE_MAPS if m not in arena_maps]
    return AVAILABLE_MAPS.copy()

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
    
    

    return 0  # reset count


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

    # All monsters in its waves
    parsed_mib = QuestEditor.parse_mib(questFilePath)
    everyMon = parsed_mib['large_monster_table']
    if len(everyMon) == 0:
        wave1=[]
        wave2=[]
        wave3=[]
    elif len(everyMon) == 1:
        wave1= everyMon[0]
        wave2=[]
        wave3=[]
    elif len(everyMon) == 2:
        wave1= everyMon[0]
        wave2= everyMon[1]
        wave3=[]
    elif len(everyMon) == 3:
        wave1= everyMon[0]
        wave2= everyMon[1]
        wave3= everyMon[2]
    print(parsed_mib['text'][:1][:1])
    for i in everyMon:
        print(i)
        print('\n')
    # Identify unique monsters
    uniqueMonsList = VariousLists.uniqueMonstersList()
    unique_monsters = [i for i in newMonstersList if i in uniqueMonsList]
    uniqueMonsCounter = len(unique_monsters)
    
    # Check if all monsters are musical (for music settings)
    allAreMusicalMonsters = checkMusicalMonsters(newMonstersList)
    
    # Get possible maps based on wave configuration and settings
    possible_maps = getPossibleMaps(questFilePath)
    
    # Handle multiple unique monsters in a quest with 3+ monsters
    if uniqueMonsCounter < len(newMonstersList) and len(newMonstersList) >= 3 and uniqueMonsCounter>1:
        # Select map first to determine wave structure
        newMap = selectMapForRegularMonsters(possible_maps, allAreMusicalMonsters)
        
        # Ensure we have enough waves for proper monster distribution
       
        
        # Place unique monsters in positions other than the first
        for i, unique_monster_id in enumerate(unique_monsters):
            # Position them at positions 1 and 2 (second and third)
            position = i + 1
            if position < len(newMonstersList):
                QuestEditor.moveMonsterToPosition(questFilePath, unique_monster_id, position)
        
        # Apply map change
        editMapData(questFilePath, newMonstersList, newMap)
        return
    # If there are multiple unique monsters in a quest with fewer than 3 monsters, restart randomization
    elif uniqueMonsCounter > 1:
        randomizeQuest(questFilePath)
        return
    
    # Handle case with exactly one unique monster
    if uniqueMonsCounter == 1:
        unique_monster_id = unique_monsters[0]
        
        # Special handling for Dah'ren Mohran (ID 46)
        if unique_monster_id == 46:
            # Always use map 6 for Dah'ren Mohran
            newMap = 6
            
            # Special handling based on monster count
            monster_count = len(newMonstersList)
            
            # Case 1: Single monster quest - just use map 6
            if monster_count == 1:
                editMapData(questFilePath, newMonstersList, newMap)
                return
                
            # Case 2: Two monster quest - handle companion
            elif monster_count == 2:
                # Ensure we have proper wave structure for arena restrictions
                
                
                # Move Dah'ren to the second wave
                QuestEditor.moveMonsterToPosition(questFilePath, 46, 1)
                
                # Apply map change
                editMapData(questFilePath, newMonstersList, newMap)
                return
                
            # Case 3: Three or more monsters - place Dah'ren last
            else:
                # Ensure we have enough waves
                
                
                QuestEditor.moveMonsterToPosition(questFilePath, 46, -1)
                #Dah'ren must ALWAYS be in its map
                newMap = 6
                editMapData(questFilePath, newMonstersList, newMap)
                return
        
        # Original handling for other unique monsters
        monster_count = len(newMonstersList)
        
        # Case 1: Single monster quest - use the unique monster's specific map
        if monster_count == 1:
            newMap = getMapForUniqueMonsterID(unique_monster_id)
        
        # Case 2: Two monster quest - special handling for second monster
        elif monster_count == 2:
            newMap = getMapForUniqueMonsterID(unique_monster_id)
            
            # Ensure we have proper wave structure for arena restrictions
            
            
            # Move unique monster to the second wave
            QuestEditor.moveMonsterToPosition(questFilePath, unique_monster_id, 1)
        
        # Case 3: Three or more monsters
        else:
            # Since unique monster will be moved to last position, use random map selection
            newMap = selectMapForRegularMonsters(possible_maps, allAreMusicalMonsters)
            
            # Ensure we have enough waves
           
            
        # Apply map change
        editMapData(questFilePath, newMonstersList, newMap)
        
        # Special handling for Gogmazios
        if unique_monster_id == 89:
            handleGogmazios(questFilePath)
            
        # If there are 3 or more monsters, reorder the unique monster to be last
        if monster_count >= 3:
                QuestEditor.moveMonsterToPosition(questFilePath, unique_monster_id, -1)
    
    # Handle regular monsters (no unique monsters)
    else:
        monster_count = len(newMonstersList)
        
        # Select map first to determine wave structure
        newMap = selectMapForRegularMonsters(possible_maps, allAreMusicalMonsters)
        
        # For two-monster quests, ensure they're in separate waves for arena maps
            
        editMapData(questFilePath, newMonstersList, newMap)
    
    return


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



def findNonUniqueMonsterInWavesAndNotInFirstWave(allWaves: list) -> list:
    """
    Finds the first unique monster that is not in the first wave (wave 0).

    Parameters:
        allWaves (list): List of wave lists, each containing monster IDs.

    Returns:
        list: A list containing [monster_id, wave_index, monster_position_in_wave]
              if a unique monster is found outside wave 0, otherwise [-1, -1, -1].
    """
    result = [-1, -1, -1]
    found = False
    wave_index = 0
    while wave_index < len(allWaves) and not found:
        wave = allWaves[wave_index]
        if wave_index != 0:  # Skip the first wave (wave 0)
            monster_position = 0
            while monster_position < len(wave) and not found:
                monster_id = wave[monster_position]
                if monster_id in VariousLists.uniqueMonstersList():
                    result = [monster_id, wave_index, monster_position]
                    found = True
                monster_position += 1
        wave_index += 1
    return result

def fixExtremeCase1Unique1NormalInWave0(allWaves: list):
    """
    Fixes the extreme case where there is only one unique monster and 1 monster in normal in wave 0.
    Creates a new wave with no monsters
    Moves the unique monster to the new wave.

    Parameters:
        allWaves (list): List of wave lists, each containing monster IDs.
    """
  

def fixQuestMonsters(full_path: str):

    rawWaves= QuestEditor.parse_mib(full_path)['large_monster_table']
    allWaves=[]
    uniqueMons=[]
    for wave in rawWaves:
        idList=[]
        for m in wave:
            idList.append(m['monster_id'])
            if m['monster_id'] in VariousLists.uniqueMonstersList():
                uniqueMons.append(m['monster_id'])
        allWaves.append(idList)
    while len(uniqueMons) > 1:
        progresionRandomizer(full_path) #reroll
        allmons= getLargeMonstersIDs(QuestEditor.parse_mib(full_path))
        uniqueMons= [m for m in allmons if m in VariousLists.uniqueMonstersList()]
        

    rawWaves= QuestEditor.parse_mib(full_path)['large_monster_table']
    allmons= getLargeMonstersIDs(QuestEditor.parse_mib(full_path))
    allWaves=[]
    
    for wave in rawWaves:
        idList=[]
        for m in wave:
            idList.append(m['monster_id'])
        allWaves.append(idList)

    if len(uniqueMons) ==1 and allmons != 1:
        
        QuestEditor.swap_large_monster(uniqueMons[0])
        replacement= findNonUniqueMonsterInWavesAndNotInFirstWave(allWaves)
        if replacement != [-1, -1, -1]:
            QuestEditor.swap_large_monster(full_path,uniqueMons[0],replacement[1], replacement[2])
        elif len(allmons) == 2:
            fixExtremeCase1Unique1NormalInWave0(allWaves)

        else:
            print("No replacement found for unique monster.")

        



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
