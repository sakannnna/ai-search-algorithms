"""题目四：使用 A* 和博弈搜索求竞争环境下的最优宝藏选择。"""

import argparse
import heapq
import json
from dataclasses import dataclass, replace
from itertools import count
from time import perf_counter


NAMES = ("A", "B", "T1", "T2", "T3", "T4")
POSITIONS = ((0, 0), (6, 6), (0, 6), (2, 2), (4, 4), (6, 0))
VALUES = {2: 9, 3: 6, 4: 7, 5: 7}
GRID = [
    ["A", 1, 1, "X", 2, 1, "T1"],
    [1, "X", 6, "X", 1, "X", 1],
    [1, 1, "T2", 1, 1, 1, 1],
    ["X", 1, "X", 8, "X", 1, "X"],
    [1, 1, 1, 1, "T3", 1, 1],
    [1, "X", 9, "X", 1, "X", 1],
    ["T4", 1, 1, "X", 1, 1, "B"],
]


def astar_cost(grid, start, end):
    """返回最小进入代价；本题所有标记格代价为 1，终点不免费。"""
    def weight(p):
        r, c = p
        if not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
            return None
        cell = grid[r][c]
        if cell == "X":
            return None
        return cell if isinstance(cell, int) else 1

    if weight(start) is None or weight(end) is None:
        return -1

    def estimate(p):
        return abs(p[0] - end[0]) + abs(p[1] - end[1])

    # 地图中的进入代价均至少为 1，因此曼哈顿距离不会高估。
    sequence = count()
    heap = [(estimate(start), next(sequence), 0, start)]
    distances = {start: 0}
    while heap:
        _, _, cost, current = heapq.heappop(heap)
        if cost != distances[current]:
            continue
        if current == end:
            return cost
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = current[0] + dr, current[1] + dc
            entry_cost = weight(neighbor)
            if entry_cost is None:
                continue
            candidate = cost + entry_cost
            if candidate < distances.get(neighbor, float("inf")):
                distances[neighbor] = candidate
                heapq.heappush(heap, (candidate + estimate(neighbor), next(sequence), candidate, neighbor))
    return -1


def build_distance_matrix():
    """分别计算所有有序位置对，不假设一般加权地图的距离对称。"""
    matrix = [[astar_cost(GRID, a, b) for b in POSITIONS] for a in POSITIONS]
    if any(distance < 0 for row in matrix for distance in row):
        raise ValueError("存在不可达的位置，当前博弈模型要求六个位置互相可达")
    return matrix


@dataclass(frozen=True)
class GameState:
    """位置与宝藏用 NAMES 下标表示；不可变状态避免污染其他分支。"""

    a_position: int = 0
    b_position: int = 1
    remaining: tuple[int, ...] = (2, 3, 4, 5)
    a_score: int = 0
    b_score: int = 0
    player: str = "A"

    @property
    def utility(self):
        return self.a_score - self.b_score


def apply_move(state, target, matrix):
    """获取一个宝藏并切换玩家；负收益行动也合法，不允许跳过回合。"""
    if target not in state.remaining:
        raise ValueError("目标宝藏已被获取或不存在")
    remaining = tuple(t for t in state.remaining if t != target)
    if state.player == "A":
        gain = VALUES[target] - matrix[state.a_position][target]
        return replace(state, a_position=target, a_score=state.a_score + gain,
                       remaining=remaining, player="B")
    gain = VALUES[target] - matrix[state.b_position][target]
    return replace(state, b_position=target, b_score=state.b_score + gain,
                   remaining=remaining, player="A")


@dataclass
class SearchResult:
    best_target: str | None
    best_value: int
    visited_nodes: int
    evaluated_leaves: int
    cutoffs: int
    elapsed_seconds: float


def search_game(matrix, depth, algorithm="alpha_beta", order="fixed", state=None):
    """按指定深度搜索；并列时选择当前访问顺序中最先遇到的最优目标。

    统计包含根节点；剪枝次数只计确实跳过剩余子节点的事件。
    耗时仅包含博弈搜索，不包含距离预计算和输出。
    """
    if depth < 0:
        raise ValueError("搜索深度不能为负")
    if algorithm not in ("minimax", "alpha_beta"):
        raise ValueError("算法必须为 minimax 或 alpha_beta")
    if order not in ("fixed", "reverse", "gain"):
        raise ValueError("访问顺序必须为 fixed、reverse 或 gain")
    started = perf_counter()
    visited = leaves = cutoffs = 0

    def targets(current):
        if order == "reverse":
            return tuple(reversed(current.remaining))
        if order == "gain":
            position = current.a_position if current.player == "A" else current.b_position
            # 双方都优先尝试自身即时收益高的行动；并列保持原顺序。
            return tuple(sorted(current.remaining,
                                key=lambda t: VALUES[t] - matrix[position][t], reverse=True))
        return current.remaining

    def visit(current, remaining_depth, alpha, beta):
        nonlocal visited, leaves, cutoffs
        visited += 1
        if remaining_depth == 0 or not current.remaining:
            leaves += 1
            return current.utility, None
        maximizing = current.player == "A"
        best = float("-inf") if maximizing else float("inf")
        best_target = None
        moves = targets(current)
        for index, target in enumerate(moves):
            child = apply_move(current, target, matrix)
            value, _ = visit(child, remaining_depth - 1, alpha, beta)
            if (maximizing and value > best) or (not maximizing and value < best):
                best, best_target = value, target
            if algorithm == "alpha_beta":
                if maximizing:
                    alpha = max(alpha, best)
                else:
                    beta = min(beta, best)
                if alpha >= beta:
                    if index + 1 < len(moves):
                        cutoffs += 1
                    break
        return best, best_target

    value, target = visit(state if state is not None else GameState(), depth,
                          float("-inf"), float("inf"))
    return SearchResult(NAMES[target] if target is not None else None, value,
                        visited, leaves, cutoffs, perf_counter() - started)


def main():
    parser = argparse.ArgumentParser(description="题目四：竞争环境下的宝藏分配")
    parser.add_argument("--compare", action="store_true", help="比较不同访问顺序的搜索统计")
    parser.add_argument("--json", action="store_true", help="仅输出 JSON 决策结果")
    parser.add_argument("--depth", type=int, choices=(2, 4), help="选择搜索深度，默认同时计算 2 和 4")
    parser.add_argument("--algorithm", choices=("minimax", "alpha_beta"), default="alpha_beta",
                        help="JSON 模式使用的算法")
    args = parser.parse_args()
    if args.json and args.compare:
        parser.error("--json 与 --compare 不能同时使用")
    started = perf_counter()
    matrix = build_distance_matrix()
    elapsed = perf_counter() - started
    depths = (args.depth,) if args.depth else (2, 4)
    if args.json:
        decisions = {}
        for depth in depths:
            outcome = search_game(matrix, depth, args.algorithm)
            decisions[str(depth)] = {"best_target": outcome.best_target, "best_value": outcome.best_value}
        print(json.dumps(decisions[str(args.depth)] if args.depth else decisions))
        return
    print("最小移动代价矩阵：")
    print("    " + "".join(f"{name:>5}" for name in NAMES))
    for name, row in zip(NAMES, matrix):
        print(f"{name:>4}" + "".join(f"{cost:>5}" for cost in row))
    print(f"距离矩阵预计算耗时：{elapsed * 1000:.4f} 毫秒")
    for depth in depths:
        for order in (("fixed", "reverse", "gain") if args.compare else ("fixed",)):
            for algorithm in ("minimax", "alpha_beta"):
                result = search_game(matrix, depth, algorithm, order)
                print(f"H={depth}，算法={algorithm}，顺序={order}："
                      f"最佳目标={result.best_target}，最优收益差={result.best_value}")
                if args.compare:
                    print(f"  访问节点={result.visited_nodes}，叶子评价={result.evaluated_leaves}，"
                          f"剪枝次数={result.cutoffs}，耗时={result.elapsed_seconds * 1000:.4f} 毫秒")


if __name__ == "__main__":
    main()
