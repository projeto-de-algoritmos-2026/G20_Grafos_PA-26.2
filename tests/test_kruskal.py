# tests/test_kruskal.py
"""
Testes automatizados para o algoritmo de Kruskal e a estrutura Union-Find.
"""

import math
import unittest
from dataclasses import dataclass

from src.graph.union_find import UnionFind
from src.algorithms.kruskal import kruskal_mst, build_complete_graph, Edge


@dataclass
class MockRoom:
    """Mock simplificado de Room contendo coordenadas de centro cx e cy."""
    cx: int
    cy: int


class TestUnionFind(unittest.TestCase):
    """Testes unitários para a estrutura de dados Union-Find (Disjoint Set)."""

    def test_initialization(self):
        uf = UnionFind([0, 1, 2, 3])
        self.assertEqual(uf.num_components, 4)
        for i in range(4):
            self.assertEqual(uf.find(i), i)

    def test_union_and_connected(self):
        uf = UnionFind([0, 1, 2, 3])
        
        # Une 0 e 1 -> deve retornar True (estavam separados)
        self.assertTrue(uf.union(0, 1))
        self.assertEqual(uf.num_components, 3)
        self.assertTrue(uf.connected(0, 1))
        self.assertFalse(uf.connected(0, 2))

        # Une 1 e 2 -> deve retornar True
        self.assertTrue(uf.union(1, 2))
        self.assertEqual(uf.num_components, 2)
        self.assertTrue(uf.connected(0, 2))  # Transitividade

        # Une 0 e 2 novamente -> deve retornar False (já na mesma componente, ciclo evitado)
        self.assertFalse(uf.union(0, 2))
        self.assertEqual(uf.num_components, 2)

    def test_path_compression(self):
        """Garante que sucessivas uniões e finds comprimem a árvore."""
        uf = UnionFind([0, 1, 2, 3, 4])
        uf.union(0, 1)
        uf.union(1, 2)
        uf.union(2, 3)
        root = uf.find(0)
        # Após find(0), o pai direto de 0 deve ser o root
        self.assertEqual(uf.find(0), root)
        self.assertEqual(uf._parent[0], root)


class TestKruskalMST(unittest.TestCase):
    """Testes unitários para a geração de MST via Kruskal."""

    def test_requires_at_least_two_rooms(self):
        with self.assertRaises(ValueError):
            kruskal_mst([])
        with self.assertRaises(ValueError):
            kruskal_mst([MockRoom(cx=0, cy=0)])

    def test_triangle_discards_heaviest_edge(self):
        """
        Em um triângulo retângulo com vértices em (0,0), (3,0) e (0,4):
        - Aresta A-B = dist 3
        - Aresta A-C = dist 4
        - Aresta B-C = dist 5 (hipotenusa)
        Kruskal deve obrigatoriamente selecionar as arestas de peso 3 e 4,
        descartando a hipotenusa de peso 5.
        """
        rooms = [
            MockRoom(cx=0, cy=0),  # 0
            MockRoom(cx=3, cy=0),  # 1
            MockRoom(cx=0, cy=4),  # 2
        ]
        mst = kruskal_mst(rooms)

        self.assertEqual(len(mst), 2)  # N - 1 arestas
        weights = sorted([e.weight for e in mst])
        self.assertAlmostEqual(weights[0], 3.0)
        self.assertAlmostEqual(weights[1], 4.0)

    def test_mst_connectivity_and_acyclic(self):
        """Para N salas aleatórias, a MST deve ter exatamente N-1 arestas e conectar todas as salas."""
        rooms = [
            MockRoom(cx=10, cy=10),
            MockRoom(cx=50, cy=10),
            MockRoom(cx=10, cy=50),
            MockRoom(cx=50, cy=50),
            MockRoom(cx=25, cy=25),
        ]
        mst = kruskal_mst(rooms)

        # 1. Quantidade de arestas: |E| = |V| - 1
        self.assertEqual(len(mst), len(rooms) - 1)

        # 2. Conexão total sem ciclos (verificado reconstruindo com Union-Find)
        uf = UnionFind(list(range(len(rooms))))
        for edge in mst:
            # Cada aresta da MST deve unir duas componentes distintas
            self.assertTrue(uf.union(edge.room_a, edge.room_b))

        # Todas as salas devem pertencer à mesma componente
        self.assertEqual(uf.num_components, 1)


if __name__ == "__main__":
    unittest.main()
