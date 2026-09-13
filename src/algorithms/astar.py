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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.graph.grid_graph import GridGraph

Coord = tuple[int, int]


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


def find_path(
    start: Coord,
    goal: Coord,
    graph: "GridGraph",
    blocked: set[Coord] | None = None,
    max_iterations: int = 10_000,
) -> list[Coord]:
    """
    Executa o algoritmo A* e retorna o caminho de *start* até *goal*.

    O caminho inclui start e goal. Se não houver caminho, retorna lista vazia.

    Args:
        start          : célula de origem (col, row).
        goal           : célula de destino (col, row).
        graph          : GridGraph com is_walkable e neighbors implementados.
        blocked        : conjunto de células adicionalmente bloqueadas (ex:
                         posições de outros monstros). None = sem bloqueios extras.
        max_iterations : limite de iterações para evitar loop infinito em mapas
                         muito grandes ou inacessíveis.

    Returns:
        list[Coord]: caminho completo [start, ..., goal], ou [] se inexistente.
    """
    # Caso trivial
    if start == goal:
        return [start]

    # Verificações de sanidade
    if not graph.is_walkable(*start) or not graph.is_walkable(*goal):
        return []

    # ── Estruturas do A* ──────────────────────────────────────────────────────
    # open_heap: min-heap de (f_score, g_score, coord)
    #   - f_score = g_score + h_score  (custo estimado total)
    #   - g_score = custo real acumulado desde start
    #   O g_score é incluído como segundo critério de desempate.
    open_heap: list[tuple[float, float, Coord]] = []
    heapq.heappush(open_heap, (0.0, 0.0, start))

    # g_score[n]: menor custo conhecido de start → n
    g_score: dict[Coord, float] = {start: 0.0}

    # came_from[n]: predecessor de n no melhor caminho conhecido
    came_from: dict[Coord, Coord] = {}

    # closed_set: nós já totalmente processados
    closed_set: set[Coord] = set()

    iterations = 0

    while open_heap:
        if iterations >= max_iterations:
            # Caminho não encontrado dentro do limite → retorna vazio
            return []
        iterations += 1

        _, g_current, current = heapq.heappop(open_heap)

        # Se chegamos ao goal, reconstrói e retorna
        if current == goal:
            return _reconstruct_path(came_from, current)

        # Ignora se já processado com custo menor (entradas duplicadas no heap)
        if current in closed_set:
            continue
        closed_set.add(current)

        # ── Expande vizinhos ──────────────────────────────────────────────────
        for neighbor, edge_weight in graph.neighbors(*current, blocked=blocked):
            if neighbor in closed_set:
                continue

            tentative_g = g_current + edge_weight

            # Só atualiza se encontrou caminho mais curto para este vizinho
            if tentative_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor]    = tentative_g
                came_from[neighbor] = current
                h = graph.heuristic_manhattan(neighbor, goal)
                f = tentative_g + h
                heapq.heappush(open_heap, (f, tentative_g, neighbor))

    # Heap esgotou sem encontrar goal
    return []


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

    Args:
        start   : posição atual do monstro.
        goal    : posição do jogador.
        graph   : GridGraph do dungeon.
        blocked : células bloqueadas (outros monstros).

    Returns:
        Coordenada do próximo passo, ou None se não há caminho.
    """
    path = find_path(start, goal, graph, blocked=blocked)
    if len(path) >= 2:
        return path[1]       # path[0] == start, path[1] == próximo passo
    return None              # sem caminho ou já está no destino
