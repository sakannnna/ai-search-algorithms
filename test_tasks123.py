"""前三题的边界验证和固定种子随机对照，可随时重新运行。"""

import unittest
from collections import deque
from random import Random

from task1_maze import astar as maze
from task2_weighted import search_terrain
from task3_game_tree import TreeNode, search_tree, tree_from_dict


class SearchTests(unittest.TestCase):
    def test_maze_boundaries(self):
        self.assertEqual(maze([], (0, 0), (0, 0)), [])
        self.assertEqual(maze([["."]], (0, 0), (0, 0)), [(0, 0)])
        self.assertEqual(maze([["X"]], (0, 0), (0, 0)), [])
        self.assertEqual(maze([["."]], (-1, 0), (0, 0)), [])
        self.assertEqual(maze([[".", "X", "."]], (0, 0), (0, 2)), [])

    def test_maze_random_against_bfs(self):
        rng = Random(42)
        for _ in range(200):
            grid = [["X" if rng.random() < .3 else "." for _ in range(8)] for _ in range(8)]
            grid[0][0] = grid[7][7] = "."
            distances = {(0, 0): 0}
            queue = deque([(0, 0)])
            while queue:
                r, c = queue.popleft()
                for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if 0 <= p[0] < 8 and 0 <= p[1] < 8 and grid[p[0]][p[1]] != "X" and p not in distances:
                        distances[p] = distances[r, c] + 1
                        queue.append(p)
            for mode in ("zero", "manhattan"):
                path = maze(grid, (0, 0), (7, 7), mode)
                self.assertEqual(len(path)-1 if path else -1, distances.get((7, 7), -1))
                if path:
                    self.assertEqual((path[0], path[-1]), ((0, 0), (7, 7)))
                    self.assertTrue(all(grid[r][c] != "X" for r, c in path))
                    self.assertTrue(all(abs(a[0]-b[0])+abs(a[1]-b[1]) == 1 for a, b in zip(path, path[1:])))

    def test_weighted_boundaries(self):
        for grid, start, end, expected in (
            ([], (0, 0), (0, 0), -1),
            ([[1]], (0, 0), (0, 0), 0),
            ([["S", "E"]], (0, 0), (0, 1), 0),
            ([["S", "X", "E"]], (0, 0), (0, 2), -1),
            ([["S", 8, "E"], [1, 1, 1]], (0, 0), (0, 2), 3),
            ([["S", 0, "E"]], (0, 0), (0, 2), 0),
        ):
            self.assertEqual(search_terrain(grid, start, end).cost, expected)
        for invalid in ([[1, -1]], [[1, 1.5]], [[1], [1, 2]]):
            with self.assertRaises(ValueError):
                search_terrain(invalid, (0, 0), (0, 0))

    def test_weighted_random_against_relaxation(self):
        rng = Random(43)
        for _ in range(200):
            grid = [["X" if rng.random() < .25 else rng.randrange(10) for _ in range(6)] for _ in range(6)]
            grid[0][0] = grid[5][5] = 1
            # 反复松弛所有边作为独立基准，不复用 A* 或其启发函数。
            distances = {(0, 0): 0}
            for _ in range(35):
                changed = False
                for (r, c), cost in list(distances.items()):
                    for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                        if not (0 <= p[0] < 6 and 0 <= p[1] < 6) or grid[p[0]][p[1]] == "X":
                            continue
                        value = cost + (0 if p == (5, 5) else grid[p[0]][p[1]])
                        if value < distances.get(p, float("inf")):
                            distances[p] = value
                            changed = True
                if not changed:
                    break
            for mode in ("zero", "manhattan"):
                result = search_terrain(grid, (0, 0), (5, 5), mode)
                self.assertEqual(result.cost, distances.get((5, 5), -1))
                if result.path:
                    self.assertEqual((result.path[0], result.path[-1]), ((0, 0), (5, 5)))
                    self.assertTrue(all(abs(a[0]-b[0])+abs(a[1]-b[1]) == 1 for a, b in zip(result.path, result.path[1:])))
                    self.assertEqual(sum(grid[r][c] for r, c in result.path[1:-1]), result.cost)

    def test_tree_random_and_boundaries(self):
        rng = Random(44)
        def build(depth):
            if depth == 0 or rng.random() < .2:
                return TreeNode(value=rng.randrange(-20, 21))
            return TreeNode(children=[build(depth-1) for _ in range(rng.randrange(1, 5))])
        def reference(node, maximizing=True):
            if not node.children:
                return node.value
            values = [reference(child, not maximizing) for child in node.children]
            return max(values) if maximizing else min(values)
        for tree in [TreeNode(value=0), TreeNode(value=-5)] + [build(5) for _ in range(200)]:
            expected = reference(tree)
            for order in ("left", "right"):
                full = search_tree(tree, "minimax", order)
                pruned = search_tree(tree, "alpha_beta", order)
                self.assertEqual(full.value, expected)
                self.assertEqual(pruned.value, expected)
                self.assertLessEqual(pruned.visited_nodes, full.visited_nodes)
        self.assertEqual(search_tree(tree_from_dict({"children": [{"value": 0}, {"value": 3}]})).value, 3)
        with self.assertRaises(ValueError):
            tree_from_dict({"is_maximizing_player": False})


if __name__ == "__main__":
    unittest.main()
