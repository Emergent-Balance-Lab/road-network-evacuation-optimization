#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C2 supplement (Fig.O2): how the linear-scalarization weight beta selects different
points along the Pareto front. Pure post-processing of the existing GA log
(output/ga_training_log.csv) -- no re-simulation. Style matches analyze_existing.py.
"""
import os, ast, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common_paths import GENERATED_DATA, GENERATED_FIGURES, GENERATED_TABLES, LEGACY

FIG, TAB, DAT = map(str, (GENERATED_FIGURES, GENERATED_TABLES, GENERATED_DATA))
plt.style.use("ggplot"); SAVE = dict(dpi=600, bbox_inches="tight")

df = pd.read_csv(LEGACY / "ga_training_log.csv")
df.columns = [c.strip() for c in df.columns]
evac = df["Evac_Score"].to_numpy(float)
cost = df["Cost_Score"].to_numpy(float)


def pareto_mask(c, e):
    n = len(c); nd = np.ones(n, bool)
    for i in range(n):
        dom = (c <= c[i]) & (e <= e[i]) & ((c < c[i]) | (e < e[i]))
        if dom.any(): nd[i] = False
    return nd


nd = pareto_mask(cost, evac)
pf = np.argsort(cost[nd]); pc = cost[nd][pf]; pe = evac[nd][pf]

betas = np.array([0.0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0])
rows = []
sel_c, sel_e = [], []
for b in betas:
    i = int(np.argmin(evac + b * cost))
    rows.append(dict(beta=b, Evac=round(float(evac[i]), 2), Cost=round(float(cost[i]), 2),
                     weighted_obj=round(float(evac[i] + b * cost[i]), 2)))
    sel_c.append(cost[i]); sel_e.append(evac[i])
pd.DataFrame(rows).to_csv(os.path.join(TAB, "TableR_C2_beta_sweep.csv"), index=False)

fig, ax = plt.subplots(figsize=(6.2, 5))
ax.plot(pc, pe, "-o", color="crimson", ms=4, lw=1.6, alpha=0.85,
        label="Post-hoc nondominated set (legacy weighted GA)")
sc = ax.scatter(sel_c, sel_e, c=np.log10(betas + 1e-3), cmap="viridis", s=90,
                edgecolors="k", zorder=6)
groups = {}
for b, c, e in zip(betas, sel_c, sel_e):
    groups.setdefault((float(c), float(e)), []).append(float(b))
for (c, e), bs in groups.items():
    label = ", ".join(f"{b:g}" for b in bs)
    ax.annotate(rf"$\beta={{{label}}}$", (c, e), textcoords="offset points",
                xytext=(6, 4), fontsize=7)
# highlight the manuscript default beta=0.1
i01 = int(np.argmin(evac + 0.1 * cost))
ax.scatter([cost[i01]], [evac[i01]], marker="D", s=80, color="royalblue",
           edgecolors="k", zorder=7, label=r"Manuscript default $\beta$=0.1")
ax.set_xlabel("Building-demolition / land-take cost proxy"); ax.set_ylabel("Evacuation score")
ax.set_title(r"Legacy $\beta$ preference examples on the post-hoc nondominated set")
cbar = fig.colorbar(sc, ax=ax); cbar.set_label(r"$\log_{10}\beta$")
ax.legend(loc="center right", fontsize=8)
fig.savefig(os.path.join(FIG, "FigR_C2_beta_sweep.png"), **SAVE); plt.close(fig)
print("[beta_sweep] done:", json.dumps(rows[:5]))
