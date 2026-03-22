"""Heuristic move selection when building teams (four moves per species)."""

from . import data, effectiveness


def _best_move_eff(move_type: str, opp_ids: list[str]) -> tuple[int, int]:
    best_exp, n_super = float("-inf"), 0
    for sid in opp_ids:
        dtypes = data.species_types.get(sid, [])
        if not dtypes:
            continue
        exp = effectiveness.sum_exponents(move_type, dtypes)
        if exp > best_exp:
            best_exp = exp
        if exp > 0:
            n_super += 1
    return (0 if best_exp == float("-inf") else best_exp), n_super


def select_moves(species_id: str, opp_ids: list[str]) -> list[str]:
    d = data.constraints[species_id]
    seen: set[str] = set()
    pool: list[str] = []
    for m in (d.get("moves", []) + d.get("comboMoves", []) +
              d.get("essentialMoves", []) + d.get("exclusiveMoves", [])):
        if m not in seen:
            seen.add(m)
            pool.append(m)

    scores: dict[str, float] = {}
    for m in pool:
        mt = data.move_types.get(m)
        if not mt:
            scores[m] = 0.0
            continue
        best_exp, n_super = _best_move_eff(mt, opp_ids)
        scores[m] = best_exp * 1000 + n_super * 10

    candidates = sorted(
        [(m, scores.get(m, 0.0), data.move_types.get(m, "Normal")) for m in pool],
        key=lambda x: (-x[1], x[0]),
    )

    selected: list[str] = []
    sel_types: set[str] = set()

    while len(selected) < 4:
        best_idx, best_adj = -1, float("-inf")
        for i, (mid, sc, mt) in enumerate(candidates):
            if mid in selected:
                continue
            adj = sc - (50 if mt in sel_types else 0)
            if adj > best_adj:
                best_adj, best_idx = adj, i
        if best_idx == -1:
            break
        mid, _, mt = candidates[best_idx]
        selected.append(mid)
        sel_types.add(mt)

    for m in pool:
        if len(selected) >= 4:
            break
        if m not in selected:
            selected.append(m)

    return selected[:4]
