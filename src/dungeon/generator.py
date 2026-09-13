# src/dungeon/generator.py
"""
DungeonGenerator — geração procedural de dungeon usando MST (Kruskal).

Pipeline:
    1. Gera N salas retangulares aleatórias sem sobreposição.
    2. Constrói o grafo completo de salas (vértices = salas, pesos = distância).
    3. Aplica Kruskal para obter a MST → lista mínima de corredores.
    4. Esculpe salas e corredores no TileMap.
    5. Posiciona armadilhas aleatoriamente em tiles de piso/corredor.
    6. Constrói o GridGraph sobre o TileMap para uso pelos algoritmos de IA.
    7. Retorna salas, arestas da MST e o TileMap/GridGraph prontos.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from src.dungeon.tilemap import TileMap, TileType
from src.graph.grid_graph import GridGraph
from src.algorithms.kruskal import kruskal_mst, Edge
from src.entities.weapon import Weapon, random_weapon
from src.entities.item import Item, random_item
from src.game.constants import (
    GRID_W, GRID_H,
    NUM_ROOMS, ROOM_MIN_SIZE, ROOM_MAX_SIZE, MAX_PLACE_TRIES,
    NUM_TRAPS,
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

    def random_interior_cell(self, rng: random.Random) -> Coord:
        """Retorna uma célula aleatória dentro da sala (excluindo bordas)."""
        c = rng.randint(self.col + 1, self.right  - 2)
        r = rng.randint(self.row + 1, self.bottom - 2)
        return (c, r)

    # Alias mantido por compatibilidade
    def random_floor_cell(self, rng: random.Random) -> Coord:
        return self.random_interior_cell(rng)


@dataclass
class DungeonData:
    """
    Resultado da geração de um dungeon.

    Attributes:
        tilemap      : grade de tiles com salas, corredores e armadilhas.
        graph        : GridGraph construído sobre o tilemap.
        rooms        : lista de salas geradas.
        mst_edges    : arestas da MST (corredores conectando as salas).
        player_start : posição inicial sugerida para o jogador.
        trap_cells   : conjunto de células que eram armadilhas (para referência).
    """
    tilemap:      TileMap
    graph:        GridGraph
    rooms:        list[Room]
    mst_edges:    list[Edge]
    player_start: Coord
    exit_pos:     Coord
    trap_cells:   set[Coord] = field(default_factory=set)
    weapons:      dict[Coord, Weapon] = field(default_factory=dict)
    items:        dict[Coord, Item] = field(default_factory=dict)


class DungeonGenerator:
    """
    Gerador de dungeon procedural.

    Usage:
        gen  = DungeonGenerator(seed=42)
        data = gen.generate()
    """

    def __init__(
        self,
        seed: int | None = None,
        width: int        = GRID_W,
        height: int       = GRID_H,
        num_rooms: int    = NUM_ROOMS,
        room_min: int     = ROOM_MIN_SIZE,
        room_max: int     = ROOM_MAX_SIZE,
        max_tries: int    = MAX_PLACE_TRIES,
        num_traps: int    = NUM_TRAPS,
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
            num_traps : número de armadilhas a posicionar no dungeon.
        """
        self._rng      = random.Random(seed)
        self.width     = width
        self.height    = height
        self.num_rooms = num_rooms
        self.room_min  = room_min
        self.room_max  = room_max
        self.max_tries = max_tries
        self.num_traps = num_traps

    # ── Geração principal ─────────────────────────────────────────────────────

    def generate(self) -> DungeonData:
        """
        Executa o pipeline completo de geração e retorna um DungeonData.

        Steps:
            1. Tenta posicionar *num_rooms* salas sem sobreposição.
            2. Aplica Kruskal para obter a MST das salas.
            3. Esculpe salas e corredores no TileMap.
            4. Posiciona armadilhas em tiles de piso/corredor.
            5. Constrói e retorna o GridGraph + DungeonData.
        """
        # 1. Salas
        rooms = self._place_rooms()

        # 2. MST via Kruskal
        mst_edges = kruskal_mst(rooms) if len(rooms) >= 2 else []

        # 3. TileMap
        tilemap = TileMap(self.width, self.height)
        self._carve_rooms(tilemap, rooms)
        self._carve_corridors(tilemap, rooms, mst_edges)

        # 4. Armadilhas (antes de construir o grafo para que os pesos estejam certos)
        player_start: Coord = rooms[0].center if rooms else (1, 1)
        trap_cells = self._place_traps(tilemap, rooms, player_start)

        # 5. Armas
        weapons = self._place_weapons(tilemap, rooms, trap_cells)

        # 5.5 Itens
        items = self._place_items(tilemap, rooms, trap_cells, weapons)

        # 6. Saída (EXIT) na sala mais distante
        exit_pos = self._place_exit(tilemap, rooms, player_start)

        # 7. GridGraph (reconstrói após armadilhas/saída para refletir pesos)
        graph = GridGraph(
            is_walkable=tilemap.is_walkable,
            get_weight=tilemap.get_weight,
            width=self.width,
            height=self.height,
        )

        return DungeonData(
            tilemap=tilemap,
            graph=graph,
            rooms=rooms,
            mst_edges=mst_edges,
            player_start=player_start,
            exit_pos=exit_pos,
            trap_cells=trap_cells,
            weapons=weapons,
            items=items,
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
                # Posição com margem de 2 tiles das bordas
                col = self._rng.randint(2, self.width  - w - 3)
                row = self._rng.randint(2, self.height - h - 3)
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

    def _place_traps(
        self,
        tilemap: TileMap,
        rooms: list[Room],
        player_start: Coord,
        safe_radius: int = 4,
    ) -> set[Coord]:
        """
        Posiciona armadilhas em tiles de FLOOR ou CORRIDOR.

        Regras:
            - Nunca dentro do raio *safe_radius* ao redor do player_start.
            - Não na sala 0 (sala inicial do jogador).
            - Evita bordas das salas (células com col/row = borda da sala).

        Args:
            tilemap      : mapa já com salas e corredores esculpidos.
            rooms        : lista de salas.
            player_start : posição inicial do jogador (zona segura).
            safe_radius  : raio em tiles ao redor do player_start sem armadilhas.

        Returns:
            Conjunto de coordenadas onde armadilhas foram colocadas.
        """
        # Candidatos: qualquer tile de piso/corredor fora da zona segura
        px, py = player_start
        candidates: list[Coord] = []

        for r in range(tilemap.height):
            for c in range(tilemap.width):
                tile = tilemap.get(c, r)
                # Apenas no piso das salas
                if tile != TileType.FLOOR:
                    continue
                # Zona segura ao redor do jogador
                if abs(c - px) + abs(r - py) <= safe_radius:
                    continue
                
                # Verifica se está perto de uma porta (adjacente a um corredor)
                is_near_door = False
                for dc in [-1, 0, 1]:
                    for dr in [-1, 0, 1]:
                        if dc == 0 and dr == 0: continue
                        nc, nr = c + dc, r + dr
                        if tilemap.in_bounds(nc, nr) and tilemap.get(nc, nr) == TileType.CORRIDOR:
                            is_near_door = True
                            break
                    if is_near_door: break
                
                if is_near_door:
                    continue

                candidates.append((c, r))

        # Embaralha e pega os primeiros num_traps
        self._rng.shuffle(candidates)
        trap_cells: set[Coord] = set()

        for coord in candidates[:self.num_traps]:
            c, r = coord
            tilemap.set(c, r, TileType.TRAP)
            trap_cells.add(coord)

        return trap_cells

    def _place_weapons(
        self,
        tilemap: TileMap,
        rooms: list[Room],
        trap_cells: set[Coord],
    ) -> dict[Coord, Weapon]:
        """Posiciona armas aleatórias pelo mapa (uma por sala, exceto sala 0)."""
        weapons: dict[Coord, Weapon] = {}
        for room in rooms[1:]:
            # Tenta encontrar uma posição livre de armadilhas na sala
            for _ in range(5):
                c, r = room.random_interior_cell(self._rng)
                if (c, r) not in trap_cells and (c, r) not in weapons:
                    weapons[(c, r)] = random_weapon(self._rng)
                    break
        return weapons

    def _place_items(
        self,
        tilemap: TileMap,
        rooms: list[Room],
        trap_cells: set[Coord],
        weapons: dict[Coord, Weapon],
    ) -> dict[Coord, Item]:
        """Posiciona itens e armaduras aleatórias pelo mapa."""
        items: dict[Coord, Item] = {}
        for room in rooms[1:]:
            # Chance de 50% de ter um item na sala
            if self._rng.random() < 0.5:
                for _ in range(5):
                    c, r = room.random_interior_cell(self._rng)
                    if (c, r) not in trap_cells and (c, r) not in weapons and (c, r) not in items:
                        items[(c, r)] = random_item(self._rng)
                        break
        return items

    def _place_exit(
        self,
        tilemap: TileMap,
        rooms: list[Room],
        player_start: Coord,
    ) -> Coord:
        """Encontra a sala mais distante do player_start e coloca a saída (EXIT) lá."""
        furthest_room = rooms[-1]
        max_dist = -1
        px, py = player_start
        for room in rooms[1:]:
            dist = abs(room.cx - px) + abs(room.cy - py)
            if dist > max_dist:
                max_dist = dist
                furthest_room = room
        
        exit_pos = furthest_room.center
        tilemap.set(exit_pos[0], exit_pos[1], TileType.EXIT)
        return exit_pos

    # ── Utilitários ───────────────────────────────────────────────────────────

    def random_spawn_in_room(self, room: Room) -> Coord:
        """
        Retorna uma posição aleatória dentro de uma sala (sem bordas).
        Útil para posicionar monstros.
        """
        return room.random_floor_cell(self._rng)
