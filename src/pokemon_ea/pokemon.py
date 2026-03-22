"""Build battle Pokémon dicts from species + moves."""

from . import data, stats


def build_pokemon(species_id: str, moves: list[str]) -> dict:
    """Mutable battle dict: HP, stats, stages, status, moves."""
    d = data.constraints[species_id]
    level = d.get("level", 100)
    bhp = data.species_base_hp[species_id]
    batk, bdef, bspe, bspc = data.BASE_STATS.get(species_id, (75, 75, 75, 75))

    hp = stats.stat_modify_hp(bhp, level, stats.DEFAULT_IV, stats.DEFAULT_EV)
    atk = stats.stat_modify_other(batk, level, stats.DEFAULT_IV, stats.DEFAULT_EV)
    dfn = stats.stat_modify_other(bdef, level, stats.DEFAULT_IV, stats.DEFAULT_EV)
    spe = stats.stat_modify_other(bspe, level, stats.DEFAULT_IV, stats.DEFAULT_EV)
    spc = stats.stat_modify_other(bspc, level, stats.DEFAULT_IV, stats.DEFAULT_EV)

    all_non_phys = all(data.move_categories.get(m) != "Physical" for m in moves)
    if all_non_phys:
        atk = stats.stat_modify_other(batk, level, iv=0, ev=0)

    return {
        "species": species_id,
        "level": level,
        "max_hp": hp,
        "hp": hp,
        "atk": atk,
        "def": dfn,
        "spe": spe,
        "spc": spc,
        "moves": list(moves),
        "status": None,
        "sleep_turns": 0,
        "atk_st": 0,
        "def_st": 0,
        "spe_st": 0,
        "spc_st": 0,
        "fainted": False,
    }


def _eff_stat(base: int, stage: int, status_penalty: float = 1.0) -> float:
    return base * stats.stage_mult(stage) * status_penalty


def eff_spe(p: dict) -> float:
    penalty = 0.25 if p["status"] == "paralyze" else 1.0
    return _eff_stat(p["spe"], p["spe_st"], penalty)
