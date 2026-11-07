"""题目三：使用 Minimax 和 Alpha-beta 求博弈树的最佳得分。"""

import argparse
import json
from pathlib import Path
from dataclasses import dataclass
from time import perf_counter
from typing import Literal


class TreeNode:
    """非叶子节点保存子节点，叶子节点保存得分。"""

    def __init__(self, value=None, children=None):
        self.value = value
        self.children = children if children is not None else []


@dataclass
class SearchResult:
    """统计实际访问节点、评估叶子及发生剪枝的次数。"""

    value: int | float
    visited_nodes: int
    evaluated_leaves: int
    cutoffs: int
    elapsed_seconds: float


def search_tree(
    root: TreeNode,
    algorithm: Literal["minimax", "alpha_beta"] = "alpha_beta",
    order: Literal["left", "right"] = "left",
) -> SearchResult:
    """根节点为 MAX，逐层交替角色；默认严格从左到右访问。

    right 仅用于访问顺序的对照实验，不修改原树的子节点列表。
    visited_nodes 包含根和叶子；cutoffs 只计确实跳过了剩余分支的事件。
    """
    started = perf_counter()
    if algorithm not in ("minimax", "alpha_beta"):
        raise ValueError("算法必须为 minimax 或 alpha_beta")
    if order not in ("left", "right"):
        raise ValueError("访问顺序必须为 left 或 right")
    visited_nodes = evaluated_leaves = cutoffs = 0

    def visit(node: TreeNode, maximizing: bool, alpha: float, beta: float):
        nonlocal visited_nodes, evaluated_leaves, cutoffs
        visited_nodes += 1
        # 用子节点列表判断叶子，避免将合法的零分误判为无值。
        if not node.children:
            if not isinstance(node.value, (int, float)) or isinstance(node.value, bool):
                raise ValueError("叶子节点必须具有数值得分")
            if not float("-inf") < node.value < float("inf"):
                raise ValueError("叶子节点得分必须是有限数值")
            evaluated_leaves += 1
            return node.value

        best = float("-inf") if maximizing else float("inf")
        children = node.children if order == "left" else reversed(node.children)
        for index, child in enumerate(children):
            value = visit(child, not maximizing, alpha, beta)
            best = max(best, value) if maximizing else min(best, value)

            if algorithm == "alpha_beta":
                # MAX 提高下界，MIN 降低上界；边界交叉时剩余分支不影响决策。
                if maximizing:
                    alpha = max(alpha, best)
                else:
                    beta = min(beta, best)
                if alpha >= beta:
                    if index + 1 < len(node.children):
                        cutoffs += 1
                    break
        return best

    value = visit(root, True, float("-inf"), float("inf"))
    return SearchResult(
        value, visited_nodes, evaluated_leaves, cutoffs, perf_counter() - started
    )


def minimax(root: TreeNode) -> int | float:
    """完整搜索，返回 MAX 的最佳得分。"""
    return search_tree(root, "minimax").value


def alpha_beta(root: TreeNode) -> int | float:
    """从左到右使用 Alpha-beta 剪枝，仅返回题目要求的最佳得分。"""
    return search_tree(root, "alpha_beta").value


def tree_from_dict(data, maximizing=True) -> TreeNode:
    """读取 PDF 的嵌套 JSON 结构，并检查角色是否逐层交替。"""
    if "is_maximizing_player" in data and data["is_maximizing_player"] is not maximizing:
        raise ValueError("节点角色必须从根节点 MAX 开始逐层交替")
    if data.get("children"):
        return TreeNode(children=[tree_from_dict(child, not maximizing) for child in data["children"]])
    return TreeNode(value=data.get("value"))


def build_example_tree() -> TreeNode:
    """按作业的构建代码创建示例；两处 max2 引用同一个节点。"""
    max1 = TreeNode(children=[TreeNode(value=3), TreeNode(value=5)])
    max2 = TreeNode(children=[TreeNode(value=6), TreeNode(value=9)])
    max3 = TreeNode(children=[TreeNode(value=1), TreeNode(value=2)])
    min1 = TreeNode(children=[max1, max2])
    min2 = TreeNode(children=[max2, max3])
    # 此处不使用缓存，共享节点在不同分支中按实际访问次数统计。
    return TreeNode(children=[min1, min2])


def main() -> None:
    parser = argparse.ArgumentParser(description="题目三：极大极小博弈树的最佳得分")
    parser.add_argument(
        "--compare", action="store_true", help="比较算法和子节点访问顺序"
    )
    parser.add_argument("--input", type=Path, help="读取 PDF 格式的 tree_structure JSON")
    parser.add_argument("--json", action="store_true", help="仅输出 JSON 结果")
    args = parser.parse_args()
    if args.json and args.compare:
        parser.error("--json 与 --compare 不能同时使用")
    root = build_example_tree()
    if args.input:
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        root = tree_from_dict(data.get("tree_structure", data))
    if args.json:
        print(json.dumps(alpha_beta(root)))
        return
    if args.compare:
        for order in ("left", "right"):
            for algorithm in ("minimax", "alpha_beta"):
                outcome = search_tree(root, algorithm, order)
                print(
                    f"算法={algorithm}，顺序={order}，最佳得分={outcome.value}，"
                    f"访问节点数={outcome.visited_nodes}，"
                    f"评估叶子数={outcome.evaluated_leaves}，"
                    f"剪枝次数={outcome.cutoffs}，"
                    f"耗时={outcome.elapsed_seconds * 1000:.4f} 毫秒"
                )
    else:
        print(alpha_beta(root))


if __name__ == "__main__":
    main()
