import VariousLists
import QuestEditor
import os
from pathlib import Path
import random



GVseed=""
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

def getMonstersIDs(parsedMib: dict)-> list:
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

for file in os.listdir(folder):
    full_path = os.path.join(folder, file)
    if os.path.isfile(full_path):
        parsedMib = QuestEditor.parse_mib(full_path)
        monstersIDs= getMonstersIDs(parsedMib)
        largeIDList = VariousLists.getLargeList()
        for i in monstersIDs:
            newMon= random.choice(largeIDList)
            
            QuestEditor.find_and_replace_monster(full_path, i, newMon, False)
    
                
                
            

        
        