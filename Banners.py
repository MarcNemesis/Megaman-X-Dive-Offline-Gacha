# -*- coding: utf-8 -*-
import random
import ArmorGear as armor
import BossChips as boss_chips
import Cards as cards
import Characters as chars
import Weapons as weaps


def process_character_memory_upgrade(char_name, memories_gained, state):
    """Adds memories to a character without automatically upgrading stars.

    If 5-Star is reached, excess memories dissolve into Character Patches.
    """
    if "inventory_chars" not in state:
        state["inventory_chars"] = {}

    if "memory_patches" not in state:
        state["memory_patches"] = 0

    is_unlocked = True if char_name == "X" else False

    if char_name not in state["inventory_chars"]:
        state["inventory_chars"][char_name] = {
            "stars": 0,
            "memories": 0,
            "unlocked": is_unlocked,
        }

    char_data = state["inventory_chars"][char_name]
    char_data["memories"] += memories_gained

    info = chars.CHAR_LOOKUP.get(char_name, {}) if hasattr(chars, "CHAR_LOOKUP") else {}
    rank = info.get("rank") if isinstance(info, dict) else info
    if not rank:
        rank = "B"

    curr_stars = char_data.get("stars", 0)
    if curr_stars >= 5 and char_data["memories"] > 0:
        patch_multiplier = 40 if rank == "S" else (20 if rank == "A" else 10)
        excess_memories = char_data["memories"]
        state["memory_patches"] += excess_memories * patch_multiplier
        char_data["memories"] = 0


def upgrade_character_star(char_name, state):
    """Attempts to upgrade a character's star rank manually using accumulated memories."""
    if "inventory_chars" not in state or char_name not in state["inventory_chars"]:
        return False, "Character not found in inventory."

    char_data = state["inventory_chars"][char_name]
    curr_stars = char_data.get("stars", 0)

    if curr_stars >= 5:
        return False, f"{char_name} is already at maximum Star Rank (5★)."

    info = chars.CHAR_LOOKUP.get(char_name, {}) if hasattr(chars, "CHAR_LOOKUP") else {}
    rank = info.get("rank") if isinstance(info, dict) else info
    if not rank:
        rank = "B"

    if rank == "S":
        thresholds = {0: 40, 1: 50, 2: 60, 3: 80, 4: 100}
    elif rank == "A":
        thresholds = {0: 30, 1: 40, 2: 50, 3: 60, 4: 80}
    else:
        thresholds = {0: 20, 1: 30, 2: 40, 3: 50, 4: 60}

    needed = thresholds.get(curr_stars, 40)

    if char_data["memories"] < needed:
        return (
            False,
            f"Not enough memories! Need {needed} memories for {curr_stars + 1}★"
            f" (have {char_data['memories']}).",
        )

    char_data["memories"] -= needed
    char_data["stars"] += 1

    if char_data["stars"] >= 5 and char_data["memories"] > 0:
        patch_multiplier = 40 if rank == "S" else (20 if rank == "A" else 10)
        excess_memories = char_data["memories"]
        state["memory_patches"] = (
            state.get("memory_patches", 0) + excess_memories * patch_multiplier
        )
        char_data["memories"] = 0

    return True, f"Successfully upgraded {char_name} to {char_data['stars']}★!"


class GachaEngine:

    def __init__(self):
        self.pull_count = 0
        self.pity_a = 0
        self.pity_s = 0

    def roll_rank(self, force_guarantee=False):
        """Calculates drop rank (S, A, B) with updated rates and pity mechanics."""
        self.pull_count += 1

        if force_guarantee:
            rank = "S" if random.random() < 0.02 else "A"
        else:
            if self.pity_s >= 49 or self.pull_count % 50 == 0:
                rank = "S"
            elif (self.pity_a >= 9 or self.pull_count % 10 == 0) and self.pull_count % 50 != 0:
                rank = "A"
            else:
                roll = random.random()
                if roll < 0.01:
                    rank = "S"
                elif roll < 0.06:
                    rank = "A"
                else:
                    rank = "B"

        if rank == "S":
            self.pity_s = 0
            self.pity_a = 0
        elif rank == "A":
            self.pity_s += 1
            self.pity_a = 0
        else:
            self.pity_s += 1
            self.pity_a += 1

        return rank

    def roll_banner(self, banner_name, chapter, state, force_guarantee=False):
        rank = self.roll_rank(force_guarantee)

        # --- CHARACTER CAPSULE ---
        if banner_name == "Character Capsule":
            pool = []
            if hasattr(chars, "CHAR_LOOKUP"):
                for name, info in chars.CHAR_LOOKUP.items():
                    r = info.get("rank") if isinstance(info, dict) else info
                    c = info.get("chapter", 1) if isinstance(info, dict) else 1
                    if r == rank and c <= chapter:
                        pool.append(name)

            if not pool and hasattr(chars, "CHAR_LOOKUP"):
                for name, info in chars.CHAR_LOOKUP.items():
                    c = info.get("chapter", 1) if isinstance(info, dict) else 1
                    if c <= chapter:
                        pool.append(name)

            if not pool and hasattr(chars, "CHAR_LOOKUP"):
                for name, info in chars.CHAR_LOOKUP.items():
                    r = info.get("rank") if isinstance(info, dict) else info
                    if r == rank:
                        pool.append(name)
                if not pool:
                    pool = list(chars.CHAR_LOOKUP.keys())

            if not pool:
                pool = ["X"]

            item = random.choice(pool)
            memories_gained = 40 if rank == "S" else (20 if rank == "A" else 10)
            process_character_memory_upgrade(item, memories_gained, state)

            return (
                rank,
                f"Character: {item} ([{rank}-Rank] +{memories_gained} Memories)",
            )

        # --- CHAPTER CHARACTER CAPSULE ---
        elif banner_name == "Chapter Character Capsule":
            pool = []
            if hasattr(chars, "CHAR_LOOKUP"):
                for name, info in chars.CHAR_LOOKUP.items():
                    r = info.get("rank") if isinstance(info, dict) else info
                    c = info.get("chapter", 1) if isinstance(info, dict) else 1
                    if r == rank and c == chapter:
                        pool.append(name)

            if not pool and hasattr(chars, "CHAR_LOOKUP"):
                for name, info in chars.CHAR_LOOKUP.items():
                    c = info.get("chapter", 1) if isinstance(info, dict) else 1
                    if c == chapter:
                        pool.append(name)

            if not pool and hasattr(chars, "CHAR_LOOKUP"):
                for name, info in chars.CHAR_LOOKUP.items():
                    r = info.get("rank") if isinstance(info, dict) else info
                    c = info.get("chapter", 1) if isinstance(info, dict) else 1
                    if r == rank and c <= chapter:
                        pool.append(name)

            if not pool and hasattr(chars, "CHAR_LOOKUP"):
                pool = list(chars.CHAR_LOOKUP.keys())

            if not pool:
                pool = ["X"]

            item = random.choice(pool)
            memories_gained = 40 if rank == "S" else (20 if rank == "A" else 10)
            process_character_memory_upgrade(item, memories_gained, state)

            return (
                rank,
                f"Character: {item} ([{rank}-Rank] +{memories_gained} Memories)",
            )

        # --- WEAPON CAPSULE ---
        elif banner_name == "Weapon Capsule":
            pool = []
            if hasattr(weaps, "DATA_WEAPONS"):
                pool = [
                    w["name"]
                    for w in weaps.DATA_WEAPONS
                    if w.get("rank") == rank and w.get("chapter", 1) <= chapter
                ]
            elif hasattr(weaps, "WEAPON_LOOKUP"):
                for name, info in weaps.WEAPON_LOOKUP.items():
                    r = info.get("rank") if isinstance(info, dict) else info
                    c = info.get("chapter", 1) if isinstance(info, dict) else 1
                    if r == rank and c <= chapter:
                        pool.append(name)

            if not pool:
                if hasattr(weaps, "DATA_WEAPONS"):
                    pool = [
                        w["name"]
                        for w in weaps.DATA_WEAPONS
                        if w.get("chapter", 1) <= chapter
                    ]
                elif hasattr(weaps, "WEAPON_LOOKUP"):
                    for name, info in weaps.WEAPON_LOOKUP.items():
                        c = info.get("chapter", 1) if isinstance(info, dict) else 1
                        if c <= chapter:
                            pool.append(name)

            if not pool:
                if hasattr(weaps, "DATA_WEAPONS"):
                    pool = [
                        w["name"] for w in weaps.DATA_WEAPONS if w.get("rank") == rank
                    ]
                elif hasattr(weaps, "WEAPON_LOOKUP"):
                    for name, info in weaps.WEAPON_LOOKUP.items():
                        r = info.get("rank") if isinstance(info, dict) else info
                        if r == rank:
                            pool.append(name)
                if not pool and hasattr(weaps, "WEAPON_LOOKUP"):
                    pool = list(weaps.WEAPON_LOOKUP.keys())

            item = random.choice(pool) if pool else "Buster"
            memories_gained = 40 if rank == "S" else (20 if rank == "A" else 10)

            if "inventory_weapons" not in state:
                state["inventory_weapons"] = {}
            if "weapon_patches" not in state:
                state["weapon_patches"] = 0

            if item not in state["inventory_weapons"]:
                state["inventory_weapons"][item] = {
                    "stars": 0,
                    "memories": memories_gained,
                    "unlocked": False,
                }
            else:
                w_data = state["inventory_weapons"][item]
                if isinstance(w_data, int):
                    w_data = {"stars": 0, "memories": memories_gained, "unlocked": True}
                    state["inventory_weapons"][item] = w_data
                else:
                    w_data["memories"] = w_data.get("memories", 0) + memories_gained

                if w_data.get("stars", 0) >= 5 and w_data["memories"] > 0:
                    patch_mult = 40 if rank == "S" else (20 if rank == "A" else 10)
                    state["weapon_patches"] += w_data["memories"] * patch_mult
                    w_data["memories"] = 0

            return (
                rank,
                f"Weapon: {item} ([{rank}-Rank] +{memories_gained} Memories)",
            )

        # --- CHAPTER WEAPON CAPSULE ---
        elif banner_name == "Chapter Weapon Capsule":
            pool = []
            if hasattr(weaps, "DATA_WEAPONS"):
                pool = [
                    w["name"]
                    for w in weaps.DATA_WEAPONS
                    if w.get("rank") == rank and w.get("chapter", 1) == chapter
                ]
            elif hasattr(weaps, "WEAPON_LOOKUP"):
                for name, info in weaps.WEAPON_LOOKUP.items():
                    r = info.get("rank") if isinstance(info, dict) else info
                    c = info.get("chapter", 1) if isinstance(info, dict) else 1
                    if r == rank and c == chapter:
                        pool.append(name)

            if not pool:
                if hasattr(weaps, "DATA_WEAPONS"):
                    pool = [
                        w["name"]
                        for w in weaps.DATA_WEAPONS
                        if w.get("chapter", 1) == chapter
                    ]
                elif hasattr(weaps, "WEAPON_LOOKUP"):
                    for name, info in weaps.WEAPON_LOOKUP.items():
                        c = info.get("chapter", 1) if isinstance(info, dict) else 1
                        if c == chapter:
                            pool.append(name)

            if not pool:
                if hasattr(weaps, "DATA_WEAPONS"):
                    pool = [
                        w["name"]
                        for w in weaps.DATA_WEAPONS
                        if w.get("rank") == rank and w.get("chapter", 1) <= chapter
                    ]
                elif hasattr(weaps, "WEAPON_LOOKUP"):
                    for name, info in weaps.WEAPON_LOOKUP.items():
                        r = info.get("rank") if isinstance(info, dict) else info
                        c = info.get("chapter", 1) if isinstance(info, dict) else 1
                        if r == rank and c <= chapter:
                            pool.append(name)

            if not pool and hasattr(weaps, "WEAPON_LOOKUP"):
                pool = list(weaps.WEAPON_LOOKUP.keys())

            item = random.choice(pool) if pool else "Buster"
            memories_gained = 40 if rank == "S" else (20 if rank == "A" else 10)

            if "inventory_weapons" not in state:
                state["inventory_weapons"] = {}
            if "weapon_patches" not in state:
                state["weapon_patches"] = 0

            if item not in state["inventory_weapons"]:
                state["inventory_weapons"][item] = {
                    "stars": 0,
                    "memories": memories_gained,
                    "unlocked": False,
                }
            else:
                w_data = state["inventory_weapons"][item]
                if isinstance(w_data, int):
                    w_data = {"stars": 0, "memories": memories_gained, "unlocked": True}
                    state["inventory_weapons"][item] = w_data
                else:
                    w_data["memories"] = w_data.get("memories", 0) + memories_gained

                if w_data.get("stars", 0) >= 5 and w_data["memories"] > 0:
                    patch_mult = 40 if rank == "S" else (20 if rank == "A" else 10)
                    state["weapon_patches"] += w_data["memories"] * patch_mult
                    w_data["memories"] = 0

            return (
                rank,
                f"Weapon: {item} ([{rank}-Rank] +{memories_gained} Memories)",
            )

        # --- ARMOR GEAR FOUNDRY ---
        elif banner_name == "Armor Gear Foundry":
            pool = []
            if hasattr(armor, "ARMOR_LOOKUP"):
                for name, info in armor.ARMOR_LOOKUP.items():
                    r = info.get("rank", "B")
                    c = info.get("chapter", 1)
                    if r == rank and c <= chapter:
                        pool.append(name)

            if not pool and hasattr(armor, "ARMOR_LOOKUP"):
                for name, info in armor.ARMOR_LOOKUP.items():
                    if info.get("chapter", 1) <= chapter:
                        pool.append(name)

            if not pool and hasattr(armor, "ARMOR_LOOKUP"):
                pool = list(armor.ARMOR_LOOKUP.keys())

            if not pool:
                pool = ["Common Helmet [B]"]

            item = random.choice(pool)
            item_rank = (
                armor.ARMOR_LOOKUP.get(item, {}).get("rank", rank)
                if hasattr(armor, "ARMOR_LOOKUP")
                else rank
            )

            if "inventory_armor" not in state:
                state["inventory_armor"] = {}

            if item not in state["inventory_armor"]:
                state["inventory_armor"][item] = {
                    "count": 1,
                    "stars": 1,
                    "rank": item_rank,
                    "unlocked": True,
                }
            else:
                state["inventory_armor"][item]["count"] += 1

            return rank, f"Armor Gear: {item} ([{rank}-Rank] Duplicate Acquired)"

        # --- CHAPTER ARMOR GEAR CAPSULE ---
        elif banner_name == "Chapter Armor Gear Capsule":
            pool = []
            if hasattr(armor, "ARMOR_LOOKUP"):
                for name, info in armor.ARMOR_LOOKUP.items():
                    r = info.get("rank", "B")
                    c = info.get("chapter", 1)
                    if r == rank and c == chapter:
                        pool.append(name)

            if not pool and hasattr(armor, "ARMOR_LOOKUP"):
                for name, info in armor.ARMOR_LOOKUP.items():
                    if info.get("chapter", 1) == chapter:
                        pool.append(name)

            if not pool and hasattr(armor, "ARMOR_LOOKUP"):
                for name, info in armor.ARMOR_LOOKUP.items():
                    r = info.get("rank", "B")
                    c = info.get("chapter", 1)
                    if r == rank and c <= chapter:
                        pool.append(name)

            if not pool and hasattr(armor, "ARMOR_LOOKUP"):
                for name, info in armor.ARMOR_LOOKUP.items():
                    if info.get("chapter", 1) <= chapter:
                        pool.append(name)

            if not pool and hasattr(armor, "ARMOR_LOOKUP"):
                pool = list(armor.ARMOR_LOOKUP.keys())

            if not pool:
                pool = ["Common Helmet [B]"]

            item = random.choice(pool)
            item_rank = (
                armor.ARMOR_LOOKUP.get(item, {}).get("rank", rank)
                if hasattr(armor, "ARMOR_LOOKUP")
                else rank
            )

            if "inventory_armor" not in state:
                state["inventory_armor"] = {}

            if item not in state["inventory_armor"]:
                state["inventory_armor"][item] = {
                    "count": 1,
                    "stars": 1,
                    "rank": item_rank,
                    "unlocked": True,
                }
            else:
                state["inventory_armor"][item]["count"] += 1

            return rank, f"Armor Gear: {item} ([{rank}-Rank] Duplicate Acquired)"

        # --- BOSS CHIP CAPSULE ---
        elif banner_name == "Boss Chip Capsule":
            pool = []
            if hasattr(boss_chips, "BOSS_CHIP_LOOKUP"):
                for name, info in boss_chips.BOSS_CHIP_LOOKUP.items():
                    r = info.get("rank", "B")
                    c = info.get("chapter", 1)
                    if r == rank and c <= chapter:
                        pool.append(name)

            if not pool and hasattr(boss_chips, "BOSS_CHIP_LOOKUP"):
                for name, info in boss_chips.BOSS_CHIP_LOOKUP.items():
                    if info.get("chapter", 1) <= chapter:
                        pool.append(name)

            if not pool and hasattr(boss_chips, "BOSS_CHIP_LOOKUP"):
                pool = list(boss_chips.BOSS_CHIP_LOOKUP.keys())

            if not pool:
                pool = ["Sigma"]

            item = random.choice(pool)
            chip_key = f"{item} Chip" if not item.endswith(" Chip") else item
            if "inventory_chips" not in state:
                state["inventory_chips"] = {}

            if chip_key not in state["inventory_chips"]:
                state["inventory_chips"][chip_key] = {
                    "count": 1,
                    "rank": rank,
                    "type": "Boss Chip",
                    "unlocked": True,
                }
            else:
                if isinstance(state["inventory_chips"][chip_key], dict):
                    state["inventory_chips"][chip_key]["count"] += 1
                else:
                    state["inventory_chips"][chip_key] = {
                        "count": int(state["inventory_chips"][chip_key]) + 1,
                        "rank": rank,
                        "type": "Boss Chip",
                        "unlocked": True,
                    }

            return rank, f"Boss Chip: {chip_key} ([{rank}-Rank])"

        # --- CHAPTER BOSS CHIP CAPSULE ---
        elif banner_name == "Chapter Boss Chip Capsule":
            pool = []
            if hasattr(boss_chips, "BOSS_CHIP_LOOKUP"):
                for name, info in boss_chips.BOSS_CHIP_LOOKUP.items():
                    r = info.get("rank", "B")
                    c = info.get("chapter", 1)
                    if r == rank and c == chapter:
                        pool.append(name)

            if not pool and hasattr(boss_chips, "BOSS_CHIP_LOOKUP"):
                for name, info in boss_chips.BOSS_CHIP_LOOKUP.items():
                    if info.get("chapter", 1) == chapter:
                        pool.append(name)

            if not pool and hasattr(boss_chips, "BOSS_CHIP_LOOKUP"):
                for name, info in boss_chips.BOSS_CHIP_LOOKUP.items():
                    r = info.get("rank", "B")
                    c = info.get("chapter", 1)
                    if r == rank and c <= chapter:
                        pool.append(name)

            if not pool and hasattr(boss_chips, "BOSS_CHIP_LOOKUP"):
                pool = list(boss_chips.BOSS_CHIP_LOOKUP.keys())

            if not pool:
                pool = ["Sigma"]

            item = random.choice(pool)
            chip_key = f"{item} Chip" if not item.endswith(" Chip") else item
            if "inventory_chips" not in state:
                state["inventory_chips"] = {}

            if chip_key not in state["inventory_chips"]:
                state["inventory_chips"][chip_key] = {
                    "count": 1,
                    "rank": rank,
                    "type": "Boss Chip",
                    "unlocked": True,
                }
            else:
                if isinstance(state["inventory_chips"][chip_key], dict):
                    state["inventory_chips"][chip_key]["count"] += 1
                else:
                    state["inventory_chips"][chip_key] = {
                        "count": int(state["inventory_chips"][chip_key]) + 1,
                        "rank": rank,
                        "type": "Boss Chip",
                        "unlocked": True,
                    }

            return rank, f"Boss Chip: {chip_key} ([{rank}-Rank])"

        # --- UNIQUE CARD CAPSULE ---
        elif banner_name in ["Unique Card Capsule", "Card Capsule"]:
            pool = []
            if hasattr(cards, "CARD_LOOKUP"):
                for name, info in cards.CARD_LOOKUP.items():
                    r = info.get("rank", "B") if isinstance(info, dict) else info
                    c = info.get("chapter", 1) if isinstance(info, dict) else 1
                    if r == rank and c <= chapter:
                        pool.append(name)

            if not pool and hasattr(cards, "CARD_LOOKUP"):
                for name, info in cards.CARD_LOOKUP.items():
                    c = info.get("chapter", 1) if isinstance(info, dict) else 1
                    if c <= chapter:
                        pool.append(name)

            if not pool and hasattr(cards, "CARD_LOOKUP"):
                pool = list(cards.CARD_LOOKUP.keys())

            if not pool:
                pool = ["Refleczer"]

            item = random.choice(pool)
            if "inventory_cards" not in state:
                state["inventory_cards"] = {}

            if item not in state["inventory_cards"]:
                state["inventory_cards"][item] = {
                    "count": 1,
                    "stars": 1,
                    "rank": rank,
                    "unlocked": True,
                }
            else:
                state["inventory_cards"][item]["count"] += 1

            return rank, f"Card: {item} ([{rank}-Rank])"

        # --- CHAPTER CARD CAPSULE ---
        elif banner_name == "Chapter Card Capsule":
            pool = []
            if hasattr(cards, "CARD_LOOKUP"):
                for name, info in cards.CARD_LOOKUP.items():
                    r = info.get("rank", "B") if isinstance(info, dict) else info
                    c = info.get("chapter", 1) if isinstance(info, dict) else 1
                    if r == rank and c == chapter:
                        pool.append(name)

            if not pool and hasattr(cards, "CARD_LOOKUP"):
                for name, info in cards.CARD_LOOKUP.items():
                    c = info.get("chapter", 1) if isinstance(info, dict) else 1
                    if c == chapter:
                        pool.append(name)

            if not pool and hasattr(cards, "CARD_LOOKUP"):
                for name, info in cards.CARD_LOOKUP.items():
                    r = info.get("rank", "B") if isinstance(info, dict) else info
                    c = info.get("chapter", 1) if isinstance(info, dict) else 1
                    if r == rank and c <= chapter:
                        pool.append(name)

            if not pool and hasattr(cards, "CARD_LOOKUP"):
                pool = list(cards.CARD_LOOKUP.keys())

            if not pool:
                pool = ["Refleczer"]

            item = random.choice(pool)
            if "inventory_cards" not in state:
                state["inventory_cards"] = {}

            if item not in state["inventory_cards"]:
                state["inventory_cards"][item] = {
                    "count": 1,
                    "stars": 1,
                    "rank": rank,
                    "unlocked": True,
                }
            else:
                state["inventory_cards"][item]["count"] += 1

            return rank, f"Card: {item} ([{rank}-Rank])"

        # --- MOBILE MASTER CAPSULE (ELEMENT) ---
        elif banner_name == "Mobile Master Capsule (Element)":
            sub_banners = [
                "Character Capsule",
                "Weapon Capsule",
                "Armor Gear Foundry",
                "Boss Chip Capsule",
                "Unique Card Capsule",
            ]
            chosen = random.choice(sub_banners)
            return self.roll_banner(chosen, chapter, state, force_guarantee)

        # --- CHAPTER PROGRESS CAPSULE ---
        elif banner_name == "Chapter Progress Capsule":
            sub_banners = [
                "Chapter Character Capsule",
                "Chapter Weapon Capsule",
                "Chapter Armor Gear Capsule",
                "Chapter Boss Chip Capsule",
                "Chapter Card Capsule",
            ]
            chosen = random.choice(sub_banners)
            return self.roll_banner(chosen, chapter, state, force_guarantee)

        # --- FALLBACK ---
        else:
            return self.roll_banner(
                "Armor Gear Foundry", chapter, state, force_guarantee
            )