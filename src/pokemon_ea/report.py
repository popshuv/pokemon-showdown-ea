"""Console reporting helpers."""

import itertools
import random

from . import data, move_selection

_SUMMARY_WIDTH = 72
_BAR_WIDTH = 32


def _fitness_bar(value: float, vmax: float, width: int = _BAR_WIDTH) -> str:
    """Block bar: fill proportional to value / vmax."""
    vmax = max(vmax, 0.01)
    filled = min(width, max(0, int(value / vmax * width)))
    return "[" + "\u2588" * filled + "\u2591" * (width - filled) + "]"


def print_team(genome: list[str], header: str = "Team") -> None:
    sample_opp = random.sample(data.ALL_SPECIES, 6)
    print(f"\n{header}")
    print("-" * min(_SUMMARY_WIDTH, 50))
    for rank, sid in enumerate(genome, 1):
        name = data.species_names.get(sid, sid)
        types = "/".join(data.species_types.get(sid, ["?"]))
        moves = move_selection.select_moves(sid, sample_opp)
        level = data.constraints[sid].get("level", 100)
        atk_b, def_b, spe_b, spc_b = data.BASE_STATS.get(sid, (75, 75, 75, 75))
        bhp = data.species_base_hp[sid]
        mv_str = "  |  ".join(m for m in moves)
        print(f"  {rank}. {name:<14} Lv{level:<3}  [{types:<16}]")
        print(f"     Moves: {mv_str}")
        print(
            f"     Base stats  HP:{bhp}  Atk:{atk_b}  Def:{def_b}  "
            f"Spe:{spe_b}  Spc:{spc_b}"
        )


def print_history(history: dict) -> None:
    """Per-round Red metrics: ``history['best']`` and ``history['avg']``."""
    best_series = history.get("best") or []
    avg_series = history.get("avg") or []

    if not best_series:
        print("\n  (no rounds recorded yet)")
        return

    vmax = max(
        2.0,
        max(best_series),
        max(avg_series) if avg_series else 0.0,
        0.01,
    )

    print(f"\n{'Red fitness by round':^{_SUMMARY_WIDTH}}")
    print("-" * _SUMMARY_WIDTH)

    for rnd, (best, avg) in enumerate(
        itertools.zip_longest(best_series, avg_series, fillvalue=0.0), start=1
    ):
        bar = _fitness_bar(best, vmax)
        print(f"Round {rnd:2d}: best={best:.4f} {bar}  avg={avg:.4f}")

    print("-" * _SUMMARY_WIDTH)


def print_run_footer(best_genome: list[str], best_fitness: float, history: dict) -> None:
    """Post-run summary, best Red team, and per-round fitness table."""
    print(f"\n{'=' * _SUMMARY_WIDTH}")
    print("  RUN COMPLETE: competitive coevolution (Red vs co-evolving Blue)")
    print(f"{'=' * _SUMMARY_WIDTH}")
    print(
        f"  best={best_fitness:.4f}  "
        f"(scale ~0..2: win rate + avg remaining HP ratio)"
    )
    print(f"{'=' * _SUMMARY_WIDTH}")
    print_team(best_genome, "BEST RED TEAM")
    print_history(history)
