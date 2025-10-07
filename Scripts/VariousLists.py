import os

#Unique monsters are monsters that need its zone for a cinematic
#Special monsters are BIG monsters that need a large zone
def getMonsterName(monsterID: int) -> str:
    MONSTER_NAMES = {
        0: "None",
        1: "Rathian",
        2: "Rathalos",
        3: "Pink Rathian",
        4: "Azure Rathalos",
        5: "Gold Rathian",
        6: "Silver Rathalos",
        7: "Yian Kut-Ku",
        8: "Blue Yian Kut-Ku",
        9: "Gypceros",
        10: "Purple Gypceros",
        11: "Tigrex",
        12: "Brute Tigrex",
        13: "Gendrome",
        14: "Iodrome",
        15: "Great Jaggi",
        16: "Velocidrome",
        17: "Congalala",
        18: "Emerald Congalala",
        19: "Rajang",
        20: "Kecha Wacha",
        21: "Tetsucabra",
        22: "Zamtrios",
        23: "Najarala",
        24: "Dalamadur (Head)",
        25: "Seltas",
        26: "Seltas Queen",
        27: "Nerscylla",
        28: "Gore Magala",
        29: "Shagaru Magala",
        30: "Yian Garuga",
        31: "Kushala Daora",
        32: "Teostra",
        33: "Akantor",
        34: "Kirin",
        35: "Oroshi Kirin",
        36: "Khezu",
        37: "Red Khezu",
        38: "Basarios",
        39: "Ruby Basarios",
        40: "Gravios",
        41: "Black Gravios",
        42: "Deviljho",
        43: "Savage Deviljho",
        44: "Brachydios",
        45: "Golden Rajang",
        46: "Dah'ren Mohran",
        47: "Lagombi",
        48: "Zinogre",
        49: "Stygian Zinogre",
        50: "Gargwa",
        51: "Rhenoplos",
        52: "Aptonoth",
        53: "Popo",
        54: "Slagtoth",
        55: "Slagtoth (Red)",
        56: "Jaggi",
        57: "Jaggia",
        58: "Velociprey",
        59: "Genprey",
        60: "Ioprey",
        61: "Remobra",
        62: "Delex",
        63: "Conga",
        64: "Kelbi",
        65: "Felyne",
        66: "Melynx",
        67: "Altaroth",
        68: "Bnahabra (Blue wings)",
        69: "Bnahabra (Yellow wings)",
        70: "Bnahabra (Green wings)",
        71: "Bnahabra (Red wings)",
        72: "Zamite",
        73: "Konchu (Yellow)",
        74: "Konchu (Green)",
        75: "Konchu (Blue)",
        76: "Konchu (Red)",
        77: "Black Fatalis",
        78: "Crimson Fatalis",
        79: "White Fatalis",
        80: "Molten Tigrex",
        81: "Rock (Large, light grey w/ green spots)",
        82: "Rusted Kushala Daora",
        83: "Dalamadur (Tail)",
        84: "Rock (Large, dark grey w/ dirty spots)",
        85: "Rock (Large, almost black)",
        86: "Rock (Large, icy)",
        87: "Rock (Large, icy ver 2)",
        88: "Seregios",
        89: "Gogmazios",
        90: "Ash Kecha Wacha",
        91: "Berserk Tetsucabra",
        92: "Tigerstripe Zamtrios",
        93: "Tidal Najarala",
        94: "Desert Seltas",
        95: "Desert Seltas Queen",
        96: "Shrouded Nerscylla",
        97: "Chaotic Gore Magala",
        98: "Raging Brachydios",
        99: "Diablos",
        100: "Black Diablos",
        101: "Monoblos",
        102: "White Monoblos",
        103: "Chameleos",
        104: "Rock (Large, brown)",
        105: "Cephadrome",
        106: "Cephalos",
        107: "Daimyo Hermitaur",
        108: "Plum Daimyo Hermitaur",
        109: "Hermitaur",
        110: "Shah Dalamadur (Head)",
        111: "Shah Dalamadur (Tail)",
        112: "Rajang (Apex)",
        113: "Deviljho (Apex)",
        114: "Zinogre (Apex)",
        115: "Gravios (Apex)",
        116: "Ukanlos",
        117: "Crimson Fatalis (Super)",
        118: "Apceros",
        119: "Diablos (Apex)",
        120: "Tidal Najarala (Apex)",
        121: "Tigrex (Apex)",
        122: "Seregios (Apex)",
        123: "Rock (Large, light grey no spots)"
    }
    return MONSTER_NAMES.get(monsterID, "Unknown")

def getLargeList()-> list:
    
    LargeList = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,
                    20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,
                    36,37,38,39,40,41,42,43,44,45,46,47,48,49,
                    77,78,79,80,82,83,88,89,90,91,92,93,94,95,96,97,
                    98,99,100,101,102,103,105,107,108,110,111,112,113,
                    114,115,116,117,119,120,121,122]
    return LargeList


def getSmallList()-> list:
    SmallList = [50,51,52,53,54,55,56,57,58,59,60,61,62,
                63,64,65,66,67,68,69,70,71,72,73,74,75,
                76,81,84,85,86,87,104,106,109,118,123]
    return SmallList

def uniqueMonstersList():
    return [
            117, # Crimson Fatalis (Super)
            110, # Shah Dalamadur (Head)
            89,  # Gogmazios
            79,  # White Fatalis
            78,  # Crimson Fatalis
            77,  # Black Fatalis
            46,  # Dah'ren Mohran
            24   # Dalamadur (Head)
           ]

def akantorAndUkanlos()->list:
    return [33,116]

def subMapsOf(i: int)->list: 
    subMaps = {
        "Sm1": [1, 2, 3, 4, 5, 6, 7, 8, 9],  # "Ancestral Steppe" / "Estepa ancestral"
        "Sm2": [1, 2, 3, 4, 5, 6, 7, 8, 9],  # "Sunken Hollow" / "Hondonada sumergida"
        "Sm3": [1, 2, 3, 4, 5, 6, 7, 8, 9],  # "Primal Forest" / "Bosque primigenio"
        "Sm4": [1, 2, 3, 4, 5, 6, 7, 9],      # "Frozen Seaway (Zamtrios)" / "Paso helado (Zamtrios)"
        "Sm5": [1, 2, 3, 5, 6, 7, 8],         # "Heaven's Mount" / "Monte cielo"
        "Sm6": [1],                               # "Great Desert (Dah'ren Mohran)" / "Gran desierto (Dah'ren Mohran)"
        "Sm7": [1],                               # "Tower Summit" / "Cima de la torre"
        "Sm8": [1],                               # "Speartip Crag (Dalamadur)" / "Risco de punta de lanza (Dalamadur)"
        "Sm9": [1],                               # "Ingle Isle" / "Isla Ingel"
        "Sm10": [1],                              # "Castle Schrade" / "Castillo Schrade"
        "Sm11": [1],                              # "Arena" / "Arena"
        "Sm12": [1],                              # "Slayground" / "Arena (2 Pisos)"
                                                  # "Everwood" / "Bosque eterno"
        "Sm14": [1],                              # "Great Sea" / "Gran mar"
        "Sm15": [1, 2, 3, 4, 5, 6, 7, 8, 9],  # "Volcanic Hollow" / "Hondonada volcánica"
        "Sm16": [1],                              # "Sanctuary (Shagaru Magala)" / "Santuario (Shagaru Magala)"
        "Sm17": [1, 2, 3, 4, 5, 7, 10], # "Dunes (Day)" / "Dunas (Día)"
        "Sm18": [1, 2, 3, 4, 5, 7, 10], # "Dunes (Night)" / "Dunas (Noche)"
        "Sm19": [2, 3],                            # "Battlequarters" / "Caserna"
        "Sm20": [1],                               # "Polar Field (Ukanlos)" / "Campo polar (Ukanlos)"
        "Sm21": [1]                                # "Great Sea (Storm)" / "Gran mar (Tormenta)"
    }
    key = f"Sm{i}"
    return subMaps.get(key,None)

def getArenaMapsList()->list:
    aList=[6,7,8,9,10,11,12,13,14,16,19,13,20,21]
    return aList 

def getNoMusicalMapsList()->list:
    nmList=[6,9,14,16,19,20,21]
    return nmList 

def getMusicalMonstersList()->list:
    mList= [ 11,12,13,14,15,16,19,24,25,28,29,30,31,32,33,34,35,36,37,42,43,44,45,46,47,48,49,77,78,79,80,82,83,88,89,97,98,103,110,111,112,113,114,116,117,121,122]
    return mList

def getListOfCoords(zone :int, area: int)->list:
    mylist = [
    [[91.0, 976.0], [45.5, -579.0], [34.5, 533.0], [477.0, 488.5], [-79.5, -862.5], [159.0, -11.5], [352.0, 147.5], [840.0, -646.5], [238.5, 238.5], [-760.5, 885.5], [-102.5, -681.0]],
    [[56.5, 142.0], [-749.0, -771.5], [-397.0, -193.0], [-68.0, 2088.5], [-91.0, -1350.5], [1316.5, 1509.5], [704.0, -249.5], [-22.5, -431.5], [1373.5, -851.5], [-85.0, -896.5], [-431.5, -1169.5]],
    [[-147.5, -147.5], [1520.5, -1895.5], [0.0, -942.0], [-420.0, 794.5], [-726.5, 817.0], [-159.0, 272.0], [726.5, 340.5], [692.5, 0.0], [283.5, -1532.5], [-23.0, -158.5]],
    [[193.0, -45.5], [-862.5, -2553.5], [863.0, 647.0], [397.5, 2406.0], [908.0, -1010.0], [-499.5, -45.0], [-1112.0, -1260.0], [1089.5, 715.0], [1135.0, -2077.0], [760.5, 1759.0]],
    [[-306.5, 318.0], [-386.0, 2281.0], [-874.0, 159.0], [1180.5, -3042.0], [442.5, 125.0], [-159.0, -408.5], [-102.5, -454.0], [113.5, 193.0], [-45.5, 102.0]],
    [[0.0,0.0]],
    [[0.0,0.0]],
    [[-465.5, 3257.5]],
    [[-68.0, 601.5]],
    [[0.0,0.0]],
    [[147.5, 11.5]],
    [[147.5, 11.5]],
    [[0.0,0.0]],
    [[0.0,0.0]],
    [[-749.0, -771.5], [874.0, -193.0], [-68.0, 2088.5], [-91.0, -1350.5], [1316.5, 1509.5], [704.0, -249.5], [-22.5, -431.5], [1566.5, -800.0], [874.0, -976.0], [-431.5, -1169.5]],
    [[-34.0, -215.5]],
    [[1418.5, -352.0], [-68.0, 1135.0], [-181.5, 56.5], [1146.0, -511.0], [-193.0, 340.5], [318.0, -79.5], [544.5, 374.5], [431.0, -182.0], [1078.5, 0.0], [170.0, -170.5], [283.5, -22.5]],
    [[1418.5, -352.0], [-68.0, 1135.0], [-181.5, 90.5], [1146.0, -511.0], [-193.0, 340.5], [318.0, -79.5], [544.5, 374.5], [431.0, -182.0], [1078.5, 0.0], [170.0, -170.5], [283.5, -22.5]],
    [[-840.0, -2383.5], [-828.5, 363.0]],
    [[-1112.5, -1975.0]],
    [[0.0,0.0]]
]
    
    Arealist= mylist[zone-1]
    newAreaIndex = subMapsOf(zone).index(area)
    returnedList=Arealist[newAreaIndex]
    return returnedList

def subMapsOfSpecials(i: int)->int: 
    subMaps = {
        "Sm1": 3,   # "Ancestral Steppe" / "Estepa ancestral"
        "Sm2": 8,   # "Sunken Hollow" / "Hondonada sumergida"
        "Sm3": 3,   # "Primal Forest" / "Bosque primigenio"
        "Sm4": 1,   # "Frozen Seaway (Zamtrios)" / "Paso helado (Zamtrios)"
        "Sm5": 3,   # "Heaven's Mount" / "Monte cielo"
        "Sm6": 1,   # "Great Desert (Dah'ren Mohran)" / "Gran desierto (Dah'ren Mohran)"
        "Sm7": 1,   # "Tower Summit" / "Cima de la torre"
        "Sm8": 1,   # "Speartip Crag (Dalamadur)" / "Risco de punta de lanza (Dalamadur)"
        "Sm9": 1,   # "Ingle Isle" / "Isla Ingel"
        "Sm10":1,   # "Castle Schrade" / "Castillo Schrade"
        "Sm11":1,   # "Arena" / "Arena"
        "Sm12":1,   # "Slayground" / "Arena (2 Pisos)"
        "Sm13":1,   # "Everwood" / "Bosque eterno"
        "Sm14":1,   # "Great Sea" / "Gran mar"
        "Sm15": 8,  # "Volcanic Hollow" / "Hondonada volcánica"
        "Sm16": 1,  # "Sanctuary (Shagaru Magala)" / "Santuario (Shagaru Magala)"
        "Sm17": 7,  # "Dunes (Day)" / "Dunas (Día)"
        "Sm18": 7,  # "Dunes (Night)" / "Dunas (Noche)"
        "Sm19": 3,  # "Battlequarters" / "Caserna"
        "Sm20": 1,  # "Polar Field (Ukanlos)" / "Campo polar (Ukanlos)"
        "Sm21": 1,  # "Great Sea (Storm)" / "Gran mar (Tormenta)"
    }
    key = f"Sm{i}"
    return subMaps.get(key,None)

def tierChancesOfRank(rank:int)->list:
    chances=[
        [1,0,0,0,0,0,0,0], #Rank 0??? Debug
        [2,3,5,10,15,20,25,20], #Rank 1
        [2, 3, 5, 10, 25, 20, 20, 15], #Rank 2
        [3, 4, 7, 20, 26, 20, 10, 10],#Rank 3
        [5, 7, 10, 23, 25, 15, 10, 5], #Rank 4
        [5, 10, 15, 25, 20, 10, 10, 5], #Rank 5
        [7, 15, 20, 25, 15, 10, 5, 3], #Rank 6
        [15, 20, 25, 20, 10, 5, 3, 2], # Rank 7: Finale
        [15, 20, 25, 20, 10, 5, 3, 2],
        [15, 20, 25, 20, 10, 5, 3, 2],
        [15, 20, 25, 20, 10, 5, 3, 2],
    ]
    #return chances[rank]
    return chances[0] #Tests

def monsterListFromTier(tier):
    tiers = [
        [25],                                               # Tier 0: (Seltas) (Error)
        [1, 7, 13, 14, 15, 16, 17, 20, 21, 25, 47, 107],   # Tier 1: (Rathian, Yian Kut-Ku, Gendrome, Iodrome, Great Jaggi, Velocidrome, Congalala, Kecha Wacha, Tetsucabra, Seltas, Lagombi, Daimyo Hermitaur)
        [2, 8, 9, 22, 23, 27, 36, 38, 94, 105],             # Tier 2: (Rathalos, Blue Yian Kut-Ku, Gypceros, Zamtrios, Najarala, Nerscylla, Khezu, Basarios, Desert Seltas, Cephadrome)
        [11, 18, 26, 40, 91, 92, 99, 101, 108],             # Tier 3: (Tigrex, Emerald Congalala, Seltas Queen, Gravios, Berserk Tetsucabra, Tigerstripe Zamtrios, Diablos, Monoblos, Plum Daimyo Hermitaur)
        [4, 10, 30, 37, 39, 44, 95, 96, 102, 90, 28],       # Tier 4: (Azure Rathalos, Purple Gypceros, Yian Garuga, Red Khezu, Ruby Basarios, Brachydios, Desert Seltas Queen, Shrouded Nerscylla, White Monoblos, Ash Kecha Wacha, Gore Magala)
        [3, 12, 29, 41, 42, 88, 93, 97, 100],               # Tier 5: (Pink Rathian, Brute Tigrex, Shagaru Magala, Black Gravios, Deviljho, Seregios, Tidal Najarala, Chaotic Gore Magala, Black Diablos)
        [5, 6, 19, 31, 32, 34, 49, 103],                    # Tier 6: (Gold Rathian, Silver Rathalos, Rajang, Kushala Daora, Teostra, Kirin, Stygian Zinogre, Chameleos)
        [33, 35, 43, 45, 82, 98,119,114,115,121,122],       # Tier 7: (Akantor, Oroshi Kirin, Savage Deviljho, Golden Rajang, Rusted Kushala Daora, Raging Brachydios, Some Apex)
        [24, 46, 77, 78, 79, 80, 89, 110,112,113,117],                  # Tier 8: (Dalamadur (Head), Dah'ren Mohran, Black Fatalis, Crimson Fatalis, White Fatalis, Molten Tigrex, Gogmazios, Shah Dalamadur (Head), Hard Apex)
    ]
    return tiers[tier]

def isLarge(i:int)-> bool:
    return i in getLargeList()



    