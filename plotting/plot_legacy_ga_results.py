import pandas as pd
import matplotlib.pyplot as plt
import io
import ast
import numpy as np
import os

from common_paths import GENERATED_FIGURES, LEGACY

# 项目根目录（python/ 的上一级）。
PROJECT_ROOT = str(LEGACY)

csv_path = str(LEGACY / "ga_training_log.csv")
fig_path = str(GENERATED_FIGURES) + os.sep
os.makedirs(fig_path, exist_ok=True)

if not os.path.exists(csv_path):
    raise FileNotFoundError(f"CSV file not found: {csv_path}")

df = pd.read_csv(csv_path)

for col in df.columns:
    print(repr(col))

# df.columns = df.columns.str.strip()
# print(df.head())
PLOT_STYLE = {
    "dpi": 600,
    "figsize_single": (6, 5),
    "linewidth": 2,
    "marker_size": 40,
    "alpha": 0.8
}


# 解析 'Solution_Widths' 列 (从字符串转换为列表)
# Solution_Widths
df['Solution_Widths_List'] = df['Solution_Widths'].apply(ast.literal_eval)

# 计算每一代基因的标准差 (作为多样性指标)
def calculate_gene_diversity(series):
    # 将该代所有个体的基因堆叠成一个矩阵
    matrix = np.array(series.tolist())
    # 计算每一列(每个基因位)的标准差，然后求平均
    return np.mean(np.std(matrix, axis=0))

# 按代分组计算统计数据
grouped = df.groupby('Generation')
stats = grouped.agg({
    'Final_Fitness': ['mean', 'min', 'max', 'std'],
    'Evac_Score': 'mean',
    'Cost_Score': 'mean',
    'Solution_Widths_List': calculate_gene_diversity
})

# 重命名列以便访问
stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
stats = stats.rename(columns={'Solution_Widths_List_calculate_gene_diversity': 'Gene_Diversity'})

# 设置绘图风格
plt.style.use('ggplot')

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# 图 1: 适应度收敛分析
# 我们关注 Min Fitness (如果是最小化问题) 或 Max Fitness (如果是最大化问题)
# 根据数据，Fitness 似乎是 Evac + Cost 的某种组合，或者类似。
# 假设这是一个最小化问题(通常 Cost 越低越好)，但也可能是最大化。
# 看数据：Generation 1 Min=1283, Generation 5 Min=1259. 看起来是最小化问题，或者在寻找特定值。
# 我们画出 Mean 和 Best (这里假设 Min 是 Best，因为数值在下降)

axes[0].plot(stats.index, stats['Final_Fitness_mean'], label='Average Fitness', marker='o', linestyle='--')
axes[0].plot(stats.index, stats['Final_Fitness_min'], label='Best (Min) Fitness', marker='s', linewidth=2)
axes[0].fill_between(stats.index, 
                     stats['Final_Fitness_mean'] - stats['Final_Fitness_std'],
                     stats['Final_Fitness_mean'] + stats['Final_Fitness_std'], 
                     alpha=0.2, label='Std Dev')
axes[0].set_title('Fitness Convergence (Fitness vs Generation)')
axes[0].set_xlabel('Generation')
axes[0].set_ylabel('Final Fitness')
axes[0].legend()
axes[0].grid(True)

# 图 2: 目标权衡 (Trade-off) - 散点图
# 用颜色表示代数，观察帕累托前沿的移动
sc = axes[1].scatter(df['Cost_Score'], df['Evac_Score'], c=df['Generation'], cmap='viridis', alpha=0.8)
axes[1].set_title('Objective Space (Cost vs Evac)')
axes[1].set_xlabel('Cost Score')
axes[1].set_ylabel('Evacuation Score')
plt.colorbar(sc, ax=axes[1], label='Generation')
axes[1].grid(True)

# 图 3: 种群多样性 (基因方差)
# 如果这个值趋近于0，说明种群已经趋同，很难再找到新解
axes[2].plot(stats.index, stats['Gene_Diversity'], color='purple', marker='^')
axes[2].set_title('Population Diversity (Gene Variance)')
axes[2].set_xlabel('Generation')
axes[2].set_ylabel('Avg Gene Std Dev')
axes[2].grid(True)

plt.tight_layout()
# plt.show()
plt.savefig(
    fig_path + "ga_all.png",
    dpi=600,
    bbox_inches="tight"
)

# 简单的文字输出
print("--- 收敛分析报告 ---")
print(f"初始代最优适应度 (Gen 1): {stats['Final_Fitness_min'].iloc[0]:.2f}")
print(f"最终代最优适应度 (Gen 5): {stats['Final_Fitness_min'].iloc[-1]:.2f}")
delta = stats['Final_Fitness_min'].iloc[0] - stats['Final_Fitness_min'].iloc[-1]
print(f"适应度改善幅度: {delta:.2f}")

if stats['Gene_Diversity'].iloc[-1] < 0.1:
    print("警告: 基因多样性极低，可能已陷入早熟收敛。")
else:
    print("状态: 种群仍保持一定的多样性，可能有进一步优化的空间。")

# Fig.1 Fitness convergence
fig, ax = plt.subplots(figsize=(6, 5))
ax.plot(
    stats.index,
    stats['Final_Fitness_mean'],
    label='Mean fitness',
    linestyle='--',
    linewidth=2
)

ax.plot(
    stats.index,
    stats['Final_Fitness_min'],
    label='Best fitness',
    linewidth=2
)

ax.fill_between(
    stats.index,
    stats['Final_Fitness_mean'] - stats['Final_Fitness_std'],
    stats['Final_Fitness_mean'] + stats['Final_Fitness_std'],
    alpha=0.2,
    label='±1 std'
)

ax.set_xlabel('Generation')
ax.set_ylabel('Final fitness')
ax.set_title('Fitness convergence')
ax.legend()
ax.grid(True)

fig.savefig(fig_path + "Fig1_fitness_convergence.png",
            dpi=600, 
            bbox_inches="tight")

plt.close(fig)


# Fig.2 Objective space
fig, ax = plt.subplots(figsize=(6, 5))

sc = ax.scatter(
    df['Cost_Score'],
    df['Evac_Score'],
    c=df['Generation'],
    cmap='viridis',
    s=30,
    alpha=0.8
)

ax.set_xlabel('Cost score')
ax.set_ylabel('Evacuation score')
ax.set_title('Objective trade-off')
ax.grid(True)

cbar = fig.colorbar(sc, ax=ax)
cbar.set_label('Generation')

fig.savefig(fig_path + "Fig2_objective_tradeoff.png",
            dpi=600, bbox_inches="tight")
plt.close(fig)

# Fig.3 Population diversity
fig, ax = plt.subplots(figsize=(6, 5))

ax.plot(
    stats.index,
    stats['Gene_Diversity'],
    marker='o',
    linewidth=2
)

ax.set_xlabel('Generation')
ax.set_ylabel('Mean gene-wise standard deviation')
ax.set_title('Population diversity')
ax.grid(True)

fig.savefig(fig_path + "Fig3_population_diversity.png",
            dpi=600, 
            bbox_inches="tight")

plt.close(fig)

#  4 
gene_matrix = np.vstack(df['Solution_Widths_List'].values)  # (N, 14)
freq_2 = (gene_matrix == 2).mean(axis=0)
freq_4 = (gene_matrix == 4).mean(axis=0)
fig, ax = plt.subplots(figsize=(7, 4))

# road_ids = np.arange(1, 16)
road_ids = np.arange(1, freq_2.size + 1)
fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=True)

# Left: 2m
axes[0].bar(road_ids, freq_2, color='tab:orange', alpha=0.8)
axes[0].set_xlabel('Road index')
axes[0].set_ylabel('Selection frequency')
axes[0].set_title('Width = 2 m')
axes[0].set_xticks(road_ids)
axes[0].grid(axis='y')

# Right: 4m
axes[1].bar(road_ids, freq_4, color='tab:blue', alpha=0.8)
axes[1].set_xlabel('Road index')
axes[1].set_title('Width = 4 m')
axes[1].set_xticks(road_ids)
axes[1].grid(axis='y')


fig.suptitle('Widening preference of road segments', 
             y=1.02)

fig.tight_layout()

fig.savefig(fig_path + "Fig4_road_widening_frequency_2m_4m.png",
            dpi=600, bbox_inches="tight")

plt.close(fig)


# 5 Fig.5 离散基因的熵多样性（高级但很加分）
from scipy.stats import entropy
def gene_entropy(series):
    mat = np.array(series.tolist())
    ent = []
    for j in range(mat.shape[1]):
        _, counts = np.unique(mat[:, j], return_counts=True)
        ent.append(entropy(counts))
    return np.mean(ent)

entropy_stats = df.groupby('Generation')['Solution_Widths_List'].apply(gene_entropy)

fig, ax = plt.subplots(figsize=(6, 5))
ax.plot(entropy_stats.index, entropy_stats.values, marker='o', linewidth=2)
ax.set_xlabel('Generation')
ax.set_ylabel('Mean gene entropy')
ax.set_title('Discrete gene diversity (entropy)')
ax.grid(True)

fig.savefig(fig_path + "Fig5_gene_entropy.png",
            dpi=600, bbox_inches="tight")
plt.close(fig)



