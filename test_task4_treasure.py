"""第四题的独立验证：Dijkstra 校验距离，排列枚举校验博弈结果。"""

import heapq
import unittest
from itertools import permutations

from task4_treasure import (
    GRID, POSITIONS, NAMES, GameState, apply_move,
    astar_cost, build_distance_matrix, search_game,
)


def reference_distance(start, end):
    """独立 Dijkstra，不调用待测 A* 的代价处理或启发函数。"""
    queue = [(0, start)]
    done = set()
    while queue:
        distance, position = heapq.heappop(queue)
        if position in done:
            continue
        done.add(position)
        if position == end:
            return distance
        r, c = position
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < 7 and 0 <= nc < 7 and GRID[nr][nc] != "X":
                cell = GRID[nr][nc]
                cost = cell if isinstance(cell, int) else 1
                heapq.heappush(queue, (distance + cost, (nr, nc)))
    return -1


def enumerate_reference(matrix, depth):
    """先枚举所有行动序列，再逐层回传，不复用待测状态更新函数。"""
    values = {2: 9, 3: 6, 4: 7, 5: 7}
    scores = {}
    for moves in permutations((2, 3, 4, 5), depth):
        positions = [0, 1]
        utility = 0
        for turn, target in enumerate(moves):
            player = turn % 2
            gain = values[target] - matrix[positions[player]][target]
            utility += gain if player == 0 else -gain
            positions[player] = target
        scores[moves] = utility
    # 一次归并一层，直到只剩各个首步对应的最优值。
    for length in range(depth - 1, 0, -1):
        parents = {}
        for moves, score in scores.items():
            parents.setdefault(moves[:length], []).append(score)
        choose = max if length % 2 == 0 else min
        scores = {prefix: choose(children) for prefix, children in parents.items()}
    best = max(scores.values())
    return best, {NAMES[moves[0]] for moves, score in scores.items() if score == best}


class TreasureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = build_distance_matrix()

    def test_distances(self):
        for i, start in enumerate(POSITIONS):
            for j, end in enumerate(POSITIONS):
                self.assertEqual(self.matrix[i][j], reference_distance(start, end))
        self.assertEqual(astar_cost([["A", "T1"]], (0, 0), (0, 1)), 1)
        self.assertEqual(astar_cost([["A", "X", "T1"]], (0, 0), (0, 2)), -1)

    def test_state_updates(self):
        original = GameState()
        after_a = apply_move(original, 3, self.matrix)
        self.assertEqual(after_a.a_position, 3)
        self.assertEqual(after_a.a_score, 6 - self.matrix[0][3])
        self.assertEqual(after_a.player, "B")
        self.assertNotIn(3, after_a.remaining)
        after_b = apply_move(after_a, 2, self.matrix)
        self.assertEqual(after_b.b_position, 2)
        self.assertEqual(after_b.b_score, 9 - self.matrix[1][2])
        self.assertEqual(after_b.player, "A")
        self.assertEqual(original, GameState())
        with self.assertRaises(ValueError):
            apply_move(after_a, 3, self.matrix)

    def test_search_against_enumeration(self):
        for depth in (1, 2, 3, 4):
            expected, targets = enumerate_reference(self.matrix, depth)
            for order in ("fixed", "reverse", "gain"):
                full = search_game(self.matrix, depth, "minimax", order)
                pruned = search_game(self.matrix, depth, "alpha_beta", order)
                for result in (full, pruned):
                    self.assertEqual(result.best_value, expected)
                    self.assertIn(result.best_target, targets)
                self.assertLessEqual(pruned.visited_nodes, full.visited_nodes)
                self.assertEqual(pruned.best_target, full.best_target)

    def test_given_examples(self):
        for depth, target, value in ((2, "T2", -1), (4, "T3", 3)):
            for algorithm in ("minimax", "alpha_beta"):
                result = search_game(self.matrix, depth, algorithm)
                self.assertEqual((result.best_target, result.best_value), (target, value))

    def test_terminal_states(self):
        for state in (GameState(a_score=5, b_score=2),
                      GameState(remaining=(), a_score=5, b_score=2)):
            result = search_game(self.matrix, 0, state=state)
            self.assertEqual((result.best_target, result.best_value), (None, 3))
        result = search_game(self.matrix, 4, state=GameState(remaining=()))
        self.assertEqual(result.visited_nodes, 1)
        self.assertIsNone(result.best_target)


if __name__ == "__main__":
    unittest.main()
