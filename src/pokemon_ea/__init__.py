"""
Pokemon Gen-1 Team Optimizer — Evolutionary Algorithm.

Public API is re-exported here for ``from pokemon_ea import run_coevolution`` when
``src`` is on ``PYTHONPATH`` (e.g. ``python -m pokemon_ea`` from the ``src`` directory).
"""

from .battle import calc_damage, pick_move, simulate_battle, use_move
from .data import (
    ALL_SPECIES,
    BASE_STATS,
    MOVE_ACCURACY,
    MOVE_POWER,
    MOVE_SECONDARY,
    STATUS_MOVES,
    constraints,
    move_categories,
    move_types,
    species_base_hp,
    species_names,
    species_types,
    type_chart_score,
)
from .ea import (
    crossfill,
    evaluate_fitness,
    genome_to_team,
    mutate_scramble,
    run_coevolution,
    tournament_select,
)
from .effectiveness import sum_exponents, type_multiplier
from .move_selection import select_moves
from .pokemon import build_pokemon, eff_spe
from .report import print_history, print_team
from .stats import DEFAULT_EV, DEFAULT_IV, stage_mult, stat_modify_hp, stat_modify_other

__all__ = [
    "ALL_SPECIES",
    "BASE_STATS",
    "MOVE_ACCURACY",
    "MOVE_POWER",
    "MOVE_SECONDARY",
    "STATUS_MOVES",
    "build_pokemon",
    "calc_damage",
    "constraints",
    "crossfill",
    "DEFAULT_EV",
    "DEFAULT_IV",
    "eff_spe",
    "evaluate_fitness",
    "genome_to_team",
    "move_categories",
    "move_types",
    "mutate_scramble",
    "pick_move",
    "print_history",
    "print_team",
    "run_coevolution",
    "select_moves",
    "simulate_battle",
    "species_base_hp",
    "species_names",
    "species_types",
    "stage_mult",
    "stat_modify_hp",
    "stat_modify_other",
    "sum_exponents",
    "tournament_select",
    "type_chart_score",
    "type_multiplier",
    "use_move",
]
