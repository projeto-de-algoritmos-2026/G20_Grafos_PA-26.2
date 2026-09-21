# src/algorithms/dijkstra.py
"""
Algoritmo de Dijkstra para busca de caminho mínimo em grafos ponderados.

Aplicações no projeto:
    1. Cálculo da Saída (Exit):
       Executa busca de fonte única a partir da posição inicial do jogador
       para encontrar o menor caminho até todas as células do dungeon. A saída
       é posicionada na sala com maior distância real no labirinto.
    2. Comparação Empírica com o A*:
       Executado em paralelo ao A* no modo debug (tecla TAB) para calcular o
       caminho do monstro até o jogador. Permite comparar número de nós
       explorados (área de busca omnidirecional vs heurística de Manhattan).

Complexidade:
    - O((V + E) log V) utilizando min-heap com heapq.
    - Onde V = células caminháveis e E = conexões cardinais válidas.
"""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.graph.grid_graph import GridGraph

Coord = tuple[int, int]


@dataclass
class DijkstraResult:
    """
    Resultado detalhado da execução do algoritmo de Dijkstra.

    Attributes:
        path           : lista de coordenadas da origem ao destino [start, ..., goal].
        cost           : custo acumulado total do caminho.
        explored_nodes : conjunto de nós totalmente avaliados (closed set).
        iterations     : número de expansões de nós no heap.
        time_us        : tempo de execução em microssegundos (µs).
    """
    path: list[Coord] = field(default_factory=list)
    cost: float = 0.0
    explored_nodes: set[Coord] = field(default_factory=set)
    iterations: int = 0
    time_us: float = 0.0


def _reconstruct_path(came_from: dict[Coord, Coord], current: Coord) -> list[Coord]:
    """Reconstrói o caminho da origem ao destino usando o dicionário de predecessores."""
    path: list[Coord] = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def dijkstra_path(
    start: Coord,
    goal: Coord,
    graph: "GridGraph",
    blocked: set[Coord] | None = None,
    max_iterations: int = 20_000,
) -> DijkstraResult:
    """
    Executa o algoritmo de Dijkstra pontual entre *start* e *goal*.

    Diferença chave para o A*:
        Dijkstra não possui heurística (h = 0 para todo nó). O critério de
        prioridade no heap é estritamente a distância percorrida g(n).
        Por isso, expande em ondas concêntricas para todas as direções.

    Args:
        start          : coordenada de origem (col, row).
        goal           : coordenada de destino (col, row).
        graph          : GridGraph do dungeon.
        blocked        : posições de outros monstros ou obstáculos dinâmicos.
        max_iterations : teto de iterações para prevenir loops.

    Returns:
        DijkstraResult contendo caminho, nós explorados e métricas.
    """
    t0 = time.perf_counter()

    if start == goal:
        elapsed = (time.perf_counter() - t0) * 1_000_000
        return DijkstraResult(
            path=[start],
            cost=0.0,
            explored_nodes={start},
            iterations=1,
            time_us=elapsed,
        )

    if not graph.is_walkable(*start) or not graph.is_walkable(*goal):
        elapsed = (time.perf_counter() - t0) * 1_000_000
        return DijkstraResult(time_us=elapsed)

    # open_heap armazena tuplas (distancia_acumulada, coord)
    open_heap: list[tuple[float, Coord]] = []
    heapq.heappush(open_heap, (0.0, start))

    dist: dict[Coord, float] = {start: 0.0}
    came_from: dict[Coord, Coord] = {}
    explored_nodes: set[Coord] = set()

    iterations = 0

    while open_heap:
        if iterations >= max_iterations:
            break
        iterations += 1

        cur_dist, current = heapq.heappop(open_heap)

        if current == goal:
            elapsed = (time.perf_counter() - t0) * 1_000_000
            explored_nodes.add(current)
            return DijkstraResult(
                path=_reconstruct_path(came_from, current),
                cost=cur_dist,
                explored_nodes=explored_nodes,
                iterations=iterations,
                time_us=elapsed,
            )

        if current in explored_nodes:
            continue
        explored_nodes.add(current)

        for neighbor, edge_weight in graph.neighbors(*current, blocked=blocked):
            if neighbor in explored_nodes:
                continue

            tentative_dist = cur_dist + edge_weight

            if tentative_dist < dist.get(neighbor, float("inf")):
                dist[neighbor] = tentative_dist
                came_from[neighbor] = current
                heapq.heappush(open_heap, (tentative_dist, neighbor))

    elapsed = (time.perf_counter() - t0) * 1_000_000
    return DijkstraResult(
        path=[],
        cost=float("inf"),
        explored_nodes=explored_nodes,
        iterations=iterations,
        time_us=elapsed,
    )


def dijkstra_all_distances(
    start: Coord,
    graph: "GridGraph",
    blocked: set[Coord] | None = None,
) -> tuple[dict[Coord, float], dict[Coord, Coord]]:
    """
    Executa Dijkstra de fonte única a partir de *start* para todos os vértices acessíveis.

    Usado na geração de dungeon para determinar as distâncias reais de menor caminho
    e encontrar a sala de maior custo para posicionar a saída (EXIT).

    Args:
        start   : célula inicial de origem (ex: spawn do jogador).
        graph   : GridGraph com as conexões e pesos dos tiles.
        blocked : células bloqueadas opcionais.

    Returns:
        (distances, came_from)
        - distances: mapeamento {coord: menor_distancia_desde_start}
        - came_from: mapeamento {coord: predecessor} para reconstrução de caminho
    """
    dist: dict[Coord, float] = {start: 0.0}
    came_from: dict[Coord, Coord] = {}
    visited: set[Coord] = set()

    open_heap: list[tuple[float, Coord]] = []
    heapq.heappush(open_heap, (0.0, start))

    while open_heap:
        cur_dist, current = heapq.heappop(open_heap)

        if current in visited:
            continue
        visited.add(current)

        for neighbor, edge_weight in graph.neighbors(*current, blocked=blocked):
            if neighbor in visited:
                continue

            tentative_dist = cur_dist + edge_weight

            if tentative_dist < dist.get(neighbor, float("inf")):
                dist[neighbor] = tentative_dist
                came_from[neighbor] = current
                heapq.heappush(open_heap, (tentative_dist, neighbor))

    return dist, came_from
