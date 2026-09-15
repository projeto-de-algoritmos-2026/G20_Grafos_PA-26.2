# src/algorithms/astar.py
"""
Algoritmo A* para busca de caminho mínimo em grafos ponderados.

Aplicação no projeto:
    Cada monstro usa A* sobre o GridGraph para encontrar o menor caminho
    até o jogador, evitando paredes e (parcialmente) outros monstros.

Heurística:
    Distância de Manhattan: h(n) = |n.x - goal.x| + |n.y - goal.y|
    Admissível para grades com movimentos cardinais (sem diagonais) e custo ≥ 1.
    Garante que A* retorne o caminho ótimo.

Complexidade:
    - O(V log V) no pior caso, onde V = número de células caminháveis.
    - Na prática muito mais rápido devido à heurística que guia a busca.

Referências:
    Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). A formal basis for the
    heuristic determination of minimum cost paths. IEEE Transactions on Systems
    Science and Cybernetics.
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
class AStarResult:
    """
    Resultado detalhado da execução do algoritmo A*.

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
    """
    Reconstrói o caminho de trás para frente a partir do mapa de predecessores.

    Args:
        came_from : dicionário {nó: predecessor}.
        current   : nó de destino (goal).

    Returns:
        Lista de coordenadas da origem ao destino (inclusive).
    """
    path: list[Coord] = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def find_path_detailed(
    start: Coord,
    goal: Coord,
    graph: "GridGraph",
    blocked: set[Coord] | None = None,
    max_iterations: int = 10_000,
) -> AStarResult:
    """
    Executa o algoritmo A* e retorna métricas detalhadas de busca.

    Args:
        start          : célula de origem (col, row).
        goal           : célula de destino (col, row).
        graph          : GridGraph com is_walkable e neighbors implementados.
        blocked        : conjunto de células adicionalmente bloqueadas.
        max_iterations : limite de iterações para evitar loop infinito.

    Returns:
        AStarResult com caminho, custo, nós explorados e tempo de execução.
    """
    t0 = time.perf_counter()

    # Caso trivial
    if start == goal:
        elapsed = (time.perf_counter() - t0) * 1_000_000
        return AStarResult(
            path=[start],
            cost=0.0,
            explored_nodes={start},
            iterations=1,
            time_us=elapsed,
        )

    # Verificações de sanidade
    if not graph.is_walkable(*start) or not graph.is_walkable(*goal):
        elapsed = (time.perf_counter() - t0) * 1_000_000
        return AStarResult(time_us=elapsed)

    # open_heap: min-heap de (f_score, g_score, coord)
    open_heap: list[tuple[float, float, Coord]] = []
    heapq.heappush(open_heap, (0.0, 0.0, start))

    g_score: dict[Coord, float] = {start: 0.0}
    came_from: dict[Coord, Coord] = {}
    closed_set: set[Coord] = set()

    iterations = 0

    while open_heap:
        if iterations >= max_iterations:
            break
        iterations += 1

        _, g_current, current = heapq.heappop(open_heap)

        if current == goal:
            elapsed = (time.perf_counter() - t0) * 1_000_000
            closed_set.add(current)
            return AStarResult(
                path=_reconstruct_path(came_from, current),
                cost=g_current,
                explored_nodes=closed_set,
                iterations=iterations,
                time_us=elapsed,
            )

        if current in closed_set:
            continue
        closed_set.add(current)

        for neighbor, edge_weight in graph.neighbors(*current, blocked=blocked):
            if neighbor in closed_set:
                continue

            tentative_g = g_current + edge_weight

            if tentative_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor]   = tentative_g
                came_from[neighbor] = current
                h = graph.heuristic_manhattan(neighbor, goal)
                f = tentative_g + h
                heapq.heappush(open_heap, (f, tentative_g, neighbor))

    elapsed = (time.perf_counter() - t0) * 1_000_000
    return AStarResult(
        path=[],
        cost=float("inf"),
        explored_nodes=closed_set,
        iterations=iterations,
        time_us=elapsed,
    )


def find_path(
    start: Coord,
    goal: Coord,
    graph: "GridGraph",
    blocked: set[Coord] | None = None,
    max_iterations: int = 10_000,
) -> list[Coord]:
    """
    Executa o algoritmo A* e retorna o caminho de *start* até *goal*.

    Conveniência para compatibilidade com o restante do projeto.
    """
    return find_path_detailed(
        start, goal, graph, blocked=blocked, max_iterations=max_iterations
    ).path


def next_step(
    start: Coord,
    goal: Coord,
    graph: "GridGraph",
    blocked: set[Coord] | None = None,
) -> Coord | None:
    """
    Retorna apenas o **próximo passo** no caminho de *start* a *goal*.

    Conveniência para MonsterAI: em vez de retornar o caminho inteiro,
    retorna somente a segunda célula (índice 1), que é o passo imediato.
    """
    path = find_path(start, goal, graph, blocked=blocked)
    if len(path) >= 2:
        return path[1]
    return None
