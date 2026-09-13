# src/graph/union_find.py
"""
Estrutura Union-Find (Disjoint Set Union) com compressão de caminho
e união por rank.

Usada pelo algoritmo de Kruskal para detectar ciclos em O(α(n)) por operação.
"""

from __future__ import annotations
from typing import Generic, Hashable, TypeVar

T = TypeVar("T", bound=Hashable)


class UnionFind(Generic[T]):
    """
    Union-Find genérico que aceita qualquer tipo hashable como elemento.

    Exemplo de uso:
        uf = UnionFind([0, 1, 2, 3])
        uf.union(0, 1)
        uf.connected(0, 1)  # True
        uf.connected(0, 2)  # False
    """

    def __init__(self, elements: list[T]) -> None:
        """
        Inicializa a estrutura com cada elemento em seu próprio conjunto.

        Args:
            elements: lista de elementos distintos a serem gerenciados.
        """
        self._parent: dict[T, T] = {e: e for e in elements}
        self._rank:   dict[T, int] = {e: 0 for e in elements}
        self._count: int = len(elements)   # número de componentes distintos

    # ── Consultas ─────────────────────────────────────────────────────────────

    def find(self, x: T) -> T:
        """
        Retorna o representante (raiz) do conjunto de *x*.
        Aplica compressão de caminho iterativa.
        """
        root = x
        # Sobe até a raiz
        while self._parent[root] != root:
            root = self._parent[root]
        # Compressão de caminho: aponta todos os nós diretamente para a raiz
        while self._parent[x] != root:
            self._parent[x], x = root, self._parent[x]
        return root

    def connected(self, x: T, y: T) -> bool:
        """Retorna True se *x* e *y* pertencem ao mesmo conjunto."""
        return self.find(x) == self.find(y)

    @property
    def num_components(self) -> int:
        """Número de componentes (conjuntos) disjuntos atualmente."""
        return self._count

    # ── Mutação ───────────────────────────────────────────────────────────────

    def union(self, x: T, y: T) -> bool:
        """
        Une os conjuntos de *x* e *y* (union por rank).

        Returns:
            True se os elementos estavam em conjuntos distintos (a aresta é
            útil para a MST); False se já estavam conectados (formaria ciclo).
        """
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False  # mesma componente → ciclo

        # Une a árvore menor à maior
        if self._rank[rx] < self._rank[ry]:
            rx, ry = ry, rx          # garante rank[rx] >= rank[ry]
        self._parent[ry] = rx
        if self._rank[rx] == self._rank[ry]:
            self._rank[rx] += 1

        self._count -= 1
        return True
