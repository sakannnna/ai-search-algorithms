# 实验二：搜索算法

四题代码、正确性测试及可复现实验。

GitHub 仓库：https://github.com/sakannnna/ai-search-algorithms

提交报告为不超过 5 页的 PDF，开头附仓库链接，另以 ZIP 打包提交。课程原始文件、带个人信息的报告和报告制作中间文件保留在本机，不纳入代码仓库。

## 环境

- Python 3.10 或以上；本机验证使用 Python 3.12.10。
- 仅使用 Python 标准库，无第三方依赖，不需要 pip 安装。
- 文件使用 UTF-8 编码，注释与说明为中文。

在 PowerShell 中进入目录后运行：

```powershell
Set-Location 'E:\Project\当代AI实验二'
python task1_maze.py
python task2_weighted.py
python task3_game_tree.py
python task4_treasure.py
```

前三题默认分别输出坐标列表、整数 7、整数 5。第四题输出距离矩阵及两种算法在 H=2、H=4 下的决策。

## 文件与函数入口

| 文件 | 入口 | 返回值 |
|---|---|---|
| task1_maze.py | astar(grid, start, end) | 最短路径坐标列表，无解为 [] |
| task2_weighted.py | astar(grid, start, end) | 最小总代价，无解为 -1 |
| task3_game_tree.py | minimax(root)、alpha_beta(root) | MAX 的最佳得分 |
| task4_treasure.py | build_distance_matrix()、search_game(matrix, depth) | 距离矩阵、含最佳目标和收益差的 SearchResult |
| test_tasks123.py | unittest | 前三题边界与固定种子随机对照 |
| test_task4_treasure.py | unittest | 第四题距离、博弈、状态更新与样例验证 |
| run_experiments.py | 命令行 | CSV 原始数据、汇总数据、环境信息 |

任务一、二的 search_maze / search_terrain 返回附带路径及统计的结果，任务三 search_tree 返回搜索统计。任务四默认使用 Alpha-beta、固定宝藏顺序。

## JSON 输入输出

任务一、二使用 --input 指定 UTF-8 JSON 文件；不指定则运行内置样例。结构为：

```json
{"start": [0, 0], "end": [0, 2], "grid": [["S", ".", "E"]]}
```

第二题将普通格改成非负整数或数字字符串，如 `[["S", 2, "E"]]`。坐标为从零开始的行、列。Python 函数接收元组，JSON 使用数组。

第三题支持 PDF 中的 tree_structure 包装，也支持直接传根节点：

```json
{"tree_structure": {"is_maximizing_player": true, "children": [{"value": 3}, {"value": 5}]}}
```

角色字段可省略；提供时必须从 MAX 根节点开始逐层交替。叶子得分必须为有限数值。

```powershell
python task1_maze.py --input examples/task1.json --json
python task2_weighted.py --input examples/task2.json --json
python task3_game_tree.py --input examples/task3.json --json
python task4_treasure.py --depth 2 --algorithm alpha_beta --json
python task4_treasure.py --depth 4 --algorithm minimax --json
```

--json 模式只输出合法 JSON；第四题单深度直接输出 best_target、best_value 字典，不指定 --depth 时输出以深度为键的结果字典。第四题当前使用题目给定地图和宝藏数据，可通过函数接口传入距离矩阵或状态开展实验。--json 与 --compare 互斥。

## 规则与实现约定

- 第一题只能上下左右移动，每步代价 1，X 不可通行，路径包含起点和终点。同长路径按堆的入堆顺序确定。
- 第二题进入格子的数字为代价，起点初始不收费，进入终点恒为 0。启发函数为 max(曼哈顿距离-1, 0) × 最小非终点进入代价；存在零代价格时退化为零启发。负代价和非整数代价会报错。
- 第三题默认从左到右访问；MAX、MIN 交替，alpha >= beta 时剪枝。PDF 构建示例的 max2 被两处引用；程序不缓存该共享节点，每次访问单独计数。
- 第四题标记 A、B、T 的进入代价均为 1，终点收费。轮流选择一个未获取宝藏，不自动收集途经宝藏，不互相阻挡，不允许跳过行动；负收益行动仍合法。
- 第四题单次收益为宝藏价值减距离；评价值为 A 累计收益减 B 累计收益，A 最大化、B 最小化。状态不可变，分支不会互相污染。
- H 表示总行动次数。H=2 的预期结果为 T2、-1；H=4 为 T3、3。并列时保留当前访问顺序中先出现的最优目标。
- 第四题 A* 面向给定的正整数代价地图；距离矩阵要求六个位置互相可达。更换为零代价、负代价或不可达地图前需要调整模型，不能直接套用。

## 正确性验证

```powershell
python -m unittest discover -v
```

前三题各有 200 组固定种子随机输入：第一题与 BFS 对照，第二题与独立反复松弛算法对照，第三题与独立完整递归评价对照。还验证无解、起终点相同、零代价、负得分等情况。

第四题的 36 项距离与独立 Dijkstra 对照；H=1～4 的两种算法及三种顺序与行动排列枚举结果对照，并检查状态更新、终止条件和给定样例。

## 性能与自设对照实验

单题快速查看：

```powershell
python task1_maze.py --compare
python task2_weighted.py --compare
python task3_game_tree.py --compare
python task4_treasure.py --compare
```

批量测量与数据保存：

```powershell
python run_experiments.py --repeats 100
```

默认生成 results/raw.csv、results/summary.csv、results/environment.json。再次运行会覆盖同名结果；需要保留多次实验时使用 --output 指定其他目录。

- 30 组配置，每组先预热一次再重复测量；原始数据包含每次耗时，汇总包含中位数、最小值和最大值。
- 题一：给定样例及固定种子 30×30 障碍地图，比较零启发与曼哈顿距离；自设地图保留一条路线。
- 题二：给定样例、绕开昂贵格子的场景、普通格代价为零的场景，比较零启发与修正曼哈顿距离。
- 题三：给定样例及访问顺序敏感的自设树，比较两种算法与左右顺序。
- 题四：两种深度、两种算法、固定/反向/即时收益排序三种访问顺序。
- 脚本自动检查同场景最优值一致及重复运行节点统计稳定。即时收益排序只改变访问顺序，不改变搜索深度或评价规则。

题一、二记录扩展节点数，即实际检查邻居的有效出堆次数，不含终点；题三、四记录访问节点数，包含根与叶子。剪枝次数只计确实跳过剩余分支的事件，不等于被跳过的节点数。

题一、二耗时包含输入检查和路径还原；题三、四耗时仅含搜索，第四题不含距离矩阵预计算。不要跨题直接比较耗时。小样例的耗时受机器负载影响，应结合节点数和重复测量中位数判断，不以单次耗时证明性能提升。

实验报告已根据本批次数据完成，含路径示意、代价累计、博弈回传、深度决策和性能分析。本文档与仓库提供代码及复现实验入口，个人报告通过课程指定渠道另行提交。
