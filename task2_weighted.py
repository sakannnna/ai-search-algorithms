"""题目二：使用 A* 算法求加权地形的最小移动代价。"""

import argparse
import heapq
import json
from pathlib import Path
from dataclasses import dataclass
from itertools import count
from time import perf_counter
from typing import Literal


Position = tuple[int, int]
Heuristic = Literal["manhattan", "zero"]


@dataclass
class SearchResult:
    """保存最小代价、路径及统计数据，耗时单位为秒。"""

    cost: int
    path: list[Position]
    expanded_nodes: int
    elapsed_seconds: float


def search_terrain(
    grid: list[list[int | str]],
    start: Position,
    end: Position,
    heuristic: Heuristic = "manhattan",
) -> SearchResult:
    """返回搜索结果；无解时 cost 为 -1，path 为空列表。

    普通格支持非负整数或对应的数字字符串，X 表示障碍。
    起点不收费，进入终点的代价恒为零；S 格再次被进入时代价为 1。
    扩展节点数为实际检查邻居的有效出堆次数，不包含终点。
    耗时包含地图检查、搜索和路径还原，不包含打印。
    """
    started = perf_counter()

    def result(cost: int, path: list[Position], expanded: int = 0) -> SearchResult:
        return SearchResult(cost, path, expanded, perf_counter() - started)

    if heuristic not in ("manhattan", "zero"):
        raise ValueError("启发函数必须为 manhattan 或 zero")
    if not grid or not grid[0]:
        return result(-1, [])
    rows, cols = len(grid), len(grid[0])
    if any(len(row) != cols for row in grid):
        raise ValueError("地图必须是行长度一致的二维数组")

    # 统一转换进入代价；None 表示障碍，方便搜索时直接查询。
    costs: dict[Position, int | None] = {}
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            position = (r, c)
            if cell == "X":
                costs[position] = None
                continue
            if cell == "S":
                if position != start:
                    raise ValueError("S 标记必须位于给定起点")
                weight = 1
            elif cell == "E":
                if position != end:
                    raise ValueError("E 标记必须位于给定终点")
                weight = 0
            elif isinstance(cell, int) and not isinstance(cell, bool):
                weight = cell
            elif isinstance(cell, str):
                try:
                    weight = int(cell)
                except ValueError:
                    raise ValueError(f"格子 {position} 的代价不是整数：{cell!r}") from None
            else:
                raise ValueError(f"格子 {position} 的代价必须是非负整数")
            if weight < 0:
                raise ValueError("A* 不支持负移动代价")
            # 即使终点以数字表示，也按本题规则将进入代价设为零。
            costs[position] = 0 if position == end else weight

    if costs.get(start) is None or costs.get(end) is None:
        return result(-1, [])

    # 非终点格子的最小进入代价，为剩余付费步数提供代价下界。
    # 若存在零代价格子，下界为零，启发函数自然退化为 h=0。
    min_cost = min(
        (weight for p, weight in costs.items() if p != end and weight is not None),
        default=0,
    )

    def estimate(position: Position) -> int:
        if heuristic == "zero":
            return 0
        distance = abs(position[0] - end[0]) + abs(position[1] - end[1])
        # 最后进入终点的一步免费，因此普通曼哈顿距离需要减去一步。
        return max(distance - 1, 0) * min_cost

    sequence = count()
    # 每条堆记录依次保存 f、入堆序号、入堆时的 g 和坐标。
    open_heap = [(estimate(start), next(sequence), 0, start)]
    g_score = {start: 0}
    came_from: dict[Position, Position] = {}
    expanded_nodes = 0
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    while open_heap:
        _, _, current_g, current = heapq.heappop(open_heap)
        # 找到更便宜路线后，旧记录仍可能留在堆中，取出时跳过即可。
        if current_g != g_score[current]:
            continue
        if current == end:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return result(current_g, path, expanded_nodes)

        expanded_nodes += 1
        for dr, dc in directions:
            neighbor = (current[0] + dr, current[1] + dc)
            weight = costs.get(neighbor)
            if weight is None:
                continue
            # 与题目一不同，每次加上进入邻居格子的代价，而不是固定加 1。
            new_g = current_g + weight
            if new_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = new_g
                came_from[neighbor] = current
                heapq.heappush(
                    open_heap,
                    (new_g + estimate(neighbor), next(sequence), new_g, neighbor),
                )

    return result(-1, [], expanded_nodes)


def astar(
    grid: list[list[int | str]],
    start: Position,
    end: Position,
    heuristic: Heuristic = "manhattan",
) -> int:
    """按题目要求仅返回最小总代价；无解返回 -1。"""
    return search_terrain(grid, start, end, heuristic).cost


def main() -> None:
    parser = argparse.ArgumentParser(description="题目二：A* 加权地形寻路")
    parser.add_argument(
        "--compare", action="store_true", help="比较零启发函数和修正曼哈顿距离"
    )
    parser.add_argument("--input", type=Path, help="读取包含 grid、start、end 的 JSON 文件")
    parser.add_argument("--json", action="store_true", help="仅输出 JSON 结果")
    args = parser.parse_args()
    if args.json and args.compare:
        parser.error("--json 与 --compare 不能同时使用")
    # 作业给定的测试地图。
    grid = [
        ["S", 1, 1, 8, 1],
        [1, 8, 3, 1, 1],
        [1, 8, 1, 8, 1],
        [1, 1, 1, 8, 1],
        [8, 8, 1, 1, "E"],
    ]
    start, end = (0, 0), (4, 4)
    if args.input:
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        grid, start, end = data["grid"], tuple(data["start"]), tuple(data["end"])
    if args.json:
        print(json.dumps(astar(grid, start, end)))
        return
    if args.compare:
        for mode in ("zero", "manhattan"):
            outcome = search_terrain(grid, start, end, mode)
            print(
                f"启发函数={mode}，最小总代价={outcome.cost}，"
                f"扩展节点数={outcome.expanded_nodes}，"
                f"耗时={outcome.elapsed_seconds * 1000:.4f} 毫秒"
            )
            print(outcome.path)
    else:
        print(astar(grid, start, end))


if __name__ == "__main__":
    main()
