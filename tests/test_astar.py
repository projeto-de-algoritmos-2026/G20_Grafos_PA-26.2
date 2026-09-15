# tests/test_astar.py
"""
Testes automatizados para o algoritmo A* e a classe GridGraph.
"""

import unittest
from src.graph.grid_graph import GridGraph
from src.algorithms.astar import find_path, find_path_detailed, next_step


class TestAStar(unittest.TestCase):
    def setUp(self):
        """Cria um grid 10x10 com todas as células caminháveis por padrão."""
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

    def test_manhattan_heuristic(self):
        """Heurística de Manhattan deve ser a soma das distâncias absolutas dx + dy."""
        h = self.graph.heuristic_manhattan((1, 2), (5, 7))
        self.assertEqual(h, 4.0 + 5.0)

    def test_straight_line_path(self):
        """Em linha reta desobstruída, o caminho deve ter passos consecutivos."""
        path = find_path((0, 0), (0, 3), self.graph)
        expected = [(0, 0), (0, 1), (0, 2), (0, 3)]
        self.assertEqual(path, expected)

    def test_next_step_helper(self):
        """next_step deve retornar a segunda célula do caminho (índice 1)."""
        step = next_step((0, 0), (0, 3), self.graph)
        self.assertEqual(step, (0, 1))

        # Start igual ao goal -> sem próximo passo
        step_same = next_step((0, 0), (0, 0), self.graph)
        self.assertIsNone(step_same)

    def test_obstacle_navigation(self):
        """A* deve contornar uma parede reta de forma ótima."""
        # Paredes em (2, 0), (2, 1), (2, 2)
        for y in range(3):
            self.walkable_cells.remove((2, y))

        start = (1, 1)
        goal = (3, 1)

        path = find_path(start, goal, self.graph)
        self.assertTrue(len(path) > 0)
        self.assertEqual(path[0], start)
        self.assertEqual(path[-1], goal)

        # O caminho não pode passar por nenhuma das paredes
        for wall in [(2, 0), (2, 1), (2, 2)]:
            self.assertNotIn(wall, path)

        # O caminho deve contornar passando por y >= 3
        max_y = max(p[1] for p in path)
        self.assertGreaterEqual(max_y, 3)

    def test_trap_weight_avoidance(self):
        """
        Dadas duas rotas possíveis:
        1. Rota direta passando por uma armadilha de peso 8.
        2. Rota de contorno com passos extras de peso 1.
        O A* deve preferir contornar se o custo total for menor.
        """
        # Caminho direto de (0,1) para (2,1) passando por (1,1)
        # Se (1,1) tiver peso 10, contornar por (0,2) -> (1,2) -> (2,2) -> (2,1)
        # custa 1 + 1 + 1 + 1 = 4 < 1 + 10 = 11.
        self.weights[(1, 1)] = 10.0

        res = find_path_detailed((0, 1), (2, 1), self.graph)
        self.assertTrue(len(res.path) > 0)
        # Não deve passar pela armadilha de peso 10
        self.assertNotIn((1, 1), res.path)
        self.assertLess(res.cost, 10.0)

    def test_unreachable_goal_returns_empty(self):
        """Se o destino estiver cercado por paredes, deve retornar lista vazia."""
        # Isola (5, 5) com paredes ao redor
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            self.walkable_cells.remove((5 + dx, 5 + dy))

        path = find_path((0, 0), (5, 5), self.graph)
        self.assertEqual(path, [])


if __name__ == "__main__":
    unittest.main()
