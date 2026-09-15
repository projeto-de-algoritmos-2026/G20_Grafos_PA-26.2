# tests/test_dijkstra.py
"""
Testes automatizados para o algoritmo de Dijkstra e sua comparação com o A*.
"""

import unittest
from src.graph.grid_graph import GridGraph
from src.algorithms.dijkstra import dijkstra_path, dijkstra_all_distances
from src.algorithms.astar import find_path_detailed, find_path


class TestDijkstra(unittest.TestCase):
    def setUp(self):
        """Cria uma grade 10x10 caminhável com pesos padrão (1.0)."""
        self.walkable_cells = {(x, y) for x in range(10) for y in range(10)}
        self.weights = {}

        def is_walkable(col: int, row: int) -> bool:
            return (col, row) in self.walkable_cells

        def get_weight(col: int, row: int) -> float:
            return self.weights.get((col, row), 1.0)

        self.graph = GridGraph(
            is_walkable=is_walkable,
            get_weight=get_weight,
            width=10,
            height=10,
        )

    def test_trivial_start_equals_goal(self):
        res = dijkstra_path((2, 2), (2, 2), self.graph)
        self.assertEqual(res.path, [(2, 2)])
        self.assertEqual(res.cost, 0.0)
        self.assertIn((2, 2), res.explored_nodes)

    def test_dijkstra_vs_astar_cost_equivalence(self):
        """Dijkstra e A* devem encontrar caminhos com o mesmo custo ótimo."""
        start = (0, 0)
        goal = (8, 8)

        d_res = dijkstra_path(start, goal, self.graph)
        a_res = find_path_detailed(start, goal, self.graph)

        self.assertTrue(len(d_res.path) > 0)
        self.assertTrue(len(a_res.path) > 0)
        self.assertEqual(d_res.path[0], start)
        self.assertEqual(d_res.path[-1], goal)
        self.assertEqual(a_res.path[0], start)
        self.assertEqual(a_res.path[-1], goal)

        # O custo acumulado do caminho deve ser estritamente igual (ambos ótimos)
        self.assertAlmostEqual(d_res.cost, a_res.cost)

        # A* deve explorar MENOS ou igual número de nós que o Dijkstra
        self.assertLessEqual(len(a_res.explored_nodes), len(d_res.explored_nodes))

    def test_dijkstra_respects_obstacles_and_weights(self):
        """Dijkstra deve contornar paredes e preferir caminhos de menor peso."""
        # Coloca uma parede vertical bloqueando de y=0 até y=7 em x=4
        for y in range(8):
            self.walkable_cells.remove((4, y))

        start = (1, 2)
        goal = (7, 2)

        res = dijkstra_path(start, goal, self.graph)
        self.assertTrue(len(res.path) > 0)
        # O caminho precisa passar por y >= 8 para contornar a parede
        max_y_in_path = max(p[1] for p in res.path)
        self.assertGreaterEqual(max_y_in_path, 8)

    def test_dijkstra_all_distances(self):
        """dijkstra_all_distances deve calcular a distância para todas as células alcançáveis."""
        start = (0, 0)
        distances, came_from = dijkstra_all_distances(start, self.graph)

        # Em grade 10x10 sem obstáculos, todas as 100 células devem ser alcançadas
        self.assertEqual(len(distances), 100)
        self.assertEqual(distances[(0, 0)], 0.0)
        # Manhattan (0,0) até (9,9) em custo 1 por passo = 18.0
        self.assertAlmostEqual(distances[(9, 9)], 18.0)

    def test_dungeon_generator_places_exit_via_dijkstra(self):
        """DungeonGenerator deve gerar mapa válido e posicionar saída alcançável via Dijkstra."""
        from src.dungeon.generator import DungeonGenerator
        from src.dungeon.tilemap import TileType

        gen = DungeonGenerator(seed=42)
        dungeon = gen.generate()

        self.assertIsNotNone(dungeon.tilemap)
        self.assertIsNotNone(dungeon.exit_pos)
        self.assertEqual(dungeon.tilemap.get(*dungeon.exit_pos), TileType.EXIT)

        # Deve existir caminho pelo labirinto do player_start até o exit_pos
        path_res = dijkstra_path(dungeon.player_start, dungeon.exit_pos, dungeon.graph)
        self.assertTrue(len(path_res.path) > 0)
        self.assertEqual(path_res.path[0], dungeon.player_start)
        self.assertEqual(path_res.path[-1], dungeon.exit_pos)


if __name__ == "__main__":
    unittest.main()
