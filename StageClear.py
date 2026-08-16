# -*- coding: utf-8 -*-
import random
from BossChips import DATA_BOSS_CHIPS, BOSS_CHIP_LOOKUP

# Pure Cards (non-chip drops)
DATA_CARDS = [
    {"name": "Maverick Hunter Card", "rank": "B", "type": "Card", "chapter": 1},
    {"name": "Vile Card", "rank": "A", "type": "Card", "chapter": 1},
    {"name": "Flame Stagger Card", "rank": "A", "type": "Card", "chapter": 2},
    {"name": "First Armor X Card", "rank": "S", "type": "Card", "chapter": 2},
    {"name": "Command Mission Card", "rank": "A", "type": "Card", "chapter": 3},
    {"name": "Ultimate Armor Card", "rank": "S", "type": "Card", "chapter": 3},
    {"name": "Tron Bonne Card", "rank": "S", "type": "Card", "chapter": 4},
    {"name": "Star Force Card", "rank": "S", "type": "Card", "chapter": 5},
    {"name": "Copy X Card", "rank": "S", "type": "Card", "chapter": 6},
    {"name": "Model ZX Card", "rank": "S", "type": "Card", "chapter": 7},
    {"name": "Iris & Colonel Card", "rank": "S", "type": "Card", "chapter": 8},
    {"name": "Absolute Zero Card", "rank": "S", "type": "Card", "chapter": 8},
    {"name": "Bass.EXE Card", "rank": "S", "type": "Card", "chapter": 12},
    {"name": "ViA Memory Card", "rank": "S", "type": "Card", "chapter": 18},
]

# Combine true Boss Chips (formatted as Chips) with Cards
DATA_CARDS_CHIPS = DATA_CARDS + [
    {
        "name": f"{chip['name']} Chip", 
        "rank": chip["rank"], 
        "type": "Chip", 
        "chapter": chip["chapter"],
        "color": chip["color"]
    }
    for chip in DATA_BOSS_CHIPS
]

CARD_CHIP_LOOKUP = {c["name"]: c for c in DATA_CARDS_CHIPS}

def calculate_stage_rewards(chapter, is_first_time, inventory_chips):
    """Calculates drops and currency yields for clearing a stage."""
    base_e, base_b = 150, 50
    base_sb = 15 if chapter >= 13 else 0
    base_p = 10
    drops = []

    if is_first_time:
        e_gain, b_gain, sb_gain, p_gain = base_e, base_b, base_sb, base_p
        chapter_pool = [c for c in DATA_CARDS_CHIPS if c["chapter"] <= chapter]
        if chapter_pool:
            looted = random.choice(chapter_pool)
            c_name, c_type, c_rank = looted["name"], looted["type"], looted["rank"]

            if c_name in inventory_chips:
                inventory_chips[c_name]["count"] += 1
            else:
                inventory_chips[c_name] = {"rank": c_rank, "type": c_type, "count": 1}
            drops.append(f"★ FIRST CLEAR GUARANTEED DROP: [{c_rank}-Rank] {c_name} ({c_type})")
    else:
        e_gain = int(base_e * 0.25)
        b_gain = int(base_b * 0.25)
        sb_gain = int(base_sb * 0.25)
        p_gain = int(base_p * 0.25)

        if random.random() < 0.20:
            chapter_pool = [c for c in DATA_CARDS_CHIPS if c["chapter"] <= chapter]
            if chapter_pool:
                looted = random.choice(chapter_pool)
                c_name, c_type, c_rank = looted["name"], looted["type"], looted["rank"]

                if c_name in inventory_chips:
                    inventory_chips[c_name]["count"] += 1
                else:
                    inventory_chips[c_name] = {"rank": c_rank, "type": c_type, "count": 1}
                drops.append(f"◇ BONUS DROP: [{c_rank}-Rank] {c_name} ({c_type})")

    return e_gain, b_gain, sb_gain, p_gain, drops