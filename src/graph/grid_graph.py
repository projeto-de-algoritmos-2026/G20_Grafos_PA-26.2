# src/graph/grid_graph.py
"""
GridGraph — representa o dungeon como um grafo ponderado implícito.

Vértices  : células (col, row) cujo tile NÃO é parede.
Arestas   : conexões entre células adjacentes nas 4 direções cardinais.
Pesos     : definidos por um dicionário externo ou pelo valor padrão WEIGHT_FLOOR.

O grafo é "implícito" — não armazenamos a lista de adjacência explicitamente;
os vizinhos são calculados sob demanda. Isso mantém o uso de memória em O(V)
em vez de O(V + E).
"""

from __future__ import annotations
from typing import Callable, Iterator

from src.game.constants import GRID_W, GRID_H, WEIGHT_FLOOR


# Tipo de coordenada
Coord = tuple[int, int]


class GridGraph:
    """
    Grafo de grade 2D construído a partir de um TileMap.

    Attributes:
        width:   largura do grid em tiles.
        height:  altura do grid em tiles.
    """

    # Direções cardinais: (dx, dy)
    DIRECTIONS: tuple[Coord, ...] = ((0, -1), (0, 1), (-1, 0), (1, 0))

    def __init__(
        self,
        is_walkable: Callable[[int, int], bool],
        get_weight: Callable[[int, int], float] | None = None,
        width: int = GRID_W,
        height: int = GRID_H,
    ) -> None:
        """
        Args:
            is_walkable : função (col, row) → bool; retorna True para tiles
                          que podem ser atravessados (piso, corredor).
            get_weight  : função (col, row) → float; retorna o custo de ENTRAR
                          naquele tile. Se None, usa WEIGHT_FLOOR = 1.
            width       : largura do grid.
            height      : altura do grid.
        """
        self.width  = width
        self.height = height
        self._is_walkable = is_walkable
        self._get_weight  = get_weight or (lambda c, r: float(WEIGHT_FLOOR))

    # ── Consultas básicas ─────────────────────────────────────────────────────

    def in_bounds(self, col: int, row: int) -> bool:
        """Verifica se (col, row) está dentro dos limites do grid."""
        return 0 <= col < self.width and 0 <= row < self.height

    def is_walkable(self, col: int, row: int) -> bool:
        """Retorna True se a célula é caminhável (não é parede)."""
        return self.in_bounds(col, row) and self._is_walkable(col, row)

    def get_weight(self, col: int, row: int) -> float:
        """Custo de entrar na célula (col, row). Assume que é caminhável."""
        return self._get_weight(col, row)

    # ── Iteração de vizinhos ───────────────────────────────────────────────────

    def neighbors(
        self,
        col: int,
        row: int,
        blocked: set[Coord] | None = None,
    ) -> Iterator[tuple[Coord, float]]:
        """
        Gera os vizinhos caminháveis de (col, row) com seus pesos.

        Args:
            col, row : célula de origem.
            blocked  : conjunto de células adicionalmente bloqueadas (ex: outros
                       monstros). Se None, apenas paredes são ignoradas.

        Yields:
            ((nc, nr), weight) para cada vizinho válido.
        """
        extra_blocked: set[Coord] = blocked or set()
        for dc, dr in self.DIRECTIONS:
            nc, nr = col + dc, row + dr
            if not self.is_walkable(nc, nr):
                continue
            if (nc, nr) in extra_blocked:
                # Ainda retorna o vizinho, mas com peso elevado (pode contornar)
                yield (nc, nr), self.get_weight(nc, nr) + 5.0
            else:
                yield (nc, nr), self.get_weight(nc, nr)

    # ── Iteradores de vértices ────────────────────────────────────────────────

    def all_vertices(self) -> Iterator[Coord]:
        """Gera todas as células caminháveis do grid."""
        for row in range(self.height):
            for col in range(self.width):
                if self.is_walkable(col, row):
                    yield (col, row)

    # ── Utilitários ───────────────────────────────────────────────────────────

    def heuristic_manhattan(self, a: Coord, b: Coord) -> float:
        """Heurística de distância de Manhattan entre dois vértices."""
        return float(abs(a[0] - b[0]) + abs(a[1] - b[1]))

    def __repr__(self) -> str:
        return f"GridGraph(width={self.width}, height={self.height})"
