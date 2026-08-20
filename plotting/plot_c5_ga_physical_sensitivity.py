#!/usr/bin/env python3
"""Summarize and plot the 50,000-person physical-scenario GA study."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common_paths import GA_PHYSICAL_SENSITIVITY, GENERATED_FIGURES, GENERATED_TABLES

RUNS = GA_PHYSICAL_SENSITIVITY / "runs"
FIG = GENERATED_FIGURES
TAB = GENERATED_TABLES
FIG.mkdir(exist_ok=True)
TAB.mkdir(exist_ok=True)

ORDER = ["base", "k050", "k200", "h180", "h300", "rho300", "rho500"]
LABELS = {
    "base": "Baseline",
    "k050": "k = 0.5",
    "k200": "k = 2.0",
    "h180": "h = 1.8 m",
    "h300": "h = 3.0 m",
    "rho300": "Density threshold = 3.0",
    "rho500": "Density threshold = 5.0",
}
COLORS = dict(zip(ORDER, plt.cm.tab10(np.linspace(0, 0.8, len(ORDER)))))


def road_set(widths: list[float]) -> set[int]:
    return {index + 1 for index, value in enumerate(widths) if value > 0}


def jaccard(left: set[int], right: set[int]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


records = []
for path in sorted(RUNS.glob("result_*.json")):
    item = json.loads(path.read_text(encoding="utf-8"))
    item["best_widths_text"] = "[" + ",".join(f"{v:.0f}" for v in item["best_widths"]) + "]"
    item["objective_improvement_pct"] = 100.0 * (
        item["zero_fitness"] - item["best_fitness"]
    ) / item["zero_fitness"]
    item["evac_improvement_pct"] = 100.0 * (
        item["zero_evac"] - item["best_evac"]
    ) / item["zero_evac"]
    item["selected_segments"] = sorted(road_set(item["best_widths"]))
    records.append(item)

if not records:
    raise SystemExit("No completed GA scenario results found")

data = pd.DataFrame(records)
base_by_seed = {
    int(row.seed): road_set(row.best_widths)
    for row in data[data["scenario"] == "base"].itertuples()
}
data["jaccard_vs_base"] = [
    jaccard(road_set(row.best_widths), base_by_seed[int(row.seed)])
    for row in data.itertuples()
]
data["scenario"] = pd.Categorical(data["scenario"], categories=ORDER, ordered=True)
data = data.sort_values(["scenario", "seed"])

columns = [
    "scenario", "seed", "crowd", "stopped_generation", "sim_calls",
    "zero_fitness", "best_fitness", "objective_improvement_pct",
    "zero_evac", "best_evac", "evac_improvement_pct", "best_cost",
    "jaccard_vs_base", "selected_segments", "best_widths_text", "wall_seconds",
]
data[columns].to_csv(TAB / "TableR_C5_ga_physical_sensitivity.csv", index=False)

summary = data.groupby("scenario", observed=True).agg(
    objective_improvement_mean=("objective_improvement_pct", "mean"),
    objective_improvement_std=("objective_improvement_pct", "std"),
    evacuation_improvement_mean=("evac_improvement_pct", "mean"),
    evacuation_improvement_std=("evac_improvement_pct", "std"),
    jaccard_mean=("jaccard_vs_base", "mean"),
    jaccard_std=("jaccard_vs_base", "std"),
    sim_calls_mean=("sim_calls", "mean"),
    stopped_generation_mean=("stopped_generation", "mean"),
).reindex(ORDER).reset_index()
summary.to_csv(TAB / "TableR_C5_ga_physical_sensitivity_summary.csv", index=False)

# Main robustness summary.
plt.style.use("ggplot")
plt.rcParams.update({
    "font.size": 8.8,
    "axes.labelsize": 9.5,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})
fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.15), sharey=True)
y = np.arange(len(ORDER))
labels = [
    "Baseline", r"$k=0.5$", r"$k=2.0$", r"$h=1.8$ m",
    r"$h=3.0$ m", r"$\rho_{\max}=3.0$", r"$\rho_{\max}=5.0$",
]

axes[0].barh(
    y, summary["objective_improvement_mean"],
    xerr=summary["objective_improvement_std"].fillna(0),
    color=[COLORS[tag] for tag in ORDER], alpha=0.85, capsize=3,
)
axes[0].set_yticks(y, labels)
axes[0].invert_yaxis()
axes[0].set_xlabel("Weighted-objective improvement (%)")
axes[0].text(-0.10, 1.03, "(a)", transform=axes[0].transAxes,
             ha="left", va="bottom", fontweight="bold", clip_on=False)

axes[1].barh(
    y, summary["jaccard_mean"],
    xerr=summary["jaccard_std"].fillna(0),
    color=[COLORS[tag] for tag in ORDER], alpha=0.85, capsize=3,
)
axes[1].set_xlim(0, 1.05)
axes[1].set_xlabel("Jaccard similarity")
axes[1].tick_params(axis="y", labelleft=False)
axes[1].text(-0.10, 1.03, "(b)", transform=axes[1].transAxes,
             ha="left", va="bottom", fontweight="bold", clip_on=False)

axes[2].barh(
    y, summary["sim_calls_mean"],
    color=[COLORS[tag] for tag in ORDER], alpha=0.85,
)
axes[2].set_xlabel("Simulator calls (mean)")
axes[2].tick_params(axis="y", labelleft=False)
axes[2].text(-0.10, 1.03, "(c)", transform=axes[2].transAxes,
             ha="left", va="bottom", fontweight="bold", clip_on=False)

fig.tight_layout(w_pad=0.7, rect=(0, 0, 1, 0.94))
fig.savefig(FIG / "FigR_C5_ga_physical_robustness.png", dpi=600, bbox_inches="tight")
fig.savefig(FIG / "FigR_C5_ga_physical_robustness.pdf", bbox_inches="tight")
plt.close(fig)

# Selected-road frequency heatmap.
frequency = np.zeros((len(ORDER), 16), dtype=float)
for row_index, scenario in enumerate(ORDER):
    subset = data[data["scenario"] == scenario]
    for row in subset.itertuples():
        frequency[row_index] += (np.asarray(row.best_widths) > 0).astype(float)
    if len(subset):
        frequency[row_index] /= len(subset)

fig, ax = plt.subplots(figsize=(13, 5.5))
image = ax.imshow(frequency, aspect="auto", vmin=0, vmax=1, cmap="YlGnBu")
ax.set_yticks(np.arange(len(ORDER)), labels)
ax.set_xticks(np.arange(16), [f"R{i}" for i in range(1, 17)])
ax.set_xlabel("Candidate road segment")
ax.set_title("Selection frequency of best solutions across two shared GA seeds")
for i in range(len(ORDER)):
    for j in range(16):
        ax.text(j, i, f"{frequency[i, j]:.1f}", ha="center", va="center", fontsize=7)
fig.colorbar(image, ax=ax, label="Selection frequency")
fig.tight_layout()
fig.savefig(FIG / "FigR_C5_ga_physical_road_frequency.png", dpi=600, bbox_inches="tight")
plt.close(fig)

# Convergence against actual simulator calls. Plot each seed to preserve the
# limited-repeat evidence rather than implying a smooth population mean.
fig, ax = plt.subplots(figsize=(10, 6.2))
for scenario in ORDER:
    subset = data[data["scenario"] == scenario]
    for number, row in enumerate(subset.itertuples()):
        path = RUNS / f"convergence_{scenario}_s{int(row.seed)}.csv"
        curve = pd.read_csv(path)
        improvement = 100.0 * (row.zero_fitness - curve["best_fitness"]) / row.zero_fitness
        ax.plot(
            curve["sim_calls"], improvement,
            color=COLORS[scenario], linewidth=2 if number == 0 else 1.2,
            alpha=0.9 if number == 0 else 0.55,
            label=LABELS[scenario] if number == 0 else None,
        )
ax.set_xlabel("Actual simulator calls")
ax.set_ylabel("Best weighted-objective improvement vs zero widening (%)")
ax.set_title("Warm-start GA convergence under physical-parameter scenarios")
ax.grid(True, alpha=0.3)
ax.legend(ncol=2, fontsize=8)
fig.tight_layout()
fig.savefig(FIG / "FigR_C5_ga_physical_convergence.png", dpi=600, bbox_inches="tight")
plt.close(fig)

print(summary.to_string(index=False))
