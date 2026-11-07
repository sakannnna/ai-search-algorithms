"""题目一：使用 A* 算法寻找迷宫中的最短路径。"""

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
    """保存路径和实验统计，耗时单位为秒。"""

    path: list[Position]
    expanded_nodes: int
    elapsed_seconds: float


def search_maze(
    grid: list[list[str]],
    start: Position,
    end: Position,
    heuristic: Heuristic = "manhattan",
) -> SearchResult:
    """搜索最短路径，并返回扩展节点数和耗时。

    X 表示障碍，其余格子可通行；坐标使用从零开始的（行，列）。
    扩展节点数指实际检查了邻居的有效出堆节点数，不包含终点。
    耗时包含输入检查、搜索和路径还原，不包含打印。
    """
    started = perf_counter()
    if heuristic not in ("manhattan", "zero"):
        raise ValueError("启发函数必须为 manhattan 或 zero")

    def result(path: list[Position], expanded: int = 0) -> SearchResult:
        return SearchResult(path, expanded, perf_counter() - started)

    if not grid or not grid[0]:
        return result([])
    rows, cols = len(grid), len(grid[0])
    if any(len(row) != cols for row in grid):
        raise ValueError("地图必须是行长度一致的二维数组")

    def passable(position: Position) -> bool:
        row, col = position
        return 0 <= row < rows and 0 <= col < cols and grid[row][col] != "X"

    if not passable(start) or not passable(end):
        return result([])

    def estimate(position: Position) -> int:
        if heuristic == "zero":
            return 0
        return abs(position[0] - end[0]) + abs(position[1] - end[1])

    # 序号用于在 f 相同时优先取出先入堆的节点，保证搜索顺序稳定。
    # 堆中每条记录依次保存 f、入堆序号、入堆时的 g 和格子坐标。
    sequence = count()
    open_heap: list[tuple[int, int, int, Position]] = []
    heapq.heappush(open_heap, (estimate(start), next(sequence), 0, start))
    g_score = {start: 0}
    came_from: dict[Position, Position] = {}
    expanded_nodes = 0

    # 固定按照上、下、左、右检查邻居。
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
    while open_heap:
        _, _, current_g, current = heapq.heappop(open_heap)

        # 同一格子的旧记录可能仍在堆里；若已有更短路线，就跳过旧记录。
        if current_g != g_score[current]:
            continue

        # 终点作为最优候选出堆时，再沿前驱还原完整路径。
        if current == end:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return result(path, expanded_nodes)

        expanded_nodes += 1
        for dr, dc in directions:
            neighbor = (current[0] + dr, current[1] + dc)
            if not passable(neighbor):
                continue

            new_g = current_g + 1
            # 只有首次到达或发现严格更短的路线时才更新，避免重复搜索。
            if new_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = new_g
                came_from[neighbor] = current
                heapq.heappush(
                    open_heap,
                    (new_g + estimate(neighbor), next(sequence), new_g, neighbor),
                )

    return result([], expanded_nodes)


def astar(
    grid: list[list[str]],
    start: Position,
    end: Position,
    heuristic: Heuristic = "manhattan",
) -> list[Position]:
    """按题目要求仅返回坐标列表；无解时返回空列表。"""
    return search_maze(grid, start, end, heuristic).path


def main() -> None:
    parser = argparse.ArgumentParser(description="题目一：A* 迷宫寻路")
    parser.add_argument(
        "--compare", action="store_true", help="比较两种启发函数的扩展节点数和耗时"
    )
    parser.add_argument("--input", type=Path, help="读取包含 grid、start、end 的 JSON 文件")
    parser.add_argument("--json", action="store_true", help="仅输出 JSON 结果")
    args = parser.parse_args()
    if args.json and args.compare:
        parser.error("--json 与 --compare 不能同时使用")

    # 作业给定的测试地图；默认运行时仅输出题目要求的路径列表。
    grid = [
        ["S", ".", ".", "X", "."],
        [".", "X", ".", ".", "."],
        [".", "X", ".", "X", "."],
        [".", ".", ".", "X", "E"],
        ["X", "X", ".", ".", "."],
    ]
    start, end = (0, 0), (3, 4)
    if args.input:
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        grid, start, end = data["grid"], tuple(data["start"]), tuple(data["end"])
    if args.json:
        print(json.dumps(astar(grid, start, end)))
        return
    if args.compare:
        for mode in ("zero", "manhattan"):
            outcome = search_maze(grid, start, end, mode)
            steps = len(outcome.path) - 1 if outcome.path else -1
            print(
                f"启发函数={mode}，路径步数={steps}，"
                f"扩展节点数={outcome.expanded_nodes}，"
                f"耗时={outcome.elapsed_seconds * 1000:.4f} 毫秒"
            )
            print(outcome.path)
    else:
        print(astar(grid, start, end))


if __name__ == "__main__":
    main()
