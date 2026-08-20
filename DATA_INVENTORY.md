# Data inventory and provenance

## 已整合的数据

- `results/legacy/`：早期 GA 训练日志、基准疏散记录、代表解和用于基本图的选定帧；
- `results/c1_macro/paired_runs/`：baseline/optimized 两种布局，各 5 个种子的 `run_record.csv` 与 `alive_series.csv`；
- `results/derived/`：修订阶段已核对的派生汇总数据；
- `results/tables/`：论文修订阶段形成的表格归档；
- `results/sim_runs/`：尺度扩展与 SPH 相关运行结果；
- `results/ga_sweep/`、`results/ga_physical_sensitivity/`：GA 参数与物理敏感性结果；
- `results/nsga2/`：早期主实验、15 维多种子实验与参数敏感性结果；
- `results/physical_optimization_sensitivity/`：最终物理优化敏感性运行、Pareto 前沿和超体积数据；
- `results/uniform_model_sensitivity/`、`results/phase2_logs/`：模型参数扫描和修订日志/数据归档。

## GitHub 友好的紧凑数据

`results/compact/` 保存两个可复绘数据集：

1. `collision_calibration_curves.csv` 和 `collision_calibration_summary.csv`：从原始碰撞标定逐帧数据按原分析逻辑提取的曲线与统计量；
2. `congestion_heatmap_downsampled.npz`：由原始三层二进制网格按 8×8 块聚合得到，包含道路掩膜、累计密度、累计拥堵和元数据。

这两个紧凑数据分别替代约 2.43 GB 的碰撞逐帧文件和约 3.52 GB 的原始热力图层。它们足以直接重绘相应图片，同时避免 GitHub 仓库被不可审查的大型中间文件占满。原修订图片仍完整保存在 `figures/revision/`，论文采用图片保存在 `manuscript/fig/`。

## 数据使用约定

- `results/` 视为只读输入；
- 重绘生成物写入 `figures/generated/` 与 `generated/`；
- 路径只由 `plotting/common_paths.py` 定义；
- 发布文件哈希记录在 `MANIFEST.sha256`；
- 本包不提供用于重新运行底层模拟的 C++ 程序，只复现结果分析与绘图。

修订目录中用于准备模拟场景或调用本地模拟器的 Python runner 不属于“从现有结果直接绘图”流程，且离开被禁止发布的可执行程序后不能独立运行，因此没有混入 `plotting/`。原有分析/绘图逻辑均已改为统一路径版本并纳入一键流程。
