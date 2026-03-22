"""Fitness evaluation and evolutionary algorithm (µ + λ)."""

import random

from . import battle, data, move_selection, pokemon


def genome_to_team(genome: list[str], opp_genome: list[str]) -> list[dict]:
    return [
        pokemon.build_pokemon(sid, move_selection.select_moves(sid, opp_genome))
        for sid in genome
    ]


def evaluate_fitness(
    genome: list[str],
    n_opponents: int = 10,
    n_battles_per_opp: int = 3,
) -> float:
    wins, total_hp_ratio, total = 0, 0.0, 0

    for _ in range(n_opponents):
        opp_genome = random.sample(data.ALL_SPECIES, 6)
        team = genome_to_team(genome, opp_genome)
        opp_team = genome_to_team(opp_genome, genome)

        for _ in range(n_battles_per_opp):
            won, hpr = battle.simulate_battle(team, opp_team)
            if won:
                wins += 1
            total_hp_ratio += hpr
            total += 1

    win_rate = wins / total
    avg_hpr = total_hp_ratio / total
    return win_rate + avg_hpr


def mutate_swap(genome: list[str]) -> list[str]:
    g = genome.copy()
    i, j = random.sample(range(len(g)), 2)
    g[i], g[j] = g[j], g[i]
    return g


def crossfill(p1: list[str], p2: list[str]) -> tuple[list[str], list[str]]:
    n = len(p1)
    k = random.randint(1, n - 1)

    def fill(main: list[str], other: list[str]) -> list[str]:
        child = main[:k]
        child_set = set(child)
        tail = [x for x in other[k:] + other[:k] if x not in child_set]
        return child + tail[:n - k]

    return fill(p1, p2), fill(p2, p1)


def tournament_select(population: list, fitnesses: list[float], k: int = 3) -> list[str]:
    idx = random.sample(range(len(population)), min(k, len(population)))
    best = max(idx, key=lambda i: fitnesses[i])
    return population[best]


def run_ea(
    pop_size: int = 20,
    n_offspring: int = 20,
    n_generations: int = 30,
    tournament_size: int = 3,
    mutation_prob: float = 0.5,
    n_opponents: int = 8,
    n_battles_per_opp: int = 3,
    verbose: bool = True,
) -> tuple[list[str], float, dict]:
    def _print(msg: str) -> None:
        if verbose:
            print(msg, flush=True)

    _print(f"\n{'='*60}")
    _print("  Pokemon Gen-1 Team Optimizer — Evolutionary Algorithm")
    _print(f"{'='*60}")
    _print(f"  pop_size={pop_size}  n_offspring={n_offspring}  generations={n_generations}")
    _print(f"  tournament_k={tournament_size}  mutation_p={mutation_prob}")
    _print(f"  opponents/eval={n_opponents}  battles/opp={n_battles_per_opp}")
    _print(f"{'='*60}\n")

    population: list[list[str]] = [
        random.sample(data.ALL_SPECIES, 6) for _ in range(pop_size)
    ]

    _print("Evaluating initial population …")
    fitnesses = [evaluate_fitness(g, n_opponents, n_battles_per_opp) for g in population]

    best_fitness = max(fitnesses)
    best_genome = population[fitnesses.index(best_fitness)]

    history = {
        "best": [best_fitness],
        "avg": [sum(fitnesses) / len(fitnesses)],
    }

    _print(f"Gen  0 | best={best_fitness:.4f}  avg={history['avg'][0]:.4f}")

    for gen in range(1, n_generations + 1):
        offspring: list[list[str]] = []
        off_fits: list[float] = []

        while len(offspring) < n_offspring:
            par1 = tournament_select(population, fitnesses, tournament_size)
            par2 = tournament_select(population, fitnesses, tournament_size)

            c1, c2 = crossfill(par1, par2)

            if random.random() < mutation_prob:
                c1 = mutate_swap(c1)
            if random.random() < mutation_prob:
                c2 = mutate_swap(c2)

            offspring.append(c1)
            if len(offspring) < n_offspring:
                offspring.append(c2)

        for child in offspring:
            off_fits.append(evaluate_fitness(child, n_opponents, n_battles_per_opp))

        combined = sorted(
            zip(population + offspring, fitnesses + off_fits),
            key=lambda x: x[1],
            reverse=True,
        )
        population = [g for g, _ in combined[:pop_size]]
        fitnesses = [f for _, f in combined[:pop_size]]

        gen_best = fitnesses[0]
        gen_avg = sum(fitnesses) / len(fitnesses)

        if gen_best > best_fitness:
            best_fitness = gen_best
            best_genome = population[0]

        history["best"].append(gen_best)
        history["avg"].append(gen_avg)

        team_str = ", ".join(data.species_names.get(s, s) for s in population[0])
        _print(
            f"Gen {gen:2d} | best={gen_best:.4f}  avg={gen_avg:.4f}  " f"| {team_str}"
        )

    return best_genome, best_fitness, history
