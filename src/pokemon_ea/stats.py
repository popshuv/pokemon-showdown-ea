"""Gen 1 stat formulas (Showdown ``statModify``) and battle stage multipliers."""

import math

DEFAULT_IV = 31
DEFAULT_EV = 0


def _trunc_ps(n: float) -> int:
    return math.trunc(n)


def stat_modify_hp(base: int, level: int, iv: int, ev: int) -> int:
    tr = _trunc_ps
    t = tr(2 * base + iv + tr(ev / 4) + 100)
    return tr(t * level / 100 + 10)


def stat_modify_other(base: int, level: int, iv: int, ev: int) -> int:
    tr = _trunc_ps
    t = tr(2 * base + iv + tr(ev / 4))
    return tr(t * level / 100 + 5)


_STAGE_TABLE = {
    -6: 2/8, -5: 2/7, -4: 2/6, -3: 2/5, -2: 2/4, -1: 2/3,
    0: 1.0,
    1: 3/2,  2: 4/2,  3: 5/2,  4: 6/2,  5: 7/2,  6: 8/2,
}


def stage_mult(stage: int) -> float:
    return _STAGE_TABLE[max(-6, min(6, stage))]
