#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C5: selected model-parameter sensitivity.

Plot only the post-normalization local-effect coefficient k, smoothing length
h, and density threshold, in that fixed order. Percent changes are measured
against the k=1 baseline run.
"""
import os
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

from common_paths import DERIVED, GENERATED_FIGURES, GENERATED_TABLES

FIG, TAB, DAT = map(str, (GENERATED_FIGURES, GENERATED_TABLES, DERIVED))
plt.style.use("ggplot"); SAVE = dict(dpi=600, bbox_inches="tight")
plt.rcParams.update({
    "font.size": 10.5,
    "axes.labelsize": 12,
    "xtick.labelsize": 10.5,
    "ytick.labelsize": 10.5,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

d = pd.read_csv(os.path.join(DAT, "sph_sensitivity_260624.csv"))
base = float(d[d["param"] == "baseline"]["metric"].iloc[0])
param_order = ["k_postnorm", "smoothing_length", "density_threshold"]
d = d[d["param"].isin(param_order)].copy()
d["pct"] = 100 * (d["metric"] - base) / base
nice = {
    "k_postnorm": r"Post-normalization coefficient $k$",
    "smoothing_length": r"Smoothing length $h$",
    "density_threshold": r"Density threshold $\rho_{\max}$",
}
d["label"] = d.apply(lambda r: f"{nice.get(r['param'], r['param'])} = {r['value']}", axis=1)
d["param"] = pd.Categorical(d["param"], categories=param_order, ordered=True)
d["value_num"] = pd.to_numeric(d["value"])
d = d.sort_values(["param", "value_num"]).drop(columns="value_num")
d.to_csv(os.path.join(TAB, "TableR_C5_sph_full_sensitivity.csv"), index=False)

fig, ax = plt.subplots(figsize=(6.8, 4.7))
colors = ["tab:red" if p > 0 else "tab:blue" for p in d["pct"]]
ax.barh(range(len(d)), d["pct"], color=colors, alpha=0.85)
ax.set_yticks(range(len(d))); ax.set_yticklabels(d["label"])
ax.invert_yaxis()
ax.axvline(0, color="k", lw=0.8)
ax.set_xlabel("Change in evacuation metric vs baseline (%)")
ax.grid(True, axis="x", alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "FigR_C5_sph_full_sensitivity.png"), **SAVE)
fig.savefig(os.path.join(FIG, "FigR_C5_sph_full_sensitivity.pdf"), bbox_inches="tight")
print(d[["param", "value", "metric", "pct"]].to_string(index=False))
