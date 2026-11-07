"""运行样例与自设对照实验，将原始测量和汇总数据导出为 CSV。"""

import argparse
import csv
import json
import platform
import statistics
import sys
from datetime import datetime
from pathlib import Path
from random import Random

from task1_maze import search_maze
from task2_weighted import search_terrain
from task3_game_tree import TreeNode, build_example_tree, search_tree
from task4_treasure import build_distance_matrix, search_game


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=100, help="预热后重复次数，默认 100")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("重复次数必须大于零")
    jobs = []
    maze_example = [list(row) for row in ("S..X.", ".X...", ".X.X.", "...XE", "XX...")]
    rng = Random(2026)
    maze_random = [["X" if rng.random() < .25 else "." for _ in range(30)] for _ in range(30)]
    # 保留一条可通行路线，确保不同策略可以比较相同的最优解。
    for i in range(30):
        maze_random[0][i] = maze_random[i][-1] = "."
    for name, grid, end in (("sample", maze_example, (3, 4)), ("random30", maze_random, (29, 29))):
        for mode in ("zero", "manhattan"):
            jobs.append(("task1", name, mode, lambda g=grid, e=end, m=mode: search_maze(g, (0, 0), e, m)))
    weighted = [["S", 1, 1, 8, 1], [1, 8, 3, 1, 1], [1, 8, 1, 8, 1], [1, 1, 1, 8, 1], [8, 8, 1, 1, "E"]]
    for name, grid, end in (("sample", weighted, (4, 4)),
                            ("detour", [["S", 8, "E"], [1, 1, 1]], (0, 2)),
                            ("zero_cost", [["S", 0, 0], [2, 2, "E"]], (1, 2))):
        for mode in ("zero", "manhattan"):
            jobs.append(("task2", name, mode, lambda g=grid, e=end, m=mode: search_terrain(g, (0, 0), e, m)))
    # 先访问最小值较高的 MIN 分支，可提高根节点下界，让后续分支尽早剪枝。
    custom = TreeNode(children=[TreeNode(children=[TreeNode(value=v) for v in row])
                                for row in ((8, 9, 10), (1, 7, 8), (2, 6, 7), (3, 5, 9))])
    for name, tree in (("sample", build_example_tree()), ("order_sensitive", custom)):
        for algorithm in ("minimax", "alpha_beta"):
            for order in ("left", "right"):
                jobs.append(("task3", name, f"{algorithm}/{order}",
                             lambda t=tree, a=algorithm, o=order: search_tree(t, a, o)))
    matrix = build_distance_matrix()
    for depth in (2, 4):
        for algorithm in ("minimax", "alpha_beta"):
            for order in ("fixed", "reverse", "gain"):
                jobs.append(("task4", f"H={depth}", f"{algorithm}/{order}",
                             lambda d=depth, a=algorithm, o=order: search_game(matrix, d, a, o)))

    raw, summary = [], []
    for task, scenario, strategy, run in jobs:
        run()  # 预热不纳入测量。
        samples = []
        signatures = set()
        for repeat in range(args.repeats):
            result = run()
            value = (len(result.path)-1 if result.path else -1) if task == "task1" else (
                result.cost if task == "task2" else result.value if task == "task3" else result.best_value)
            nodes = result.expanded_nodes if task in ("task1", "task2") else result.visited_nodes
            row = dict(task=task, scenario=scenario, strategy=strategy, repeat=repeat+1,
                       value=value, nodes=nodes, leaves=getattr(result, "evaluated_leaves", ""),
                       cutoffs=getattr(result, "cutoffs", ""), target=getattr(result, "best_target", ""),
                       elapsed_ms=result.elapsed_seconds*1000)
            raw.append(row)
            samples.append(row["elapsed_ms"])
            signatures.add((value, nodes, row["leaves"], row["cutoffs"], row["target"]))
        if len(signatures) != 1:
            raise AssertionError("重复运行结果不稳定")
        summary.append({k: v for k, v in row.items() if k not in ("repeat", "elapsed_ms")}
                       | {"repeats": args.repeats, "median_ms": statistics.median(samples),
                          "min_ms": min(samples), "max_ms": max(samples)})
    # 同一场景各策略的最优值必须一致，性能对照才有意义。
    values = {}
    for row in summary:
        key = row["task"], row["scenario"]
        values.setdefault(key, set()).add(row["value"])
    if any(len(v) != 1 for v in values.values()):
        raise AssertionError("不同策略的结果不一致")
    args.output.mkdir(parents=True, exist_ok=True)
    for name, rows in (("raw.csv", raw), ("summary.csv", summary)):
        with (args.output / name).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    metadata = dict(python=sys.version, executable=sys.executable, platform=platform.platform(),
                    generated_at=datetime.now().astimezone().isoformat(), seed=2026,
                    repeats=args.repeats, warmup=1,
                    timing="任务1/2包含输入检查与路径还原；任务3/4仅搜索，任务4不含距离预计算")
    (args.output / "environment.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已完成 {len(jobs)} 组实验，每组 {args.repeats} 次；结果目录：{args.output.resolve()}")


if __name__ == "__main__":
    main()
