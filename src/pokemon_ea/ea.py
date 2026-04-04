"""Fitness evaluation and evolutionary algorithm (µ + λ)."""

import random

from . import battle, data, move_selection, pokemon


def genome_to_team(genome: list[str], opp_genome: list[str]) -> list[dict]:
    """Convert a list of 6 species IDs into a ready-to-battle team."""
    return [
        pokemon.build_pokemon(sid, move_selection.select_moves(sid, opp_genome))
        for sid in genome
    ]


def coeval_fitness(
    genome: list[str],
    opponent_pool: list[list[str]],
    n_opponents: int = 10,
    n_battles: int = 3,
) -> float:
    """
    Competitive coevolution fitness.

    Randomly samples `n_opponents` genomes from `opponent_pool` and
    battles `genome` against each one, repeating every matchup
    `n_battles` times to average out accuracy RNG.

    fitness = win_rate + avg_hp_ratio   (bounded [0, 2])

    The score depends on which opponents are in ``opponent_pool``.
    """
    wins, total_hp_ratio, total = 0, 0.0, 0

    sampled = random.sample(opponent_pool, min(n_opponents, len(opponent_pool)))
    for opp_genome in sampled:
        team     = genome_to_team(genome, opp_genome)
        opp_team = genome_to_team(opp_genome, genome)

        for _ in range(n_battles):
            won, hpr = battle.simulate_battle(team, opp_team)
            if won:
                wins += 1
            total_hp_ratio += hpr
            total += 1

    if total == 0:
        return 0.0

    return wins / total + total_hp_ratio / total


# ──────────────────────────────────────────────────────────────
# EVOLUTIONARY OPERATORS
# ──────────────────────────────────────────────────────────────

def mutate_scramble(genome: list[str]) -> list[str]:
    """
    Mutation: randomly shuffle a subsequence of the genome. To perserve
    permutation validity. 
    """
    g = genome.copy()

    # Pick two indices
    i, j = sorted(random.sample(range(len(g)), 2))

    # Extract and shuffle the subsequence
    subset = g[i: j + 1]
    random.shuffle(subset)

    # Place it back 
    g[i: j + 1] = subset
    
    return g


def crossfill(p1: list[str], p2: list[str]) -> tuple[list[str], list[str]]:
    """
    Cut-and-Crossfill recombination (order-preserving).

    1. Choose a random crossover point k in [1, n-1].
    2. Child 1 = p1[:k] + (elements of p2 not yet in child, in their p2 order,
                            starting from index k and wrapping around).
    3. Child 2 = symmetric with roles reversed.
    """
    n = len(p1)
    k = random.randint(1, n - 1)

    def fill(main: list[str], other: list[str]) -> list[str]:
        child     = main[:k]
        child_set = set(child)
        # Values from `other` starting after crossover point, wrapping, skipping duplicates
        tail = [x for x in other[k:] + other[:k] if x not in child_set]
        return child + tail[:n - k]

    return fill(p1, p2), fill(p2, p1)


def tournament_select(population: list, fitnesses: list[float], k: int = 3) -> list[str]:
    """
    Tournament selection: draw k individuals at random, return the fittest.
    """
    idx    = random.sample(range(len(population)), min(k, len(population)))
    best   = max(idx, key=lambda i: fitnesses[i])
    return population[best]

# ──────────────────────────────────────────────────────────────
# COMPETITIVE COEVOLUTION  (µ + λ, Red vs Blue)
# ──────────────────────────────────────────────────────────────

def run_coevolution(
    pop_size:        int   = 30,
    n_offspring:     int   = 20,
    n_generations:   int   = 30,
    tournament_size: int   = 3,
    mutation_prob:   float = 0.75,
    n_opponents:     int   = 8,
    n_battles:       int   = 3,
    verbose:         bool  = True,
) -> tuple[list[str], float, dict]:
    """
    Competitive coevolution between Red and Blue populations.

    Red is the team we want to optimise. Blue is an internal adversary
    that co-evolves purely to apply adaptive selection pressure on Red —
    it is never returned. Both populations use the same operators and
    µ+λ survivor selection.

    Each generation:
      1. Evolve offspring for both populations (parents chosen by tournament).
      2. Evaluate every µ+λ candidate (parents ∪ offspring) against the *current*
         adversary population on the other side.
      3. Truncate to µ survivors per side (highest fresh fitness).

    Parameters
    ----------
    pop_size        : µ — survivors per population each generation
    n_offspring     : λ — children produced per population each generation
    n_generations   : number of generations
    tournament_size : k for tournament parent selection
    mutation_prob   : probability a child is mutated after recombination
    n_opponents     : number of random opponent teams per fitness eval
    n_battles       : battle repetitions per matchup (averages out RNG)

    Returns
    -------
    (best_genome, best_fitness, history_dict)
        ``history`` has aligned lists per round: ``best`` (top-1 Red fitness
        that round), ``avg`` (mean Red fitness in the surviving population).
    """
    def _print(msg: str) -> None:
        if verbose:
            print(msg, flush=True)

    # ── Header ────────────────────────────────────────────────
    _print(f"\n{'='*60}")
    _print(f"  Pokemon Gen-1 Team Optimizer — Competitive Coevolution")
    _print(f"{'='*60}")
    _print(f"  µ={pop_size}  λ={n_offspring}  rounds={n_generations}")
    _print(f"  tournament_k={tournament_size}  mutation_p={mutation_prob}")
    _print(f"  opponents/eval={n_opponents} battles/opponent={n_battles}")
    _print(f"{'='*60}\n")

    # ── Initialise both populations ───────────────────────────
    red  = [random.sample(data.ALL_SPECIES, 6) for _ in range(pop_size)]
    blue = [random.sample(data.ALL_SPECIES, 6) for _ in range(pop_size)]

    # ── Fitness helpers ───────────────────────────────────────
    def _eval_red(red_pop, blue_live):
        return [coeval_fitness(g, blue_live, n_opponents, n_battles) for g in red_pop]

    def _eval_blue(blue_pop, red_live):
        # Blue is scored from its own perspective: it "wins" when Red loses
        return [coeval_fitness(g, red_live, n_opponents, n_battles) for g in blue_pop]

    def _offspring(pop, fits):
        children = []
        while len(children) < n_offspring:
            p1 = tournament_select(pop, fits, tournament_size)
            p2 = tournament_select(pop, fits, tournament_size)
            c1, c2 = crossfill(p1, p2)
            if random.random() < mutation_prob:
                c1 = mutate_scramble(c1)
            if random.random() < mutation_prob:
                c2 = mutate_scramble(c2)
            children.append(c1)
            if len(children) < n_offspring:
                children.append(c2)
        return children

    def _mu_lambda_select(candidates: list, fits: list[float]) -> tuple[list, list[float]]:
        combined = sorted(zip(candidates, fits), key=lambda x: x[1], reverse=True)
        top = combined[:pop_size]
        return [g for g, _ in top], [f for _, f in top]

    # ── Initial evaluation ────────────────────────────────────
    _print("Evaluating initial populations …")
    red_fits  = _eval_red(red, blue)
    blue_fits = _eval_blue(blue, red)

    best_genome  = red[red_fits.index(max(red_fits))]
    best_fitness = max(red_fits)

    # best: top Red fitness this round; avg: mean Red in surviving population.
    history: dict[str, list] = {"best": [], "avg": []}

    # ── Main loop ─────────────────────────────────────────────
    for gen in range(1, n_generations + 1):

        # Produce offspring for both populations
        red_children  = _offspring(red, red_fits)
        blue_children = _offspring(blue, blue_fits)

        # Fresh fitness for every parent and child vs current adversary (no stale fits)
        red_all       = red + red_children
        red_all_fits  = _eval_red(red_all, blue)
        blue_all      = blue + blue_children
        blue_all_fits = _eval_blue(blue_all, red)

        red,  red_fits  = _mu_lambda_select(red_all, red_all_fits)
        blue, blue_fits = _mu_lambda_select(blue_all, blue_all_fits)

        # Track best Red genome across all generations
        if red_fits[0] > best_fitness:
            best_fitness = red_fits[0]
            best_genome  = red[0]

        gen_avg = sum(red_fits) / len(red_fits)
        history["best"].append(red_fits[0])
        history["avg"].append(gen_avg)

        team_str = ", ".join(data.species_names.get(s, s) for s in red[0])
        _print(
            f"Round {gen:2d} | best={red_fits[0]:.4f}  avg={gen_avg:.4f}  | {team_str}"
        )

    return best_genome, best_fitness, history


evaluate_fitness = coeval_fitness
