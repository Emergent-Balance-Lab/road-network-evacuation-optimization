#!/usr/bin/env python3
"""Analyze and plot the uniform +/-10% and +/-20% OFAT experiment."""
from __future__ import annotations

from pathlib import Path
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common_paths import DERIVED, GENERATED_FIGURES, GENERATED_TABLES

SOURCE = DERIVED / "sph_model_parameter_sensitivity_uniform.csv"
FIG = GENERATED_FIGURES
TAB = GENERATED_TABLES
MANUSCRIPT_FIG = GENERATED_FIGURES
FIG.mkdir(exist_ok=True)
TAB.mkdir(exist_ok=True)
MANUSCRIPT_FIG.mkdir(parents=True, exist_ok=True)

PARAMETERS = ["k_postnorm", "neighborhood_length", "density_threshold"]
BASELINES = {
    "k_postnorm": 1.0,
    "neighborhood_length": 2.4,
    "density_threshold": 4.0,
}
LABELS = {
    "k_postnorm": r"Local-effect coefficient $k$",
    "neighborhood_length": r"Neighborhood length $h$",
    "density_threshold": r"Density threshold $\rho_{\max}$",
}
UNITS = {
    "k_postnorm": "",
    "neighborhood_length": " m",
    "density_threshold": r" ped m$^{-2}$",
}


raw = pd.read_csv(SOURCE)
baseline_rows = raw[raw["param"] == "baseline"]
if len(baseline_rows) < 2:
    raise ValueError("at least two baseline replicates are required")
if baseline_rows["replicate"].duplicated().any():
    raise ValueError("baseline replicate identifiers must be unique")
baseline_by_replicate = baseline_rows.set_index("replicate")["metric"].to_dict()
baseline_metric = float(baseline_rows["metric"].mean())

records: list[dict] = []
for parameter in PARAMETERS:
    subset = raw[raw["param"] == parameter].copy()
    if sorted(subset["perturbation_pct"].astype(int).unique()) != [-20, -10, 10, 20]:
        raise ValueError(f"incomplete perturbation levels for {parameter}")
    for row in subset.to_dict("records"):
        records.append(row)
    for baseline_record in baseline_rows.to_dict("records"):
        baseline_record.update(
            param=parameter,
            perturbation_pct=0,
            value=BASELINES[parameter],
            unit="dimensionless" if parameter == "k_postnorm" else (
                "m" if parameter == "neighborhood_length" else "ped_per_m2"
            ),
        )
        records.append(baseline_record)

data = pd.DataFrame(records)
data["baseline_metric_same_replicate"] = data["replicate"].map(baseline_by_replicate)
if data["baseline_metric_same_replicate"].isna().any():
    raise ValueError("every scenario replicate must have a matching baseline replicate")
data["pct_change_metric"] = 100.0 * (
    data["metric"] - data["baseline_metric_same_replicate"]
) / data["baseline_metric_same_replicate"]
data["elasticity"] = np.where(
    data["perturbation_pct"] != 0,
    data["pct_change_metric"] / data["perturbation_pct"],
    np.nan,
)
data["param"] = pd.Categorical(data["param"], categories=PARAMETERS, ordered=True)
data = data.sort_values(["param", "perturbation_pct"]).reset_index(drop=True)
data.to_csv(TAB / "TableR_C5_model_parameter_sensitivity_uniform_runs.csv", index=False)

aggregate = data.groupby(
    ["param", "perturbation_pct", "value"], observed=True, as_index=False
).agg(
    metric_mean=("metric", "mean"),
    metric_sd=("metric", "std"),
    metric_change_mean_pct=("pct_change_metric", "mean"),
    metric_change_sd_pct=("pct_change_metric", "std"),
    replicates=("replicate", "nunique"),
)
aggregate["param"] = pd.Categorical(
    aggregate["param"], categories=PARAMETERS, ordered=True
)
aggregate = aggregate.sort_values(["param", "perturbation_pct"]).reset_index(drop=True)
aggregate.to_csv(TAB / "TableR_C5_model_parameter_sensitivity_uniform.csv", index=False)

summary_rows = []
for parameter in PARAMETERS:
    subset = aggregate[aggregate["param"] == parameter].set_index("perturbation_pct")
    central_10 = (
        float(subset.loc[10, "metric_change_mean_pct"])
        - float(subset.loc[-10, "metric_change_mean_pct"])
    ) / 20.0
    central_20 = (
        float(subset.loc[20, "metric_change_mean_pct"])
        - float(subset.loc[-20, "metric_change_mean_pct"])
    ) / 40.0
    summary_rows.append(
        {
            "param": parameter,
            "central_elasticity_10pct": central_10,
            "central_elasticity_20pct": central_20,
            "max_abs_metric_change_pct": float(subset["metric_change_mean_pct"].abs().max()),
            "metric_change_range_pct_points": float(
                subset["metric_change_mean_pct"].max()
                - subset["metric_change_mean_pct"].min()
            ),
        }
    )
summary = pd.DataFrame(summary_rows)
summary.to_csv(TAB / "TableR_C5_model_parameter_sensitivity_summary.csv", index=False)

plt.rcParams.update(
    {
        "font.size": 9.2,
        "axes.labelsize": 9.5,
        "axes.titlesize": 10,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)
fig, axes = plt.subplots(1, 3, figsize=(7.25, 3.05), sharex=True, sharey=True)
letters = ["(a)", "(b)", "(c)"]

for ax, parameter, letter in zip(axes, PARAMETERS, letters):
    subset = aggregate[aggregate["param"] == parameter]
    x = subset["perturbation_pct"].to_numpy(float)
    y = subset["metric_change_mean_pct"].to_numpy(float)
    yerr = subset["metric_change_sd_pct"].fillna(0).to_numpy(float)
    ax.axhline(0, color="0.35", linewidth=0.8)
    ax.axvline(0, color="0.72", linewidth=0.8, linestyle="--")
    ax.plot(x, y, color="#2474B5", marker="o", linewidth=1.8, markersize=4.5)
    ax.errorbar(
        x, y, yerr=yerr, fmt="none", ecolor="#2474B5",
        elinewidth=0.9, capsize=2.5, alpha=0.8,
    )
    for x_value, y_value in zip(x, y):
        if x_value == 0:
            continue
        offset = 5 if y_value >= 0 else -11
        horizontal_offset = 0
        horizontal_alignment = "center"
        if x_value == x.min():
            horizontal_offset = 2
            horizontal_alignment = "left"
        elif x_value == x.max():
            horizontal_offset = -2
            horizontal_alignment = "right"
        ax.annotate(
            f"{y_value:+.1f}%",
            (x_value, y_value),
            xytext=(horizontal_offset, offset),
            textcoords="offset points",
            ha=horizontal_alignment,
            fontsize=7.4,
        )
    ax.set_title(LABELS[parameter], pad=7)
    ax.set_xticks([-20, -10, 0, 10, 20])
    ax.set_xlabel("Parameter perturbation (%)")
    ax.grid(True, color="0.88", linewidth=0.6)
    ax.text(
        -0.055, 1.035, letter,
        transform=ax.transAxes,
        ha="right", va="bottom", fontweight="bold", clip_on=False,
    )

axes[0].set_ylabel("Change in evacuation metric (%)\n(lower is better)")
finite_y = np.concatenate(
    [
        aggregate["metric_change_mean_pct"].to_numpy(float)
        - aggregate["metric_change_sd_pct"].fillna(0).to_numpy(float),
        aggregate["metric_change_mean_pct"].to_numpy(float)
        + aggregate["metric_change_sd_pct"].fillna(0).to_numpy(float),
    ]
)
padding = max(2.0, 0.17 * (finite_y.max() - finite_y.min()))
axes[0].set_ylim(finite_y.min() - padding, finite_y.max() + padding)
fig.tight_layout(w_pad=0.8)

png = FIG / "FigR_C5_model_parameter_sensitivity_uniform.png"
pdf = FIG / "FigR_C5_model_parameter_sensitivity_uniform.pdf"
fig.savefig(png, dpi=600, bbox_inches="tight")
fig.savefig(pdf, bbox_inches="tight")
plt.close(fig)

# Keep the stable manuscript include path while replacing its contents with the
# uniform-perturbation experiment.
shutil.copy2(png, MANUSCRIPT_FIG / "Fig_R5_sph_parameter_sensitivity.png")
shutil.copy2(pdf, MANUSCRIPT_FIG / "Fig_R5_sph_parameter_sensitivity.pdf")

print(f"baseline metric: {baseline_metric:.6f}")
print(aggregate.to_string(index=False))
print("\nNormalized central sensitivities:")
print(summary.to_string(index=False))
