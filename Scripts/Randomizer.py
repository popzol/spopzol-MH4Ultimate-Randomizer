import VariousLists
import QuestEditor
import os
from pathlib import Path
import random



GVseed=""
settingRandomMap = True

def setSeed(Seed: str):
    GVseed= Seed
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

setSeed(random.randint(1, 1000000))
folder=getQuestFolder()

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
    # evitar map 13
    while newMap == 13:
        newMap = random.randint(1, 21)

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

def randomizeMap(questFilePath :str, newMonstersList: list):

    uniqueMonsCounter=0
    for i in newMonstersList:
        if i in [24, 46, 77, 78, 79, 83, 89, 46, 117, 110, 111]:
            uniqueMonsCounter +=1

    if uniqueMonsCounter>1:
        #Reroll
        randomizeQuest(questFilePath)

    elif uniqueMonsCounter==0:
        newMap=random.randint(1,21)
        editMapData(questFilePath, newMonstersList,newMap)

    if uniqueMonsCounter ==1:
        
        if 24 in newMonstersList or 83 in newMonstersList or 110 in newMonstersList or 111 in newMonstersList: #Dalamadurs in Crag
            editMapData(questFilePath, newMonstersList, 8)
        elif 46 in newMonstersList: #Dahren
            editMapData(questFilePath, newMonstersList, 6)
        elif 77 in newMonstersList or 79 in newMonstersList: #Fattys
            editMapData(questFilePath, newMonstersList, 10)
        elif 78 in newMonstersList or 117 in newMonstersList: #Fire Fattys
            editMapData(questFilePath, newMonstersList, 9)
        elif 89 in newMonstersList:
            QuestEditor.setArea_large(questFilePath, newMonstersList.index(89),89,3)
            editMapData(questFilePath, newMonstersList, 19)




        
        

        



def randomizeQuest(full_path: str):
    if os.path.isfile(full_path):
            parsedMib = QuestEditor.parse_mib(full_path)
            monstersIDs= getLargeMonstersIDs(parsedMib)
            largeIDList = VariousLists.getLargeList()

            
            for i in monstersIDs:
                
                newMon= random.choice(largeIDList)
                QuestEditor.find_and_replace_monster_individual(full_path, i, newMon, False)

            if settingRandomMap:
                parsedMib = QuestEditor.parse_mib(full_path)
                monstersIDs= getLargeMonstersIDs(parsedMib)
                randomizeMap(full_path, monstersIDs)

                

def main():
    for file in os.listdir(folder):
        full_path = os.path.join(folder, file)
        randomizeQuest(full_path)
        
    
def mainTests():
    for file in os.listdir(folder):
        full_path = os.path.join(folder, file)
        if file=="m10111.1BBFD18E":
            QuestEditor.pretty_print_quest_summary(full_path)
            QuestEditor.find_and_replace_monster(full_path,1,5,False)
           

if True:
    sed= input("Enter a seed"'\n')
    setSeed(sed)
    main()
else:
    mainTests()

#QuestEditor.expand_large_monster_table(full_path,0,1)