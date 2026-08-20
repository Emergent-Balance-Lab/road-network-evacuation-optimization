import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

from common_paths import FUNDAMENTAL_FRAMES, GENERATED_FIGURES

# 项目根目录（python/ 的上一级）。
PROJECT_ROOT = str(FUNDAMENTAL_FRAMES)

# 1. 设置文件路径
file_path = str(FUNDAMENTAL_FRAMES / "20.csv")

def uniform_sample(df, max_points=5000):
    """
    对 DataFrame 进行均匀采样（等间隔采样）
    max_points: 最多保留多少个点
    """
    n = len(df)
    if n <= max_points:
        return df

    step = max(1, n // max_points)
    return df.iloc[::step].reset_index(drop=True)

# --- 自动检测演示数据逻辑 (可选) ---
# 如果该路径下没有文件，生成一个模拟文件以确保代码可运行
if not os.path.exists(file_path):
    print(f"提示: 未找到文件 {file_path}，正在生成模拟数据用于演示...")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    # 创建模拟数据: ID, State, Speed, Flow, Density
    # 基本交通流关系: Flow = Speed * Density
    mock_density = np.linspace(5, 120, 200)
    mock_speed = 120 * (1 - mock_density / 140) + np.random.normal(0, 5, 200) # 简单的线性跟驰模型 + 噪声
    mock_speed = np.maximum(mock_speed, 0) # 速度不能小于0
    mock_flow = mock_speed * mock_density
    
    mock_df = pd.DataFrame({
        'ID': range(1, 201),
        'State': [1]*190 + [0]*10, # 混入一些 State=0
        'Speed': mock_speed,
        'Flow': mock_flow,
        'Density': mock_density
    })
    mock_df.to_csv(file_path, index=False)
# --------------------------------

# 2. 读取并预处理数据 (保留你原本的逻辑)
cleaned_data = []
header = []

try:
    # 尝试打开文件读取
    with open(file_path, 'r', encoding='utf-8') as f:
        # 读取所有行，去除空白字符
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    if not lines:
        raise ValueError("File is empty")

    # Handle header
    header = lines[0].split(',')
    num_columns = len(header)

    # 处理数据行
    for line in lines[1:]:
        parts = line.split(',')
        # 确保行长度一致，不足的补 None，防止 pandas 报错
        if len(parts) < num_columns:
            parts += [None] * (num_columns - len(parts))
        # 如果行太长，截断（虽然这种情况少见）
        elif len(parts) > num_columns:
            parts = parts[:num_columns]
            
        cleaned_data.append(parts)

    print(f"Successfully read file: {file_path}")

except FileNotFoundError:
    print(f"Error: File '{file_path}' not found")
    cleaned_data = []
except Exception as e:
    print(f"Error reading file: {e}")
    cleaned_data = []

# Create DataFrame
df = pd.DataFrame(cleaned_data, columns=header)

# 3. Data Cleaning
if not df.empty:
    # Convert required columns to numeric, coerce errors to NaN
    # 检查列是否存在，防止文件列名不匹配
    required_cols = ['State', 'Speed', 'Flow', 'Density']
    available_cols = [col for col in required_cols if col in df.columns]

    for col in available_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 过滤 State 为 0 的行
    # 注意：dropna 会移除转换失败产生的 NaN
    if 'State' in df.columns:
        df_clean = df[df['State'] != 0].dropna(subset=available_cols)
    else:
        df_clean = df.dropna(subset=available_cols)
else:
    df_clean = pd.DataFrame()

# 4. Visualization
if not df_clean.empty and 'Density' in df_clean.columns:

    # ---------- 1️⃣ 只保留 State == 1 ----------
    df_valid = df_clean[df_clean['State'] == 1].copy()

    if df_valid.empty:
        raise ValueError("No data with State == 1 after cleaning.")

    # ---------- 2️⃣ 均匀采样 ----------
    df_sampled = uniform_sample(df_valid, max_points=6000)

    print(f"After uniform sampling: {len(df_sampled)} points")

    # ---------- 3️⃣ 绘图设置 ----------
    # plt.rcParams['font.sans-serif'] = [
    #     'SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'sans-serif'
    # ]
    # plt.rcParams['axes.unicode_minus'] = False
    plt.style.use('ggplot')

    # ---------- 4️⃣ 并排绘制两个子图 ----------
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # --- 左图：Speed vs Density ---
    axes[0].scatter(
        df_sampled['Density'],
        df_sampled['Speed'],
        c='tab:blue',
        marker='x',
        s=15,
        linewidths=0.8,
        alpha=0.9
    )

    # median_speed = df_sampled['Speed'].median()

    # Density 分成 10 个等宽区间
    bins = np.linspace(df_sampled['Density'].min(),
                    df_sampled['Density'].max(), 20)

    df_sampled['Density_bin'] = pd.cut(df_sampled['Density'], bins)

    # 每个密度区间的中位数
    median_speed_by_bin = (
        df_sampled
        .groupby('Density_bin', observed=True)['Speed']
        .median()
    )

    # 区间中心
    bin_centers = [interval.mid for interval in median_speed_by_bin.index]

    axes[0].plot(
    bin_centers,
    median_speed_by_bin.values,
    color='black',
    linewidth=2,
    label='Median Speed (binned)')


    axes[0].set_title('Speed–Density Relationship')
    axes[0].set_xlabel('Density')
    axes[0].set_ylabel('Speed')
    axes[0].grid(True)
    axes[0].legend()

    # --- 右图：Flow vs Density ---
    axes[1].scatter(
        df_sampled['Density'],
        df_sampled['Flow'],
        c='tab:blue',
        marker='x',
        s=15,
        linewidths=0.8,
        alpha=0.9
    )

    median_flow_by_bin = (
        df_sampled
        .groupby('Density_bin', observed=True)['Flow']
        .median()
    )

    axes[1].plot(
    bin_centers,
    median_flow_by_bin.values,
    color='black',
    linewidth=2,
    label='Median Flow (binned)'
    )

    axes[1].set_title('Flow–Density Relationship')
    axes[1].set_xlabel('Density')
    axes[1].set_ylabel('Flow')
    axes[1].grid(True)
    axes[1].legend()

    # ---------- 5️⃣ 保存 + 展示 ----------
    plt.tight_layout()

    output_path = str(GENERATED_FIGURES / "traffic_fundamental_diagram.png")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=600, bbox_inches="tight")
    print(f"Figure saved to: {os.path.abspath(output_path)}")

    # plt.show()

else:
    print("\nNo valid data available for plotting.")
