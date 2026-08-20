import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common_paths import FUNDAMENTAL_FRAMES, GENERATED_FIGURES

# 项目根目录（python/ 的上一级）。
PROJECT_ROOT = str(FUNDAMENTAL_FRAMES)

def binned_median(x, y, bins=30, min_count=20):
    """按 x 的分位数分箱，在每箱内取 x/y 中位数，返回折线点"""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < min_count:
        return np.array([]), np.array([])

    edges = np.unique(np.quantile(x, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return np.array([]), np.array([])

    xb, yb = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        idx = (x >= a) & (x <= b if b == edges[-1] else x < b)
        if idx.sum() < min_count:
            continue
        xb.append(np.median(x[idx]))
        yb.append(np.median(y[idx]))
    return np.array(xb), np.array(yb)

def plot_speed_flow_density_from_csv(csv_path,
                                     state_keep=1,
                                     bins=30,
                                     min_count=20,
                                     xlim_density=(0, 4.5),
                                     ylim_speed=(0, 2.0),
                                     ylim_flow=(0, 2.5),
                                     sample_n=None,
                                     out_png=None):
    """
    读取 CSV（允许坏行），筛选 State==state_keep，
    绘制 Speed–Density 与 Flow–Density 两张图（左右）。
    """
    # 1) 读入（跳过坏行，比如 "3,0"）
    df = pd.read_csv(csv_path, on_bad_lines="skip")
    df.columns = [c.strip() for c in df.columns]

    # 2) 只取需要的列（兼容大小写/不同命名）
    # 你给的列名：State, Vx, Vy, Speed, Flow, Density
    col_map = {c.lower(): c for c in df.columns}
    def pick(name):
        return col_map.get(name.lower(), None)

    c_state   = pick("State")
    c_vx      = pick("Vx")
    c_vy      = pick("Vy")
    c_speed   = pick("Speed")
    c_flow    = pick("Flow")
    c_density = pick("Density")

    if c_state is None or c_density is None:
        raise ValueError("CSV must contain at least 'State' and 'Density' columns.")

    # 3) 数值化 + 过滤 state
    df[c_state] = pd.to_numeric(df[c_state], errors="coerce")
    df = df[df[c_state] == state_keep].copy()

    # Density
    df[c_density] = pd.to_numeric(df[c_density], errors="coerce")

    # Speed：优先用现成 Speed；否则用 Vx,Vy 算
    if c_speed is not None:
        df[c_speed] = pd.to_numeric(df[c_speed], errors="coerce")
        df["speed_"] = df[c_speed]
    else:
        if c_vx is None or c_vy is None:
            raise ValueError("Need either 'Speed' or both 'Vx' and 'Vy'.")
        df[c_vx] = pd.to_numeric(df[c_vx], errors="coerce")
        df[c_vy] = pd.to_numeric(df[c_vy], errors="coerce")
        df["speed_"] = np.sqrt(df[c_vx]**2 + df[c_vy]**2)

    # Flow：优先用现成 Flow；否则用 speed*density
    if c_flow is not None:
        df[c_flow] = pd.to_numeric(df[c_flow], errors="coerce")
        df["flow_"] = df[c_flow]
    else:
        df["flow_"] = df["speed_"] * df[c_density]

    # 4) 清理无效行
    df = df.dropna(subset=[c_density, "speed_", "flow_"])
    df = df[(df[c_density] >= 0) & (df["speed_"] >= 0) & (df["flow_"] >= 0)]

    # 5) 可选：均匀抽样减少点数（避免太密）
    if sample_n is not None and len(df) > sample_n:
        idx = np.linspace(0, len(df) - 1, sample_n, dtype=int)
        idx = np.unique(idx)
        df = df.iloc[idx].copy()

    print(f"Loaded: {csv_path}")
    print(f"Kept State={state_keep}: {len(df)} rows")

    # 6) 绘图
    plt.figure(figsize=(12, 5))

    # (A) Speed–Density
    ax1 = plt.subplot(1, 2, 1)
    ax1.scatter(df[c_density] * 2, 
                df["speed_"], 
                s=8, 
                marker="o", 
                alpha=0.30,
                color="steelblue",
                edgecolors="none",)

    xline, yline = binned_median(df[c_density] * 2, df["speed_"], bins=bins, min_count=min_count)
    if len(xline):
        ax1.plot(xline, yline, linewidth=2, color="k", label="Binned median")
    ax1.set_title("Speed–Density Relationship (State=1)")
    ax1.set_xlabel("Density")
    ax1.set_ylabel("Speed")
    ax1.set_xlim(*xlim_density)
    ax1.set_ylim(*ylim_speed)
    ax1.grid(True, alpha=0.2)
    ax1.legend()

    # (B) Flow–Density
    ax2 = plt.subplot(1, 2, 2)
    ax2.scatter(df[c_density] * 2, 
                df["flow_"] * 2, 
                s=8, 
                marker="o", 
                alpha=0.30,
                color="steelblue",
                edgecolors="none",)

    xline2, yline2 = binned_median(df[c_density] * 2, df["flow_"] * 2, bins=bins, min_count=min_count)
    if len(xline2):
        ax2.plot(xline2, yline2, linewidth=2, color="k", label="Binned median")
    ax2.set_title("Flow–Density Relationship (State=1)")
    ax2.set_xlabel("Density")
    ax2.set_ylabel("Flow (= Speed × Density)")
    ax2.set_xlim(*xlim_density)
    ax2.set_ylim(*ylim_flow)
    ax2.grid(True, alpha=0.2)
    ax2.legend()

    plt.tight_layout()

    if out_png:
        os.makedirs(os.path.dirname(out_png) or ".", exist_ok=True)
        plt.savefig(out_png, dpi=600, bbox_inches="tight")
        print("Saved:", out_png)

    # plt.show()


# Example:
plot_speed_flow_density_from_csv(
    csv_path=str(FUNDAMENTAL_FRAMES / "10.csv"),
    state_keep=1,
    bins=25,
    min_count=30,
    sample_n=10000,
    out_png=str(GENERATED_FIGURES / "speed_flow_density_state1.png")
)
