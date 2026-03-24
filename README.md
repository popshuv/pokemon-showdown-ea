# Pokémon Showdown EA — Gen 1 Team Optimizer

A small Python experiment that searches for **strong orderings of six Pokémon species** in a **Generation 1** context. It uses **competitive coevolution**: two populations (**Red**, the team you care about, and **Blue**, an internal adversary) both evolve under the same **(μ + λ)** rules. Each candidate is scored with a **built-in battle simulator** and a **heuristic move picker** driven by JSON data (species, moves, types, stats).

This project is **inspired by** competitive team-building and [Pokémon Showdown](https://github.com/smogon/pokemon-showdown) ideas, but the battle code here is **not** the official Showdown engine—it is a **simplified** Gen 1–style model (see [Limitations](#limitations)).

---

## What the EA optimizes

- **Genotype:** A **permutation of 6 species IDs** (no duplicates), drawn from the species available in `data/species/data.json`.
- **Phenotype:** For each genome, the code builds six Pokémon with **four moves each** (`select_moves`), using types and learnsets from JSON. Move choice depends on the **opponent’s** six species so fitness reflects matchups, not a fixed moveset per species alone.
- **Fitness (coevolution):** When scoring **Red**, battles are sampled against genomes from the **current Blue population** (and Blue is scored against **Red**). Each matchup is repeated **`n_battles`** times.  
  **Fitness = win rate + average remaining HP ratio** for the evaluated side (roughly **[0, 2]**; higher is better).

So the EA searches **which six species** and **in which lead / order** perform best **against an adapting opponent**, not against a fixed random pool.

---

## Evolutionary algorithm concepts

| Concept | Typical meaning | In this project |
|--------|-------------------|-----------------|
| **Individual** | One candidate solution | One 6-species ordering (genome) |
| **Fitness** | How good a solution is | Win rate + mean HP ratio vs opponents sampled from the **other** population |
| **Selection** | Choose parents for breeding | **Tournament selection** (pick best of *k* random individuals) |
| **Crossover** | Combine two parents into children | **Cut-and-crossfill** (`crossfill`): order-preserving; fills the rest from the other parent without duplicates |
| **Mutation** | Small random change | **Shuffle a random contiguous subsequence** of the team (`mutate_scramble`; also exported as `mutate_swap`) |
| **Survival** | Who goes to the next generation | **(μ + λ)** per side: merge parents + offspring, sort by fitness, keep the top **μ** (`pop_size`) |

Each generation, **λ** children are produced **per population** from tournament-selected parents; each child may be mutated with probability **`mutation_prob`**. The run returns the **best Red** genome and fitness; Blue is only used as selection pressure.

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

From the **`src`** directory (so Python can import `pokemon_ea`):

```bash
cd src
python -m pokemon_ea
```

Alternatively, from the **repository root**, set `PYTHONPATH` to `src` (e.g. PowerShell **`$env:PYTHONPATH="src"`** or Unix **`export PYTHONPATH=src`**) and run **`python -m pokemon_ea`**.

The demo uses `random.seed(...)` and the parameters in `pokemon_ea/__main__.py`, then prints the summary from `pokemon_ea/report.py` (`print_run_footer`).

### Use as a module

With `src` on the module search path (e.g. after `cd src`):

```bash
python -c "import pokemon_ea as pe; print(pe.run_coevolution(pop_size=10, n_generations=5, verbose=False))"
```

Adjust `run_coevolution` in code or call it from your own script; see `run_coevolution` in `src/pokemon_ea/ea.py` for parameters.

### Main tuning knobs (`run_coevolution`)

| Parameter | Role |
|-----------|------|
| `pop_size` (μ) | Survivors each generation **per population** |
| `n_offspring` (λ) | Children produced **per population** each generation |
| `n_generations` | How long the EA runs |
| `tournament_size` | Parent selection pressure |
| `mutation_prob` | Probability each child is mutated after crossover |
| `n_opponents` | Opponent genomes sampled per fitness evaluation |
| `n_battles` | Repeats per opponent matchup (reduces RNG variance) |
| `verbose` | Print progress to stdout |

---

## Limitations

- **Not the Showdown server** — mechanics are approximated (status, damage, priority, etc.). Do not expect bit-for-bit parity with [smogon/pokemon-showdown](https://github.com/smogon/pokemon-showdown).
- **No manual switching** — battles are a **1v1 ladder** until one team is wiped. The **lead** is **slot 0** in team order. **After a faint**, the next Pokémon is the **next unfainted slot** after the current one in list order (wrapping to the start), not a free switch by type.
- **Moves** are chosen by a **deterministic heuristic**, not by a full human or Showdown AI.
- **Data scope** is whatever is in the JSON files (Gen 1–oriented species and moves in this repo).
