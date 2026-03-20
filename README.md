# pokemon-showdown-ea

Simulating **Pokémon team battles** with a **custom, lightweight battle model** (not a full Pokémon Showdown clone). Teams are evolved with **evolutionary algorithms (EA)** so you can study how EA behaves on this problem.

---

## Prerequisites

- **[Node.js](https://nodejs.org/)** 18+ recommended (any recent LTS works).
- This repo is **standalone**: you do **not** need the main [Pokémon Showdown](https://github.com/smogon/pokemon-showdown) simulator checked out to run battles or fitness evaluation.
- Optional: if you want to **regenerate** the move/type/status snapshots from Showdown source files, clone Showdown next to this project and run `generate-snapshots.js` (see [Regenerating datasets](#regenerating-datasets)).

---

## Clone this repo

```bash
git clone https://github.com/popshuv/pokemon-showdown-ea.git
cd pokemon-showdown-ea
```

Then use the commands below from the project root.

---

## Quick start

From the **root of this repository** (`pokemon-showdown-ea/`):

```bash
node -e "const ea = require('./index.js');
const team = ea.generateTeam({ seed: 42 });
const opponent = ea.generateTeam({ seed: 99 });
const result = ea.simulateBattle(team, opponent, { seed: 7, maxTurns: 100 });
console.log('Winner:', result.winner, 'Turns:', result.turns);
"
```

Evaluate a team against several random opponents (fitness-style):

```bash
node -e "const ea = require('./index.js');
const team = ea.generateTeam({ seed: 1 });
const fitness = ea.evaluateFitness(team, { seed: 2, numOpponents: 10, maxTurns: 80 });
console.log(fitness);
"
```

There is **no `npm install`** for the core API: everything uses Node’s built-in `require()` and JSON datasets.

---

## What this project does

1. **Genotype** = an ordered team of **6** distinct Pokémon (no duplicates), chosen from a fixed Gen 1 random-battle-style pool in `datasets/gen1-pokemon-dataset.json`.
2. **Battle** = a **simplified turn-based simulator**: both sides use the same **greedy move policy** (pick the move with highest heuristic score). There is **no switching** mid-battle; when the active Pokémon faints, the next living team member is used automatically.
3. **Fitness** (via `evaluateFitness`) = fraction of wins (and average battle length) against a set of opponent teams.

The battle model is **on purpose** not 1:1 with real Gen 1—it’s fast and stable enough to run many EA generations.

---

## Evolutionary algorithms — core ideas

An **evolutionary algorithm** mimics simplified “evolution”:

| Concept | Meaning |
|--------|---------|
| **Population** | A set of candidate solutions (here: many teams). |
| **Genotype** | How a solution is encoded (here: array of 6 Pokémon IDs, order matters). |
| **Fitness** | A number saying how good a solution is (here: win rate vs opponents). |
| **Selection** | Preferentially keep or reproduce higher-fitness teams. |
| **Crossover** | Combine two parent teams (e.g. swap slots) to make offspring. |
| **Mutation** | Randomly change a team (e.g. replace one species). |
| **Generation** | One loop: evaluate → select → breed → mutate → repeat. |

Over generations, the population tends to drift toward teams that score well under your fitness function.

### How EA maps to this repo

- **You provide** (or will add): population initialization, selection, crossover, mutation, and a generation loop.
- **This repo already provides**:
  - `generateTeam` — random valid team (useful for opponents or initial population).
  - `simulateBattle` — greedy vs greedy, deterministic given seeds.
  - `evaluateFitness` — run many battles and return `winRate`, `avgTurns`, etc.

The next step for a full EA is a small `src/ea/` (or `scripts/evolve.js`) that calls `evaluateFitness` each generation.

---

## Project layout

```
pokemon-showdown-ea/
├── index.js                 # Public API entry point
├── generate-snapshots.js    # Optional: rebuild datasets from Showdown source
├── README.md
├── datasets/                # Static Gen 1 JSON snapshots
│   ├── gen1-pokemon-dataset.json
│   ├── gen1-moves-dataset.json
│   ├── gen1-type-effectiveness.json
│   └── gen1-status-dataset.json
└── src/
    ├── data/datasets.js     # Loads JSON into memory + pokemonById map
    ├── core/                # RNG, types, damage, status helpers
    ├── policy/move-policy.js # Greedy move choice
    └── sim/                 # Team gen, battle state, turn engine, battle engine
```

---

## API reference (`index.js`)

| Export | Description |
|--------|-------------|
| `datasets` | `{ pokemon, moves, typeEffectiveness, statuses, pokemonById }` |
| `generateTeam({ seed?, teamSize? })` | Random team without duplicate species (default size 6). |
| `simulateBattle(teamA, teamB, { seed?, maxTurns?, policyA?, policyB? })` | Turn-based battle; default is **greedy vs greedy**. |
| `evaluateFitness(candidateTeam, { seed?, numOpponents?, opponents?, maxTurns? })` | Win rate vs generated opponents. |
| `createRng(seed)` | Seeded PRNG for reproducibility. |

---

## Regenerating datasets

If you have `pokemon-showdown` at:

`../pokemon-showdown` (sibling folder to this repo),

from this repo root run:

```bash
node generate-snapshots.js
```

That refreshes `datasets/gen1-moves-dataset.json`, `gen1-type-effectiveness.json`, and `gen1-status-dataset.json` from Showdown data.  
**`gen1-pokemon-dataset.json`** is not produced by this script in the current workflow; keep the checked-in copy or regenerate it with your own pipeline if you change species/move pools.

---

## Limitations

- Not a faithful Pokémon Showdown / cartridge-accurate simulator.
- Greedy policies only by default; battles depend on heuristics (damage, STAB, types, status bonuses).
- EA loop (selection / crossover / mutation) is left for you to implement on top of `evaluateFitness`.

---

## License

Use and modify as you like for research and learning. Pokémon is a trademark of Nintendo / The Pokémon Company; this project is an independent educational experiment.
