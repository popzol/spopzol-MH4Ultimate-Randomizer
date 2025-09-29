import VariousLists
import QuestEditor
import os
from pathlib import Path
import random

AVAILABLE_MAPS = [1,2,3,4,5,6,7,8,9,10,11,12,14,15,16,17,18,19,20,21]  # Avoid map 13

GVseed=""
settingRandomMap = True
settingProgresion = True
settingAlwaysMusic= True
settingNoMoreThanOneInArena= True

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

def randomizeMap(questFilePath: str, newMonstersList: list):
    uniqueMonsList = VariousLists.uniqueMonstersList()
    unique_monsters = [i for i in newMonstersList if i in uniqueMonsList]
    uniqueMonsCounter = len(unique_monsters)

    if uniqueMonsCounter > 1:
        # Reroll
        randomizeQuest(questFilePath)

    else:
        allAreMusicalMonsters = True
        if settingAlwaysMusic:
            for i in newMonstersList:
                if not i in VariousLists.getMusicalMonstersList():
                    allAreMusicalMonsters = False

        # Arena restriction: exclude arena maps if there are exactly 2 monsters and setting is active
        possible_maps = AVAILABLE_MAPS
        if settingNoMoreThanOneInArena and len(newMonstersList) == 2:
            arena_maps = VariousLists.getArenaMapsList()
            possible_maps = [m for m in AVAILABLE_MAPS if m not in arena_maps]

        # Choose map for unique monster if needed
        if uniqueMonsCounter == 1:
            unique_monster_id = unique_monsters[0]
            if not QuestEditor.is_large_monster_not_first_and_table_has_three(QuestEditor.parse_mib(questFilePath), unique_monster_id):
                newMap = get_map_for_unique_monster_id(unique_monster_id)
                # If the chosen map is not allowed, pick a random allowed map
                if newMap not in possible_maps:
                    newMap = random.choice(possible_maps)
                editMapData(questFilePath, newMonstersList, newMap)
                # Special handling for Gogmazios (id 89) AFTER editMapData
                if unique_monster_id == 89:
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
            return

        # For 0 unique monsters (or any other case)
        newMap = random.choice(possible_maps)
        while (settingAlwaysMusic and newMap in VariousLists.getNoMusicalMapsList() and not allAreMusicalMonsters):
            newMap = random.choice(possible_maps)

        editMapData(questFilePath, newMonstersList, newMap)


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

folder=getQuestFolder()
if True:
    
    sed= input("Enter a seed"'\n')
    setSeed(sed)
    main()
else:
    mainTests()

#QuestEditor.expand_large_monster_table(full_path,0,1)