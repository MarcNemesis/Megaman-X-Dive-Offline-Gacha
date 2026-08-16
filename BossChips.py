# -*- coding: utf-8 -*-
"""
BossChips.py
Contains the complete roster of Equippable Weapon Chips categorized by Color Element.
"""

DATA_BOSS_CHIPS = [
    # --- BLUE CHIPS (8) ---
    {"name": "Asimov", "color": "Blue", "rank": "S", "chapter": 3},
    {"name": "Bit", "color": "Blue", "rank": "S", "chapter": 4},
    {"name": "Chill Penguin", "color": "Blue", "rank": "A", "chapter": 1},
    {"name": "Mad Nautilus", "color": "Blue", "rank": "S", "chapter": 8},
    {"name": "Maverick S-01", "color": "Blue", "rank": "A", "chapter": 2},
    {"name": "Overdrive Ostrich", "color": "Blue", "rank": "A", "chapter": 2},
    {"name": "Raging Gazer", "color": "Blue", "rank": "S", "chapter": 5},
    {"name": "Sting Chameleon", "color": "Blue", "rank": "A", "chapter": 2},

    # --- GREEN CHIPS (9) ---
    {"name": "Chameleon Project", "color": "Green", "rank": "A", "chapter": 3},
    {"name": "Copy X", "color": "Green", "rank": "S", "chapter": 6},
    {"name": "Dr. Psyche", "color": "Green", "rank": "S", "chapter": 7},
    {"name": "Flier", "color": "Green", "rank": "B", "chapter": 1},
    {"name": "Silver Horn", "color": "Green", "rank": "S", "chapter": 5},
    {"name": "Spark Mandrill", "color": "Green", "rank": "A", "chapter": 2},
    {"name": "Spider", "color": "Green", "rank": "A", "chapter": 4},
    {"name": "ViA", "color": "Green", "rank": "S", "chapter": 10},
    {"name": "Vile", "color": "Green", "rank": "A", "chapter": 3},

    # --- YELLOW CHIPS (9) ---
    {"name": "Boomerang Kuwanger", "color": "Yellow", "rank": "A", "chapter": 2},
    {"name": "Droitclair", "color": "Yellow", "rank": "S", "chapter": 9},
    {"name": "Goliath", "color": "Yellow", "rank": "A", "chapter": 4},
    {"name": "Magma Dragoon", "color": "Yellow", "rank": "S", "chapter": 6},
    {"name": "Rex Trick", "color": "Yellow", "rank": "A", "chapter": 3},
    {"name": "RiCO", "color": "Yellow", "rank": "S", "chapter": 10},
    {"name": "Shagujail", "color": "Yellow", "rank": "S", "chapter": 8},
    {"name": "Super Mega Man", "color": "Yellow", "rank": "S", "chapter": 7},
    {"name": "Volnutt", "color": "Yellow", "rank": "A", "chapter": 5},

    # --- RED CHIPS (9) ---
    {"name": "Angepitoyeir", "color": "Red", "rank": "S", "chapter": 9},
    {"name": "BBit", "color": "Red", "rank": "A", "chapter": 3},
    {"name": "Dr Doppler", "color": "Red", "rank": "S", "chapter": 7},
    {"name": "Epsilon", "color": "Red", "rank": "S", "chapter": 8},
    {"name": "Eratoeir", "color": "Red", "rank": "S", "chapter": 9},
    {"name": "Flame Mammoth", "color": "Red", "rank": "A", "chapter": 2},
    {"name": "McQuarrie", "color": "Red", "rank": "A", "chapter": 4},
    {"name": "Sashu", "color": "Red", "rank": "A", "chapter": 5},
    {"name": "Storm Eagle", "color": "Red", "rank": "A", "chapter": 2},

    # --- NON-COLORED / BASIC BOSS CHIPS (3) ---
    {"name": "Maoh the Giant", "color": "None", "rank": "B", "chapter": 1},
    {"name": "Gigantic Mechaniloid CF-0", "color": "None", "rank": "B", "chapter": 1},
    {"name": "Mega Scorpio", "color": "None", "rank": "B", "chapter": 1},
]

# Quick lookup mappings for Execute.py and StageClear.py
BOSS_CHIP_LOOKUP = {c["name"]: c for c in DATA_BOSS_CHIPS}