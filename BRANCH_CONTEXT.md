# Branch context reference

Snapshot for agents and reviewers working on this repo. Regenerate the merge-base diff after large merges.

## Git

| Field | Value |
|---|---|
| **Default branch** | `main` (`origin/HEAD` → `origin/main`) |
| **Current branch** | `main` |
| **Merge base** (`main`…`HEAD`) | `1ea1f8de69a4a672f7de6d4c5717ee82c32096af` |
| **Merge-base diff** | Empty at last update (HEAD matches merge base; local edits may be unstaged) |

Refresh diff:

```bash
git merge-base HEAD origin/main
git -c diff.autoRefreshIndex=false diff --no-color --ignore-space-change <merge-base> HEAD
```

## Active work (vs `main` at merge base)

Uncommitted / in-progress on `main`:

1. **`mutation_prob = 0.3`** — default in `run_coevolution` (was `0.75`).
2. **Lead optimization** — genome index `0` is the battle lead; `mutate_swap_slots` swaps two slots (including lead) with probability `mutation_prob`; `crossfill` preserves parent order for offspring.
3. **Hall of fame** — `pokemon_ea.hof.HallOfFame` archives each side’s round-best genome; fitness sampling uses `live_population + hof.genomes` as the opponent pool (`hof_size` default `12`).
4. **`mutate_swap`** — replaces one species with a random species not on the team (replaces former `mutate_scramble`).

## Key files

| Area | Path |
|---|---|
| EA loop, operators | `src/pokemon_ea/ea.py` |
| Opponent memory | `src/pokemon_ea/hof.py` |
| Battle / lead slot 0 | `src/pokemon_ea/battle.py` |
| Demo entry | `src/pokemon_ea/__main__.py` |

## Recent `main` history (context)

- `1ea1f8d` — Merge branch `co-evolution` into `main`
- `ae9abcb` — Type/stat switch AI; EA entry defaults
- `7d67c0c` — `mutate_scramble` only (superseded locally by `mutate_swap` + slot swap)
