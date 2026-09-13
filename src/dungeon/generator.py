# src/dungeon/generator.py
"""
DungeonGenerator — geração procedural de dungeon usando MST (Kruskal).

Pipeline:
    1. Gera N salas retangulares aleatórias sem sobreposição.
    2. Constrói o grafo completo de salas (vértices = salas, pesos = distância).
    3. Aplica Kruskal para obter a MST → lista mínima de corredores.
    4. Esculpe salas e corredores no TileMap.
    5. Constrói o GridGraph sobre o TileMap para uso pelos algoritmos de IA.
    6. Retorna salas, arestas da MST e o TileMap/GridGraph prontos.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from src.dungeon.tilemap import TileMap, TileType
from src.graph.grid_graph import GridGraph
from src.algorithms.kruskal import kruskal_mst, Edge
from src.game.constants import (
    GRID_W, GRID_H,
    NUM_ROOMS, ROOM_MIN_SIZE, ROOM_MAX_SIZE, MAX_PLACE_TRIES,
)


# Tipo de coordenada
Coord = tuple[int, int]


@dataclass
class Room:
    """
    Sala retangular definida por canto superior-esquerdo (col, row)
    e dimensões (width, height).

    Attributes:
        col, row : posição do canto superior-esquerdo no grid.
        width    : largura em tiles.
        height   : altura em tiles.
    """
    col:    int
    row:    int
    width:  int
    height: int

    # ── Propriedades derivadas ─────────────────────────────────────────────

    @property
    def cx(self) -> int:
        """Coluna do centro da sala (arredondado para baixo)."""
        return self.col + self.width // 2

    @property
    def cy(self) -> int:
        """Linha do centro da sala (arredondado para baixo)."""
        return self.row + self.height // 2

    @property
    def center(self) -> Coord:
        return (self.cx, self.cy)

    @property
    def right(self) -> int:
        return self.col + self.width

    @property
    def bottom(self) -> int:
        return self.row + self.height

    def overlaps(self, other: "Room", margin: int = 1) -> bool:
        """
        Verifica sobreposição com margem de *margin* tiles de espaço.
        A margem garante pelo menos 1 tile de parede entre salas adjacentes.
        """
        return (
            self.col  - margin < other.right   and
            self.right + margin > other.col    and
            self.row  - margin < other.bottom  and
            self.bottom + margin > other.row
        )

    def random_floor_cell(self, rng: random.Random) -> Coord:
        """Retorna uma célula aleatória de piso dentro da sala (excl. bordas)."""
        c = rng.randint(self.col + 1, self.right  - 2)
        r = rng.randint(self.row + 1, self.bottom - 2)
        return (c, r)


@dataclass
class DungeonData:
    """
    Resultado da geração de um dungeon.

    Attributes:
        tilemap     : grade de tiles com salas e corredores esculpidos.
        graph       : GridGraph construído sobre o tilemap.
        rooms       : lista de salas geradas.
        mst_edges   : arestas da MST (corredores conectando as salas).
        player_start: posição inicial sugerida para o jogador.
    """
    tilemap:      TileMap
    graph:        GridGraph
    rooms:        list[Room]
    mst_edges:    list[Edge]
    player_start: Coord


class DungeonGenerator:
    """
    Gerador de dungeon procedural.

    Usage:
        gen  = DungeonGenerator(seed=42)
        data = gen.generate()
        # data.tilemap, data.graph, data.rooms, data.mst_edges, data.player_start
    """

    def __init__(
        self,
        seed: int | None = None,
        width: int   = GRID_W,
        height: int  = GRID_H,
        num_rooms: int         = NUM_ROOMS,
        room_min: int          = ROOM_MIN_SIZE,
        room_max: int          = ROOM_MAX_SIZE,
        max_tries: int         = MAX_PLACE_TRIES,
    ) -> None:
        """
        Args:
            seed      : semente para reprodutibilidade. None = aleatório.
            width     : largura do grid em tiles.
            height    : altura do grid em tiles.
            num_rooms : número de salas a gerar.
            room_min  : dimensão mínima de uma sala.
            room_max  : dimensão máxima de uma sala.
            max_tries : tentativas de posicionar cada sala sem sobreposição.
        """
        self._rng      = random.Random(seed)
        self.width     = width
        self.height    = height
        self.num_rooms = num_rooms
        self.room_min  = room_min
        self.room_max  = room_max
        self.max_tries = max_tries

    # ── Geração principal ─────────────────────────────────────────────────────

    def generate(self) -> DungeonData:
        """
        Executa o pipeline completo de geração e retorna um DungeonData.

        Steps:
            1. Tenta posicionar *num_rooms* salas sem sobreposição.
            2. Aplica Kruskal para obter a MST das salas.
            3. Esculpe salas e corredores no TileMap.
            4. Constrói e retorna o GridGraph + DungeonData.
        """
        # 1. Salas
        rooms = self._place_rooms()

        # 2. MST via Kruskal
        mst_edges = kruskal_mst(rooms) if len(rooms) >= 2 else []

        # 3. TileMap
        tilemap = TileMap(self.width, self.height)
        self._carve_rooms(tilemap, rooms)
        self._carve_corridors(tilemap, rooms, mst_edges)

        # 4. GridGraph
        graph = GridGraph(
            is_walkable=tilemap.is_walkable,
            get_weight=tilemap.get_weight,
            width=self.width,
            height=self.height,
        )

        # 5. Posição inicial do jogador: centro da primeira sala
        player_start: Coord = rooms[0].center if rooms else (1, 1)

        return DungeonData(
            tilemap=tilemap,
            graph=graph,
            rooms=rooms,
            mst_edges=mst_edges,
            player_start=player_start,
        )

    # ── Etapas internas ───────────────────────────────────────────────────────

    def _place_rooms(self) -> list[Room]:
        """
        Tenta posicionar *num_rooms* salas sem sobreposição.

        Usa *max_tries* tentativas por sala; salas que não couberem sem
        sobreposição após as tentativas são descartadas silenciosamente.

        Returns:
            Lista de Room posicionadas com sucesso (pode ser < num_rooms).
        """
        placed: list[Room] = []
        for _ in range(self.num_rooms):
            for _attempt in range(self.max_tries):
                w = self._rng.randint(self.room_min, self.room_max)
                h = self._rng.randint(self.room_min, self.room_max)
                # Posição com margem de 1 tile das bordas
                col = self._rng.randint(1, self.width  - w - 2)
                row = self._rng.randint(1, self.height - h - 2)
                candidate = Room(col=col, row=row, width=w, height=h)

                if all(not candidate.overlaps(p) for p in placed):
                    placed.append(candidate)
                    break   # passa para a próxima sala

        return placed

    def _carve_rooms(self, tilemap: TileMap, rooms: list[Room]) -> None:
        """Esculpe todas as salas como FLOOR no TileMap."""
        for room in rooms:
            tilemap.carve_rect(room.col, room.row, room.width, room.height)

    def _carve_corridors(
        self,
        tilemap: TileMap,
        rooms: list[Room],
        mst_edges: list[Edge],
    ) -> None:
        """
        Para cada aresta da MST, esculpe um corredor em 'L' entre os centros
        das duas salas conectadas.

        A escolha entre horizontal-primeiro e vertical-primeiro é aleatória,
        o que adiciona variedade visual ao dungeon.
        """
        for edge in mst_edges:
            a = rooms[edge.room_a]
            b = rooms[edge.room_b]
            h_first = self._rng.choice([True, False])
            tilemap.carve_l_corridor(a.cx, a.cy, b.cx, b.cy, h_first)

    # ── Utilitários ───────────────────────────────────────────────────────────

    def random_spawn_in_room(self, room: Room) -> Coord:
        """
        Retorna uma posição aleatória dentro de uma sala (sem bordas).
        Útil para posicionar monstros.
        """
        return room.random_floor_cell(self._rng)
