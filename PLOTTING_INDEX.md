# Result-to-figure index

全部脚本集中在 `plotting/`，输入统一来自 `results/`，输出统一进入 `figures/generated/`、`generated/tables/` 或 `generated/data/`。

| 主题 | 脚本 | 主要输入 | 主要输出 |
|---|---|---|---|
| 单次宏观指标 | `analyze_c1_macro_metrics.py` | `results/c1_macro/paired_runs/` | `generated/data/c1_macro_metrics_single_run/` |
| 早期疏散分布 | `plot_legacy_evacuation_hist.py` | `results/legacy/baseline_run_record.csv` | `hist_time_distance.png` |
| 早期基本图 | `plot_legacy_fundamental_diagram.py`; `plot_legacy_fundamental_diagram_alt.py` | `results/legacy/fundamental_frames/` | `speed_flow_density_state1.png`; `traffic_fundamental_diagram.png` |
| 早期 GA 结果 | `plot_legacy_ga_results.py` | `results/legacy/ga_training_log.csv` | `Fig1`–`Fig5`; `ga_all.png` |
| 修订总览 | `plot_revision_overview.py` | `results/derived/`, `results/legacy/`, `results/sim_runs/` | C1/C2/C4/C5 总览图及汇总表 |
| C1 物理基本图 | `plot_c1_fundamental_physical.py` | `results/legacy/fundamental_frames/` | `FigR_C1_fundamental_physical.png`; 对应表 |
| C1 碰撞标定 | `plot_c1_collision_calibration.py` | `results/compact/collision_calibration_*.csv` | `FigR_C1_collision_calibration.png`; 对应表 |
| C1 拥堵热力图 | `plot_c1_congestion_heatmap.py` | `results/compact/congestion_heatmap_downsampled.npz` | `FigR_C1_congestion_heatmap.png` |
| C1 成对宏观比较 | `plot_c1_paired_macro.py` | `results/c1_macro/paired_runs/` | 清空曲线、空间时间图、下界检查图及成对比较表 |
| C1 空间组合图 | `plot_c1_macro_spatial_composite.py` | 成对原始记录及上一步派生数据 | `FigR_C1_macro_spatial_composite.png` |
| C2 beta 扫描 | `plot_c2_beta_sweep.py` | `results/legacy/ga_training_log.csv` | `FigR_C2_beta_sweep.png`; 对应表 |
| C2 早期 NSGA-II | `plot_c2_nsga2_legacy.py` | `results/nsga2/legacy_main/` | `FigR_C2_nsga2.png`; 代表解表 |
| C2 15 维 Pareto | `plot_c2_pareto_15d.py` | `results/nsga2/main15/` | `FigR_C2_pareto_15d_multiseed.png`; 多种子 Pareto 数据和表 |
| C4 运行时优化 | `plot_c4_runtime_optimization.py` | `results/derived/scaling_timing*.csv` | `FigR_C4_optimization.png`; 对应表 |
| C4 扩展性与 SPH | `plot_c4_runtime_and_sph.py` | `results/sim_runs/`, `results/derived/` | C4 扩展性图和 C5 SPH 图/表 |
| C5 GA 参数扫描 | `plot_c5_ga_sweep.py` | `results/ga_sweep/` | GA 鲁棒性和参数敏感性图/表 |
| C5 GA 物理敏感性 | `plot_c5_ga_physical_sensitivity.py` | `results/ga_physical_sensitivity/` | 收敛、道路频率和鲁棒性图/表 |
| C5 k 后归一化 | `plot_c5_k_postnorm_sensitivity.py` | `results/derived/sph_k_postnorm_sensitivity_20260710.csv` | `FigR_C5_k_postnorm_sensitivity.png`; 对应表 |
| C5 完整 SPH | `plot_c5_sph_full.py` | `results/derived/sph_sensitivity_260624.csv` | `FigR_C5_sph_full_sensitivity.*`; 对应表 |
| C5 均匀模型参数 | `plot_c5_uniform_model_sensitivity.py` | `results/derived/uniform_model_sensitivity.csv` | 模型参数敏感性 PNG/PDF 和表 |
| C5 NSGA-II 参数 | `plot_c5_nsga2_sensitivity.py` | `results/nsga2/sensitivity/` | NSGA-II 参数敏感性 PNG/PDF 和表 |
| C5 物理优化参数 | `plot_c5_physical_optimization_sensitivity.py` | `results/physical_optimization_sensitivity/final_runs/` | 物理优化与疏散指标敏感性 PNG/PDF 和表 |

`plotting/run_all.py` 是唯一的全流程入口；`plotting/common_paths.py` 是唯一的路径定义文件。

