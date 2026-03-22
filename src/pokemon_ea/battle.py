"""Turn-based battle simulation and move AI."""

import copy
import random

from . import data, effectiveness, pokemon, stats


def _base_damage_formula(attacker: dict, move_id: str, defender: dict) -> float:
    category = data.move_categories.get(move_id, "Physical")
    move_type = data.move_types.get(move_id, "Normal")
    power = data.MOVE_POWER.get(move_id, 0)
    if power == 0:
        return 0.0

    if category == "Physical":
        raw_atk = attacker["atk"] * stats.stage_mult(attacker["atk_st"])
        raw_def = defender["def"] * stats.stage_mult(defender["def_st"])
        if attacker["status"] == "burn":
            raw_atk /= 2
    else:
        raw_atk = attacker["spc"] * stats.stage_mult(attacker["spc_st"])
        raw_def = defender["spc"] * stats.stage_mult(defender["spc_st"])

    stab = 1.5 if move_type in data.species_types.get(attacker["species"], []) else 1.0
    eff = effectiveness.type_multiplier(
        move_type, data.species_types.get(defender["species"], ["Normal"])
    )
    if eff == 0:
        return 0.0

    dmg = ((2 * attacker["level"] / 5 + 2) * power * raw_atk / max(1, raw_def)) / 50 + 2
    dmg *= stab * eff
    return float(dmg)


def calc_damage(attacker: dict, move_id: str, defender: dict) -> int:
    d = _base_damage_formula(attacker, move_id, defender)
    if d <= 0:
        return 0
    r = 0.85 + random.random() * 0.15
    return max(1, int(d * r))


def _expected_damage_for_choice(attacker: dict, move_id: str, defender: dict) -> float:
    if move_id in ("seismictoss", "nightshade"):
        return float(attacker["level"])
    if move_id == "superfang":
        return float(max(1, defender["hp"] // 2))
    if move_id == "counter":
        return float(max(1, int(attacker["atk"] * 0.5)))

    d = _base_damage_formula(attacker, move_id, defender)
    if d <= 0:
        return 0.0
    return max(1.0, d * 0.925)


def _best_expected_attack_score(attacker: dict, defender: dict) -> float:
    best = 0.0
    for m in attacker["moves"]:
        if data.move_categories.get(m, "Physical") == "Status":
            continue
        ed = _expected_damage_for_choice(attacker, m, defender)
        acc = data.MOVE_ACCURACY.get(m, 1.0)
        best = max(best, ed * acc)
    return best


def _has_physical_attacker(attacker: dict) -> bool:
    for m in attacker["moves"]:
        if data.move_categories.get(m, "Physical") != "Physical":
            continue
        if data.MOVE_POWER.get(m, 0) > 0 or m in (
            "seismictoss", "nightshade", "superfang", "counter"
        ):
            return True
    return False


def _has_special_attacker(attacker: dict) -> bool:
    for m in attacker["moves"]:
        if data.move_categories.get(m, "Physical") != "Special":
            continue
        if data.MOVE_POWER.get(m, 0) > 0:
            return True
    return False


def _score_status_or_setup(
    move_id: str,
    attacker: dict,
    defender: dict,
    offense_weak: bool,
) -> float:
    acc = data.MOVE_ACCURACY.get(move_id, 1.0)

    if move_id in data.STATUS_MOVES:
        if defender["status"] is not None:
            return -1.0
        base = 135.0 if offense_weak else 38.0
        return base * acc

    if move_id in ("leer", "tailwhip", "sandattack"):
        return (58.0 if offense_weak else 20.0) * acc

    if move_id in ("smokescreen",):
        return (45.0 if offense_weak else 16.0) * acc

    if move_id == "swordsdance":
        if attacker["atk_st"] >= 6:
            return -1.0
        if not _has_physical_attacker(attacker):
            return 8.0 * acc
        room = (6 - attacker["atk_st"]) * 28.0
        return (room + (55.0 if offense_weak else 12.0)) * acc

    if move_id == "amnesia":
        if attacker["spc_st"] >= 6:
            return -1.0
        if not _has_special_attacker(attacker):
            return 8.0 * acc
        room = (6 - attacker["spc_st"]) * 28.0
        return (room + (55.0 if offense_weak else 12.0)) * acc

    if move_id == "agility":
        if attacker["spe_st"] >= 6:
            return -1.0
        room = (6 - attacker["spe_st"]) * 22.0
        return (room + (35.0 if offense_weak else 10.0)) * acc

    if move_id in ("reflect", "acidarmor"):
        if move_id == "reflect" and attacker["def_st"] >= 6:
            return -1.0
        if move_id == "acidarmor" and attacker["def_st"] >= 6:
            return -1.0
        return (38.0 if offense_weak else 14.0) * acc

    if move_id in ("recover", "softboiled"):
        pct = attacker["hp"] / max(1, attacker["max_hp"])
        if pct > 0.88:
            return 12.0 * acc
        return (95.0 + (1.0 - pct) * 120.0) * acc

    if move_id == "rest":
        if attacker["hp"] > attacker["max_hp"] * 0.55:
            return 10.0 * acc
        return 105.0 * acc

    if move_id == "substitute":
        if attacker["hp"] <= attacker["max_hp"] * 0.22:
            return 6.0 * acc
        return (35.0 if offense_weak else 12.0) * acc

    if move_id in ("meditate",):
        if attacker["atk_st"] >= 6:
            return -1.0
        return (32.0 if offense_weak else 12.0) * acc

    if move_id in ("mimic", "mirrormove", "transform"):
        return 14.0 * acc

    if data.move_categories.get(move_id, "Physical") == "Status":
        return 18.0 * acc

    return float("-inf")


def pick_move(attacker: dict, defender: dict) -> str | None:
    moves = attacker["moves"]
    if not moves:
        return None

    hp = max(1, defender["hp"])
    max_hp = max(1, defender["max_hp"])
    best_att = _best_expected_attack_score(attacker, defender)
    offense_weak = best_att < max(28.0, hp * 0.20, max_hp * 0.085)

    best_move: str | None = None
    best_score = float("-inf")

    for m in moves:
        cat = data.move_categories.get(m, "Physical")

        if cat in ("Physical", "Special"):
            ed = _expected_damage_for_choice(attacker, m, defender)
            score = ed * data.MOVE_ACCURACY.get(m, 1.0)
            if defender["hp"] > 0 and ed >= defender["hp"]:
                score += max_hp * 0.45
        elif cat == "Status":
            score = _score_status_or_setup(m, attacker, defender, offense_weak)
        else:
            score = float("-inf")

        if score > best_score:
            best_score = score
            best_move = m

    if best_move is None or best_score == float("-inf"):
        return moves[0] if moves else None
    return best_move


def use_move(attacker: dict, move_id: str, defender: dict) -> int:
    if attacker["status"] == "sleep":
        if attacker["sleep_turns"] > 0:
            attacker["sleep_turns"] -= 1
            if attacker["sleep_turns"] == 0:
                attacker["status"] = None
        return 0

    if attacker["status"] == "freeze":
        if random.random() < 0.20:
            attacker["status"] = None
        else:
            return 0

    if attacker["status"] == "paralyze":
        if random.random() < 0.25:
            return 0

    if attacker["status"] == "confuse":
        if random.random() < 0.50:
            dmg = max(1, int(calc_damage(attacker, "bodyslam", attacker) * 0.5))
            attacker["hp"] = max(0, attacker["hp"] - dmg)
            if attacker["hp"] == 0:
                attacker["fainted"] = True
            return 0

    if random.random() > data.MOVE_ACCURACY.get(move_id, 1.0):
        return 0

    cat = data.move_categories.get(move_id, "Physical")

    if cat == "Status":
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
            defender["spe_st"] = max(-6, defender["spe_st"] - 1)
        elif move_id in ("recover", "softboiled"):
            attacker["hp"] = min(
                attacker["max_hp"],
                attacker["hp"] + attacker["max_hp"] // 2,
            )
        elif move_id == "rest":
            attacker["hp"] = attacker["max_hp"]
            attacker["status"] = "sleep"
            attacker["sleep_turns"] = 2
        elif move_id == "substitute":
            cost = attacker["max_hp"] // 4
            attacker["hp"] = max(0, attacker["hp"] - cost)
            if attacker["hp"] == 0:
                attacker["fainted"] = True
        elif move_id in data.STATUS_MOVES:
            tgt_status = data.STATUS_MOVES[move_id]
            if defender["status"] is None:
                defender["status"] = tgt_status
                if tgt_status == "sleep":
                    defender["sleep_turns"] = random.randint(1, 7)
        return 0

    dmg_dealt = 0

    if move_id in ("seismictoss", "nightshade"):
        dmg_dealt = attacker["level"]
    elif move_id == "superfang":
        dmg_dealt = max(1, defender["hp"] // 2)
    elif move_id == "counter":
        dmg_dealt = max(1, int(attacker["atk"] * 0.5))
    else:
        dmg_dealt = calc_damage(attacker, move_id, defender)
        if move_id in ("explosion", "selfdestruct"):
            attacker["hp"] = 0
            attacker["fainted"] = True
            dmg_dealt *= 2
        elif move_id in ("doubleedge", "submission", "takedown"):
            recoil = {"doubleedge": 0.25, "submission": 0.25, "takedown": 0.25}
            attacker["hp"] = max(
                0,
                attacker["hp"] - max(1, int(dmg_dealt * recoil[move_id])),
            )
            if attacker["hp"] == 0:
                attacker["fainted"] = True
        elif move_id == "highjumpkick" and dmg_dealt == 0:
            attacker["hp"] = max(0, attacker["hp"] - attacker["max_hp"] // 8)
            if attacker["hp"] == 0:
                attacker["fainted"] = True

    defender["hp"] = max(0, defender["hp"] - dmg_dealt)
    if defender["hp"] == 0:
        defender["fainted"] = True

    if move_id in data.MOVE_SECONDARY and not defender["fainted"]:
        eff_status, prob = data.MOVE_SECONDARY[move_id]
        if eff_status != "flinch" and random.random() < prob:
            if defender["status"] is None:
                defender["status"] = eff_status
                if eff_status == "sleep":
                    defender["sleep_turns"] = random.randint(1, 7)

    for victim in (attacker, defender):
        if victim["fainted"]:
            continue
        if victim["status"] in ("poison", "burn"):
            dot = max(1, victim["max_hp"] // 16)
            victim["hp"] = max(0, victim["hp"] - dot)
            if victim["hp"] == 0:
                victim["fainted"] = True

    return dmg_dealt


def _first_unfainted_mon(team: list[dict]) -> tuple[int, dict] | None:
    for j in range(len(team)):
        if not team[j]["fainted"]:
            return j, team[j]
    return None


def _opp_reference_for_switch(other_team: list[dict], other_i: int) -> dict | None:
    if other_i < len(other_team) and not other_team[other_i]["fainted"]:
        return other_team[other_i]
    first = _first_unfainted_mon(other_team)
    return first[1] if first else None


def _stat_total(p: dict) -> int:
    return int(p["max_hp"] + p["atk"] + p["def"] + p["spe"] + p["spc"])


def _switch_sort_key(p: dict, opp: dict) -> tuple[int, int]:
    our_types = data.species_types.get(p["species"], ["Normal"])
    opp_types = data.species_types.get(opp["species"], ["Normal"])
    offensive = sum(effectiveness.sum_exponents(t, opp_types) for t in our_types)
    defensive = -sum(effectiveness.sum_exponents(t, our_types) for t in opp_types)
    type_score = offensive * 100 + defensive
    return (type_score, _stat_total(p))


def choose_switch_in(team: list[dict], opp: dict | None) -> int | None:
    cand = [j for j in range(len(team)) if not team[j]["fainted"]]
    if not cand:
        return None
    if opp is None:
        return max(cand, key=lambda j: _stat_total(team[j]))
    return max(cand, key=lambda j: _switch_sort_key(team[j], opp))


def simulate_battle(team1: list[dict], team2: list[dict]) -> tuple[bool, float]:
    t1 = [copy.deepcopy(p) for p in team1]
    t2 = [copy.deepcopy(p) for p in team2]

    i1, i2 = 0, 0
    MAX_TURNS = 300

    for _ in range(MAX_TURNS):
        ref2 = _opp_reference_for_switch(t2, i2)
        if i1 < len(t1) and t1[i1]["fainted"]:
            n = choose_switch_in(t1, ref2)
            if n is None:
                break
            i1 = n
        ref1 = _opp_reference_for_switch(t1, i1)
        if i2 < len(t2) and t2[i2]["fainted"]:
            n = choose_switch_in(t2, ref1)
            if n is None:
                break
            i2 = n

        if i1 >= len(t1) or i2 >= len(t2):
            break
        if t1[i1]["fainted"] or t2[i2]["fainted"]:
            continue

        p1, p2 = t1[i1], t2[i2]

        m1 = pick_move(p1, p2)
        m2 = pick_move(p2, p1)
        if m1 is None or m2 is None:
            break

        sp1 = pokemon.eff_spe(p1) + (1_000 if m1 == "quickattack" else 0)
        sp2 = pokemon.eff_spe(p2) + (1_000 if m2 == "quickattack" else 0)
        first_p1 = sp1 >= sp2

        if first_p1:
            if not p1["fainted"]:
                use_move(p1, m1, p2)
            if not p2["fainted"]:
                use_move(p2, m2, p1)
        else:
            if not p2["fainted"]:
                use_move(p2, m2, p1)
            if not p1["fainted"]:
                use_move(p1, m1, p2)

    alive1 = [p for p in t1 if not p["fainted"]]
    alive2 = [p for p in t2 if not p["fainted"]]

    hp1 = sum(p["hp"] for p in t1)
    hp2 = sum(p["hp"] for p in t2)

    if len(alive1) != len(alive2):
        team1_wins = len(alive1) > len(alive2)
    else:
        team1_wins = hp1 >= hp2

    total_hp = sum(p["max_hp"] for p in t1)
    hp_ratio = hp1 / total_hp if total_hp > 0 else 0.0

    return team1_wins, hp_ratio
