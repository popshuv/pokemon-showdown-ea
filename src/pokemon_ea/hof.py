"""Hall of fame archive for competitive coevolution."""

from __future__ import annotations


class HallOfFame:
    """
    Fixed-size archive of the best genomes seen so far (by reported fitness).

    Genomes are keyed by full order (species + lead slot). When the same
    ordering is re-inserted with higher fitness, the stored score is updated.
    """

    def __init__(self, max_size: int = 12) -> None:
        self.max_size = max_size
        self._entries: list[tuple[tuple[str, ...], list[str], float]] = []

    def __len__(self) -> int:
        return len(self._entries)

    def add(self, genome: list[str], fitness: float) -> None:
        key = tuple(genome)
        for i, (k, g, f) in enumerate(self._entries):
            if k == key:
                if fitness > f:
                    self._entries[i] = (key, genome.copy(), fitness)
                return
        self._entries.append((key, genome.copy(), fitness))
        self._entries.sort(key=lambda x: x[2], reverse=True)
        if len(self._entries) > self.max_size:
            self._entries = self._entries[: self.max_size]

    @property
    def genomes(self) -> list[list[str]]:
        return [g for _, g, _ in self._entries]

    def extend_pool(self, live_population: list[list[str]]) -> list[list[str]]:
        """Live population plus archived genomes (archives may duplicate live)."""
        return list(live_population) + self.genomes
