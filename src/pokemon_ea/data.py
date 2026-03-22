"""Load JSON game data from ``data/{species,moves,types}/`` at the repo root."""

import json
from pathlib import Path

# ``data.py`` is ``src/pokemon_ea/data.py``; repo root is two levels above this file.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA = _REPO_ROOT / "data"
_SPECIES = DATA / "species"
_MOVES = DATA / "moves"
_TYPES = DATA / "types"


def load_json(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


constraints = load_json(_SPECIES / "data.json")
move_types = load_json(_MOVES / "moveTypes.json")
move_categories = load_json(_MOVES / "moveCategories.json")
species_names = load_json(_SPECIES / "speciesNames.json")
species_types = load_json(_SPECIES / "speciesTypes.json")
species_base_hp = load_json(_SPECIES / "speciesBaseHp.json")
type_chart_score = load_json(_TYPES / "typeChartScore.json")

_base_stats_raw = load_json(_SPECIES / "speciesBaseStats.json")
BASE_STATS: dict[str, tuple[int, int, int, int]] = {
    k: tuple(v) for k, v in _base_stats_raw.items()
}

MOVE_POWER: dict[str, int] = load_json(_MOVES / "movePower.json")
MOVE_ACCURACY: dict[str, float] = load_json(_MOVES / "moveAccuracy.json")
STATUS_MOVES: dict[str, str] = load_json(_MOVES / "statusMoves.json")
MOVE_SECONDARY: dict[str, tuple[str, float]] = {
    k: (v[0], v[1]) for k, v in load_json(_MOVES / "moveSecondary.json").items()
}

ALL_SPECIES = list(constraints.keys())
