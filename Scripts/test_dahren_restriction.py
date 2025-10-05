#!/usr/bin/env python3
"""
Test script for Dah'ren Mohran restriction functionality.
This script tests the new functions that prevent multiple Dah'ren Mohran (ID 46) in a quest.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import Randomizer
import VariousLists
import QuestEditor

def test_dahren_restriction():
    """Test the Dah'ren Mohran restriction logic."""
    print("=" * 60)
    print("Testing Dah'ren Mohran Restriction Logic")
    print("=" * 60)
    
    # Test 1: Check tier 8 monsters
    tier8_monsters = VariousLists.monsterListFromTier(8)
    print(f"Tier 8 monsters: {tier8_monsters}")
    print(f"Dah'ren Mohran (46) in tier 8: {46 in tier8_monsters}")
    
    # Test 2: Test hasDahrenMohran function with a sample quest
    quest_folder = Randomizer.getQuestFolder()
    quest_files = [f for f in os.listdir(quest_folder) if f.endswith('.1BBFD18E')][:5]
    
    print(f"\nTesting hasDahrenMohran function on {len(quest_files)} quest files:")
    for quest_file in quest_files:
        full_path = os.path.join(quest_folder, quest_file)
        try:
            has_dahren = Randomizer.hasDahrenMohran(full_path)
            parsed = QuestEditor.parse_mib(full_path)
            monsters = Randomizer.getLargeMonstersIDs(parsed)
            print(f"  {quest_file}: Has Dah'ren Mohran: {has_dahren}, Monsters: {monsters}")
        except Exception as e:
            print(f"  {quest_file}: Error - {e}")
    
    # Test 3: Test selectTier8MonsterSafe function
    print(f"\nTesting selectTier8MonsterSafe function:")
    for quest_file in quest_files[:3]:
        full_path = os.path.join(quest_folder, quest_file)
        try:
            selected_monster = Randomizer.selectTier8MonsterSafe(full_path)
            has_dahren = Randomizer.hasDahrenMohran(full_path)
            print(f"  {quest_file}: Selected tier 8 monster: {selected_monster} ({VariousLists.getMonsterName(selected_monster)})")
            print(f"    Quest has Dah'ren Mohran: {has_dahren}")
            if has_dahren and selected_monster == 46:
                print(f"    WARNING: Selected Dah'ren Mohran despite quest already having one!")
            else:
                print(f"    OK: Restriction working correctly")
        except Exception as e:
            print(f"  {quest_file}: Error - {e}")
    
    print("\n" + "=" * 60)
    print("Dah'ren Mohran restriction test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_dahren_restriction()