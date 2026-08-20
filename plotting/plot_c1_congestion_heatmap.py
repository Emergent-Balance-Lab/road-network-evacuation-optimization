"""Plot congestion fields from the compact downsampled result archive."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common_paths import COMPACT, GENERATED_FIGURES


archive = np.load(COMPACT / "congestion_heatmap_downsampled.npz")
road = archive["road_mask"]
density = archive["cumulative_density"]
congestion = archive["cumulative_congestion"]
factor = int(archive["downsample_factor"])
original_width = int(archive["original_width"])
original_height = int(archive["original_height"])

ys, xs = np.where(road)
y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()


def panel(axis, field, title, cmap):
    values = field[y0:y1 + 1, x0:x1 + 1].astype(float)
    mask = road[y0:y1 + 1, x0:x1 + 1]
    shown = np.where(mask, values, np.nan)
    upper = np.nanpercentile(shown, 99)
    image = axis.imshow(shown, origin="lower", cmap=cmap, vmax=upper)
    axis.set_title(title)
    axis.set_xticks([])
    axis.set_yticks([])
    plt.colorbar(image, ax=axis, fraction=0.046, pad=0.04)


fig, axes = plt.subplots(1, 2, figsize=(13, 6))
panel(axes[0], density, "Cumulative crowd density (bottlenecks)", "inferno")
panel(axes[1], congestion, "Cumulative congestion time", "viridis")
fig.suptitle("Spatial distribution of congestion (C1 behavioural validation)", y=1.0)
fig.tight_layout()
fig.savefig(GENERATED_FIGURES / "FigR_C1_congestion_heatmap.png",
            dpi=600, bbox_inches="tight")
plt.close(fig)
print(
    f"compact grid={road.shape[1]}x{road.shape[0]} factor={factor}; "
    f"original={original_width}x{original_height}; "
    f"road blocks={int(road.sum())}; density max={float(density.max()):.1f}"
)
