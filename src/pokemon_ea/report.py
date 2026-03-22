"""Console reporting helpers."""

import random

from . import data, move_selection


def print_team(genome: list[str], header: str = "Team") -> None:
    sample_opp = random.sample(data.ALL_SPECIES, 6)
    print(f"\n{header}")
    print("-" * 50)
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
            f"     Base stats — HP:{bhp}  Atk:{atk_b}  Def:{def_b}  "
            f"Spe:{spe_b}  Spc:{spc_b}"
        )


def print_history(history: dict) -> None:
    print("\nFitness History")
    print("-" * 60)
    max_val = max(history["best"]) if history["best"] else 2.0
    bar_width = 30
    for i, (b, a) in enumerate(zip(history["best"], history["avg"])):
        bar_len = int(b / max(max_val, 0.01) * bar_width)
        bar = "█" * bar_len + "░" * (bar_width - bar_len)
        print(f"  Gen {i:2d}: {b:.4f} [{bar}]  avg={a:.4f}")
