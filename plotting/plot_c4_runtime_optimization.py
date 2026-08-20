#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C4 optimization figure: O(N^2) single-bucket vs O(N) spatial-hash neighbour search.
Overlays the original timing (scaling_timing.csv, cpp/1213) against the optimized
binary (scaling_timing_260624.csv, cpp/260624). Style: ggplot, dpi=600.
"""
import os, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

from common_paths import DERIVED, GENERATED_FIGURES, GENERATED_TABLES

FIG, TAB, DAT = map(str, (GENERATED_FIGURES, GENERATED_TABLES, DERIVED))
plt.style.use("ggplot"); SAVE = dict(dpi=600, bbox_inches="tight")

old = pd.read_csv(os.path.join(DAT, "scaling_timing.csv"))
new = pd.read_csv(os.path.join(DAT, "scaling_timing_260624.csv"))
go = old.groupby("crowd")["wall_s"].mean()
gn = new.groupby("crowd")["wall_s"].mean()
crowd = sorted(set(go.index) & set(gn.index))
wo = np.array([go[c] for c in crowd]); wn = np.array([gn[c] for c in crowd])
crowd = np.array(crowd, float); speed = wo / wn

T = pd.DataFrame(dict(crowd=crowd.astype(int), old_Onsq_s=np.round(wo, 1),
                      new_On_s=np.round(wn, 1), speedup=np.round(speed, 2)))
T.to_csv(os.path.join(TAB, "TableR_C4_optimization.csv"), index=False)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].plot(crowd, wo, "-o", color="tab:red", lw=2, label="Single-bucket O(N$^2$) (cpp/1213)")
axes[0].plot(crowd, wn, "-o", color="tab:green", lw=2, label="Spatial-hash O(N) (cpp/260624)")
# reference slopes anchored at the largest N
axes[0].plot(crowd, wo[-1] * (crowd / crowd[-1]) ** 2, "--", color="gray", lw=1, label="O(N$^2$) ref")
axes[0].plot(crowd, wn[-1] * (crowd / crowd[-1]), ":", color="gray", lw=1, label="O(N) ref")
axes[0].set_xscale("log"); axes[0].set_yscale("log")
axes[0].set_xlabel("Number of agents N"); axes[0].set_ylabel("Wall-clock time (s)")
axes[0].set_title("Simulation runtime before / after neighbour-search fix")
axes[0].grid(True, which="both", alpha=0.3); axes[0].legend(fontsize=7)

axes[1].plot(crowd, speed, "-o", color="tab:blue", lw=2)
for c, s in zip(crowd, speed):
    axes[1].annotate(f"{s:.1f}x", (c, s), textcoords="offset points", xytext=(0, 6), fontsize=7, ha="center")
axes[1].set_xscale("log"); axes[1].set_xlabel("Number of agents N"); axes[1].set_ylabel("Speedup (old / new)")
axes[1].set_title("Speedup grows with N (signature of O(N$^2$)→O(N))")
axes[1].grid(True, alpha=0.3)
fig.suptitle("GPU neighbour-search optimization (RTX 5090, same scenario)", y=1.02)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "FigR_C4_optimization.png"), **SAVE)
print(T.to_string(index=False))
