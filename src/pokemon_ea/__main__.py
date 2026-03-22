"""Run the EA demo when executing ``python -m pokemon_ea`` (from ``src``)."""

import random
import sys
from pathlib import Path

# Direct ``python .../pokemon_ea/__main__.py`` leaves ``__package__`` unset; relative imports fail.
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from pokemon_ea.ea import run_ea
    from pokemon_ea.report import print_history, print_team
else:
    from .ea import run_ea
    from .report import print_history, print_team


def main() -> None:
    random.seed(42)

    best_genome, best_fitness, history = run_ea(
        pop_size=30,
        n_offspring=20,
        n_generations=30,
        tournament_size=3,
        mutation_prob=0.50,
        n_opponents=8,
        n_battles_per_opp=3,
        verbose=True,
    )

    print(f"\n{'='*60}")
    print("  OPTIMISATION COMPLETE")
    print(f"  Best fitness achieved: {best_fitness:.4f}  (max ≈ 2.0)")
    print(f"{'='*60}")

    print_team(best_genome, "BEST TEAM")
    print_history(history)


if __name__ == "__main__":
    main()
