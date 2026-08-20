#!/usr/bin/env python3
"""Plot the isolated post-normalization k sensitivity experiment."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common_paths import DERIVED, GENERATED_FIGURES, GENERATED_TABLES

source = DERIVED / "sph_k_postnorm_sensitivity_20260710.csv"
table = GENERATED_TABLES / "TableR_C5_k_postnorm_sensitivity.csv"
figure = GENERATED_FIGURES / "FigR_C5_k_postnorm_sensitivity.png"

data = pd.read_csv(source)
baseline = float(data.loc[data["k_postnorm"] == 1.0, "metric"].iloc[0])
data["pct_change_vs_k1"] = 100.0 * (data["metric"] - baseline) / baseline
data.to_csv(table, index=False)

fig, ax = plt.subplots(figsize=(6.4, 4.6))
ax.plot(data["k_postnorm"], data["metric"], "-o", linewidth=2)
ax.axvline(1.0, color="tab:red", linestyle="--", linewidth=1.2, label="baseline k=1")
for row in data.itertuples():
    ax.annotate(
        f"{row.pct_change_vs_k1:+.1f}%",
        (row.k_postnorm, row.metric),
        xytext=(0, 8),
        textcoords="offset points",
        ha="center",
        fontsize=9,
    )
ax.set_xlabel("Post-normalization local-effect coefficient k")
ax.set_ylabel("Evacuation metric (lower is better)")
ax.set_title("Sensitivity to post-normalization coefficient k\nShipai, crowd=8000, zero widening")
ax.grid(True, alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig(figure, dpi=600, bbox_inches="tight")
plt.close(fig)

print(data.to_string(index=False))
