# Código que toma un texto con un literal JS (sin comillas en claves),
# lo convierte a un dict Python y devuelve una lista de 20 zonas.
# Cada zona es una lista con tantas subzonas como encuentre, y cada subzona
# es una lista [x_mid, z_mid].
# Si prefieres "y" en vez de "z", al final muestro cómo renombrarlo.

import re, json

def js_text_to_json_text(js_text):
    # quitar comentarios // y /* */
    js_text = re.sub(r'//.*?$|/\*.*?\*/', '', js_text, flags=re.M|re.S)
    # quitar prefijos de asignación como "const zones ="
    js_text = re.sub(r'^\s*(?:const|let|var)\s+[A-Za-z0-9_]+\s*=\s*', '', js_text, flags=re.M)
    # Añadir comillas a claves no citadas (claves simples sin espacios ni símbolos)
    js_text = re.sub(r'([{\[,]\s*)([A-Za-z0-9_]+)\s*:', r'\1"\2":', js_text)
    # eliminar comas finales antes de } o ]
    js_text = re.sub(r',\s*(?=[}\]])', '', js_text)
    # quitar punto y coma final (si hay)
    js_text = js_text.strip().rstrip(';')
    return js_text

def keys_to_ints(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            try:
                newk = int(k)
            except Exception:
                newk = k
            out[newk] = keys_to_ints(v)
        return out
    if isinstance(obj, list):
        return [keys_to_ints(x) for x in obj]
    return obj

def parse_js_object_string(js_text):
    json_like = js_text_to_json_text(js_text)
    data = json.loads(json_like)
    return keys_to_ints(data)

def build_zones_subzones(data, total_zones=20, decimals=2):
    """
    Devuelve una lista de longitud total_zones.
    Cada posición i-1 contiene una lista de subzonas encontradas en la zona i.
    Cada subzona es [x_mid, z_mid] (floats redondeados a `decimals`).
    Si la zona no existe, se devuelve una lista vacía.
    """
    zones = []
    for zone in range(1, total_zones + 1):
        subzonas = data.get(zone, {})
        zone_list = []
        for sub_id, vals in sorted(subzonas.items(), key=lambda x: int(x[0]) if isinstance(x[0], (str,int)) else x[0]):
            # asegurar que las claves esenciales estén presentes
            if all(k in vals for k in ("max_x","min_x","max_z","min_z")):
                x_mid = (vals["max_x"] + vals["min_x"]) / 2.0
                z_mid = (vals["max_z"] + vals["min_z"]) / 2.0
                if decimals is not None:
                    x_mid = round(x_mid, decimals)
                    z_mid = round(z_mid, decimals)
                zone_list.append([x_mid, z_mid])
            else:
                # Si faltan claves, omitimos la subzona
                pass
        zones.append(zone_list)
    return zones

# ----------------------------
# EJEMPLO DE USO con los datos que diste (zonas 19 y 20)
# ----------------------------
js_text = """
{
1: {
        0: {
            max_x: 681,
            min_x: -499,
            max_z: 2338,
            min_z: -386,
            max_x_img: 74,
            min_x_img: 55,
            max_z_img: 93,
            min_z_img: 49
        },
        1: {
            max_x: 3950,
            min_x: -3859,
            max_z: 681,
            min_z: -1839,
            max_x_img: 95,
            min_x_img: 27,
            max_z_img: 75,
            min_z_img: 47
        },
        2: {
            max_x: 2384,
            min_x: -2315,
            max_z: 4131,
            min_z: -3065,
            max_x_img: 85,
            min_x_img: 38,
            max_z_img: 90,
            min_z_img: 27
        },
        3: {
            max_x: 3746,
            min_x: -2792,
            max_z: 3065,
            min_z: -2088,
            max_x_img: 98,
            min_x_img: 39,
            max_z_img: 97,
            min_z_img: 53
        },
        4: {
            max_x: 4131,
            min_x: -4290,
            max_z: 2361,
            min_z: -4086,
            max_x_img: 95,
            min_x_img: 24,
            max_z_img: 90,
            min_z_img: 37
        },
        5: {
            max_x: 2951,
            min_x: -2633,
            max_z: 2406,
            min_z: -2429,
            max_x_img: 110,
            min_x_img: 25,
            max_z_img: 98,
            min_z_img: 28
        },
        6: {
            max_x: 1839,
            min_x: -1135,
            max_z: 2747,
            min_z: -2452,
            max_x_img: 73,
            min_x_img: 44,
            max_z_img: 80,
            min_z_img: 30
        },
        7: {
            max_x: 3791,
            min_x: -2111,
            max_z: 6697,
            min_z: -7990,
            max_x_img: 84,
            min_x_img: 52,
            max_z_img: 111,
            min_z_img: 18
        },
        8: {
            max_x: 3405,
            min_x: -2928,
            max_z: 3178,
            min_z: -2701,
            max_x_img: 92,
            min_x_img: 39,
            max_z_img: 93,
            min_z_img: 38
        },
        9: {
            max_x: 953,
            min_x: -2474,
            max_z: 6061,
            min_z: -4290,
            max_x_img: 74,
            min_x_img: 43,
            max_z_img: 108,
            min_z_img: 20
        },
        10: {
            max_x: 885,
            min_x: -1090,
            max_z: 681,
            min_z: -2043,
            max_x_img: 75,
            min_x_img: 43,
            max_z_img: 80,
            min_z_img: 37
        }
    },
    2: {
        0: {
            max_x: 976,
            min_x: -863,
            max_z: 375,
            min_z: -91,
            max_x_img: 80,
            min_x_img: 34,
            max_z_img: 70,
            min_z_img: 57
        },
        1: {
            max_x: 2815,
            min_x: -4313,
            max_z: 2520,
            min_z: -4063,
            max_x_img: 70,
            min_x_img: 19,
            max_z_img: 83,
            min_z_img: 35
        },
        2: {
            max_x: 409,
            min_x: -1203,
            max_z: 2338,
            min_z: -2724,
            max_x_img: 71,
            min_x_img: 53,
            max_z_img: 89,
            min_z_img: 46
        },
        3: {
            max_x: 2679,
            min_x: -2815,
            max_z: 4177,
            min_z: 0,
            max_x_img: 98,
            min_x_img: 35,
            max_z_img: 109,
            min_z_img: 61
        },
        4: {
            max_x: 1816,
            min_x: -1998,
            max_z: 976,
            min_z: -3677,
            max_x_img: 73,
            min_x_img: 34,
            max_z_img: 90,
            min_z_img: 42
        },
        5: {
            max_x: 2792,
            min_x: -159,
            max_z: 3178,
            min_z: -159,
            max_x_img: 100,
            min_x_img: 63,
            max_z_img: 101,
            min_z_img: 60
        },
        6: {
            max_x: 3587,
            min_x: -2179,
            max_z: 1816,
            min_z: -2315,
            max_x_img: 100,
            min_x_img: 41,
            max_z_img: 77,
            min_z_img: 34
        },
        7: {
            max_x: 3655,
            min_x: -3700,
            max_z: 1725,
            min_z: -2588,
            max_x_img: 89,
            min_x_img: 13,
            max_z_img: 83,
            min_z_img: 37
        },
        8: {
            max_x: 8172,
            min_x: -5425,
            max_z: 976,
            min_z: -2679,
            max_x_img: 116,
            min_x_img: 28,
            max_z_img: 71,
            min_z_img: 47
        },
        9: {
            max_x: 3201,
            min_x: -3371,
            max_z: 2066,
            min_z: -3859,
            max_x_img: 99,
            min_x_img: 27,
            max_z_img: 98,
            min_z_img: 32
        },
        10: {
            max_x: 295,
            min_x: -1158,
            max_z: 45,
            min_z: -2384,
            max_x_img: 64,
            min_x_img: 36,
            max_z_img: 91,
            min_z_img: 44
        }
    },
    3: {
        1: {
            max_x: 3564,
            min_x: -3859,
            max_z: 1430,
            min_z: -1725,
            max_x_img: 88,
            min_x_img: 31,
            max_z_img: 78,
            min_z_img: 53
        },
        2: {
            max_x: 4744,
            min_x: -1703,
            max_z: 1362,
            min_z: -5153,
            max_x_img: 95,
            min_x_img: 41,
            max_z_img: 86,
            min_z_img: 32
        },
        3: {
            max_x: 2043,
            min_x: -2043,
            max_z: 4449,
            min_z: -6333,
            max_x_img: 79,
            min_x_img: 48,
            max_z_img: 107,
            min_z_img: 23
        },
        4: {
            max_x: 2769,
            min_x: -3609,
            max_z: 3519,
            min_z: -1930,
            max_x_img: 92,
            min_x_img: 27,
            max_z_img: 95,
            min_z_img: 39
        },
        5: {
            max_x: 2520,
            min_x: -3973,
            max_z: 4381,
            min_z: -2747,
            max_x_img: 86,
            min_x_img: 23,
            max_z_img: 103,
            min_z_img: 34
        },
        6: {
            max_x: 2111,
            min_x: -2429,
            max_z: 3450,
            min_z: -2906,
            max_x_img: 94,
            min_x_img: 39,
            max_z_img: 106,
            min_z_img: 30
        },
        7: {
            max_x: 4154,
            min_x: -2701,
            max_z: 2429,
            min_z: -1748,
            max_x_img: 101,
            min_x_img: 23,
            max_z_img: 97,
            min_z_img: 49
        },
        8: {
            max_x: 2520,
            min_x: -1135,
            max_z: 1793,
            min_z: -1793,
            max_x_img: 99,
            min_x_img: 56,
            max_z_img: 81,
            min_z_img: 40
        },
        9: {
            max_x: 3473,
            min_x: -2906,
            max_z: 204,
            min_z: -3269,
            max_x_img: 96,
            min_x_img: 22,
            max_z_img: 67,
            min_z_img: 27
        },
        10: {
            max_x: 431,
            min_x: -477,
            max_z: 341,
            min_z: -658,
            max_x_img: 56,
            min_x_img: 43,
            max_z_img: 89,
            min_z_img: 75
        }
    },
    4: {
        0: {
            max_x: 931,
            min_x: -545,
            max_z: 272,
            min_z: -363,
            max_x_img: 64,
            min_x_img: 41,
            max_z_img: 68,
            min_z_img: 58
        },
        1: {
            max_x: 3201,
            min_x: -4926,
            max_z: 795,
            min_z: -5902,
            max_x_img: 88,
            min_x_img: 31,
            max_z_img: 91,
            min_z_img: 44
        },
        2: {
            max_x: 3814,
            min_x: -2088,
            max_z: 3632,
            min_z: -2338,
            max_x_img: 95,
            min_x_img: 46,
            max_z_img: 94,
            min_z_img: 44
        },
        3: {
            max_x: 2679,
            min_x: -1884,
            max_z: 8172,
            min_z: -3360,
            max_x_img: 83,
            min_x_img: 50,
            max_z_img: 111,
            min_z_img: 30
        },
        4: {
            max_x: 4449,
            min_x: -2633,
            max_z: 1680,
            min_z: -3700,
            max_x_img: 107,
            min_x_img: 34,
            max_z_img: 85,
            min_z_img: 29
        },
        5: {
            max_x: 1521,
            min_x: -2520,
            max_z: 636,
            min_z: -726,
            max_x_img: 89,
            min_x_img: 53,
            max_z_img: 65,
            min_z_img: 53
        },
        6: {
            max_x: 2747,
            min_x: -4971,
            max_z: 45,
            min_z: -2565,
            max_x_img: 94,
            min_x_img: 25,
            max_z_img: 64,
            min_z_img: 40
        },
        7: {
            max_x: 3609,
            min_x: -1430,
            max_z: 5017,
            min_z: -3587,
            max_x_img: 90,
            min_x_img: 45,
            max_z_img: 87,
            min_z_img: 9
        },
        8: {
            max_x: 2611,
            min_x: -341,
            max_z: 386,
            min_z: -4540,
            max_x_img: 90,
            min_x_img: 60,
            max_z_img: 92,
            min_z_img: 41
        },
        9: {
            max_x: 2656,
            min_x: -1135,
            max_z: 4540,
            min_z: -1022,
            max_x_img: 82,
            min_x_img: 41,
            max_z_img: 95,
            min_z_img: 34
        }
    },
    5: {
        0: {
            max_x: 295,
            min_x: -908,
            max_z: 795,
            min_z: -159,
            max_x_img: 68,
            min_x_img: 47,
            max_z_img: 79,
            min_z_img: 62
        },
        1: {
            max_x: 1952,
            min_x: -2724,
            max_z: 5266,
            min_z: -704,
            max_x_img: 88,
            min_x_img: 40,
            max_z_img: 107,
            min_z_img: 44
        },
        2: {
            max_x: 1884,
            min_x: -3632,
            max_z: 2792,
            min_z: -2474,
            max_x_img: 86,
            min_x_img: 21,
            max_z_img: 107,
            min_z_img: 46
        },
        3: {
            max_x: 3496,
            min_x: -1135,
            max_z: 1135,
            min_z: -7219,
            max_x_img: 89,
            min_x_img: 50,
            max_z_img: 90,
            min_z_img: 20
        },
        4: {
            max_x: 4086,
            min_x: -3201,
            max_z: 250,
            min_z: 0,
            max_x_img: 105,
            min_x_img: 19,
            max_z_img: 68,
            min_z_img: 64
        },
        5: {
            max_x: 2769,
            min_x: -3087,
            max_z: 1884,
            min_z: -2701,
            max_x_img: 89,
            min_x_img: 24,
            max_z_img: 85,
            min_z_img: 35
        },
        6: {
            max_x: 2088,
            min_x: -2293,
            max_z: 3178,
            min_z: -4086,
            max_x_img: 71,
            min_x_img: 34,
            max_z_img: 96,
            min_z_img: 34
        },
        7: {
            max_x: 2497,
            min_x: -2270,
            max_z: 2429,
            min_z: -2043,
            max_x_img: 86,
            min_x_img: 31,
            max_z_img: 89,
            min_z_img: 36
        },
        8: {
            max_x: 3087,
            min_x: -3178,
            max_z: 1566,
            min_z: -1362,
            max_x_img: 104,
            min_x_img: 23,
            max_z_img: 84,
            min_z_img: 46
        }
    },
    8: {
        1: {
            max_x: 2111,
            min_x: -3042,
            max_z: 7423,
            min_z: -908,
            max_x_img: 86,
            min_x_img: 38,
            max_z_img: 116,
            min_z_img: 36
        }
    },
    9: {
        1: {
            max_x: 6651,
            min_x: -6787,
            max_z: 5266,
            min_z: -4063,
            max_x_img: 107,
            min_x_img: 24,
            max_z_img: 96,
            min_z_img: 37
        }
    },
    11: {
        1: {
            max_x: 3405,
            min_x: -3110,
            max_z: 4926,
            min_z: -4903,
            max_x_img: 97,
            min_x_img: 32,
            max_z_img: 112,
            min_z_img: 16
        }
    },
    12: {
        1: {
            max_x: 3405,
            min_x: -3110,
            max_z: 4926,
            min_z: -4903,
            max_x_img: 97,
            min_x_img: 32,
            max_z_img: 112,
            min_z_img: 16
        }
    },
    15: {
        0: {
            max_x: 976,
            min_x: -863,
            max_z: 375,
            min_z: -91,
            max_x_img: 80,
            min_x_img: 34,
            max_z_img: 70,
            min_z_img: 57
        },
        1: {
            max_x: 2815,
            min_x: -4313,
            max_z: 2520,
            min_z: -4063,
            max_x_img: 70,
            min_x_img: 19,
            max_z_img: 83,
            min_z_img: 35
        },
        2: {
            max_x: 2951,
            min_x: -1203,
            max_z: 2338,
            min_z: -2724,
            max_x_img: 94,
            min_x_img: 51,
            max_z_img: 83,
            min_z_img: 31
        },
        3: {
            max_x: 2679,
            min_x: -2815,
            max_z: 4177,
            min_z: 0,
            max_x_img: 98,
            min_x_img: 35,
            max_z_img: 109,
            min_z_img: 61
        },
        4: {
            max_x: 1816,
            min_x: -1998,
            max_z: 976,
            min_z: -3677,
            max_x_img: 73,
            min_x_img: 34,
            max_z_img: 90,
            min_z_img: 42
        },
        5: {
            max_x: 2792,
            min_x: -159,
            max_z: 3178,
            min_z: -159,
            max_x_img: 100,
            min_x_img: 63,
            max_z_img: 101,
            min_z_img: 60
        },
        6: {
            max_x: 3587,
            min_x: -2179,
            max_z: 1816,
            min_z: -2315,
            max_x_img: 100,
            min_x_img: 41,
            max_z_img: 77,
            min_z_img: 34
        },
        7: {
            max_x: 3655,
            min_x: -3700,
            max_z: 1725,
            min_z: -2588,
            max_x_img: 89,
            min_x_img: 13,
            max_z_img: 83,
            min_z_img: 37
        },
        8: {
            max_x: 8558,
            min_x: -5425,
            max_z: 1067,
            min_z: -2667,
            max_x_img: 118,
            min_x_img: 29,
            max_z_img: 72,
            min_z_img: 47
        },
        9: {
            max_x: 5153,
            min_x: -3405,
            max_z: 1907,
            min_z: -3859,
            max_x_img: 111,
            min_x_img: 22,
            max_z_img: 99,
            min_z_img: 39
        },
        10: {
            max_x: 295,
            min_x: -1158,
            max_z: 45,
            min_z: -2384,
            max_x_img: 64,
            min_x_img: 36,
            max_z_img: 91,
            min_z_img: 44
        }
    },
    16: {
        1: {
            max_x: 3519,
            min_x: -3587,
            max_z: 2497,
            min_z: -2928,
            max_x_img: 109,
            min_x_img: 25,
            max_z_img: 99,
            min_z_img: 33
        }
    },
    17: {
        0: {
            max_x: 1657,
            min_x: -953,
            max_z: 1180,
            min_z: -1430,
            max_x_img: 97,
            min_x_img: 51,
            max_z_img: 82,
            min_z_img: 37
        },
        1: {
            max_x: 3178,
            min_x: -341,
            max_z: 2111,
            min_z: -2815,
            max_x_img: 97,
            min_x_img: 57,
            max_z_img: 97,
            min_z_img: 41
        },
        2: {
            max_x: 3859,
            min_x: -3995,
            max_z: 5471,
            min_z: -3201,
            max_x_img: 83,
            min_x_img: 23,
            max_z_img: 94,
            min_z_img: 27
        },
        3: {
            max_x: 2043,
            min_x: -2406,
            max_z: 2338,
            min_z: -2225,
            max_x_img: 77,
            min_x_img: 30,
            max_z_img: 91,
            min_z_img: 44
        },
        4: {
            max_x: 3677,
            min_x: -1385,
            max_z: 3246,
            min_z: -4268,
            max_x_img: 98,
            min_x_img: 47,
            max_z_img: 100,
            min_z_img: 25
        },
        5: {
            max_x: 2293,
            min_x: -2679,
            max_z: 4313,
            min_z: -3632,
            max_x_img: 87,
            min_x_img: 41,
            max_z_img: 108,
            min_z_img: 36
        },
        6: {
            max_x: 2270,
            min_x: -1634,
            max_z: 1589,
            min_z: -1748,
            max_x_img: 80,
            min_x_img: 29,
            max_z_img: 99,
            min_z_img: 56
        },
        7: {
            max_x: 5743,
            min_x: -4654,
            max_z: 7355,
            min_z: -6606,
            max_x_img: 101,
            min_x_img: 33,
            max_z_img: 106,
            min_z_img: 16
        },
        8: {
            max_x: 2179,
            min_x: -1317,
            max_z: 1407,
            min_z: -1771,
            max_x_img: 80,
            min_x_img: 34,
            max_z_img: 93,
            min_z_img: 53
        },
        9: {
            max_x: 2452,
            min_x: -295,
            max_z: 1362,
            min_z: -1362,
            max_x_img: 77,
            min_x_img: 41,
            max_z_img: 72,
            min_z_img: 37
        },
        10: {
            max_x: 3859,
            min_x: -3519,
            max_z: 3904,
            min_z: -4245,
            max_x_img: 102,
            min_x_img: 26,
            max_z_img: 108,
            min_z_img: 24
        },
        11: {
            max_x: 1407,
            min_x: -840,
            max_z: 999,
            min_z: -1044,
            max_x_img: 83,
            min_x_img: 38,
            max_z_img: 86,
            min_z_img: 44
        }
    },
        18: {
        0: {
            max_x: 1657,
            min_x: -953,
            max_z: 1180,
            min_z: -1430,
            max_x_img: 97,
            min_x_img: 51,
            max_z_img: 82,
            min_z_img: 37
        },
        1: {
            max_x: 3178,
            min_x: -341,
            max_z: 2111,
            min_z: -2815,
            max_x_img: 97,
            min_x_img: 57,
            max_z_img: 97,
            min_z_img: 41
        },
        2: {
            max_x: 3859,
            min_x: -3995,
            max_z: 5471,
            min_z: -3201,
            max_x_img: 83,
            min_x_img: 23,
            max_z_img: 94,
            min_z_img: 27
        },
        3: {
            max_x: 2043,
            min_x: -2406,
            max_z: 2406,
            min_z: -2225,
            max_x_img: 77,
            min_x_img: 30,
            max_z_img: 91,
            min_z_img: 44
        },
        4: {
            max_x: 3677,
            min_x: -1385,
            max_z: 3246,
            min_z: -4268,
            max_x_img: 98,
            min_x_img: 47,
            max_z_img: 100,
            min_z_img: 25
        },
        5: {
            max_x: 2293,
            min_x: -2679,
            max_z: 4313,
            min_z: -3632,
            max_x_img: 87,
            min_x_img: 41,
            max_z_img: 108,
            min_z_img: 36
        },
        6: {
            max_x: 2270,
            min_x: -1634,
            max_z: 1589,
            min_z: -1748,
            max_x_img: 80,
            min_x_img: 29,
            max_z_img: 99,
            min_z_img: 56
        },
        7: {
            max_x: 5743,
            min_x: -4654,
            max_z: 7355,
            min_z: -6606,
            max_x_img: 101,
            min_x_img: 33,
            max_z_img: 106,
            min_z_img: 16
        },
        8: {
            max_x: 2179,
            min_x: -1317,
            max_z: 1407,
            min_z: -1771,
            max_x_img: 80,
            min_x_img: 34,
            max_z_img: 93,
            min_z_img: 53
        },
        9: {
            max_x: 2452,
            min_x: -295,
            max_z: 1362,
            min_z: -1362,
            max_x_img: 77,
            min_x_img: 41,
            max_z_img: 72,
            min_z_img: 37
        },
        10: {
            max_x: 3859,
            min_x: -3519,
            max_z: 3904,
            min_z: -4245,
            max_x_img: 102,
            min_x_img: 26,
            max_z_img: 108,
            min_z_img: 24
        },
        11: {
            max_x: 1407,
            min_x: -840,
            max_z: 999,
            min_z: -1044,
            max_x_img: 83,
            min_x_img: 38,
            max_z_img: 86,
            min_z_img: 44
        }
    },
    19: {
        1: {
            max_x: 2611,
            min_x: -23,
            max_z: 1748,
            min_z: -681,
            max_x_img: 96,
            min_x_img: 63,
            max_z_img: 79,
            min_z_img: 48
        },
        2: {
            max_x: 1385,
            min_x:-3065,
            max_z: 454,
            min_z: -5221,
            max_x_img: 92,
            min_x_img: 40,
            max_z_img: 107,
            min_z_img: 41
        },
        3: {
            max_x: 2838,
            min_x: -4495,
            max_z: 5266,
            min_z: -4540,
            max_x_img: 84,
            min_x_img: 32,
            max_z_img: 101,
            min_z_img: 31
        }
    },
    20: {
        1: {
            max_x: 2542,
            min_x: -4767,
            max_z: 3155,
            min_z: -7105,
            max_x_img: 95,
            min_x_img: 36,
            max_z_img: 105,
            min_z_img: 23
        }
    }
}
"""

# parsear y construir la estructura solicitada
data = parse_js_object_string(js_text)
zones = build_zones_subzones(data, total_zones=20, decimals=2)

# imprimir por pantalla la lista de 20 zonas (cada zona = lista de subzonas)
print("Resultado: lista de 20 zonas. Cada zona es una lista de subzonas [x_mid, z_mid]:\n")
for i, sublist in enumerate(zones, start=1):
    print(f"Zona {i:2d}: {sublist}")
print("\nLista completa (como objeto Python):")
print(zones)

# Si prefieres que las subzonas usen [x, y] en vez de [x, z], puedes transformar así:
zones_xy = [[[x, z] for x,z in zone] for zone in zones]  # mismo orden; nomenclatura 'y' es semántica
