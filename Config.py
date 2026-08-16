# -*- coding: utf-8 -*-
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(SCRIPT_DIR, "gacha_save.json")
BACKUP_FILE = os.path.join(SCRIPT_DIR, "gacha_save.json.bak")
SAVE_SCHEMA_VERSION = 9

RANK_PRIORITY = {"S": 3, "A": 2, "B": 1}
RANK_UPGRADES = {"B": "A", "A": "S"}

# Gacha Rates & Costs
COST_METALS_SINGLE = 100
COST_METALS_TEN = 1000

PITY_S_THRESHOLD = 50
PITY_A_THRESHOLD = 10