#!/usr/bin/env python3
"""
Pokemon Gen 1 Team Optimizer — Evolutionary Algorithm
======================================================
Genotype  : Permutation of 6 species IDs (from ~151 available)
Phenotype : Fully built Gen-1 Pokemon team with heuristic-selected moves
Mutation  : Swap two positions in the team
Recombine : Cut-and-crossfill (order-preserving)
Selection : Tournament (parent) + µ+λ (survivor)
Fitness   : Win Rate + Avg Remaining HP Ratio (max ≈ 2.0)
"""

import json
import math
import copy
import random
import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# DATA LOADING  (all JSON files sit alongside this script)
# ──────────────────────────────────────────────────────────────

HERE = Path(__file__).parent


def _load(name: str):
    with open(HERE / name) as fh:
        return json.load(fh)


constraints     = _load("data.json")           # species → {level, moves, ...}
move_types      = _load("moveTypes.json")       # move → Type string
move_categories = _load("moveCategories.json")  # move → Physical/Special/Status
species_names   = _load("speciesNames.json")    # species → display name
species_types   = _load("speciesTypes.json")    # species → [Type, ...]
species_base_hp = _load("speciesBaseHp.json")   # species → base HP int
type_chart_score= _load("typeChartScore.json")  # defenderType → attackType → exponent

ALL_SPECIES = list(constraints.keys())          # ~151 species

# ──────────────────────────────────────────────────────────────
# STATIC GAME DATA
# ──────────────────────────────────────────────────────────────

# Gen-1 base stats: (Atk, Def, Spe, Spc)  — used for damage calculations
BASE_STATS: dict[str, tuple[int, int, int, int]] = {
    "bulbasaur":   (49,  49, 45,  65), "ivysaur":    (62,  63, 60,  80),
    "venusaur":    (82,  83, 80, 100), "charmander":  (52,  43, 65,  50),
    "charmeleon":  (64,  58, 80,  65), "charizard":   (84,  78,100,  85),
    "squirtle":    (48,  65, 43,  50), "wartortle":   (63,  80, 58,  65),
    "blastoise":   (83, 100, 78,  85), "butterfree":  (45,  50, 70,  90),
    "beedrill":    (90,  40, 75,  45), "pidgey":      (45,  40, 56,  35),
    "pidgeotto":   (60,  55, 71,  50), "pidgeot":     (80,  75,101,  70),
    "rattata":     (56,  35, 72,  25), "raticate":    (81,  60, 97,  50),
    "spearow":     (60,  30, 70,  31), "fearow":      (90,  65,100,  61),
    "ekans":       (60,  44, 55,  40), "arbok":       (95,  69, 80,  65),
    "pikachu":     (55,  40, 90,  50), "raichu":      (90,  55,110,  90),
    "sandshrew":   (75,  85, 40,  30), "sandslash":   (100,110, 65,  55),
    "nidoranf":    (47,  52, 41,  40), "nidorina":    (62,  67, 56,  55),
    "nidoqueen":   (92,  87, 76,  75), "nidoranm":    (57,  40, 50,  40),
    "nidorino":    (72,  57, 65,  55), "nidoking":    (102, 77, 85,  75),
    "clefairy":    (45,  48, 35,  60), "clefable":    (70,  73, 60,  85),
    "vulpix":      (41,  40, 65,  65), "ninetales":   (76,  75,100, 100),
    "jigglypuff":  (45,  20, 20,  25), "wigglytuff":  (70,  45, 45,  50),
    "zubat":       (45,  35, 55,  40), "golbat":      (80,  70, 90,  75),
    "oddish":      (50,  55, 30,  75), "gloom":       (65,  70, 40,  85),
    "vileplume":   (80,  85, 50, 100), "paras":       (70,  55, 25,  55),
    "parasect":    (95,  80, 30,  80), "venonat":     (55,  50, 45,  40),
    "venomoth":    (65,  60, 90,  90), "diglett":     (55,  25, 95,  45),
    "dugtrio":     (80,  50,120,  70), "meowth":      (45,  35, 90,  40),
    "persian":     (70,  60,115,  65), "psyduck":     (52,  48, 55,  50),
    "golduck":     (82,  78, 85,  80), "mankey":      (80,  35, 70,  35),
    "primeape":    (105, 60, 95,  60), "growlithe":   (70,  45, 60,  50),
    "arcanine":    (110, 80, 95,  80), "poliwag":     (50,  40, 90,  40),
    "poliwhirl":   (65,  65, 90,  50), "poliwrath":   (95,  95, 70,  70),
    "abra":        (20,  15, 90, 105), "kadabra":     (35,  30,105, 120),
    "alakazam":    (50,  45,120, 135), "machop":      (80,  50, 35,  35),
    "machoke":     (100, 70, 45,  50), "machamp":     (130, 80, 55,  65),
    "bellsprout":  (75,  35, 40,  70), "weepinbell":  (90,  50, 55,  85),
    "victreebel":  (105, 65, 70, 100), "tentacool":   (40,  35, 70, 100),
    "tentacruel":  (70,  65,100, 120), "geodude":     (80, 100, 20,  30),
    "graveler":    (95, 115, 35,  45), "golem":       (120,130, 45,  55),
    "ponyta":      (85,  55, 90,  65), "rapidash":    (100, 70,105,  80),
    "slowpoke":    (65,  65, 15,  40), "slowbro":     (75, 110, 30,  80),
    "magnemite":   (35,  70, 45,  95), "magneton":    (60,  95, 70, 120),
    "farfetchd":   (65,  55, 60,  58), "doduo":       (85,  45, 75,  35),
    "dodrio":      (110, 70,100,  60), "seel":        (45,  55, 45,  70),
    "dewgong":     (70,  80, 70,  95), "grimer":      (80,  50, 25,  40),
    "muk":         (105, 75, 50,  65), "shellder":    (65, 100, 40,  45),
    "cloyster":    (95, 180, 70,  85), "gastly":      (35,  30, 80, 100),
    "haunter":     (50,  45, 95, 115), "gengar":      (65,  60,110, 130),
    "onix":        (45, 160, 70,  30), "drowzee":     (48,  45, 42,  90),
    "hypno":       (73,  70, 67, 115), "krabby":      (105, 90, 50,  25),
    "kingler":     (130,115, 75,  50), "voltorb":     (30,  50,100,  55),
    "electrode":   (50,  70,140,  80), "exeggcute":   (40,  80, 40,  60),
    "exeggutor":   (95,  85, 55, 125), "cubone":      (50,  95, 35,  40),
    "marowak":     (80, 110, 45,  50), "hitmonlee":   (120, 53, 87,  35),
    "hitmonchan":  (105, 79, 76,  35), "lickitung":   (55,  75, 30,  60),
    "koffing":     (65,  95, 35,  60), "weezing":     (90, 120, 60,  85),
    "rhyhorn":     (85,  95, 25,  30), "rhydon":      (130,120, 40,  45),
    "chansey":     (5,    5, 30, 105), "tangela":     (55, 115, 60, 100),
    "kangaskhan":  (95,  80, 90,  40), "horsea":      (40,  70, 60,  70),
    "seadra":      (65,  95, 85,  95), "goldeen":     (67,  60, 63,  50),
    "seaking":     (92,  65, 68,  65), "staryu":      (45,  55, 85,  70),
    "starmie":     (75,  85,115, 100), "mrmime":      (45,  65, 90, 100),
    "scyther":     (110, 80,105,  55), "jynx":        (50,  35, 95,  95),
    "electabuzz":  (83,  57,105,  85), "magmar":      (95,  57, 93,  85),
    "pinsir":      (125,100, 85,  55), "tauros":      (100, 95,110,  70),
    "gyarados":    (125, 79, 81, 100), "lapras":      (85,  80, 60,  95),
    "ditto":       (48,  48, 48,  48), "eevee":       (55,  50, 55,  65),
    "vaporeon":    (65,  60, 65, 110), "jolteon":     (65,  60,130, 110),
    "flareon":     (130, 60, 65, 110), "porygon":     (60,  70, 40,  75),
    "omanyte":     (40, 100, 35,  90), "omastar":     (60, 125, 55, 115),
    "kabuto":      (80,  90, 55,  45), "kabutops":    (115,105, 80,  70),
    "aerodactyl":  (105, 65,130,  60), "snorlax":     (110, 65, 30,  65),
    "articuno":    (85, 100, 85, 125), "zapdos":      (90,  85,100, 125),
    "moltres":     (100, 90, 90, 125), "dratini":     (64,  45, 50,  50),
    "dragonair":   (84,  65, 70,  70), "dragonite":   (134, 95, 80, 100),
    "mewtwo":      (110, 90,130, 154), "mew":         (100,100,100, 100),
}

# Move base power (0 = special mechanic or status)
MOVE_POWER: dict[str, int] = {
    "bodyslam": 85,  "razorleaf": 55,  "hyperbeam": 150, "slash": 70,
    "fireblast": 120,"submission": 80, "earthquake": 100,"blizzard": 120,
    "hydropump": 110,"surf": 95,       "psychic": 90,    "doubleedge": 100,
    "megadrain": 40, "twineedle": 25,  "quickattack": 40,"skyattack": 140,
    "thunderbolt": 95,"drillpeck": 80, "rockslide": 75,  "thunder": 120,
    "doublekick": 30,"bubblebeam": 65, "flamethrower": 95,"wingattack": 35,
    "lowkick": 50,   "megakick": 120,  "explosion": 250, "stomp": 65,
    "sludge": 65,    "crabhammer": 90, "takedown": 90,   "highjumpkick": 85,
    "rollingkick": 60,"icebeam": 95,   "pinmissile": 14, "triattack": 80,
    "selfdestruct": 200,
    # Special-mechanic moves (handled separately, power listed as 0)
    "seismictoss": 0, "nightshade": 0, "superfang": 0, "counter": 0,
}

# Move accuracy (probability of hitting, 1.0 = always)
MOVE_ACCURACY: dict[str, float] = {
    "bodyslam": 1.00, "razorleaf": 0.95, "hyperbeam": 0.90, "slash": 1.00,
    "fireblast": 0.85,"submission": 0.80,"earthquake": 1.00,"blizzard": 0.90,
    "hydropump": 0.80,"surf": 1.00,      "psychic": 1.00,   "doubleedge": 1.00,
    "megadrain": 1.00,"twineedle": 1.00, "quickattack": 1.00,"skyattack": 0.90,
    "thunderbolt":1.00,"drillpeck": 1.00,"rockslide": 0.90, "thunder": 0.70,
    "doublekick": 1.00,"bubblebeam":1.00,"flamethrower":1.00,"wingattack": 1.00,
    "lowkick": 0.90,  "megakick": 0.75, "explosion": 1.00, "stomp": 1.00,
    "sludge": 1.00,   "crabhammer": 0.85,"takedown": 0.85, "highjumpkick": 0.90,
    "rollingkick":0.85,"icebeam": 1.00,  "pinmissile": 0.85,"triattack": 1.00,
    "selfdestruct":1.00,"seismictoss":1.00,"nightshade":1.00,"superfang": 0.90,
    "counter": 1.00,
    # Status moves
    "sleeppowder":0.75,"stunspore": 0.75,"thunderwave":1.00,"spore": 1.00,
    "glare": 0.75,    "confuseray": 1.00,"sing": 0.55,     "lovelykiss":0.75,
    "hypnosis": 0.60, "agility": 1.00,  "swordsdance":1.00,"amnesia": 1.00,
    "meditate": 1.00, "reflect": 1.00,  "recover": 1.00,  "softboiled":1.00,
    "rest": 1.00,     "substitute":1.00,"smokescreen":1.00,"sandattack":1.00,
    "leer": 1.00,     "tailwhip": 1.00, "acidarmor": 1.00,"mimic": 1.00,
    "mirrormove":1.00,"transform": 1.00,
}

# Moves that inflict a primary status on the target
STATUS_MOVES: dict[str, str] = {
    "sleeppowder": "sleep",  "spore":    "sleep",  "sing":   "sleep",
    "lovelykiss":  "sleep",  "hypnosis": "sleep",
    "stunspore":   "paralyze","thunderwave":"paralyze","glare": "paralyze",
    "confuseray":  "confuse",
}

# Moves with secondary effect chances: move → (status, probability)
MOVE_SECONDARY: dict[str, tuple[str, float]] = {
    "bodyslam":    ("paralyze", 0.30),
    "thunderbolt": ("paralyze", 0.10),
    "thunder":     ("paralyze", 0.10),
    "blizzard":    ("freeze",   0.10),
    "icebeam":     ("freeze",   0.10),
    "fireblast":   ("burn",     0.30),
    "flamethrower":("burn",     0.10),
    "sludge":      ("poison",   0.40),
    "twineedle":   ("poison",   0.20),
    "stomp":       ("flinch",   0.30),
    "rockslide":   ("flinch",   0.30),
}

# ──────────────────────────────────────────────────────────────
# TYPE EFFECTIVENESS
# ──────────────────────────────────────────────────────────────

def type_multiplier(attack_type: str, defender_types: list[str]) -> float:
    """Return the combined type-effectiveness multiplier (uses loaded type chart)."""
    mult = 1.0
    for dt in defender_types:
        score = type_chart_score.get(dt, {}).get(attack_type, 0)
        if score == 1:
            mult *= 2.0
        elif score == -1:
            mult *= 0.5
        elif score <= -4:
            return 0.0
    return mult

# ──────────────────────────────────────────────────────────────
# GEN-1 STAT FORMULAS
# ──────────────────────────────────────────────────────────────

def _hp_formula(base: int, level: int, iv: int = 30) -> int:
    return math.floor((base + iv) * 2 * level / 100) + level + 10

def _stat_formula(base: int, level: int, iv: int = 30) -> int:
    return math.floor((base + iv) * 2 * level / 100) + 5

_STAGE_TABLE = {
    -6: 2/8, -5: 2/7, -4: 2/6, -3: 2/5, -2: 2/4, -1: 2/3,
     0: 1.0,
     1: 3/2,  2: 4/2,  3: 5/2,  4: 6/2,  5: 7/2,  6: 8/2,
}

def stage_mult(stage: int) -> float:
    return _STAGE_TABLE[max(-6, min(6, stage))]

# ──────────────────────────────────────────────────────────────
# POKEMON OBJECT
# ──────────────────────────────────────────────────────────────

def build_pokemon(species_id: str, moves: list[str]) -> dict:
    """Construct a mutable Pokemon battle dict."""
    data   = constraints[species_id]
    level  = data.get("level", 100)
    bhp    = species_base_hp[species_id]
    batk, bdef, bspe, bspc = BASE_STATS.get(species_id, (75, 75, 75, 75))

    hp  = _hp_formula(bhp,  level)
    atk = _stat_formula(batk, level)
    dfn = _stat_formula(bdef, level)
    spe = _stat_formula(bspe, level)
    spc = _stat_formula(bspc, level)

    # Mirror Showdown's EV heuristic: lower Atk IVs when all moves are non-physical
    all_non_phys = all(move_categories.get(m) != "Physical" for m in moves)
    if all_non_phys:
        atk = _stat_formula(batk, level, iv=2)

    return {
        "species":     species_id,
        "level":       level,
        "max_hp":      hp,
        "hp":          hp,
        "atk":         atk,
        "def":         dfn,
        "spe":         spe,
        "spc":         spc,
        "moves":       list(moves),
        # Status: None | "sleep" | "paralyze" | "poison" | "burn" | "freeze" | "confuse"
        "status":      None,
        "sleep_turns": 0,
        # Stat stages
        "atk_st":  0,  "def_st":  0,
        "spe_st":  0,  "spc_st":  0,
        "fainted": False,
    }

def _eff_stat(base: int, stage: int, status_penalty: float = 1.0) -> float:
    return base * stage_mult(stage) * status_penalty

def eff_spe(p: dict) -> float:
    penalty = 0.25 if p["status"] == "paralyze" else 1.0
    return _eff_stat(p["spe"], p["spe_st"], penalty)

# ──────────────────────────────────────────────────────────────
# MOVE SELECTION HEURISTIC (ported from teamFromGenome6.mjs)
# ──────────────────────────────────────────────────────────────

def _sum_exponents(attack_type: str, defender_types: list[str]) -> int:
    total = 0
    for dt in defender_types:
        total += type_chart_score.get(dt, {}).get(attack_type, 0)
    return total

def _best_move_eff(move_type: str, opp_ids: list[str]) -> tuple[int, int]:
    best_exp, n_super = float("-inf"), 0
    for sid in opp_ids:
        dtypes = species_types.get(sid, [])
        if not dtypes:
            continue
        exp = _sum_exponents(move_type, dtypes)
        if exp > best_exp:
            best_exp = exp
        if exp > 0:
            n_super += 1
    return (0 if best_exp == float("-inf") else best_exp), n_super

def select_moves(species_id: str, opp_ids: list[str]) -> list[str]:
    """
    Deterministic heuristic move selection (mirrors JS teamFromGenome6.mjs).
    Prefers moves super-effective vs. opponent types; diversifies move types.
    """
    data  = constraints[species_id]
    seen: set[str] = set()
    pool: list[str] = []
    for m in (data.get("moves", []) + data.get("comboMoves", []) +
              data.get("essentialMoves", []) + data.get("exclusiveMoves", [])):
        if m not in seen:
            seen.add(m)
            pool.append(m)

    scores: dict[str, float] = {}
    for m in pool:
        mt = move_types.get(m)
        if not mt:
            scores[m] = 0.0
            continue
        best_exp, n_super = _best_move_eff(mt, opp_ids)
        scores[m] = best_exp * 1000 + n_super * 10

    candidates = sorted(
        [(m, scores.get(m, 0.0), move_types.get(m, "Normal")) for m in pool],
        key=lambda x: (-x[1], x[0]),
    )

    selected: list[str] = []
    sel_types: set[str]  = set()

    while len(selected) < 4:
        best_idx, best_adj = -1, float("-inf")
        for i, (mid, sc, mt) in enumerate(candidates):
            if mid in selected:
                continue
            adj = sc - (50 if mt in sel_types else 0)
            if adj > best_adj:
                best_adj, best_idx = adj, i
        if best_idx == -1:
            break
        mid, _, mt = candidates[best_idx]
        selected.append(mid)
        sel_types.add(mt)

    # Safety fill — should not normally be needed
    for m in pool:
        if len(selected) >= 4:
            break
        if m not in selected:
            selected.append(m)

    return selected[:4]

# ──────────────────────────────────────────────────────────────
# BATTLE SIMULATOR
# ──────────────────────────────────────────────────────────────

def _calc_damage(attacker: dict, move_id: str, defender: dict) -> int:
    """Standard Gen-1 damage formula."""
    category = move_categories.get(move_id, "Physical")
    move_type = move_types.get(move_id, "Normal")
    power     = MOVE_POWER.get(move_id, 0)

    if power == 0:
        return 0

    # Attack / defence stat to use
    if category == "Physical":
        raw_atk = attacker["atk"] * stage_mult(attacker["atk_st"])
        raw_def = defender["def"] * stage_mult(defender["def_st"])
        # Burn halves physical attack
        if attacker["status"] == "burn":
            raw_atk /= 2
    else:
        raw_atk = attacker["spc"] * stage_mult(attacker["spc_st"])
        raw_def = defender["spc"] * stage_mult(defender["spc_st"])

    # STAB
    stab = 1.5 if move_type in species_types.get(attacker["species"], []) else 1.0

    # Type effectiveness
    eff = type_multiplier(move_type, species_types.get(defender["species"], ["Normal"]))
    if eff == 0:
        return 0

    # Core Gen-1 formula
    dmg  = ((2 * attacker["level"] / 5 + 2) * power * raw_atk / max(1, raw_def)) / 50 + 2
    dmg *= stab * eff

    # Random roll 85–100 %
    r = 0.85 + random.random() * 0.15
    return max(1, int(dmg * r))


def _pick_move(attacker: dict, defender: dict) -> str | None:
    """
    Simple greedy move picker:
    - Prefer attacking moves with highest expected damage (type-effective × power × accuracy × STAB).
    - Fall back to status/setup moves if no attacking option exists.
    """
    def_types = species_types.get(defender["species"], ["Normal"])
    best_move, best_val = None, -1.0

    for m in attacker["moves"]:
        cat = move_categories.get(m, "Physical")
        if cat == "Status":
            continue
        pw = MOVE_POWER.get(m, 0)
        if pw == 0:
            # Special-mechanic moves: give them a fixed appeal
            best_move = best_move or m
            continue
        mt  = move_types.get(m, "Normal")
        eff = type_multiplier(mt, def_types)
        stab= 1.5 if mt in species_types.get(attacker["species"], []) else 1.0
        val = pw * eff * stab * MOVE_ACCURACY.get(m, 1.0)
        if val > best_val:
            best_val, best_move = val, m

    # If no attacking move found, pick a useful setup move
    if best_move is None:
        for m in attacker["moves"]:
            if m in ("swordsdance", "amnesia", "agility", "recover",
                     "softboiled", "rest", "substitute"):
                return m
        best_move = attacker["moves"][0] if attacker["moves"] else None

    return best_move


def _use_move(attacker: dict, move_id: str, defender: dict) -> int:
    """
    Execute one move. Returns HP damage dealt to defender.
    Side-effects: modifies attacker/defender hp, status, stages, fainted.
    """
    # ── Pre-move status checks ────────────────────────────────
    if attacker["status"] == "sleep":
        if attacker["sleep_turns"] > 0:
            attacker["sleep_turns"] -= 1
            if attacker["sleep_turns"] == 0:
                attacker["status"] = None
        return 0

    if attacker["status"] == "freeze":
        # 20 % chance to thaw each turn (simplified)
        if random.random() < 0.20:
            attacker["status"] = None
        else:
            return 0

    if attacker["status"] == "paralyze":
        if random.random() < 0.25:   # fully paralysed
            return 0

    if attacker["status"] == "confuse":
        if random.random() < 0.50:   # hurt itself
            dmg = max(1, int(_calc_damage(attacker, "bodyslam", attacker) * 0.5))
            attacker["hp"] = max(0, attacker["hp"] - dmg)
            if attacker["hp"] == 0:
                attacker["fainted"] = True
            return 0

    # ── Accuracy roll ─────────────────────────────────────────
    if random.random() > MOVE_ACCURACY.get(move_id, 1.0):
        return 0   # missed

    cat = move_categories.get(move_id, "Physical")

    # ── Status moves ──────────────────────────────────────────
    if cat == "Status":
        # Stat-boost moves
        if move_id == "swordsdance":
            attacker["atk_st"] = min(6, attacker["atk_st"] + 2)
        elif move_id == "amnesia":
            attacker["spc_st"] = min(6, attacker["spc_st"] + 2)
        elif move_id == "agility":
            attacker["spe_st"] = min(6, attacker["spe_st"] + 2)
        elif move_id == "meditate":
            attacker["atk_st"] = min(6, attacker["atk_st"] + 1)
        elif move_id == "reflect":
            attacker["def_st"] = min(6, attacker["def_st"] + 2)
        elif move_id == "acidarmor":
            attacker["def_st"] = min(6, attacker["def_st"] + 2)
        elif move_id in ("leer", "tailwhip"):
            defender["def_st"] = max(-6, defender["def_st"] - 1)
        elif move_id == "sandattack":
            defender["spe_st"] = max(-6, defender["spe_st"] - 1)   # accuracy drop simplified as speed
        elif move_id in ("recover", "softboiled"):
            attacker["hp"] = min(attacker["max_hp"],
                                 attacker["hp"] + attacker["max_hp"] // 2)
        elif move_id == "rest":
            attacker["hp"]          = attacker["max_hp"]
            attacker["status"]      = "sleep"
            attacker["sleep_turns"] = 2
        elif move_id == "substitute":
            cost = attacker["max_hp"] // 4
            attacker["hp"] = max(0, attacker["hp"] - cost)
            if attacker["hp"] == 0:
                attacker["fainted"] = True
        elif move_id in STATUS_MOVES:
            tgt_status = STATUS_MOVES[move_id]
            if defender["status"] is None:
                defender["status"] = tgt_status
                if tgt_status == "sleep":
                    defender["sleep_turns"] = random.randint(1, 7)
        return 0

    # ── Special-mechanic damaging moves ───────────────────────
    dmg_dealt = 0

    if move_id in ("seismictoss", "nightshade"):
        dmg_dealt = attacker["level"]

    elif move_id == "superfang":
        dmg_dealt = max(1, defender["hp"] // 2)

    elif move_id == "counter":
        # Simplified: deal 2× attacker's current ATK as flat damage
        dmg_dealt = max(1, int(attacker["atk"] * 0.5))

    else:
        # ── Standard damage ───────────────────────────────────
        dmg_dealt = _calc_damage(attacker, move_id, defender)

        # Explosion / Self-destruct: user instantly faints
        if move_id in ("explosion", "selfdestruct"):
            attacker["hp"] = 0
            attacker["fainted"] = True
            dmg_dealt *= 2   # the moves hit harder when user faints

        # Recoil moves
        elif move_id in ("doubleedge", "submission", "takedown"):
            recoil = {"doubleedge": 0.25, "submission": 0.25, "takedown": 0.25}
            attacker["hp"] = max(0, attacker["hp"] - max(1, int(dmg_dealt * recoil[move_id])))
            if attacker["hp"] == 0:
                attacker["fainted"] = True

        # High Jump Kick crash
        elif move_id == "highjumpkick" and dmg_dealt == 0:
            attacker["hp"] = max(0, attacker["hp"] - attacker["max_hp"] // 8)
            if attacker["hp"] == 0:
                attacker["fainted"] = True

    # ── Apply damage to defender ──────────────────────────────
    defender["hp"] = max(0, defender["hp"] - dmg_dealt)
    if defender["hp"] == 0:
        defender["fainted"] = True

    # ── Secondary status effects ──────────────────────────────
    if move_id in MOVE_SECONDARY and not defender["fainted"]:
        eff_status, prob = MOVE_SECONDARY[move_id]
        if eff_status != "flinch" and random.random() < prob:
            if defender["status"] is None:
                defender["status"] = eff_status
                if eff_status == "sleep":
                    defender["sleep_turns"] = random.randint(1, 7)

    # ── End-of-turn residual damage (poison / burn) ───────────
    for victim in (attacker, defender):
        if victim["fainted"]:
            continue
        if victim["status"] in ("poison", "burn"):
            dot = max(1, victim["max_hp"] // 16)
            victim["hp"] = max(0, victim["hp"] - dot)
            if victim["hp"] == 0:
                victim["fainted"] = True

    return dmg_dealt


def simulate_battle(team1: list[dict], team2: list[dict]) -> tuple[bool, float]:
    """
    Simulate a Gen-1 battle: no switching, order matters.

    Returns
    -------
    (team1_wins, hp_ratio)
        team1_wins : bool – True if team1 wins or draws on HP
        hp_ratio   : float in [0, 1] – fraction of team1's total HP remaining
    """
    t1 = [copy.deepcopy(p) for p in team1]
    t2 = [copy.deepcopy(p) for p in team2]

    i1, i2 = 0, 0
    MAX_TURNS = 300

    for _ in range(MAX_TURNS):
        # Advance past fainted mons
        while i1 < len(t1) and t1[i1]["fainted"]:
            i1 += 1
        while i2 < len(t2) and t2[i2]["fainted"]:
            i2 += 1
        if i1 >= len(t1) or i2 >= len(t2):
            break

        p1, p2 = t1[i1], t2[i2]

        m1 = _pick_move(p1, p2)
        m2 = _pick_move(p2, p1)
        if m1 is None or m2 is None:
            break

        # Speed determines who moves first (Quick Attack has implicit priority)
        sp1 = eff_spe(p1) + (1_000 if m1 == "quickattack" else 0)
        sp2 = eff_spe(p2) + (1_000 if m2 == "quickattack" else 0)
        first_p1 = sp1 >= sp2

        if first_p1:
            if not p1["fainted"]:
                _use_move(p1, m1, p2)
            if not p2["fainted"]:
                _use_move(p2, m2, p1)
        else:
            if not p2["fainted"]:
                _use_move(p2, m2, p1)
            if not p1["fainted"]:
                _use_move(p1, m1, p2)

    # ── Tally results ─────────────────────────────────────────
    alive1 = [p for p in t1 if not p["fainted"]]
    alive2 = [p for p in t2 if not p["fainted"]]

    hp1 = sum(p["hp"] for p in t1)
    hp2 = sum(p["hp"] for p in t2)

    if len(alive1) != len(alive2):
        team1_wins = len(alive1) > len(alive2)
    else:
        team1_wins = hp1 >= hp2      # tiebreak on remaining HP

    total_hp = sum(p["max_hp"] for p in t1)
    hp_ratio  = hp1 / total_hp if total_hp > 0 else 0.0

    return team1_wins, hp_ratio

# ──────────────────────────────────────────────────────────────
# FITNESS EVALUATION
# ──────────────────────────────────────────────────────────────

def genome_to_team(genome: list[str], opp_genome: list[str]) -> list[dict]:
    """Convert a list of 6 species IDs into a ready-to-battle team."""
    return [build_pokemon(sid, select_moves(sid, opp_genome)) for sid in genome]


def evaluate_fitness(
    genome: list[str],
    n_opponents: int = 10,
    n_battles_per_opp: int = 3,
) -> float:
    """
    Fitness = win_rate + avg_hp_ratio   (max ≈ 2.0)

    Battles against `n_opponents` randomly sampled teams,
    each repeated `n_battles_per_opp` times (due to accuracy RNG).
    """
    wins, total_hp_ratio, total = 0, 0.0, 0

    for _ in range(n_opponents):
        opp_genome = random.sample(ALL_SPECIES, 6)
        team       = genome_to_team(genome, opp_genome)
        opp_team   = genome_to_team(opp_genome, genome)

        for _ in range(n_battles_per_opp):
            won, hpr = simulate_battle(team, opp_team)
            if won:
                wins += 1
            total_hp_ratio += hpr
            total += 1

    win_rate = wins / total
    avg_hpr  = total_hp_ratio / total
    return win_rate + avg_hpr

# ──────────────────────────────────────────────────────────────
# EVOLUTIONARY OPERATORS
# ──────────────────────────────────────────────────────────────

def mutate_swap(genome: list[str]) -> list[str]:
    """
    Mutation: swap positions of two randomly chosen Pokémon in the team.
    This is the canonical mutation operator for permutation representations.
    """
    g = genome.copy()
    i, j = random.sample(range(len(g)), 2)
    g[i], g[j] = g[j], g[i]
    return g


def crossfill(p1: list[str], p2: list[str]) -> tuple[list[str], list[str]]:
    """
    Cut-and-Crossfill recombination (order-preserving).

    1. Choose a random crossover point k in [1, n-1].
    2. Child 1 = p1[:k] + (elements of p2 not yet in child, in their p2 order,
                            starting from index k and wrapping around).
    3. Child 2 = symmetric with roles reversed.
    """
    n = len(p1)
    k = random.randint(1, n - 1)

    def fill(main: list[str], other: list[str]) -> list[str]:
        child     = main[:k]
        child_set = set(child)
        # Values from `other` starting after crossover point, wrapping, skipping duplicates
        tail = [x for x in other[k:] + other[:k] if x not in child_set]
        return child + tail[:n - k]

    return fill(p1, p2), fill(p2, p1)


def tournament_select(population: list, fitnesses: list[float], k: int = 3) -> list[str]:
    """
    Tournament selection: draw k individuals at random, return the fittest.
    """
    idx    = random.sample(range(len(population)), min(k, len(population)))
    best   = max(idx, key=lambda i: fitnesses[i])
    return population[best]

# ──────────────────────────────────────────────────────────────
# EVOLUTIONARY ALGORITHM  (µ + λ)
# ──────────────────────────────────────────────────────────────

def run_ea(
    pop_size:          int   = 20,
    n_offspring:       int   = 20,
    n_generations:     int   = 30,
    tournament_size:   int   = 3,
    mutation_prob:     float = 0.5,
    n_opponents:       int   = 8,
    n_battles_per_opp: int   = 3,
    verbose:           bool  = True,
) -> tuple[list[str], float, dict]:
    """
    Run the full Evolutionary Algorithm.

    Parameters
    ----------
    pop_size          : µ  – number of survivors kept each generation
    n_offspring       : λ  – children produced per generation
    n_generations     : number of EA generations
    tournament_size   : k  for tournament parent selection
    mutation_prob     : probability that each child is mutated after recombination
    n_opponents       : number of random opponent teams per fitness eval
    n_battles_per_opp : battles vs each opponent (averages out RNG noise)
    verbose           : print progress per generation

    Returns
    -------
    (best_genome, best_fitness, history_dict)
    """

    def _print(msg: str) -> None:
        if verbose:
            print(msg, flush=True)

    # ── Initialisation ────────────────────────────────────────
    _print(f"\n{'='*60}")
    _print(f"  Pokemon Gen-1 Team Optimizer — Evolutionary Algorithm")
    _print(f"{'='*60}")
    _print(f"  µ={pop_size}  λ={n_offspring}  generations={n_generations}")
    _print(f"  tournament_k={tournament_size}  mutation_p={mutation_prob}")
    _print(f"  opponents/eval={n_opponents}  battles/opp={n_battles_per_opp}")
    _print(f"{'='*60}\n")

    population: list[list[str]] = [random.sample(ALL_SPECIES, 6) for _ in range(pop_size)]

    _print("Evaluating initial population …")
    fitnesses = [evaluate_fitness(g, n_opponents, n_battles_per_opp) for g in population]

    best_fitness = max(fitnesses)
    best_genome  = population[fitnesses.index(best_fitness)]

    history = {
        "best": [best_fitness],
        "avg":  [sum(fitnesses) / len(fitnesses)],
    }

    _print(f"Gen  0 | best={best_fitness:.4f}  avg={history['avg'][0]:.4f}")

    # ── Main loop ─────────────────────────────────────────────
    for gen in range(1, n_generations + 1):

        # ── Offspring production ──────────────────────────────
        offspring: list[list[str]]   = []
        off_fits:  list[float]        = []

        while len(offspring) < n_offspring:
            par1 = tournament_select(population, fitnesses, tournament_size)
            par2 = tournament_select(population, fitnesses, tournament_size)

            c1, c2 = crossfill(par1, par2)

            if random.random() < mutation_prob:
                c1 = mutate_swap(c1)
            if random.random() < mutation_prob:
                c2 = mutate_swap(c2)

            offspring.append(c1)
            if len(offspring) < n_offspring:
                offspring.append(c2)

        # ── Evaluate offspring ────────────────────────────────
        for child in offspring:
            off_fits.append(evaluate_fitness(child, n_opponents, n_battles_per_opp))

        # ── µ + λ survivor selection ──────────────────────────
        combined = sorted(
            zip(population + offspring, fitnesses + off_fits),
            key=lambda x: x[1],
            reverse=True,
        )
        population = [g for g, _ in combined[:pop_size]]
        fitnesses  = [f for _, f in combined[:pop_size]]

        gen_best = fitnesses[0]
        gen_avg  = sum(fitnesses) / len(fitnesses)

        if gen_best > best_fitness:
            best_fitness = gen_best
            best_genome  = population[0]

        history["best"].append(gen_best)
        history["avg"].append(gen_avg)

        team_str = ", ".join(species_names.get(s, s) for s in population[0])
        _print(f"Gen {gen:2d} | best={gen_best:.4f}  avg={gen_avg:.4f}  "
               f"| {team_str}")

    return best_genome, best_fitness, history

# ──────────────────────────────────────────────────────────────
# REPORT HELPERS
# ──────────────────────────────────────────────────────────────

def print_team(genome: list[str], header: str = "Team") -> None:
    """Pretty-print a team with selected moves."""
    # Use a balanced representative opponent to pick moves against
    sample_opp = random.sample(ALL_SPECIES, 6)
    print(f"\n{header}")
    print("-" * 50)
    for rank, sid in enumerate(genome, 1):
        name  = species_names.get(sid, sid)
        types = "/".join(species_types.get(sid, ["?"]))
        moves = select_moves(sid, sample_opp)
        level = constraints[sid].get("level", 100)
        atk_b, def_b, spe_b, spc_b = BASE_STATS.get(sid, (75, 75, 75, 75))
        bhp   = species_base_hp[sid]
        mv_str = "  |  ".join(m for m in moves)
        print(f"  {rank}. {name:<14} Lv{level:<3}  [{types:<16}]")
        print(f"     Moves: {mv_str}")
        print(f"     Base stats — HP:{bhp}  Atk:{atk_b}  Def:{def_b}  "
              f"Spe:{spe_b}  Spc:{spc_b}")


def print_history(history: dict) -> None:
    """Print a generation-by-generation fitness chart."""
    print("\nFitness History")
    print("-" * 60)
    max_val = max(history["best"]) if history["best"] else 2.0
    bar_width = 30
    for i, (b, a) in enumerate(zip(history["best"], history["avg"])):
        bar_len = int(b / max(max_val, 0.01) * bar_width)
        bar = "█" * bar_len + "░" * (bar_width - bar_len)
        print(f"  Gen {i:2d}: {b:.4f} [{bar}]  avg={a:.4f}")

# ──────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Reproducible seed – remove or change for stochastic runs
    random.seed(42)

    # ── Run the EA ────────────────────────────────────────────
    best_genome, best_fitness, history = run_ea(
        pop_size          = 20,
        n_offspring       = 20,
        n_generations     = 30,
        tournament_size   = 3,
        mutation_prob     = 0.50,
        n_opponents       = 8,
        n_battles_per_opp = 3,
        verbose           = True,
    )

    # ── Final report ──────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  OPTIMISATION COMPLETE")
    print(f"  Best fitness achieved: {best_fitness:.4f}  (max ≈ 2.0)")
    print(f"{'='*60}")

    print_team(best_genome, "BEST TEAM")
    print_history(history)
