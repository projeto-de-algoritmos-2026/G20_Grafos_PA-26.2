# src/dungeon/tilemap.py
"""
TileMap — representa a grade de tiles do dungeon.

Cada célula (col, row) contém um valor do enum TileType:
    WALL     : parede sólida, intransponível.
    FLOOR    : piso de sala.
    CORRIDOR : piso de corredor gerado pela MST.

O TileMap também expõe callables compatíveis com o construtor de GridGraph.
"""

from __future__ import annotations

from enum import IntEnum

from src.game.constants import GRID_W, GRID_H, WEIGHT_FLOOR


class TileType(IntEnum):
    WALL     = 0
    FLOOR    = 1
    CORRIDOR = 2


class TileMap:
    """
    Grade bidimensional de tiles com utilitários para consulta e mutação.

    Internamente armazena uma lista de listas: self._grid[row][col].
    """

    def __init__(self, width: int = GRID_W, height: int = GRID_H) -> None:
        self.width  = width
        self.height = height
        # Inicializa tudo como WALL
        self._grid: list[list[TileType]] = [
            [TileType.WALL] * width for _ in range(height)
        ]

    # ── Acesso ────────────────────────────────────────────────────────────────

    def get(self, col: int, row: int) -> TileType:
        """Retorna o tile em (col, row). Levanta IndexError se fora dos limites."""
        if not (0 <= col < self.width and 0 <= row < self.height):
            raise IndexError(f"Tile ({col}, {row}) fora dos limites do mapa.")
        return self._grid[row][col]

    def set(self, col: int, row: int, tile: TileType) -> None:
        """Define o tile em (col, row)."""
        if not (0 <= col < self.width and 0 <= row < self.height):
            return   # ignora silenciosamente tiles fora dos limites
        self._grid[row][col] = tile

    def in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.width and 0 <= row < self.height

    # ── Escultores ────────────────────────────────────────────────────────────

    def carve_rect(
        self,
        col: int,
        row: int,
        w: int,
        h: int,
        tile: TileType = TileType.FLOOR,
    ) -> None:
        """
        Preenche o retângulo [col, col+w) × [row, row+h) com *tile*.
        Usado para esculpir salas.
        """
        for r in range(row, row + h):
            for c in range(col, col + w):
                self.set(c, r, tile)

    def carve_corridor_h(self, col1: int, col2: int, row: int) -> None:
        """Esculpe um corredor horizontal entre col1 e col2 na linha row."""
        for c in range(min(col1, col2), max(col1, col2) + 1):
            if self.get(c, row) == TileType.WALL:
                self.set(c, row, TileType.CORRIDOR)

    def carve_corridor_v(self, row1: int, row2: int, col: int) -> None:
        """Esculpe um corredor vertical entre row1 e row2 na coluna col."""
        for r in range(min(row1, row2), max(row1, row2) + 1):
            if self.get(col, r) == TileType.WALL:
                self.set(col, r, TileType.CORRIDOR)

    def carve_l_corridor(
        self,
        cx1: int, cy1: int,
        cx2: int, cy2: int,
        horizontal_first: bool = True,
    ) -> None:
        """
        Esculpe um corredor em 'L' (dois segmentos) entre dois centros.

        Args:
            cx1, cy1          : centro de origem.
            cx2, cy2          : centro de destino.
            horizontal_first  : se True, vai horizontal primeiro depois vertical;
                                caso contrário, inverte.
        """
        if horizontal_first:
            self.carve_corridor_h(cx1, cx2, cy1)
            self.carve_corridor_v(cy1, cy2, cx2)
        else:
            self.carve_corridor_v(cy1, cy2, cx1)
            self.carve_corridor_h(cx1, cx2, cy2)

    # ── Callables para GridGraph ──────────────────────────────────────────────

    def is_walkable(self, col: int, row: int) -> bool:
        """Retorna True para tiles não-parede (FLOOR ou CORRIDOR)."""
        if not self.in_bounds(col, row):
            return False
        return self._grid[row][col] != TileType.WALL

    def get_weight(self, col: int, row: int) -> float:
        """Custo de entrar em (col, row). Futuro: armadilhas teriam peso > 1."""
        return float(WEIGHT_FLOOR)

    # ── Iteradores ────────────────────────────────────────────────────────────

    def walkable_cells(self) -> list[tuple[int, int]]:
        """Retorna lista de todas as células caminháveis."""
        return [
            (c, r)
            for r in range(self.height)
            for c in range(self.width)
            if self._grid[r][c] != TileType.WALL
        ]

    def __repr__(self) -> str:
        return f"TileMap({self.width}×{self.height})"
