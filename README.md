# Pokémon Showdown EA — Gen 1 Team Optimizer

A small Python experiment that searches for **strong orderings of six Pokémon species** in a **Generation 1** context. It uses an **evolutionary algorithm** (EA) to evolve permutations of a team; each candidate is scored with a **built-in battle simulator** and a **heuristic move picker** driven by JSON data (species, moves, types, stats).

This project is **inspired by** competitive team-building and [Pokémon Showdown](https://github.com/smogon/pokemon-showdown) ideas, but the battle code here is **not** the official Showdown engine—it is a **simplified** Gen 1–style model (see [Limitations](#limitations)).

---

## What the EA optimizes

- **Genotype:** A **permutation of 6 species IDs** (no duplicates), drawn from the species available in `data/species/data.json`.
- **Phenotype:** For each genome, the code builds six Pokémon with **four moves each** (`select_moves`), using types and learnsets from JSON. Move choice depends on the **opponent’s** six species so fitness reflects matchups, not a fixed moveset per species alone.
- **Fitness:** For each evaluation, the team fights several **random opponent teams**.  
  **Fitness = win rate + average remaining HP ratio** on your side (roughly in **[0, 2]**; higher is better). Stochastic battles are repeated to reduce noise from accuracy and damage rolls.

So the EA is mainly searching **which six species** and **in which lead / order** they perform best under this simulator—not full Showdown sets (items, precise EV spreads, switches, etc.).

---

## Evolutionary algorithm concepts

Evolutionary algorithms maintain a **population** of candidate solutions and improve them over **generations** using **selection**, **recombination (crossover)**, and **mutation**, guided by a **fitness** function.

| Concept | Typical meaning | In this project |
|--------|-------------------|-----------------|
| **Individual** | One candidate solution | One 6-species ordering (genome) |
| **Fitness** | How good a solution is | Win rate + mean HP ratio vs random opponents |
| **Selection** | Choose parents for breeding | **Tournament selection** (pick best of *k* random individuals) |
| **Crossover** | Combine two parents into children | **Cut-and-crossfill** (`crossfill`): keeps order, fills the rest from the other parent without duplicates |
| **Mutation** | Small random change | **Swap** two positions in the team (`mutate_swap`) |
| **Survival** | Who goes to the next generation | **(μ + λ)** style: merge parents + offspring, sort by fitness, keep the top **μ** (`pop_size`) |

Default strategy: produce **λ** children per generation from tournament-selected parents, optionally mutate each child, evaluate fitness, then **truncate** the combined pool to the best μ genomes.

---

## Repository layout

```
pokemon-showdown-ea/
├── README.md
├── src/
│   └── pokemon_ea/      # Package: EA, battle sim, data loading, reporting
│       ├── __init__.py
│       ├── __main__.py  # Demo entry (`python -m pokemon_ea` from `src/`)
│       ├── data.py
│       ├── ea.py
│       ├── battle.py
│       └── ...
└── data/
    ├── species/         # Species metadata, learnsets, base stats, HP, names, types
    ├── moves/           # Move types, categories, power, accuracy, status / secondary effects
    └── types/           # Type chart (effectiveness scoring)
```

Game data is loaded from `data/` at the **repository root** (paths are resolved from `src/pokemon_ea/data.py`).

---

## Requirements

- **Python 3.10+** (uses modern type hints such as `str | None`)
- **Standard library only** (`json`, `math`, `copy`, `random`, `pathlib`) — no `pip install` needed for a basic run

---

## How to run

**From the repository root** (simplest):

```bash
python run.py
```

`run.py` adds `src/` to the module path and runs the same entry as `python -m pokemon_ea`.

Other options:

- **`cd src`** then **`python -m pokemon_ea`** (package directory on `sys.path`).
- **Editable install** (once): from the repo root run **`pip install -e .`** so `python -m pokemon_ea` works from any working directory.
- **Manual `PYTHONPATH`**: e.g. PowerShell **`$env:PYTHONPATH="src"`** then **`python -m pokemon_ea`** from the repo root.

The demo uses the parameters in `pokemon_ea/__main__.py` and prints the full report from `pokemon_ea/report.py`.

### Use as a module

With `src` on the module search path (e.g. `cd src`):

```bash
python -c "import pokemon_ea as pe; print(pe.run_coevolution(pop_size=10, n_generations=5))"
```

Adjust `run_coevolution` arguments in code or call it from your own script; see `run_coevolution` in `src/pokemon_ea/ea.py` for parameters.

### Main tuning knobs (`run_coevolution`)

| Parameter | Role |
|-----------|------|
| `pop_size` (μ) | Survivors each generation |
| `n_offspring` (λ) | Children generated per generation |
| `n_generations` | How long the EA runs |
| `tournament_size` | Parent selection pressure |
| `mutation_prob` | Chance each child gets a swap mutation |
| `n_opponents` | Random opponent teams per fitness evaluation |
| `n_battles` | Repeats per opponent (reduces RNG variance) |

---

## Limitations

- **Not the Showdown server** — mechanics are approximated (status, damage, priority, etc.). Do not expect bit-for-bit parity with [smogon/pokemon-showdown](https://github.com/smogon/pokemon-showdown).
- **No manual switching** — battles are a **1v1 ladder** until one team is wiped. The **opening** lead is still slot 1 in team order; **after a faint**, the next Pokémon is chosen by **type matchup** (then total stats), not fixed list order.
- **Moves** are chosen by a **deterministic heuristic**, not by a full human or Showdown AI.
- **Data scope** is whatever is in the JSON files (Gen 1–oriented species and moves in this repo).
