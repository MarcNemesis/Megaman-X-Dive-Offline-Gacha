# -*- coding: utf-8 -*-
from Config import RANK_UPGRADES

ARMOR_TIERS = [
    {"level": 10, "bracket": "Common", "chapter": 1, "cost": 10, "currency": "Bolts"},
    {"level": 20, "bracket": "Lightweight", "chapter": 2, "cost": 10, "currency": "Bolts"},
    {"level": 30, "bracket": "Processed", "chapter": 3, "cost": 10, "currency": "Bolts"},
    {"level": 40, "bracket": "Impact-Resistance", "chapter": 4, "cost": 10, "currency": "Bolts"},
    {"level": 50, "bracket": "Precision", "chapter": 5, "cost": 10, "currency": "A-Bolts"},
    {"level": 60, "bracket": "Reinforced", "chapter": 6, "cost": 10, "currency": "A-Bolts"},
    {"level": 70, "bracket": "Advanced", "chapter": 7, "cost": 30, "currency": "A-Bolts"},
    {"level": 80, "bracket": "Assault", "chapter": 8, "cost": 30, "currency": "A-Bolts"},
    {"level": 90, "bracket": "Berserker", "chapter": 9, "cost": 30, "currency": "S-Bolts"},
    {"level": 100, "bracket": "Retribution", "chapter": 10, "cost": 30, "currency": "S-Bolts"},
    {"level": 110, "bracket": "Exquisite", "chapter": 11, "cost": 30, "currency": "S-Bolts"},
    {"level": 120, "bracket": "Fearless", "chapter": 12, "cost": 30, "currency": "S-Bolts"},
    {"level": 130, "bracket": "Faith", "chapter": 13, "cost": 50, "currency": "S-Bolts"},
    {"level": 140, "bracket": "Tenacity", "chapter": 14, "cost": 50, "currency": "S-Bolts"},
    {"level": 150, "bracket": "Absolute", "chapter": 15, "cost": 50, "currency": "S-Bolts"},
    {"level": 160, "bracket": "Infinity", "chapter": 16, "cost": 50, "currency": "S-Bolts"},
    {"level": 170, "bracket": "Eternal", "chapter": 17, "cost": 50, "currency": "S-Bolts"},
    {"level": 180, "bracket": "Apocalypse", "chapter": 18, "cost": 50, "currency": "S-Bolts"},
    {"level": 190, "bracket": "Genesis", "chapter": 18, "cost": 50, "currency": "S-Bolts"},
    {"level": 200, "bracket": "Mythos", "chapter": 18, "cost": 50, "currency": "S-Bolts"},
]

ARMOR_PARTS = [
    ("Helmet", "Head Part"),
    ("Armor", "Chestplate"),
    ("Arm", "Buster Part"),
    ("Belt", "Waist Part"),
    ("Boots", "Foot Part"),
    ("Drive", "Processor Component"),
]

DATA_ARMOR = []
for tier in ARMOR_TIERS:
    for part_name, part_desc in ARMOR_PARTS:
        for rank in ["B", "A", "S"]:
            DATA_ARMOR.append({
                "name": f"{tier['bracket']} {part_name} [{rank}]",
                "bracket": tier["bracket"],
                "part": part_name,
                "desc": part_desc,
                "level": tier["level"],
                "chapter": tier["chapter"],
                "cost": tier["cost"],
                "currency": tier["currency"],
                "rank": rank,
            })

ARMOR_LOOKUP = {a["name"]: a for a in DATA_ARMOR}

def get_current_armor_cost(current_chapter=1):
    """Calculates crafting cost based on highest unlocked armor chapter."""
    available_tiers = [t for t in ARMOR_TIERS if t["chapter"] <= max(1, current_chapter)]
    if not available_tiers:
        available_tiers = [ARMOR_TIERS[0]]
    latest = available_tiers[-1]
    return latest["cost"], latest["currency"]

def craft_armor(armor_name, state):
    """Crafts an Armor Gear item only if it has reached S-Tier, 3-Star rank, and required player level."""
    armor_inv = state.get("inventory_armor", {})
    if armor_name not in armor_inv:
        return False, f"'{armor_name}' is not in your inventory."

    armor_data = armor_inv[armor_name]
    if armor_data.get("crafted", False):
        return False, f"'{armor_name}' is already crafted!"

    rank = armor_data.get("rank", "B")
    stars = armor_data.get("stars", 1)

    if rank != "S" or stars < 3:
        return False, f"'{armor_name}' cannot be crafted. Must reach S-Tier and 3-Star rank (Current: {rank}-Tier, {stars}★)."

    # Level requirement validation
    lookup = ARMOR_LOOKUP.get(armor_name, {})
    req_level = lookup.get("level", armor_data.get("item_lv", 1))
    player_level = state.get("player_level", 1)

    if player_level < req_level:
        return False, f"'{armor_name}' requires Player Level {req_level} to craft (Current Level: {player_level})."

    cost = lookup.get("cost", 0)
    currency = lookup.get("currency", "Bolts")
    curr_key = "bolts" if currency == "Bolts" else ("a_bolts" if currency == "A-Bolts" else "s_bolts")

    if state.get(curr_key, 0) < cost:
        return False, f"Not enough {currency}! Required: {cost}, Have: {state.get(curr_key, 0)}."

    state[curr_key] -= cost
    armor_data["crafted"] = True
    armor_data["unlocked"] = True
    return True, f"Successfully crafted '{armor_name}'!"

def process_armor_autoupgrade(inventory_armor, armor_name):
    """Handles duplicate upgrades, rank evolution, and excess dissolution into Bolts."""
    if armor_name not in inventory_armor:
        return armor_name, None, 0

    current_key = armor_name
    dissolved_currency = None
    dissolved_amount = 0

    while True:
        armor_data = inventory_armor.get(current_key)
        if not armor_data:
            break

        changed = False
        curr_rank = armor_data.get("rank", "B")
        curr_stars = armor_data.get("stars", 1)
        curr_count = armor_data.get("count", 0)

        # Step 1: 3 Qty -> +1 Star Rank
        if curr_count >= 3 and (curr_rank in RANK_UPGRADES or curr_stars < 3):
            armor_data["stars"] += 1
            armor_data["count"] -= 3
            changed = True
            continue

        # Step 2: 3 Stars -> Next Rank Grade
        if armor_data.get("stars", 1) >= 3 and curr_rank in RANK_UPGRADES:
            next_rank = RANK_UPGRADES[curr_rank]
            new_name = current_key.replace(f"[{curr_rank}]", f"[{next_rank}]")

            # Reset star rank to 1 upon evolving to next Rank Grade
            armor_data["stars"] = 1
            armor_data["rank"] = next_rank

            if current_key != new_name:
                old_data = inventory_armor.pop(current_key)

                if new_name in inventory_armor:
                    target = inventory_armor[new_name]
                    target["count"] += old_data.get("count", 0)
                    target["stars"] = max(target.get("stars", 1), old_data.get("stars", 1))
                    target["unlocked"] = target.get("unlocked", True) or old_data.get("unlocked", True)
                else:
                    old_data["name"] = new_name
                    if new_name in ARMOR_LOOKUP:
                        old_data["level"] = ARMOR_LOOKUP[new_name]["level"]
                    inventory_armor[new_name] = old_data

                current_key = new_name

            changed = True
            continue

        # Step 3: Only dissolve if at max stars/rank and duplicates remain (count > 0)
        maxed_rank = curr_rank not in RANK_UPGRADES
        maxed_stars = curr_stars >= 3
        
        if (maxed_rank and maxed_stars) and curr_count > 0:
            excess_qty = curr_count
            lookup_info = ARMOR_LOOKUP.get(current_key, {})
            currency_type = lookup_info.get("currency", "Bolts")

            dissolve_gain = excess_qty * lookup_info.get("cost", 10)
            armor_data["count"] = 0
            dissolved_currency = currency_type
            dissolved_amount += dissolve_gain
            changed = True
            continue

        if not changed:
            break

    return current_key, dissolved_currency, dissolved_amount

def clean_all_existing_duplicates(state):
    """Processes all existing duplicate armor in inventory and credits the resulting bolts."""
    inventory_armor = state.get("inventory_armor", {})
    keys = list(inventory_armor.keys())
    
    for key in keys:
        if key in inventory_armor:
            _, currency, amount = process_armor_autoupgrade(inventory_armor, key)
            if currency and amount > 0:
                if currency == "Bolts":
                    state["bolts"] = state.get("bolts", 0) + amount
                elif currency == "A-Bolts":
                    state["a_bolts"] = state.get("a_bolts", 0) + amount
                elif currency == "S-Bolts":
                    state["s_bolts"] = state.get("s_bolts", 0) + amount