import os

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

def subMapsOf(i: int)->list: 
    subMaps = {
        "Sm1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # "Ancestral Steppe" / "Estepa ancestral"
        "Sm2": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # "Sunken Hollow" / "Hondonada sumergida"
        "Sm3": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # "Primal Forest" / "Bosque primigenio"
        "Sm4": [1, 2, 3, 4, 5, 6, 7, 8, 9],      # "Frozen Seaway (Zamtrios)" / "Paso helado (Zamtrios)"
        "Sm5": [1, 2, 3, 4, 5, 6, 7, 8],         # "Heaven's Mount" / "Monte cielo"
        "Sm6": [1],                               # "Great Desert (Dah'ren Mohran)" / "Gran desierto (Dah'ren Mohran)"
        "Sm7": [1],                               # "Tower Summit" / "Cima de la torre"
        "Sm8": [1],                               # "Speartip Crag (Dalamadur)" / "Risco de punta de lanza (Dalamadur)"
        "Sm9": [1],                               # "Ingle Isle" / "Isla Ingel"
        "Sm10": [1],                              # "Castle Schrade" / "Castillo Schrade"
        "Sm11": [1],                              # "Arena" / "Arena"
        "Sm12": [1],                              # "Slayground" / "Arena (2 Pisos)"
        "Sm13": [1],                              # "Everwood" / "Bosque eterno"
        "Sm14": [1],                              # "Great Sea" / "Gran mar"
        "Sm15": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], # "Volcanic Hollow" / "Hondonada volcánica"
        "Sm16": [1],                              # "Sanctuary (Shagaru Magala)" / "Santuario (Shagaru Magala)"
        "Sm17": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], # "Dunes (Day)" / "Dunas (Día)"
        "Sm18": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], # "Dunes (Night)" / "Dunas (Noche)"
        "Sm19": [2, 3],                        # "Battlequarters" / "Caserna"
        "Sm20": [1],                               # "Polar Field (Ukanlos)" / "Campo polar (Ukanlos)"
        "Sm21": [1]                                # "Great Sea (Storm)" / "Gran mar (Tormenta)"
    }
    key = f"Sm{i}"
    return subMaps.get(key,None)


def subMapsOfSpecials(i: int)->int: 
    subMaps = {
        "Sm1": 3,  # "Ancestral Steppe" / "Estepa ancestral"
        "Sm2": 8,  # "Sunken Hollow" / "Hondonada sumergida"
        "Sm3": 3,  # "Primal Forest" / "Bosque primigenio"
        "Sm4": 1,      # "Frozen Seaway (Zamtrios)" / "Paso helado (Zamtrios)"
        "Sm5": 3,         # "Heaven's Mount" / "Monte cielo"
        "Sm6": 1,                              # "Great Desert (Dah'ren Mohran)" / "Gran desierto (Dah'ren Mohran)"
        "Sm7": 1,                              # "Tower Summit" / "Cima de la torre"
        "Sm8": 1,                              # "Speartip Crag (Dalamadur)" / "Risco de punta de lanza (Dalamadur)"
        "Sm9": 1,                              # "Ingle Isle" / "Isla Ingel"
        "Sm10":1,                              # "Castle Schrade" / "Castillo Schrade"
        "Sm11":1,                              # "Arena" / "Arena"
        "Sm12":1,                              # "Slayground" / "Arena (2 Pisos)"
        "Sm13":1,                              # "Everwood" / "Bosque eterno"
        "Sm14":1,                              # "Great Sea" / "Gran mar"
        "Sm15": 8, # "Volcanic Hollow" / "Hondonada volcánica"
        "Sm16": 1,                              # "Sanctuary (Shagaru Magala)" / "Santuario (Shagaru Magala)"
        "Sm17": 7, # "Dunes (Day)" / "Dunas (Día)"
        "Sm18": 7, # "Dunes (Night)" / "Dunas (Noche)"
        "Sm19": 3,                        # "Battlequarters" / "Caserna"
        "Sm20": 1,                               # "Polar Field (Ukanlos)" / "Campo polar (Ukanlos)"
        "Sm21": 1,                                # "Great Sea (Storm)" / "Gran mar (Tormenta)"
    }
    key = f"Sm{i}"
    return subMaps.get(key,None)



def isLarge(i:int)-> bool:
    return i in getLargeList()



    