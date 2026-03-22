"""Type chart: effectiveness multipliers and exponent sums for heuristics."""

from . import data


def type_multiplier(attack_type: str, defender_types: list[str]) -> float:
    """
    Combined type-effectiveness multiplier vs. one or two defending types.

    Chart values are *exponents* summed in ``sum_exponents`` for move scoring;
    here we map them per type and multiply: +1 → ×2, −1 → ×0.5, ≤−4 → immune (×0).
    """
    mult = 1.0
    for dt in defender_types:
        score = data.type_chart_score.get(dt, {}).get(attack_type, 0)
        if score == 1:
            mult *= 2.0
        elif score == -1:
            mult *= 0.5
        elif score <= -4:
            return 0.0
    return mult


def sum_exponents(attack_type: str, defender_types: list[str]) -> int:
    """Sum chart exponents across the defender's types (heuristic aggressiveness)."""
    total = 0
    for dt in defender_types:
        total += data.type_chart_score.get(dt, {}).get(attack_type, 0)
    return total
