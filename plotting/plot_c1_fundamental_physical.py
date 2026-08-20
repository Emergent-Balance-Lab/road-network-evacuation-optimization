#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C1 validation — PHYSICAL fundamental diagram (replaces the SPH-density x2 artifact).

The csv `Density` column is an UNNORMALISED SPH kernel sum (Sum d_mass*(1-r/h)^2),
not ped/m^2. Here density is measured the standard empirical way directly from agent
positions, with three estimators so the reader can see method sensitivity:
  * measurement circle (R=1.0 m): n_neighbours / (pi R^2)
  * k-nearest-neighbour (k=6):    k / (pi r_k^2)
  * Voronoi cell:                 1 / area(finite Voronoi cell)
Flow = rho * v. Pooled over frames spanning free-flow -> congestion.
Overlaid with the Weidmann (1993) speed-density model. Style: ggplot, dpi=600.
"""
import os, numpy as np, pandas as pd
from scipy.spatial import cKDTree, Voronoi
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common_paths import FUNDAMENTAL_FRAMES, GENERATED_FIGURES, GENERATED_TABLES

FIG, TAB = str(GENERATED_FIGURES), str(GENERATED_TABLES)
plt.style.use("ggplot"); SAVE = dict(dpi=600, bbox_inches="tight")
FRAMES = [50, 150, 300, 450, 600, 750, 900]
R_CIRCLE, K_NN = 1.0, 6


def poly_area(pts):
    x, y = pts[:, 0], pts[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def frame_estimators(px, py, v):
    P = np.column_stack([px, py]); tree = cKDTree(P)
    # measurement circle
    cnt = tree.query_ball_point(P, R_CIRCLE, return_length=True) - 1
    rho_circ = cnt / (np.pi * R_CIRCLE ** 2)
    # kNN
    dk, _ = tree.query(P, k=K_NN + 1)
    rk = dk[:, -1]
    rho_knn = K_NN / (np.pi * np.maximum(rk, 1e-3) ** 2)
    # Voronoi (finite cells only)
    rho_vor = np.full(len(P), np.nan)
    try:
        vor = Voronoi(P)
        for i, reg_idx in enumerate(vor.point_region):
            reg = vor.regions[reg_idx]
            if reg and -1 not in reg:
                a = poly_area(vor.vertices[reg])
                if a > 1e-6:
                    rho_vor[i] = 1.0 / a
    except Exception:
        pass
    return rho_circ, rho_knn, rho_vor


def weidmann(rho, v0=1.34, rho_jam=5.4, gamma=1.913):
    return v0 * (1 - np.exp(-gamma * (1.0 / np.maximum(rho, 1e-3) - 1.0 / rho_jam)))


# ---- pool frames ----
acc = {k: [] for k in ("circ", "knn", "vor")}
accv = {k: [] for k in ("circ", "knn", "vor")}
for fr in FRAMES:
    p = str(FUNDAMENTAL_FRAMES / f"{fr}.csv")
    if not os.path.exists(p):
        continue
    d = pd.read_csv(p, on_bad_lines="skip"); d.columns = [c.strip() for c in d.columns]
    for c in ("State", "Px", "Py", "Speed"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d[d["State"] == 1].dropna(subset=["Px", "Py", "Speed"])
    rc, rk, rv = frame_estimators(d["Px"].to_numpy(), d["Py"].to_numpy(), d["Speed"].to_numpy())
    v = d["Speed"].to_numpy()
    for key, rho in (("circ", rc), ("knn", rk), ("vor", rv)):
        m = np.isfinite(rho)
        acc[key].append(rho[m]); accv[key].append(v[m])
for k in acc:
    acc[k] = np.concatenate(acc[k]); accv[k] = np.concatenate(accv[k])


def binned_median(rho, y, bins=24, min_count=40):
    edges = np.unique(np.quantile(rho, np.linspace(0, 1, bins + 1)))
    xb, yb = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (rho >= a) & (rho < b)
        if m.sum() < min_count:
            continue
        xb.append(np.median(rho[m])); yb.append(np.median(y[m]))
    return np.array(xb), np.array(yb)


labels = {"circ": f"Measurement circle (R={R_CIRCLE} m)", "knn": f"kNN (k={K_NN})", "vor": "Voronoi cell"}
colors = {"circ": "tab:blue", "knn": "tab:green", "vor": "tab:purple"}

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
rows = []
for key in ("circ", "knn", "vor"):
    rho, v = acc[key], accv[key]
    flow = rho * v
    xs, vs = binned_median(rho, v)
    xf, ff = binned_median(rho, flow)
    axes[0].plot(xs, vs, "-o", ms=3, color=colors[key], lw=1.8, label=labels[key])
    axes[1].plot(xf, ff, "-o", ms=3, color=colors[key], lw=1.8, label=labels[key])
    cap = float(np.nanmax(ff)) if len(ff) else np.nan
    free = float(np.nanmedian(v[rho < 0.3])) if (rho < 0.3).any() else np.nan
    rows.append(dict(method=labels[key], free_speed=round(free, 3),
                     capacity_ped_m_s=round(cap, 3),
                     rho_at_capacity=round(float(xf[np.nanargmax(ff)]), 2) if len(ff) else np.nan,
                     max_density=round(float(np.nanpercentile(rho, 99)), 2)))
# Weidmann reference
rr = np.linspace(0.1, 5.4, 100)
axes[0].plot(rr, weidmann(rr), "k--", lw=1.8, label="Weidmann 1993")
axes[1].plot(rr, rr * weidmann(rr), "k--", lw=1.8, label="Weidmann 1993")
axes[1].axhline(1.3, color="tab:red", ls=":", lw=1.4, label="SFPE capacity ~1.3")
axes[0].set_xlabel("Density (ped/m$^2$)"); axes[0].set_ylabel("Speed (m/s)")
axes[0].set_title("Speed–density"); axes[0].set_xlim(0, 5.5); axes[0].set_ylim(0, 1.6)
axes[0].legend(fontsize=7); axes[0].grid(True, alpha=0.3)
axes[1].set_xlabel("Density (ped/m$^2$)"); axes[1].set_ylabel("Flow (ped/m/s)")
axes[1].set_title("Flow–density"); axes[1].set_xlim(0, 5.5)
axes[1].legend(fontsize=7); axes[1].grid(True, alpha=0.3)
fig.suptitle("Physical fundamental diagram (measured from agent positions, pooled frames)", y=1.02)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "FigR_C1_fundamental_physical.png"), **SAVE); plt.close(fig)

T = pd.DataFrame(rows)
T.to_csv(os.path.join(TAB, "TableR_C1_fundamental_physical.csv"), index=False)
print(T.to_string(index=False))
print(f"\nframes pooled: {FRAMES}  |  sample sizes:",
      {k: len(acc[k]) for k in acc})
