# 实验二：搜索算法

这个仓库保存了当代人工智能实验二的代码、测试和实验数据。前两题用 A* 寻路，第三题比较 Minimax 和 Alpha-beta，第四题把寻路与博弈搜索结合起来，决定先拿哪个宝藏。

实验报告另外以 PDF 提交，报告开头的代码链接指向本仓库。

## 先运行给定样例

需要 Python 3.10 或以上版本，本次实验使用 Python 3.12.10。代码只用标准库，安装好 Python 后就能运行，不需要额外安装依赖。

```powershell
git clone https://github.com/sakannnna/ai-search-algorithms.git
cd ai-search-algorithms
python task1_maze.py
python task2_weighted.py
python task3_game_tree.py
python task4_treasure.py
```

不带参数时，程序运行作业给定的样例：

| 文件 | 解决的问题 | 样例结果 |
|---|---|---|
| [task1_maze.py](task1_maze.py) | 返回迷宫最短路径上的坐标 | 7 步，路径含起点和终点 |
| [task2_weighted.py](task2_weighted.py) | 计算加权地图的最小移动代价 | 7 |
| [task3_game_tree.py](task3_game_tree.py) | 计算 MAX 的最佳得分 | 5 |
| [task4_treasure.py](task4_treasure.py) | 输出距离矩阵，并比较两种深度的宝藏选择 | H=2 选 T2，收益差为 -1；H=4 选 T3，收益差为 3 |

## 换一组输入

前三题可以用 `--input` 读取 JSON 文件。[examples](examples) 中保存了对应样例，可以复制一份，修改里面的地图、坐标或树，再交给程序运行。加上 `--json` 后，输出也会使用 JSON 格式，方便其他程序读取。

```powershell
python task1_maze.py --input examples/task1.json --json
python task2_weighted.py --input examples/task2.json --json
python task3_game_tree.py --input examples/task3.json --json
```

题一、二的文件包含 `grid`、`start`、`end` 三项。坐标按“行、列”填写，从 0 开始。例如，下面是一张可以直接用于第一题的小地图：

```json
{
  "start": [0, 0],
  "end": [0, 2],
  "grid": [["S", ".", "E"]]
}
```

第二题把普通格改成非负整数或数字字符串，例如 `[["S", 2, "E"]]`。第一题无解时输出空列表，第二题无解时输出 -1。

第三题的树用 `children` 列出子节点，叶子用 `value` 保存得分，可以直接传根节点，也可以像作业样例一样包在 `tree_structure` 中。根节点默认为 MAX，之后逐层交替；如果填写了 `is_maximizing_player`，程序会检查它是否符合这个顺序。叶子得分可以为 0 或负数，但不能是无穷或 NaN。

第四题的命令行固定使用作业地图，可以单独选择深度和算法：

```powershell
python task4_treasure.py --depth 2 --algorithm alpha_beta --json
python task4_treasure.py --depth 4 --algorithm minimax --json
```

指定深度后，JSON 结果直接包含 `best_target` 和 `best_value`；不指定深度时，会同时返回 H=2 和 H=4 的结果。`--json` 和下面的 `--compare` 用途不同，不能同时使用。

也可以在 Python 中直接调用：题一、二的 `astar(grid, start, end)` 分别返回路径和最小代价；题三提供 `minimax(root)`、`alpha_beta(root)`。需要路径或节点统计时，使用 `search_maze`、`search_terrain`、`search_tree`；第四题先调用 `build_distance_matrix()`，再把矩阵传给 `search_game(matrix, depth)`。

## 查看对照实验

四个程序都支持 `--compare`，可以查看同一输入下不同方法的结果、搜索节点数和耗时：

```powershell
python task1_maze.py --compare
python task2_weighted.py --compare
python task3_game_tree.py --compare
python task4_treasure.py --compare
```

如果要重复测量并保存数据，运行：

```powershell
python run_experiments.py --repeats 100 --output .local-results
```

脚本运行 30 组配置，每组先预热一次，再测量指定次数。这里把新结果放在 `.local-results` 中，保留仓库里原有的数据；省略 `--output` 则会覆盖 `results` 下的同名文件。

保存的文件有三份：`raw.csv` 记录每一次测量，`summary.csv` 汇总节点数和耗时的中位数、最小值、最大值，`environment.json` 记录 Python 版本、系统和测量设置。本次报告使用的数据保存在 [results](results) 中。

除了给定样例，脚本还设置了几组额外输入：大一些的迷宫用于比较启发函数，绕行和零代价地图用于检查加权寻路，另外构造的博弈树用于比较访问顺序。第四题则同时比较两种深度，以及固定顺序、反向顺序和按即时收益排序的搜索方式。

看这些结果时，需要把搜索量和运行时间分开。题一、二统计真正检查过邻居的次数，不包含终点；题三、四统计每次节点访问，根节点和叶子都计入。第三题样例在两个分支中用了同一棵子树，因此会记录两次访问，统计的不是不同节点对象的数量。剪枝次数记录“提前停止检查剩余子节点”的次数，并不等于跳过的节点总数。

计时范围也有所不同：题一、二包括输入检查和路径还原，题三、四只计搜索，第四题不包含距离预计算。因此，耗时主要用于同一题内的方法对照。小程序的计时容易波动，脚本又是先测完一组再测下一组；少搜索几个节点，并不一定会更快。

## 检查结果是否正确

```powershell
python -m unittest discover -v
```

[test_tasks123.py](test_tasks123.py) 给前三题各准备了 200 组固定种子的随机输入，再分别用 BFS、反复松弛求最小代价、完整递归求博弈树得分，与待测算法核对。测试还包含无解、起终点相同、零代价、负得分等情况。

[test_task4_treasure.py](test_task4_treasure.py) 把距离和决策分开检查：先用独立 Dijkstra 核对六个位置之间的距离，再枚举行动顺序，检查不同深度下 Minimax 和 Alpha-beta 的结果。状态更新、终止条件和作业样例也在测试中。

实验脚本会检查不同策略的结果是否一致，但独立基准的正确性检查放在这些测试文件中。复现时可以先运行测试，再查看性能对照。

## 几处容易混淆的规则

第二题和第四题的终点规则不同。第二题进入 E 的代价为 0，因此启发函数扣除了最后这一步，再乘上可通行非终点格子的最小进入代价；普通格出现零代价时，启发值就变成 0。第四题的 A、B、宝藏格代价都是 1，走到目标也照常计入，所以不能把第二题的终点处理直接搬过去。

第三题默认从左到右访问子节点；反向顺序只用于对照。第四题按 A、B、A、B 行动，H 指总行动次数，不是每名玩家各走几次。拿走宝藏后要更新位置，经过其他宝藏不会自动收集，另一名玩家也不会挡路。每轮都要选择一个剩余宝藏，即使移动代价高于价值，也不能跳过这一轮。

第四题中，A 最大化的是“A 的累计收益减 B 的累计收益”，B 则最小化这个差值。同深度的 Minimax 和 Alpha-beta 应得到相同的最优值；出现并列时，保留当前访问顺序中最先找到的最优目标。第四题寻路按本题的正整数权值实现，距离矩阵要求六个位置互相可达；若要换成其他地图，需要先检查是否仍满足这些条件。
