import os
from pathlib import Path

def getQuestFolder():
    # Get the absolute path of the current script
    script_path = os.path.abspath(__file__)
    # Get the directory where the script is located
    base_folder = os.path.dirname(script_path)
    # Build the path to loc/quest
    target_folder = os.path.join(base_folder, "loc", "quest")
    return target_folder

def changeByteAtOffset_For_In(offset: int, new_value: bytes, questFilePath: str):
    """
    Change the byte(s) at a given offset in the file.
    """
    if not os.path.exists(questFilePath):
        raise FileNotFoundError(f"File not found: {questFilePath}")
    size = os.path.getsize(questFilePath)
    if offset < 0 or offset + len(new_value) > size:
        raise ValueError(f"Write outside file bounds: offset=0x{offset:X}, len={len(new_value)}, size=0x{size:X}")
    
    with open(questFilePath, "r+b") as f:   # read+write in binary mode
        f.seek(offset)
        f.write(new_value)
        f.flush()
        os.fsync(f.fileno())
    print(f"[DEBUG] Successfully wrote {new_value.hex().upper()} at offset 0x{offset:X}")

def last_byte_pos(path: str) -> int:
    """Return the index of the last byte in the file (size-1)."""
    size = Path(path).stat().st_size
    if size == 0:
        raise ValueError("file is empty")
    return size - 1

def getSpawnByte(filePath: str) -> int:
    """Given the last-byte index (e.g. 0x177F) return the spawn offset (first column) using -0x90 rule."""
    lastByteIndex = last_byte_pos(filePath)

    base_row = (lastByteIndex // 0x10) * 0x10   # HxD row base (col 00)
    spawn = base_row - 0x90
    if spawn < 0:
        raise ValueError("calculated spawn offset is negative")
    return spawn

def replaceMonsterWith_In(oldMonsterStr: str,newMonsterStr: str, questFileName: str):
    
    questFolder = getQuestFolder()

    questFilePath = os.path.join(questFolder, questFileName)
    if not os.path.exists(questFilePath):
        raise FileNotFoundError(f"File not found: {questFilePath}")
    
    oldMonster = bytes.fromhex(oldMonsterStr)
    newMonster = bytes.fromhex(newMonsterStr)
    print(f"[DEBUG] oldMonster = {oldMonster.hex().upper()}, newMonster = {newMonster.hex().upper()}")


    changeByteAtOffset_For_In(0xD0 , newMonster, questFilePath)
    changeByteAtOffset_For_In(0xE0 , newMonster, questFilePath)
   

    spawnByte= getSpawnByte(questFilePath)

    print(f"[DEBUG] Calculated spawnByte offset = 0x{spawnByte:X}")
    changeByteAtOffset_For_In(spawnByte, newMonster, questFilePath)
    print(f"[INFO] Patched {questFileName} at 0x{spawnByte:X} (and 0xD0, 0xE0) with {newMonsterStr.upper()}")

def replaceZoneWith_In(zoneIDStr: str, questFileName: str):
    questFolder = getQuestFolder()
    questFilePath = os.path.join(questFolder, questFileName)
    if not os.path.exists(questFilePath):
        raise FileNotFoundError(f"File not found: {questFilePath}")
    newZoneID = bytes.fromhex(zoneIDStr)
    changeByteAtOffset_For_In(0xC4, newZoneID,questFilePath)
    
def replaceSubzone_In(subzoneIDStr: str, questFileName: str):
    questFolder = getQuestFolder()
    questFilePath = os.path.join(questFolder, questFileName)
    spawnZoneByte= getSpawnByte(questFilePath) + 0x09
    newZoneID = bytes.fromhex(subzoneIDStr)
    changeByteAtOffset_For_In(spawnZoneByte, newZoneID, questFilePath)


questFolder= getQuestFolder()
if __name__ == "__main__":
    # ensure questFolder exists (keeps your convention)
    questFolder = getQuestFolder()
    print(f"[DEBUG] questFolder = {questFolder}")

    print("Enter quest filename (inside loc/quest):")
    questFileName = input("> ").strip()

    print("Enter new monster hex (e.g. DEADBEEF or DE AD BE EF):")
    newMonsterHex = input("> ").strip().replace(" ", "").replace("0x", "").upper()
    # ensure even-length hex
    if len(newMonsterHex) % 2 == 1:
        newMonsterHex = "0" + newMonsterHex
        print(f"[DEBUG] questFileName = {questFileName}, newMonsterHex = {newMonsterHex}")

    try:
        # we pass the same hex as old and new so length check passes
        replaceMonsterWith_In(newMonsterHex, newMonsterHex, questFileName)
    except Exception as e:
        print("Error:", e)