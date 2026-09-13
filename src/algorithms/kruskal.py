# src/algorithms/kruskal.py
"""
Algoritmo de Kruskal para geração de Árvore Geradora Mínima (MST).

Aplicação no projeto:
    As salas do dungeon são os VÉRTICES do grafo.
    Todas as combinações de pares de salas formam as ARESTAS do grafo completo,
    com peso = distância euclidiana entre os centros das salas.
    O Kruskal seleciona o subconjunto de arestas de menor custo total que
    conecta todas as salas sem formar ciclos → lista de corredores a construir.

Complexidade:
    - O(E log E) para ordenar as arestas, onde E = N*(N-1)/2 para N salas.
    - O(E · α(V)) para as operações Union-Find.
    - Total efetivo: O(N² log N) para um grafo completo de salas.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.graph.union_find import UnionFind

if TYPE_CHECKING:
    from src.dungeon.generator import Room


@dataclass(frozen=True, order=True)
class Edge:
    """
    Aresta ponderada entre duas salas.

    Attributes:
        weight : custo da aresta (distância euclidiana entre centros).
        room_a : índice da primeira sala na lista de salas.
        room_b : índice da segunda sala na lista de salas.
    """
    weight: float
    room_a: int = field(compare=False)
    room_b: int = field(compare=False)


def _euclidean(ax: float, ay: float, bx: float, by: float) -> float:
    """Distância euclidiana entre dois pontos."""
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


def build_complete_graph(rooms: list["Room"]) -> list[Edge]:
    """
    Constrói o grafo completo de salas: aresta entre cada par (i, j).

    Args:
        rooms: lista de objetos Room com atributos cx, cy (centro).

    Returns:
        Lista de Edge não ordenada com N*(N-1)/2 arestas.
    """
    edges: list[Edge] = []
    n = len(rooms)
    for i in range(n):
        for j in range(i + 1, n):
            w = _euclidean(rooms[i].cx, rooms[i].cy, rooms[j].cx, rooms[j].cy)
            edges.append(Edge(weight=w, room_a=i, room_b=j))
    return edges


def kruskal_mst(rooms: list["Room"]) -> list[Edge]:
    """
    Executa o algoritmo de Kruskal para obter a MST entre as salas.

    Passos:
        1. Constrói o grafo completo de salas.
        2. Ordena as arestas por peso crescente.
        3. Itera sobre as arestas; adiciona aquelas que não formam ciclo
           (verificado via Union-Find).
        4. Para quando |MST| = N − 1 arestas.

    Args:
        rooms: lista de Room com pelo menos 2 elementos.

    Returns:
        Lista de Edge da MST (len = len(rooms) - 1).

    Raises:
        ValueError: se a lista de salas for vazia ou tiver apenas 1 sala.
    """
    if len(rooms) < 2:
        raise ValueError("Kruskal requer pelo menos 2 salas.")

    # 1. Grafo completo ordenado
    edges = sorted(build_complete_graph(rooms))          # O(E log E)

    # 2. Union-Find inicializado com índices das salas
    uf = UnionFind(list(range(len(rooms))))

    mst_edges: list[Edge] = []
    target = len(rooms) - 1    # MST de N vértices tem exatamente N-1 arestas

    # 3. Iteração de Kruskal
    for edge in edges:
        if len(mst_edges) == target:
            break                                        # MST completa

        # union() retorna True apenas se os vértices estão em componentes
        # distintas, ou seja, adicionar esta aresta NÃO forma um ciclo.
        if uf.union(edge.room_a, edge.room_b):
            mst_edges.append(edge)

    return mst_edges
