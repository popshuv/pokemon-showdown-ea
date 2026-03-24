"""Run the EA demo when executing ``python -m pokemon_ea`` (from ``src``)."""

import random
import sys
from pathlib import Path

# Direct ``python .../pokemon_ea/__main__.py`` leaves ``__package__`` unset; relative imports fail.
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from pokemon_ea.ea import run_coevolution
    from pokemon_ea.report import print_run_footer
else:
    from .ea import run_coevolution
    from .report import print_run_footer


def main() -> None:
    random.seed(24)
    best_genome, best_fitness, history = run_coevolution(
        pop_size=30,
        n_offspring=20,
        n_generations=30,
        tournament_size=3,
        mutation_prob=0.75,
        n_opponents=8,
        n_battles=3,
    )

    print_run_footer(best_genome, best_fitness, history)


if __name__ == "__main__":
    main()
