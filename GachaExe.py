# -*- coding: utf-8 -*-
import json
import os
import random
import re
import shutil
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

# Local Module Imports
import ArmorGear as armor
import BossChips as boss_chips
import Cards as cards
import Characters as chars
import Config as cfg
import StageClear as stages
import Weapons as weaps
from Banners import GachaEngine


def upgrade_character_star(hunter, state):
  """Upgrades a character's Star Rank, allowing Character Patches

  to act as a substitute for Memories if the character does not have
  enough memories and enough Character Patches have been accumulated.
  """
  char_inv = state.get("inventory_chars", {})
  if hunter not in char_inv:
    return False, f"Character {hunter} not found in inventory."

  char_data = char_inv[hunter]
  stars = char_data.get("stars", 0)
  if stars >= 5:
    return False, f"{hunter} is already at maximum 5-Star rank!"

  memories = char_data.get("memories", 0)
  patches = state.get("memory_patches", 0)

  # Determine character rank
  rank = "B"
  if hasattr(chars, "CHAR_LOOKUP") and hunter in chars.CHAR_LOOKUP:
    info = chars.CHAR_LOOKUP[hunter]
    if isinstance(info, dict):
      rank = info.get("rank", "B")
    else:
      rank = info if info else "B"

  costs = {
      "S": [10, 20, 40, 80, 100],
      "A": [10, 20, 40, 80, 100],
      "B": [5, 10, 20, 40, 80],
  }
  rank_costs = costs.get(rank, [10, 20, 40, 80, 100])
  required_mems = rank_costs[stars] if stars < len(rank_costs) else 100

  # Check if total available (memories + patches) is sufficient
  total_available = memories + patches
  if total_available < required_mems:
    return (
        False,
        f"Not enough memories or Character Patches! Required:"
        f" {required_mems}, Have Memories: {memories}, Patches:"
        f" {patches}.",
    )

  # Deduct memories first, then use Character Patches as substitute
  if memories >= required_mems:
    char_data["memories"] = memories - required_mems
    used_mems = required_mems
    used_patches = 0
  else:
    used_mems = memories
    char_data["memories"] = 0
    deficit = required_mems - used_mems
    state["memory_patches"] = patches - deficit
    used_patches = deficit

  char_data["stars"] = stars + 1
  msg = (
      f"Successfully upgraded {hunter} from {stars}★ to {stars+1}★! (Used"
      f" {used_mems} memories and {used_patches} Character Patches)."
  )
  return True, msg


def upgrade_weapon_star(weapon, state):
  """Upgrades a weapon's Star Rank, allowing Weapon Patches

  to act as a substitute for Memories if the weapon does not have
  enough memories and enough Weapon Patches have been accumulated.
  """
  weap_inv = state.get("inventory_weapons", {})
  if weapon not in weap_inv:
    return False, f"Weapon {weapon} not found in inventory."

  weap_data = weap_inv[weapon]
  if isinstance(weap_data, int):
    weap_data = {"stars": 0, "memories": 0, "unlocked": True}
    weap_inv[weapon] = weap_data

  stars = weap_data.get("stars", 0)
  if stars >= 5:
    return False, f"{weapon} is already at maximum 5-Star rank!"

  memories = weap_data.get("memories", 0)
  patches = state.get("weapon_patches", 0)

  # Determine weapon rank
  rank = "B"
  if hasattr(weaps, "DATA_WEAPONS"):
    for w in weaps.DATA_WEAPONS:
      if w.get("name") == weapon:
        rank = w.get("rank", "B")
        break
  elif hasattr(weaps, "WEAPON_LOOKUP") and weapon in weaps.WEAPON_LOOKUP:
    info = weaps.WEAPON_LOOKUP[weapon]
    if isinstance(info, dict):
      rank = info.get("rank", "B")
    else:
      rank = info if info else "B"

  costs = {
      "S": [10, 20, 40, 80, 100],
      "A": [10, 20, 40, 80, 100],
      "B": [5, 10, 20, 40, 80],
  }
  rank_costs = costs.get(rank, [10, 20, 40, 80, 100])
  required_mems = rank_costs[stars] if stars < len(rank_costs) else 100

  total_available = memories + patches
  if total_available < required_mems:
    return (
        False,
        f"Not enough memories or Weapon Patches! Required: {required_mems},"
        f" Have Memories: {memories}, Patches: {patches}.",
    )

  if memories >= required_mems:
    weap_data["memories"] = memories - required_mems
    used_mems = required_mems
    used_patches = 0
  else:
    used_mems = memories
    weap_data["memories"] = 0
    deficit = required_mems - used_mems
    state["weapon_patches"] = patches - deficit
    used_patches = deficit

  weap_data["stars"] = stars + 1
  msg = (
      f"Successfully upgraded {weapon} from {stars}★ to {stars+1}★! (Used"
      f" {used_mems} memories and {used_patches} Weapon Patches)."
  )
  return True, msg


class DarkConsoleView(tk.Frame):
  """Dark terminal-styled list widget with color tagging for ranks, stars, and status."""

  def __init__(self, parent, *args, **kwargs):
    super().__init__(parent, *args, **kwargs)

    self.text = tk.Text(
        self,
        wrap="none",
        state="disabled",
        bg="#1E1E1E",
        fg="#FFFFFF",
        insertbackground="white",
        font=("Consolas", 10),
        relief="sunken",
        bd=2,
    )
    self.scrollbar = ttk.Scrollbar(
        self, orient="vertical", command=self.text.yview
    )
    self.text.configure(yscrollcommand=self.scrollbar.set)

    self.text.pack(side="left", fill="both", expand=True)
    self.scrollbar.pack(side="right", fill="y")

    # Color Tags
    self.text.tag_configure(
        "rank_s", foreground="#FF4500", font=("Consolas", 10, "bold")
    )  # Orange-Red
    self.text.tag_configure(
        "rank_a", foreground="#BA55D3", font=("Consolas", 10, "bold")
    )  # Purple
    self.text.tag_configure(
        "rank_b", foreground="#1E90FF", font=("Consolas", 10, "bold")
    )  # Blue
    self.text.tag_configure("gold_star", foreground="#FFD700")  # Gold ★
    self.text.tag_configure("unlocked", foreground="#32CD32")  # Lime Green
    self.text.tag_configure("locked", foreground="#FF6347")  # Red
    self.text.tag_configure("crafted", foreground="#00FFFF")  # Cyan for Crafted
    self.text.tag_configure(
        "highlight", foreground="#00FFFF", font=("Consolas", 10, "bold")
    )  # Cyan

  def clear(self):
    self.text.config(state="normal")
    self.text.delete("1.0", tk.END)
    self.text.config(state="disabled")

  def insert_line(self, line_text, at_top=False):
    self.text.config(state="normal")

    # Tokenize and colorize specific tags
    tokens = re.split(
        r"(\[S-Rank\]|\[A-Rank\]|\[B-Rank\]|UNLOCKED|LOCKED|CRAFTED|★|===.*?===)",
        line_text,
    )

    if at_top:
      self.text.mark_set("top_mark", "1.0")
      self.text.mark_gravity("top_mark", tk.RIGHT)
      target_pos = "top_mark"
    else:
      target_pos = tk.END

    for token in tokens:
      if token == "[S-Rank]":
        self.text.insert(target_pos, token, "rank_s")
      elif token == "[A-Rank]":
        self.text.insert(target_pos, token, "rank_a")
      elif token == "[B-Rank]":
        self.text.insert(target_pos, token, "rank_b")
      elif token == "UNLOCKED":
        self.text.insert(target_pos, token, "unlocked")
      elif token == "LOCKED":
        self.text.insert(target_pos, token, "locked")
      elif token == "CRAFTED":
        self.text.insert(target_pos, token, "crafted")
      elif token == "★":
        self.text.insert(target_pos, token, "gold_star")
      elif token and token.startswith("===") and token.endswith("==="):
        self.text.insert(target_pos, token, "highlight")
      else:
        self.text.insert(target_pos, token)

    self.text.insert(target_pos, "\n")
    self.text.config(state="disabled")


class MegamanXDiVEApp(tk.Tk):

  def __init__(self):
    super().__init__()
    self.title("Mega Man X DiVE Mobile - Memory Capsule Engine")
    self.geometry("1020x760")

    # Custom Tab & Notebook Styling
    self.style = ttk.Style(self)
    if "clam" in self.style.theme_names():
      self.style.theme_use("clam")

    self.style.configure(
        "TNotebook", background="#F0F0F0", tabmargins=[2, 5, 2, 0]
    )
    self.style.configure(
        "TNotebook.Tab",
        font=("TkDefaultFont", 9, "bold"),
        padding=[12, 5],
        background="#E1BEE7",
        foreground="#333333",
    )
    self.style.map(
        "TNotebook.Tab",
        background=[("selected", "#1E88E5"), ("active", "#C2D4E5")],
        foreground=[("selected", "#FFFFFF"), ("active", "#000000")],
    )

    self.gacha_engine = GachaEngine()

    # Application State Default Template
    self.state = self.get_default_state()

    self.drop_slots = []
    self.load_game()
    self.process_max_star_conversions()
    self.build_ui()
    self.refresh_all_views()

  def get_default_state(self):
    """Returns clean initial default state dictionary."""
    return {
        "version": cfg.SAVE_SCHEMA_VERSION,
        "player_level": 1,
        "element": 0,
        "bolts": 0,
        "a_bolts": 0,
        "s_bolts": 0,
        "memory_patches": 0,
        "weapon_patches": 0,
        "current_chapter": 1,
        "stage_clears": {},
        "inventory_chars": {"X": {"stars": 0, "memories": 0, "unlocked": True}},
        "inventory_weapons": {
            "Buster": {
                "stars": 0,
                "memories": 0,
                "unlocked": True,
            },
            "Standard Saber": {
                "stars": 0,
                "memories": 0,
                "unlocked": True,
            },
        },
        "inventory_chips": {},
        "inventory_cards": {
            "Refleczer": {"count": 1, "stars": 1, "rank": "B", "unlocked": True},
            "Metall C-15": {
                "count": 1,
                "stars": 1,
                "rank": "B",
                "unlocked": True,
            },
            "Ball De Voux": {
                "count": 1,
                "stars": 1,
                "rank": "B",
                "unlocked": True,
            },
            "Dig Labour": {"count": 1, "stars": 1, "rank": "B", "unlocked": True},
        },
        "inventory_armor": {},
    }

  def process_max_star_conversions(self):
    """Automatically converts leftover character and weapon memories

    into Character Patches and Weapon Patches when 5-Star is reached,
    and cleans up duplicate Armor Gear into Bolts.
    """
    converted_chars = []
    # 1. Process Character Memories for 5-Star Characters
    char_inv = self.state.get("inventory_chars", {})
    for char_name, char_data in char_inv.items():
      if isinstance(char_data, dict):
        stars = char_data.get("stars", 0)
        mems = char_data.get("memories", 0)
        if stars >= 5 and mems > 0:
          self.state["memory_patches"] = (
              self.state.get("memory_patches", 0) + mems
          )
          converted_chars.append((char_name, mems))
          char_data["memories"] = 0

    # 2. Process Weapon Memories for 5-Star Weapons
    weap_inv = self.state.get("inventory_weapons", {})
    for weap_name, weap_data in weap_inv.items():
      if isinstance(weap_data, dict):
        stars = weap_data.get("stars", 0)
        mems = weap_data.get("memories", 0)

        if stars >= 5 and mems > 0:
          self.state["weapon_patches"] = (
              self.state.get("weapon_patches", 0) + mems
          )
          weap_data["memories"] = 0

    # 3. Clean up existing Armor Gear duplicates and convert to Bolts
    armor.clean_all_existing_duplicates(self.state)

    return converted_chars

  # --- SAVE / LOAD ---
  def load_game(self):
    if os.path.exists(cfg.SAVE_FILE):
      try:
        with open(cfg.SAVE_FILE, "r", encoding="utf-8") as f:
          data = json.load(f)
          self.state.update(data)
          # Ensure starter weapons are present and unlocked correctly
          if "inventory_weapons" not in self.state:
            self.state["inventory_weapons"] = {}
          for w in ("Buster", "Standard Saber"):
            if w not in self.state["inventory_weapons"]:
              self.state["inventory_weapons"][w] = {
                  "stars": 0,
                  "memories": 0,
                  "unlocked": True,
              }
            elif isinstance(self.state["inventory_weapons"][w], dict):
              self.state["inventory_weapons"][w].pop("count", None)
              if "unlocked" not in self.state["inventory_weapons"][w]:
                self.state["inventory_weapons"][w]["unlocked"] = True
            else:
              self.state["inventory_weapons"][w] = {
                  "stars": 0,
                  "memories": 0,
                  "unlocked": True,
              }
      except Exception as e:
        print(f"Error loading save: {e}")
    else:
      self.save_game()

  def save_game(self):
    try:
      if os.path.exists(cfg.SAVE_FILE):
        shutil.copy(cfg.SAVE_FILE, cfg.BACKUP_FILE)
      with open(cfg.SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(self.state, f, indent=4)
    except Exception as e:
      messagebox.showerror("Save Error", f"Failed to save game state: {e}")

  # --- MAIN UI BUILDING ---
  def build_ui(self):
    # Top Header Frame: Player Profile & Wallet
    self.frame_header = tk.LabelFrame(
        self,
        text=" Player Profile & Wallet ",
        font=("TkDefaultFont", 10, "bold"),
        padx=10,
        pady=8,
    )
    self.frame_header.pack(fill="x", padx=10, pady=5)

    lbl_frame = tk.Frame(self.frame_header)
    lbl_frame.pack(fill="x", pady=2)

    self.lbl_element = tk.Label(
        lbl_frame,
        text="Element: 0",
        font=("TkDefaultFont", 11, "bold"),
        fg="#0000FF",
    )
    self.lbl_element.pack(side="left", padx=(5, 15))

    self.lbl_bolts = tk.Label(
        lbl_frame,
        text="B-Bolts: 0",
        font=("TkDefaultFont", 11, "bold"),
        fg="#228B22",
    )
    self.lbl_bolts.pack(side="left", padx=15)

    self.lbl_a_bolts = tk.Label(
        lbl_frame,
        text="A-Bolts: 0",
        font=("TkDefaultFont", 11, "bold"),
        fg="#800080",
    )
    self.lbl_a_bolts.pack(side="left", padx=15)

    self.lbl_s_bolts = tk.Label(
        lbl_frame,
        text="S-Bolts: 0",
        font=("TkDefaultFont", 11, "bold"),
        fg="#FF4500",
    )
    self.lbl_s_bolts.pack(side="left", padx=15)

    self.lbl_patches = tk.Label(
        lbl_frame,
        text="Character Patches: 0",
        font=("TkDefaultFont", 11, "bold"),
        fg="#D9534F",
    )
    self.lbl_patches.pack(side="left", padx=15)

    self.lbl_weapon_patches = tk.Label(
        lbl_frame,
        text="Weapon Patches: 0",
        font=("TkDefaultFont", 11, "bold"),
        fg="#4682B4",
    )
    self.lbl_weapon_patches.pack(side="left", padx=15)

    tk.Label(lbl_frame, text="Lv:").pack(side="left", padx=(15, 2))
    self.spin_player_level = ttk.Spinbox(
        lbl_frame,
        from_=1,
        to=200,
        width=4,
        command=self.on_level_changed,
    )
    self.spin_player_level.set(str(self.state.get("player_level", 1)))
    self.spin_player_level.bind("<FocusOut>", self.on_level_changed)
    self.spin_player_level.bind("<Return>", self.on_level_changed)
    self.spin_player_level.pack(side="left")

    tk.Label(lbl_frame, text="Chapter:").pack(side="left", padx=(15, 2))
    self.combo_chapter = ttk.Combobox(
        lbl_frame,
        values=[str(i) for i in range(1, 19)],
        width=4,
        state="readonly",
    )
    self.combo_chapter.set(str(self.state.get("current_chapter", 1)))
    self.combo_chapter.bind("<<ComboboxSelected>>", self.on_chapter_changed)
    self.combo_chapter.pack(side="left")

    # Quick Adjust Wallet Toolbar
    ctrl_frame = tk.Frame(self.frame_header)
    ctrl_frame.pack(fill="x", pady=(8, 2))

    tk.Label(
        ctrl_frame, text="Modify Amount:", font=("TkDefaultFont", 9, "bold")
    ).pack(side="left", padx=5)
    self.ent_modify_amount = tk.Entry(ctrl_frame, width=6)
    self.ent_modify_amount.insert(0, "10000")
    self.ent_modify_amount.pack(side="left", padx=5)

    tk.Button(
        ctrl_frame,
        text="+ Metal",
        bg="#B0E0E6",
        command=lambda: self.adjust_wallet("element", True),
    ).pack(side="left", padx=2)
    tk.Button(
        ctrl_frame,
        text="- Metal",
        bg="#FFC0CB",
        command=lambda: self.adjust_wallet("element", False),
    ).pack(side="left", padx=2)
    tk.Button(
        ctrl_frame,
        text="+ B-Bolts",
        bg="#C8E6C9",
        command=lambda: self.adjust_wallet("bolts", True),
    ).pack(side="left", padx=2)
    tk.Button(
        ctrl_frame,
        text="- B-Bolts",
        bg="#FFCDD2",
        command=lambda: self.adjust_wallet("bolts", False),
    ).pack(side="left", padx=2)
    tk.Button(
        ctrl_frame,
        text="+ A-Bolts",
        bg="#E1BEE7",
        command=lambda: self.adjust_wallet("a_bolts", True),
    ).pack(side="left", padx=2)
    tk.Button(
        ctrl_frame,
        text="- A-Bolts",
        bg="#F8BBD0",
        command=lambda: self.adjust_wallet("a_bolts", False),
    ).pack(side="left", padx=2)
    tk.Button(
        ctrl_frame,
        text="+ S-Bolts",
        bg="#FFCC80",
        command=lambda: self.adjust_wallet("s_bolts", True),
    ).pack(side="left", padx=2)
    tk.Button(
        ctrl_frame,
        text="- S-Bolts",
        bg="#FFE0B2",
        command=lambda: self.adjust_wallet("s_bolts", False),
    ).pack(side="left", padx=2)
    tk.Button(
        ctrl_frame,
        text="Reset Profile",
        bg="#FF8A80",
        command=self.reset_profile,
    ).pack(side="left", padx=(15, 2))

    # Main Tabs Notebook
    self.notebook = ttk.Notebook(self)
    self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

    self.setup_tab_gacha()
    self.setup_tab_stages()
    self.setup_tab_chars()
    self.setup_tab_weapons()
    self.setup_tab_chips()
    self.setup_tab_cards()
    self.setup_tab_armor()

  # --- TAB 1: GACHA BANNERS ---
  def setup_tab_gacha(self):
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text="Gacha Banners")

    top_container = tk.Frame(tab)
    top_container.pack(fill="x", pady=10)

    self.combo_banner = ttk.Combobox(
        top_container,
        values=[
            "Character Capsule",
            "Weapon Capsule",
            "Armor Gear Foundry",
            "Boss Chip Capsule",
            "Unique Card Capsule",
            "Mobile Master Capsule (Element)",
            "Chapter Character Capsule",
            "Chapter Weapon Capsule",
            "Chapter Armor Gear Capsule",
            "Chapter Boss Chip Capsule",
            "Chapter Card Capsule",
            "Chapter Progress Capsule",
        ],
        state="readonly",
        width=40,
        font=("TkDefaultFont", 10),
    )
    self.combo_banner.current(0)
    self.combo_banner.pack(anchor="center", pady=3)

    tk.Label(
        top_container,
        text="Cost: 100 Element Single / 1000 Element Multi",
        font=("TkDefaultFont", 9, "italic"),
    ).pack(anchor="center", pady=2)

    btn_single = tk.Button(
        top_container,
        text="Single Pull (100 Element)",
        bg="#EEDC82",
        activebackground="#E6C653",
        font=("TkDefaultFont", 10),
        width=45,
        command=lambda: self.execute_pull(1),
    )
    btn_single.pack(anchor="center", pady=3)

    btn_ten = tk.Button(
        top_container,
        text="10x Multi-Pull (1000 Element)",
        bg="#FFA500",
        activebackground="#FF8C00",
        font=("TkDefaultFont", 10, "bold"),
        width=45,
        command=lambda: self.execute_pull(10),
    )
    btn_ten.pack(anchor="center", pady=3)

    drop_frame = tk.LabelFrame(tab, text=" Drop Screen Results ")
    drop_frame.pack(fill="both", expand=True, padx=15, pady=10)

    self.drop_slots = []
    for i in range(10):
      lbl = tk.Label(
          drop_frame,
          text="- Empty Drop Slot -",
          bg="#222222",
          fg="#FFFFFF",
          font=("Consolas", 10),
          anchor="center",
          relief="ridge",
          bd=2,
      )
      lbl.pack(fill="x", padx=10, pady=2, ipady=3)
      self.drop_slots.append(lbl)

  def execute_pull(self, count):
    cost = cfg.COST_METALS_SINGLE if count == 1 else cfg.COST_METALS_TEN
    if self.state["element"] < cost:
      messagebox.showwarning(
          "Insufficient Funds", "You do not have enough Element!"
      )
      return

    self.state["element"] -= cost
    banner = self.combo_banner.get()

    for slot in self.drop_slots:
      slot.config(text="- Empty Drop Slot -", fg="#888888")

    for i in range(count):
      guarantee = count == 10 and i == 9
      rank, result_str = self.gacha_engine.roll_banner(
          banner,
          self.state["current_chapter"],
          self.state,
          force_guarantee=guarantee,
      )

      color_map = {"S": "#FF4500", "A": "#BA55D3", "B": "#1E90FF"}
      fg_color = color_map.get(rank, "#FFFFFF")
      self.drop_slots[i].config(text=f"- {result_str} -", fg=fg_color)

    # Process automatic 5-star conversions after pulling
    self.process_max_star_conversions()
    self.save_game()
    self.refresh_all_views()

  # --- TAB 2: STAGE CLEARED ---
  def setup_tab_stages(self):
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text="Stage Cleared")

    stage_ctrl = tk.LabelFrame(
        tab, text=" Stage Simulator & Progression ", padx=10, pady=5
    )
    stage_ctrl.pack(fill="x", padx=10, pady=5)

    tk.Label(
        stage_ctrl, text="Select Chapter:", font=("TkDefaultFont", 9, "bold")
    ).pack(side="left", padx=5)
    self.spin_stage_chap = ttk.Spinbox(
        stage_ctrl, from_=1, to=18, width=5, command=self.refresh_stages_view
    )
    self.spin_stage_chap.set(self.state.get("current_chapter", 1))
    self.spin_stage_chap.pack(side="left", padx=5)

    self.stage_btn_frame = tk.Frame(stage_ctrl)
    self.stage_btn_frame.pack(side="left", padx=15)

    self.stage_console = DarkConsoleView(tab)
    self.stage_console.pack(fill="both", expand=True, padx=10, pady=5)

  def refresh_stages_view(self):
    for w in self.stage_btn_frame.winfo_children():
      w.destroy()

    try:
      chap = int(self.spin_stage_chap.get())
    except ValueError:
      chap = 1

    for s in range(1, 7):
      stage_key = f"C{chap}S{s}"
      is_cleared = self.state["stage_clears"].get(stage_key, False)

      if s == 1:
        if chap == 1:
          is_unlocked = True
        else:
          prev_stage_key = f"C{chap - 1}S6"
          is_unlocked = self.state["stage_clears"].get(prev_stage_key, False)
      else:
        prev_stage_key = f"C{chap}S{s - 1}"
        is_unlocked = self.state["stage_clears"].get(prev_stage_key, False)

      btn_txt = f"Stage {chap}-{s}" + (" (Boss)" if s == 6 else "")

      if is_cleared:
        btn_bg = "#C8E6C9"
        btn_state = "normal"
      elif is_unlocked:
        btn_bg = "#FFE0B2"
        btn_state = "normal"
      else:
        btn_bg = "#E0E0E0"
        btn_state = "disabled"

      btn = tk.Button(
          self.stage_btn_frame,
          text=btn_txt,
          bg=btn_bg,
          state=btn_state,
          font=("TkDefaultFont", 9),
          command=lambda c=chap, st=s: self.clear_stage(c, st),
      )
      btn.pack(side="left", padx=3)

  def clear_stage(self, chapter, stage):
    stage_key = f"C{chapter}S{stage}"
    is_repeat = self.state["stage_clears"].get(stage_key, False)

    if stage > 1:
      prev_key = f"C{chapter}S{stage - 1}"
      if not self.state["stage_clears"].get(prev_key, False):
        messagebox.showwarning(
            "Stage Locked", f"You must clear Stage {chapter}-{stage - 1} first!"
        )
        return
    elif chapter > 1:
      prev_key = f"C{chapter - 1}S6"
      if not self.state["stage_clears"].get(prev_key, False):
        messagebox.showwarning(
            "Chapter Locked",
            f"You must clear Chapter {chapter - 1} Stage 6 first!",
        )
        return

    self.state["stage_clears"][stage_key] = True

    now_str = datetime.now().strftime("%d-%b-%Y %H:%M")
    log_lines = [
        f"[{now_str}] === [Chapter {chapter} - Stage {stage}] CLEARED ==="
    ]

    if not is_repeat:
      if chapter <= 4:
        self.state["element"] += 12
        self.state["bolts"] += 4
        log_lines.append(
            f"[{now_str}] First-Time Clear Bonus: +12 Element, +4 B-Bolts"
        )
      elif 5 <= chapter <= 8:
        self.state["element"] += 12
        self.state["a_bolts"] += 4
        log_lines.append(
            f"[{now_str}] First-Time Clear Bonus: +12 Element, +4 A-Bolts"
        )
      elif 9 <= chapter <= 18:
        self.state["element"] += 12
        self.state["s_bolts"] += 4
        log_lines.append(
            f"[{now_str}] First-Time Clear Bonus: +12 Element, +4 S-Bolts"
        )
    else:
      if chapter <= 4:
        elem_add = int(12 * 0.25)
        bolt_add = int(4 * 0.25)
        self.state["element"] += elem_add
        self.state["bolts"] += bolt_add
        log_lines.append(
            f"[{now_str}] Repeat Clear Bonus (25%): +{elem_add} Element,"
            f" +{bolt_add} B-Bolts"
        )
      elif 5 <= chapter <= 8:
        elem_add = int(12 * 0.25)
        bolt_add = int(4 * 0.25)
        self.state["element"] += elem_add
        self.state["a_bolts"] += bolt_add
        log_lines.append(
            f"[{now_str}] Repeat Clear Bonus (25%): +{elem_add} Element,"
            f" +{bolt_add} A-Bolts"
        )
      elif 9 <= chapter <= 18:
        elem_add = int(12 * 0.25)
        bolt_add = int(4 * 0.25)
        self.state["element"] += elem_add
        self.state["s_bolts"] += bolt_add
        log_lines.append(
            f"[{now_str}] Repeat Clear Bonus (25%): +{elem_add} Element,"
            f" +{bolt_add} S-Bolts"
        )

    if (
        stage == 6
        and chapter == self.state["current_chapter"]
        and chapter < 18
    ):
      self.state["current_chapter"] += 1
      self.combo_chapter.set(str(self.state["current_chapter"]))

    log_lines.append(
        "-----------------------------------------------------------------"
    )

    for line in reversed(log_lines):
      self.stage_console.insert_line(line, at_top=True)

    self.save_game()
    self.refresh_all_views()

  # --- TAB 3: CHARACTERS ---
  def setup_tab_chars(self):
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text="Characters")

    inj_frame = tk.LabelFrame(tab, text=" Character Manager ", padx=10, pady=5)
    inj_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(
        inj_frame, text="Hunter:", font=("TkDefaultFont", 9, "bold")
    ).pack(side="left", padx=(2, 5))

    self.combo_hunter = ttk.Combobox(
        inj_frame, values=[], state="readonly", width=22
    )
    self.combo_hunter.pack(side="left", padx=5)

    tk.Button(
        inj_frame,
        text="🔒 Lock/Unlock",
        bg="#E1BEE7",
        command=self.toggle_hunter_lock,
    ).pack(side="left", padx=(10, 2))

    tk.Button(
        inj_frame,
        text="⭐ Upgrade Star",
        bg="#FFD700",
        command=self.upgrade_hunter_star_ui,
    ).pack(side="left", padx=(5, 2))

    tk.Label(
        inj_frame, text="Sort By:", font=("TkDefaultFont", 9, "bold")
    ).pack(side="left", padx=(20, 2))
    self.combo_sort = ttk.Combobox(
        inj_frame,
        values=[
            "Name (A-Z)",
            "Name (Z-A)",
            "Rank (S->B)",
            "Rank (B->S)",
            "Chapter (Low->High)",
            "Chapter (High->Low)",
            "Status (Unlocked First)",
            "Status (Locked First)",
            "Star Rank (High->Low)",
            "Star Rank (Low->High)",
            "Memories (High->Low)",
            "Memories (Low->High)",
        ],
        state="readonly",
        width=22,
    )
    self.combo_sort.set("Name (A-Z)")
    self.combo_sort.bind(
        "<<ComboboxSelected>>", lambda e: self.refresh_chars_view()
    )
    self.combo_sort.pack(side="left", padx=5)

    self.char_console = DarkConsoleView(tab)
    self.char_console.pack(fill="both", expand=True, padx=10, pady=5)

  def toggle_hunter_lock(self):
    hunter = self.combo_hunter.get()
    if not hunter or hunter == "(No Characters)":
      return
    if hunter not in self.state["inventory_chars"]:
      is_unlocked = True if hunter == "X" else False
      self.state["inventory_chars"][hunter] = {
          "stars": 0,
          "memories": 0,
          "unlocked": not is_unlocked,
      }
    else:
      status = self.state["inventory_chars"][hunter].get("unlocked", False)
      self.state["inventory_chars"][hunter]["unlocked"] = not status

    self.save_game()
    self.refresh_chars_view()

  def upgrade_hunter_star_ui(self):
    hunter = self.combo_hunter.get()
    if not hunter or hunter == "(No Characters)":
      return

    # Track star level and memories before upgrade
    char_inv = self.state.get("inventory_chars", {})
    char_data = char_inv.get(hunter, {})
    old_stars = char_data.get("stars", 0)
    old_mems = char_data.get("memories", 0)

    success, msg = upgrade_character_star(hunter, self.state)
    if success:
      new_char_data = char_inv.get(hunter, {})
      new_stars = new_char_data.get("stars", 0)
      new_mems = new_char_data.get("memories", 0)

      dissolved_mems = 0
      # If the character reached 5-Stars during this upgrade, convert memories to patches
      if old_stars < 5 and new_stars >= 5:
        dissolved_mems = old_mems + new_mems
        if dissolved_mems > 0:
          self.state["memory_patches"] = (
              self.state.get("memory_patches", 0) + dissolved_mems
          )
          new_char_data["memories"] = 0
      else:
        converted = self.process_max_star_conversions()
        for name, mems in converted:
          if name == hunter:
            dissolved_mems = mems

      self.save_game()
      self.refresh_all_views()

      full_msg = msg
      if dissolved_mems > 0:
        full_msg += (
            f"\n\nCharacter reached 5-Star! {dissolved_mems} memories"
            " were converted into Character Patches."
        )

      messagebox.showinfo("Star Upgrade", full_msg)
    else:
      messagebox.showwarning("Star Upgrade Failed", msg)

  def refresh_chars_view(self):
    self.char_console.clear()

    char_dict = self.state.get("inventory_chars", {})
    active_char_names = sorted(list(char_dict.keys()))

    if hasattr(self, "combo_hunter"):
      self.combo_hunter["values"] = active_char_names
      curr_sel = self.combo_hunter.get()
      if active_char_names:
        if curr_sel not in active_char_names:
          self.combo_hunter.set(active_char_names[0])
      else:
        self.combo_hunter.set("(No Characters)")

    char_items = []
    for name, data in char_dict.items():
      info = chars.CHAR_LOOKUP.get(name, {})
      if isinstance(info, dict):
        rank = info.get("rank", "B")
        chap = info.get("chapter", 1)
      else:
        rank = info if info else "B"
        chap = 1
      char_items.append((name, rank, data, chap))

    sort_mode = (
        self.combo_sort.get()
        if hasattr(self, "combo_sort")
        else "Name (A-Z)"
    )
    rank_order = {"S": 0, "A": 1, "B": 2}
    rank_order_rev = {"B": 0, "A": 1, "S": 2}

    if sort_mode == "Name (A-Z)":
      char_items.sort(key=lambda x: x[0])
    elif sort_mode == "Name (Z-A)":
      char_items.sort(key=lambda x: x[0], reverse=True)
    elif sort_mode == "Rank (S->B)":
      char_items.sort(key=lambda x: (rank_order.get(x[1], 3), x[0]))
    elif sort_mode == "Rank (B->S)":
      char_items.sort(key=lambda x: (rank_order_rev.get(x[1], 3), x[0]))
    elif sort_mode == "Chapter (Low->High)":
      char_items.sort(key=lambda x: (x[3], x[0]))
    elif sort_mode == "Chapter (High->Low)":
      char_items.sort(key=lambda x: (x[3], x[0]), reverse=True)
    elif sort_mode == "Status (Unlocked First)":
      char_items.sort(
          key=lambda x: (0 if x[2].get("unlocked", False) else 1, x[0])
      )
    elif sort_mode == "Status (Locked First)":
      char_items.sort(
          key=lambda x: (1 if x[2].get("unlocked", False) else 0, x[0])
      )
    elif sort_mode == "Star Rank (High->Low)":
      char_items.sort(
          key=lambda x: (x[2].get("stars", 0), x[0]), reverse=True
      )
    elif sort_mode == "Star Rank (Low->High)":
      char_items.sort(key=lambda x: (x[2].get("stars", 0), x[0]))
    elif sort_mode == "Memories (High->Low)":
      char_items.sort(
          key=lambda x: (x[2].get("memories", 0), x[0]), reverse=True
      )
    elif sort_mode == "Memories (Low->High)":
      char_items.sort(key=lambda x: (x[2].get("memories", 0), x[0]))

    if not char_items:
      self.char_console.insert_line("=== No characters currently available ===")
      return

    for name, rank, data, chap in char_items:
      unlocked_str = "UNLOCKED" if data.get("unlocked", False) else "LOCKED"
      stars = data.get("stars", 0)
      mems = data.get("memories", 0)

      line = (
          f"[{rank}-Rank] {name:<26} | Ch. {chap:<2} | Status:"
          f" {unlocked_str:<8} ({stars}★) | Memories: {mems}"
      )
      self.char_console.insert_line(line)

  # --- TAB 4: WEAPONS ---
  def setup_tab_weapons(self):
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text="Weapons")

    inj_frame = tk.LabelFrame(tab, text=" Weapon Manager ", padx=10, pady=5)
    inj_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(
        inj_frame, text="Weapon:", font=("TkDefaultFont", 9, "bold")
    ).pack(side="left", padx=(2, 5))

    self.combo_weapon = ttk.Combobox(
        inj_frame, values=[], state="readonly", width=25
    )
    self.combo_weapon.pack(side="left", padx=5)

    tk.Button(
        inj_frame,
        text="🔒 Lock/Unlock",
        bg="#E1BEE7",
        command=self.toggle_weapon_lock,
    ).pack(side="left", padx=(10, 2))

    tk.Button(
        inj_frame,
        text="⭐ Upgrade Star",
        bg="#FFD700",
        command=self.upgrade_weapon_star_ui,
    ).pack(side="left", padx=(5, 2))

    tk.Label(
        inj_frame, text="Sort By:", font=("TkDefaultFont", 9, "bold")
    ).pack(side="left", padx=(20, 2))
    self.combo_weap_sort = ttk.Combobox(
        inj_frame,
        values=[
            "Name (A-Z)",
            "Name (Z-A)",
            "Rank (S->B)",
            "Rank (B->S)",
            "Chapter (Low->High)",
            "Chapter (High->Low)",
            "Status (Unlocked First)",
            "Status (Locked First)",
            "Star Rank (High->Low)",
            "Star Rank (Low->High)",
            "Memories (High->Low)",
            "Memories (Low->High)",
        ],
        state="readonly",
        width=22,
    )
    self.combo_weap_sort.set("Name (A-Z)")
    self.combo_weap_sort.bind(
        "<<ComboboxSelected>>", lambda e: self.refresh_weapons_view()
    )
    self.combo_weap_sort.pack(side="left", padx=5)

    self.weap_console = DarkConsoleView(tab)
    self.weap_console.pack(fill="both", expand=True, padx=10, pady=5)

  def toggle_weapon_lock(self):
    weapon = self.combo_weapon.get()
    if not weapon or weapon == "(No Weapons)":
      return

    is_unlocked_default = (
        True if weapon in ("Buster", "Standard Saber") else False
    )

    if weapon not in self.state["inventory_weapons"]:
      self.state["inventory_weapons"][weapon] = {
          "stars": 0,
          "memories": 0,
          "unlocked": is_unlocked_default,
      }
    elif isinstance(self.state["inventory_weapons"][weapon], int):
      self.state["inventory_weapons"][weapon] = {
          "stars": 0,
          "memories": 0,
          "unlocked": is_unlocked_default,
      }
    else:
      status = self.state["inventory_weapons"][weapon].get(
          "unlocked", is_unlocked_default
      )
      self.state["inventory_weapons"][weapon]["unlocked"] = not status

    self.save_game()
    self.refresh_weapons_view()

  def upgrade_weapon_star_ui(self):
    weapon = self.combo_weapon.get()
    if not weapon or weapon == "(No Weapons)":
      return

    weap_inv = self.state.get("inventory_weapons", {})
    weap_data = weap_inv.get(weapon, {})
    if isinstance(weap_data, int):
      weap_data = {
          "stars": 0,
          "memories": 0,
          "unlocked": True,
      }
      weap_inv[weapon] = weap_data

    old_stars = weap_data.get("stars", 0)
    old_mems = weap_data.get("memories", 0)

    success, msg = upgrade_weapon_star(weapon, self.state)
    if success:
      new_weap_data = weap_inv.get(weapon, {})
      new_stars = new_weap_data.get("stars", 0)
      new_mems = new_weap_data.get("memories", 0)

      dissolved_mems = 0
      if old_stars < 5 and new_stars >= 5:
        dissolved_mems = old_mems + new_mems
        if dissolved_mems > 0:
          self.state["weapon_patches"] = (
              self.state.get("weapon_patches", 0) + dissolved_mems
          )
          new_weap_data["memories"] = 0
      else:
        self.process_max_star_conversions()

      self.save_game()
      self.refresh_all_views()

      full_msg = msg
      if dissolved_mems > 0:
        full_msg += (
            f"\n\nWeapon reached 5-Star! {dissolved_mems} memories"
            " were converted into Weapon Patches."
        )

      messagebox.showinfo("Star Upgrade", full_msg)
    else:
      messagebox.showwarning("Star Upgrade Failed", msg)

  def refresh_weapons_view(self):
    self.weap_console.clear()

    weap_dict = self.state.get("inventory_weapons", {})
    active_weap_names = sorted(list(weap_dict.keys()))

    if hasattr(self, "combo_weapon"):
      self.combo_weapon["values"] = active_weap_names
      curr_sel = self.combo_weapon.get()
      if active_weap_names:
        if curr_sel not in active_weap_names:
          self.combo_weapon.set(active_weap_names[0])
      else:
        self.combo_weapon.set("(No Weapons)")

    weap_items = []
    for name, data in weap_dict.items():
      rank = "B"
      chap = 1
      if hasattr(weaps, "DATA_WEAPONS"):
        for w in weaps.DATA_WEAPONS:
          if w.get("name") == name:
            chap = w.get("chapter", 1)
            rank = w.get("rank", "B")
            break
      elif hasattr(weaps, "WEAPON_LOOKUP") and name in weaps.WEAPON_LOOKUP:
        r_info = weaps.WEAPON_LOOKUP[name]
        if isinstance(r_info, dict):
          rank = r_info.get("rank", "B")
          chap = r_info.get("chapter", 1)
        else:
          rank = r_info

      if isinstance(data, dict):
        stars = data.get("stars", 0)
        mems = data.get("memories", 0)
        is_unlocked = data.get(
            "unlocked", True if name in ("Buster", "Standard Saber") else False
        )
      else:
        stars = 0
        mems = 0
        is_unlocked = True if name in ("Buster", "Standard Saber") else False
      weap_items.append((name, rank, stars, mems, is_unlocked, chap))

    sort_val = (
        self.combo_weap_sort.get()
        if hasattr(self, "combo_weap_sort")
        else "Name (A-Z)"
    )
    rank_order = {"S": 0, "A": 1, "B": 2}
    rank_order_rev = {"B": 0, "A": 1, "S": 2}

    if sort_val == "Name (A-Z)":
      weap_items.sort(key=lambda x: x[0])
    elif sort_val == "Name (Z-A)":
      weap_items.sort(key=lambda x: x[0], reverse=True)
    elif sort_val == "Rank (S->B)":
      weap_items.sort(key=lambda x: (rank_order.get(x[1], 3), x[0]))
    elif sort_val == "Rank (B->S)":
      weap_items.sort(key=lambda x: (rank_order_rev.get(x[1], 3), x[0]))
    elif sort_val == "Chapter (Low->High)":
      weap_items.sort(key=lambda x: (x[5], x[0]))
    elif sort_val == "Chapter (High->Low)":
      weap_items.sort(key=lambda x: (x[5], x[0]), reverse=True)
    elif sort_val == "Status (Unlocked First)":
      weap_items.sort(key=lambda x: (0 if x[4] else 1, x[0]))
    elif sort_val == "Status (Locked First)":
      weap_items.sort(key=lambda x: (1 if x[4] else 0, x[0]))
    elif sort_val == "Star Rank (High->Low)":
      weap_items.sort(key=lambda x: (x[2], x[0]), reverse=True)
    elif sort_val == "Star Rank (Low->High)":
      weap_items.sort(key=lambda x: (x[2], x[0]))
    elif sort_val == "Memories (High->Low)":
      weap_items.sort(key=lambda x: (x[3], x[0]), reverse=True)
    elif sort_val == "Memories (Low->High)":
      weap_items.sort(key=lambda x: (x[3], x[0]))

    if not weap_items:
      self.weap_console.insert_line("=== No weapons currently available ===")
      return

    for name, rank, stars, mems, is_unlocked, chap in weap_items:
      status_str = "UNLOCKED" if is_unlocked else "LOCKED"
      line = (
          f"[{rank}-Rank] {name:<26} | Ch. {chap:<2} | Status: {status_str:<8}"
          f" ({stars}★) | Memories: {mems}"
      )
      self.weap_console.insert_line(line)

  # --- TAB 5: CHIPS ---
  def setup_tab_chips(self):
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text="Chips")

    inj_frame = tk.LabelFrame(tab, text=" Chip Manager ", padx=10, pady=5)
    inj_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(inj_frame, text="Chip:", font=("TkDefaultFont", 9, "bold")).pack(
        side="left", padx=(2, 5)
    )

    self.combo_chip = ttk.Combobox(
        inj_frame, values=[], state="readonly", width=25
    )
    self.combo_chip.pack(side="left", padx=5)

    tk.Button(
        inj_frame,
        text="🔒 Lock/Unlock",
        bg="#E1BEE7",
        command=self.toggle_chip_lock,
    ).pack(side="left", padx=(10, 2))

    tk.Label(
        inj_frame, text="Sort By:", font=("TkDefaultFont", 9, "bold")
    ).pack(side="left", padx=(20, 2))
    self.combo_chip_sort = ttk.Combobox(
        inj_frame,
        values=[
            "Name (A-Z)",
            "Name (Z-A)",
            "Rank (S->B)",
            "Rank (B->S)",
            "Chapter (Low->High)",
            "Chapter (High->Low)",
            "Status (Unlocked First)",
            "Status (Locked First)",
            "Element (A-Z)",
            "Quantity (High->Low)",
            "Quantity (Low->High)",
        ],
        state="readonly",
        width=22,
    )
    self.combo_chip_sort.set("Name (A-Z)")
    self.combo_chip_sort.bind(
        "<<ComboboxSelected>>", lambda e: self.refresh_chips_view()
    )
    self.combo_chip_sort.pack(side="left", padx=5)

    self.chip_console = DarkConsoleView(tab)
    self.chip_console.pack(fill="both", expand=True, padx=10, pady=5)

  def toggle_chip_lock(self):
    chip = self.combo_chip.get()
    if not chip or chip == "(No Chips)":
      return

    item_key = f"{chip} Chip" if not chip.endswith(" Chip") else chip
    base_name = chip[:-5] if chip.endswith(" Chip") else chip
    chip_info = boss_chips.BOSS_CHIP_LOOKUP.get(base_name, {})
    rank = chip_info.get("rank", "B")

    if item_key not in self.state["inventory_chips"]:
      self.state["inventory_chips"][item_key] = {
          "count": 1,
          "rank": rank,
          "type": "Boss Chip",
          "unlocked": True,
      }
    elif not isinstance(self.state["inventory_chips"][item_key], dict):
      cnt = self.state["inventory_chips"][item_key]
      self.state["inventory_chips"][item_key] = {
          "count": cnt,
          "rank": rank,
          "type": "Boss Chip",
          "unlocked": True,
      }
    else:
      status = self.state["inventory_chips"][item_key].get("unlocked", False)
      self.state["inventory_chips"][item_key]["unlocked"] = not status

    self.save_game()
    self.refresh_chips_view()

  def refresh_chips_view(self):
    self.chip_console.clear()

    chip_items = []
    active_chip_names = []

    for name, data in self.state.get("inventory_chips", {}).items():
      if isinstance(data, dict):
        chip_type = data.get("type", "Chip")
        if chip_type.lower() == "card":
          continue
        rank = data.get("rank", "B")
        count = data.get("count", 1)
        is_unlocked = data.get("unlocked", False)
      else:
        chip_type = "Chip"
        rank = "B"
        count = int(data)
        is_unlocked = False

      base_name = name[:-5] if name.endswith(" Chip") else name
      chap = 1
      color = "None"
      if (
          hasattr(boss_chips, "BOSS_CHIP_LOOKUP")
          and base_name in boss_chips.BOSS_CHIP_LOOKUP
      ):
        info = boss_chips.BOSS_CHIP_LOOKUP[base_name]
        chap = info.get("chapter", 1)
        color = info.get("color", "None")

      chip_items.append(
          (name, rank, chip_type, count, is_unlocked, chap, color)
      )

      if base_name not in active_chip_names:
        active_chip_names.append(base_name)

    active_chip_names.sort()

    if hasattr(self, "combo_chip"):
      self.combo_chip["values"] = active_chip_names
      curr_sel = self.combo_chip.get()
      if active_chip_names:
        if curr_sel not in active_chip_names:
          self.combo_chip.set(active_chip_names[0])
      else:
        self.combo_chip.set("(No Chips)")

    sort_val = (
        self.combo_chip_sort.get()
        if hasattr(self, "combo_chip_sort")
        else "Name (A-Z)"
    )
    rank_order = {"S": 0, "A": 1, "B": 2}
    rank_order_rev = {"B": 0, "A": 1, "S": 2}

    if sort_val == "Name (A-Z)":
      chip_items.sort(key=lambda x: x[0])
    elif sort_val == "Name (Z-A)":
      chip_items.sort(key=lambda x: x[0], reverse=True)
    elif sort_val == "Rank (S->B)":
      chip_items.sort(key=lambda x: (rank_order.get(x[1], 3), x[0]))
    elif sort_val == "Rank (B->S)":
      chip_items.sort(key=lambda x: (rank_order_rev.get(x[1], 3), x[0]))
    elif sort_val == "Chapter (Low->High)":
      chip_items.sort(key=lambda x: (x[5], x[0]))
    elif sort_val == "Chapter (High->Low)":
      chip_items.sort(key=lambda x: (x[5], x[0]), reverse=True)
    elif sort_val == "Status (Unlocked First)":
      chip_items.sort(key=lambda x: (0 if x[4] else 1, x[0]))
    elif sort_val == "Status (Locked First)":
      chip_items.sort(key=lambda x: (1 if x[4] else 0, x[0]))
    elif sort_val == "Element (A-Z)":
      chip_items.sort(key=lambda x: (x[6], x[0]))
    elif sort_val == "Quantity (High->Low)":
      chip_items.sort(key=lambda x: (x[3], x[0]), reverse=True)
    elif sort_val == "Quantity (Low->High)":
      chip_items.sort(key=lambda x: (x[3], x[0]))

    if not chip_items:
      self.chip_console.insert_line("=== No chips currently available ===")
      return

    for name, rank, chip_type, count, is_unlocked, chap, color in chip_items:
      color_info = f" | Element: {color:<6}" if color != "None" else ""
      status_str = "UNLOCKED" if is_unlocked else "LOCKED"
      line = (
          f"[{rank}-Rank] {name:<26} | Ch. {chap:<2} | Status: {status_str:<8}"
          f" | Type: {chip_type:<8}{color_info} | Quantity: x{count}"
      )
      self.chip_console.insert_line(line)

  # --- TAB 6: CARDS ---
  def setup_tab_cards(self):
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text="Cards")

    inj_frame = tk.LabelFrame(tab, text=" Card Manager ", padx=10, pady=5)
    inj_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(inj_frame, text="Card:", font=("TkDefaultFont", 9, "bold")).pack(
        side="left", padx=(2, 5)
    )

    self.combo_card = ttk.Combobox(
        inj_frame, values=[], state="readonly", width=25
    )
    self.combo_card.pack(side="left", padx=5)

    tk.Button(
        inj_frame,
        text="🔒 Lock/Unlock",
        bg="#E1BEE7",
        command=self.toggle_card_lock,
    ).pack(side="left", padx=(10, 2))

    tk.Label(
        inj_frame, text="Sort By:", font=("TkDefaultFont", 9, "bold")
    ).pack(side="left", padx=(20, 2))
    self.combo_card_sort = ttk.Combobox(
        inj_frame,
        values=[
            "Name (A-Z)",
            "Name (Z-A)",
            "Rank (S->B)",
            "Rank (B->S)",
            "Chapter (Low->High)",
            "Chapter (High->Low)",
            "Status (Unlocked First)",
            "Status (Locked First)",
            "Star Rank (High->Low)",
            "Star Rank (Low->High)",
            "Quantity (High->Low)",
            "Quantity (Low->High)",
        ],
        state="readonly",
        width=22,
    )
    self.combo_card_sort.set("Name (A-Z)")
    self.combo_card_sort.bind(
        "<<ComboboxSelected>>", lambda e: self.refresh_cards_view()
    )
    self.combo_card_sort.pack(side="left", padx=5)

    self.card_console = DarkConsoleView(tab)
    self.card_console.pack(fill="both", expand=True, padx=10, pady=5)

  def toggle_card_lock(self):
    card_name = self.combo_card.get()
    if not card_name or card_name == "(No Cards)":
      return

    card_info = {}
    if hasattr(cards, "CARD_LOOKUP"):
      card_info = cards.CARD_LOOKUP.get(card_name, {})
    rank = card_info.get("rank", "B")

    if "inventory_cards" not in self.state:
      self.state["inventory_cards"] = {}

    starter_cards = ["Refleczer", "Metall C-15", "Ball De Voux", "Dig Labour"]
    is_starter = card_name in starter_cards

    if card_name not in self.state["inventory_cards"]:
      self.state["inventory_cards"][card_name] = {
          "count": 1,
          "stars": 1,
          "rank": rank,
          "unlocked": not is_starter,
      }
    else:
      status = self.state["inventory_cards"][card_name].get(
          "unlocked", is_starter
      )
      self.state["inventory_cards"][card_name]["unlocked"] = not status

    self.save_game()
    self.refresh_cards_view()

  def refresh_cards_view(self):
    self.card_console.clear()

    card_items_dict = {}
    if "inventory_cards" in self.state:
      card_items_dict.update(self.state["inventory_cards"])

    for name, data in self.state.get("inventory_chips", {}).items():
      if isinstance(data, dict) and data.get("type", "").lower() == "card":
        card_items_dict[name] = data

    active_card_names = sorted(list(card_items_dict.keys()))

    if hasattr(self, "combo_card"):
      self.combo_card["values"] = active_card_names
      curr_sel = self.combo_card.get()
      if active_card_names:
        if curr_sel not in active_card_names:
          self.combo_card.set(active_card_names[0])
      else:
        self.combo_card.set("(No Cards)")

    card_items = []
    for name, data in card_items_dict.items():
      rank = data.get("rank", "B")
      count = data.get("count", 1)
      stars = data.get("stars", 1)

      starter_cards = ["Refleczer", "Metall C-15", "Ball De Voux", "Dig Labour"]
      default_unlocked = True if name in starter_cards else False
      is_unlocked = data.get("unlocked", default_unlocked)

      chap = 1
      if hasattr(cards, "CARD_LOOKUP"):
        info = cards.CARD_LOOKUP.get(name, {})
        chap = info.get("chapter", 1) if isinstance(info, dict) else 1

      card_items.append((name, rank, stars, count, is_unlocked, chap))

    sort_val = (
        self.combo_card_sort.get()
        if hasattr(self, "combo_card_sort")
        else "Name (A-Z)"
    )
    rank_order = {"S": 0, "A": 1, "B": 2}
    rank_order_rev = {"B": 0, "A": 1, "S": 2}

    if sort_val == "Name (A-Z)":
      card_items.sort(key=lambda x: x[0])
    elif sort_val == "Name (Z-A)":
      card_items.sort(key=lambda x: x[0], reverse=True)
    elif sort_val == "Rank (S->B)":
      card_items.sort(key=lambda x: (rank_order.get(x[1], 3), x[0]))
    elif sort_val == "Rank (B->S)":
      card_items.sort(key=lambda x: (rank_order_rev.get(x[1], 3), x[0]))
    elif sort_val == "Chapter (Low->High)":
      card_items.sort(key=lambda x: (x[5], x[0]))
    elif sort_val == "Chapter (High->Low)":
      card_items.sort(key=lambda x: (x[5], x[0]), reverse=True)
    elif sort_val == "Status (Unlocked First)":
      card_items.sort(key=lambda x: (0 if x[4] else 1, x[0]))
    elif sort_val == "Status (Locked First)":
      card_items.sort(key=lambda x: (1 if x[4] else 0, x[0]))
    elif sort_val == "Star Rank (High->Low)":
      card_items.sort(key=lambda x: (x[2], x[0]), reverse=True)
    elif sort_val == "Star Rank (Low->High)":
      card_items.sort(key=lambda x: (x[2], x[0]))
    elif sort_val == "Quantity (High->Low)":
      card_items.sort(key=lambda x: (x[3], x[0]), reverse=True)
    elif sort_val == "Quantity (Low->High)":
      card_items.sort(key=lambda x: (x[3], x[0]))

    if not card_items:
      self.card_console.insert_line("=== No cards currently available ===")
      return

    for name, rank, stars, count, is_unlocked, chap in card_items:
      status_str = "UNLOCKED" if is_unlocked else "LOCKED"
      line = (
          f"[{rank}-Rank] {name:<26} | Ch. {chap:<2} | Status: {status_str:<8}"
          f" | Star Rank: ({stars}★) | Quantity: x{count}"
      )
      self.card_console.insert_line(line)

  # --- TAB 7: ARMOR GEAR ---
  def setup_tab_armor(self):
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text="Armor Gear")

    inj_frame = tk.LabelFrame(tab, text=" Armor Gear Manager ", padx=10, pady=5)
    inj_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(inj_frame, text="Armor:", font=("TkDefaultFont", 9, "bold")).pack(
        side="left", padx=(2, 5)
    )

    self.combo_armor = ttk.Combobox(
        inj_frame, values=[], state="readonly", width=25
    )
    self.combo_armor.pack(side="left", padx=5)

    tk.Button(
        inj_frame,
        text="🔒 Lock/Unlock",
        bg="#E1BEE7",
        command=self.toggle_armor_lock,
    ).pack(side="left", padx=(10, 2))

    tk.Button(
        inj_frame,
        text="🔨 Craft",
        bg="#FFD700",
        command=self.craft_armor_ui,
    ).pack(side="left", padx=(5, 2))

    tk.Label(
        inj_frame, text="Sort By:", font=("TkDefaultFont", 9, "bold")
    ).pack(side="left", padx=(20, 2))
    self.combo_armor_sort = ttk.Combobox(
        inj_frame,
        values=[
            "Name (A-Z)",
            "Name (Z-A)",
            "Rank (S->B)",
            "Rank (B->S)",
            "Chapter (Low->High)",
            "Chapter (High->Low)",
            "Status (Unlocked First)",
            "Status (Locked First)",
            "Status (Crafted First)",
            "Star Rank (High->Low)",
            "Star Rank (Low->High)",
            "Duplicates (High->Low)",
            "Duplicates (Low->High)",
        ],
        state="readonly",
        width=22,
    )
    self.combo_armor_sort.set("Name (A-Z)")
    self.combo_armor_sort.bind(
        "<<ComboboxSelected>>", lambda e: self.refresh_armor_view()
    )
    self.combo_armor_sort.pack(side="left", padx=5)

    self.armor_console = DarkConsoleView(tab)
    self.armor_console.pack(fill="both", expand=True, padx=10, pady=5)

  def toggle_armor_lock(self):
    armor_name = self.combo_armor.get()
    if not armor_name or armor_name == "(No Armor)":
      return

    armor_info = {}
    if hasattr(armor, "ARMOR_LOOKUP"):
      armor_info = armor.ARMOR_LOOKUP.get(armor_name, {})
    rank = armor_info.get("rank", "B")

    if armor_name not in self.state["inventory_armor"]:
      self.state["inventory_armor"][armor_name] = {
          "count": 1,
          "stars": 1,
          "rank": rank,
          "unlocked": True,
      }
    else:
      status = self.state["inventory_armor"][armor_name].get("unlocked", False)
      self.state["inventory_armor"][armor_name]["unlocked"] = not status

    self.save_game()
    self.refresh_armor_view()

  def craft_armor_ui(self):
    armor_name = self.combo_armor.get()
    if not armor_name or armor_name == "(No Armor)":
      return

    if hasattr(armor, "craft_armor"):
      success, msg = armor.craft_armor(armor_name, self.state)
      if success:
        messagebox.showinfo("Armor Crafting", msg)
      else:
        messagebox.showwarning("Crafting Failed", msg)
    else:
      armor_inv = self.state.get("inventory_armor", {})
      armor_data = armor_inv.get(armor_name)
      if not armor_data:
        messagebox.showwarning("Crafting Failed", f"'{armor_name}' is not in your inventory.")
        return

      if armor_data.get("crafted", False):
        messagebox.showinfo("Armor Crafting", f"'{armor_name}' is already crafted!")
        return

      rank = armor_data.get("rank", "B")
      stars = armor_data.get("stars", 1)
      if rank != "S" or stars < 3:
        messagebox.showwarning(
            "Crafting Failed",
            f"'{armor_name}' cannot be crafted yet! Must reach S-Tier and 3-Star rank (Current: {rank}-Tier, {stars}★)."
        )
        return

      lookup = getattr(armor, "ARMOR_LOOKUP", {}).get(armor_name, {})
      req_level = lookup.get("level", armor_data.get("item_lv", 1))
      player_level = self.state.get("player_level", 1)
      if player_level < req_level:
        messagebox.showwarning(
            "Crafting Failed",
            f"'{armor_name}' requires Player Level {req_level} to craft (Current Level: {player_level})."
        )
        return

      armor_data["crafted"] = True
      armor_data["unlocked"] = True
      messagebox.showinfo(
          "Armor Crafting", f"Successfully crafted '{armor_name}'!"
      )

    self.save_game()
    self.refresh_armor_view()

  def refresh_armor_view(self):
    self.armor_console.clear()

    armor_dict = self.state.get("inventory_armor", {})
    active_armor_names = sorted(list(armor_dict.keys()))

    if hasattr(self, "combo_armor"):
      self.combo_armor["values"] = active_armor_names
      curr_sel = self.combo_armor.get()
      if active_armor_names:
        if curr_sel not in active_armor_names:
          self.combo_armor.set(active_armor_names[0])
      else:
        self.combo_armor.set("(No Armor)")

    armor_items = []
    notified_any = False
    for name, data in armor_dict.items():
      rank = data.get("rank", "B")
      stars = data.get("stars", 1)
      count = data.get("count", 0)
      is_unlocked = data.get("unlocked", False)
      is_crafted = data.get("crafted", False)

      # Check for S-Rank and 3-Star crafting milestone
      if rank == "S" and stars >= 3 and not data.get("craft_notified", False):
        messagebox.showinfo(
            "Crafting Available",
            f"'{name}' has reached S-Rank and 3-Stars (100%) and can now be crafted!",
        )
        data["craft_notified"] = True
        notified_any = True

      chap = 1
      item_lv = data.get("item_lv", 1)
      if hasattr(armor, "ARMOR_LOOKUP"):
        info = armor.ARMOR_LOOKUP.get(name, {})
        chap = info.get("chapter", 1)
        item_lv = data.get("item_lv", info.get("item_lv", info.get("level", 1)))

      armor_items.append(
          (name, rank, stars, count, is_unlocked, is_crafted, chap, item_lv)
      )

    if notified_any:
      self.save_game()

    sort_val = (
        self.combo_armor_sort.get()
        if hasattr(self, "combo_armor_sort")
        else "Name (A-Z)"
    )
    rank_order = {"S": 0, "A": 1, "B": 2}
    rank_order_rev = {"B": 0, "A": 1, "S": 2}

    if sort_val == "Name (A-Z)":
      armor_items.sort(key=lambda x: x[0])
    elif sort_val == "Name (Z-A)":
      armor_items.sort(key=lambda x: x[0], reverse=True)
    elif sort_val == "Rank (S->B)":
      armor_items.sort(key=lambda x: (rank_order.get(x[1], 3), x[0]))
    elif sort_val == "Rank (B->S)":
      armor_items.sort(key=lambda x: (rank_order_rev.get(x[1], 3), x[0]))
    elif sort_val == "Chapter (Low->High)":
      armor_items.sort(key=lambda x: (x[6], x[0]))
    elif sort_val == "Chapter (High->Low)":
      armor_items.sort(key=lambda x: (x[6], x[0]), reverse=True)
    elif sort_val == "Status (Unlocked First)":
      armor_items.sort(key=lambda x: (0 if x[4] else 1, x[0]))
    elif sort_val == "Status (Locked First)":
      armor_items.sort(key=lambda x: (1 if x[4] else 0, x[0]))
    elif sort_val == "Status (Crafted First)":
      armor_items.sort(key=lambda x: (0 if x[5] else 1, x[0]))
    elif sort_val == "Star Rank (High->Low)":
      armor_items.sort(key=lambda x: (x[2], x[0]), reverse=True)
    elif sort_val == "Star Rank (Low->High)":
      armor_items.sort(key=lambda x: (x[2], x[0]))
    elif sort_val == "Duplicates (High->Low)":
      armor_items.sort(key=lambda x: (x[3], x[0]), reverse=True)
    elif sort_val == "Duplicates (Low->High)":
      armor_items.sort(key=lambda x: (x[3], x[0]))

    if not armor_items:
      self.armor_console.insert_line("=== No armor gear currently available ===")
      return

    for (
        name,
        rank,
        stars,
        count,
        is_unlocked,
        is_crafted,
        chap,
        item_lv,
    ) in armor_items:
      if is_crafted:
        status_str = "CRAFTED"
      elif is_unlocked:
        status_str = "UNLOCKED"
      else:
        status_str = "LOCKED"
      line = (
          f"[{rank}-Rank] {name:<26} | Ch. {chap:<2} | Item Lv: {item_lv:<3} |"
          f" Status: {status_str:<8} | Star Rank: ({stars}★) | Duplicates:"
          f" x{count}"
      )
      self.armor_console.insert_line(line)

  # --- HELPERS ---
  def adjust_wallet(self, key, is_add):
    try:
      val = int(self.ent_modify_amount.get())
    except ValueError:
      val = 10000

    if not is_add:
      val = -val

    self.state[key] = max(0, self.state.get(key, 0) + val)
    self.save_game()
    self.refresh_all_views()

  def reset_profile(self):
    if messagebox.askyesno(
        "Confirm Reset",
        "Are you sure you want to completely reset your profile and save file"
        " to default state?",
    ):
      self.state = self.get_default_state()

      self.gacha_engine.pity_a = 0
      self.gacha_engine.pity_s = 0

      if hasattr(self, "spin_player_level"):
        self.spin_player_level.set(1)
      if hasattr(self, "combo_chapter"):
        self.combo_chapter.set("1")
      if hasattr(self, "spin_stage_chap"):
        self.spin_stage_chap.set(1)

      if hasattr(self, "stage_console"):
        self.stage_console.clear()

      for slot in self.drop_slots:
        slot.config(text="- Empty Drop Slot -", fg="#888888")

      self.save_game()
      self.refresh_all_views()
      messagebox.showinfo(
          "Reset Complete",
          "Profile and save data have been reset to default state.",
      )

  def on_level_changed(self, event=None):
    try:
      val = int(self.spin_player_level.get())
      val = max(1, min(200, val))
    except ValueError:
      val = self.state.get("player_level", 1)
    self.state["player_level"] = val
    self.spin_player_level.set(str(val))
    self.save_game()

  def on_chapter_changed(self, event):
    self.state["current_chapter"] = int(self.combo_chapter.get())
    if hasattr(self, "spin_stage_chap"):
      self.spin_stage_chap.set(self.state["current_chapter"])
      self.refresh_stages_view()
    self.save_game()

  def refresh_all_views(self):
    if hasattr(self, "spin_player_level"):
      self.spin_player_level.set(str(self.state.get("player_level", 1)))
    self.lbl_element.config(text=f"Element: {self.state['element']}")
    self.lbl_bolts.config(text=f"B-Bolts: {self.state['bolts']}")
    self.lbl_a_bolts.config(text=f"A-Bolts: {self.state['a_bolts']}")
    self.lbl_s_bolts.config(text=f"S-Bolts: {self.state.get('s_bolts', 0)}")
    self.lbl_patches.config(
        text=f"Character Patches: {self.state['memory_patches']}"
    )
    self.lbl_weapon_patches.config(
        text=f"Weapon Patches: {self.state.get('weapon_patches', 0)}"
    )

    self.refresh_stages_view()
    self.refresh_chars_view()
    self.refresh_weapons_view()
    self.refresh_chips_view()
    self.refresh_cards_view()
    self.refresh_armor_view()


if __name__ == "__main__":
  try:
    app = MegamanXDiVEApp()
    app.mainloop()
  except Exception as e:
    import traceback
    import tkinter as tk
    from tkinter import messagebox

    err_details = traceback.format_exc()
    print(err_details)

    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Startup Error Crash Log",
        f"Application failed to launch:\n\n{err_details}",
    )