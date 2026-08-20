"""Plot collision-distance calibration from compact binned result curves."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common_paths import COMPACT, GENERATED_FIGURES, GENERATED_TABLES


curves = pd.read_csv(COMPACT / "collision_calibration_curves.csv")
summary = pd.read_csv(COMPACT / "collision_calibration_summary.csv")
styles = {
    "coll060": ("tab:red", "collision 0.6 m (current)"),
    "coll049": ("tab:green", "collision 0.49 m (calibrated)"),
}

plt.style.use("ggplot")
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for variant, (color, label) in styles.items():
    subset = curves[curves.variant == variant]
    speed = subset[subset.metric == "speed"].sort_values("density")
    flow = subset[subset.metric == "flow"].sort_values("density")
    axes[0].plot(speed.density, speed.value, "-o", ms=3, color=color, lw=1.8, label=label)
    axes[1].plot(flow.density, flow.value, "-o", ms=3, color=color, lw=1.8, label=label)

axes[1].axhline(1.3, color="k", ls=":", lw=1.4, label="SFPE ~1.3")
axes[0].set(xlabel="Density (ped/m$^2$)", ylabel="Speed (m/s)",
            title="Speed-density (kNN)", xlim=(0, 6))
axes[1].set(xlabel="Density (ped/m$^2$)", ylabel="Flow (ped/m/s)",
            title="Flow-density (kNN)", xlim=(0, 6))
for axis in axes:
    axis.legend(fontsize=7)
    axis.grid(True, alpha=0.3)
fig.suptitle("Collision-distance calibration: 0.6 m vs 0.49 m", y=1.02)
fig.tight_layout()
fig.savefig(GENERATED_FIGURES / "FigR_C1_collision_calibration.png",
            dpi=600, bbox_inches="tight")
plt.close(fig)
summary.to_csv(GENERATED_TABLES / "TableR_C1_collision_calibration.csv", index=False)
print(summary.to_string(index=False))
