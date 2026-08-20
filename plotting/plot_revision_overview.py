#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revision 2026 — data-driven answers to reviewer comments, computed from the
EXISTING 2249-run simulation dataset (no re-simulation required).

Covers:
  C2  — full Pareto front (Cost vs Evac), knee, beta=0.1 weighted optimum, hypervolume
  C5a — global sensitivity of objectives to the 15 road-widening decisions + GA convergence
  C1  — model validation: fundamental diagram + macroscopic evacuation curves + macro table
  C4  — optimization-scale cost: best-so-far convergence vs evaluations + compute proxy

Plot style matches the original manuscript scripts (ggplot, dpi=600, viridis, tab colors).
All released inputs are read-only; outputs go to the unified generated directories.
"""
import os, ast, json, math, glob
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common_paths import (
    DERIVED, FUNDAMENTAL_FRAMES, GENERATED_DATA, GENERATED_FIGURES,
    GENERATED_TABLES, LEGACY, REPRESENTATIVE_RUNS,
)

ROOT = str(LEGACY)
FIG  = str(GENERATED_FIGURES)
TAB  = str(GENERATED_TABLES)
DAT  = str(GENERATED_DATA)
for d in (FIG, TAB, DAT): os.makedirs(d, exist_ok=True)

plt.style.use("ggplot")
DPI = 600
SAVE = dict(dpi=DPI, bbox_inches="tight")

def log(msg):
    print(f"[analyze] {msg}", flush=True)

# ----------------------------------------------------------------------
# Load optimization log
# ----------------------------------------------------------------------
LOG = str(LEGACY / "ga_training_log.csv")
df = pd.read_csv(LOG)
df.columns = [c.strip() for c in df.columns]
genes = np.array(df["Solution_Widths"].apply(ast.literal_eval).tolist(), dtype=float)
NG = genes.shape[1]
evac = df["Evac_Score"].to_numpy(float)
cost = df["Cost_Score"].to_numpy(float)
fit  = df["Final_Fitness"].to_numpy(float)
gen  = df["Generation"].to_numpy(int)
runid = df["Run_ID"].to_numpy(int)
log(f"loaded {len(df)} evals, {NG} genes, gens {gen.min()}-{gen.max()}")

# ======================================================================
# C2 — Pareto front
# ======================================================================
def pareto_mask(c, e):
    """non-dominated for minimization of (c, e)"""
    n = len(c); nd = np.ones(n, bool)
    order = np.argsort(c)
    best_e = np.inf
    for i in order:
        if e[i] < best_e - 1e-12:
            best_e = e[i]
        elif e[i] > best_e + 1e-12:
            nd[i] = False
    # strict domination cleanup (handle equal-cost ties)
    for i in range(n):
        if not nd[i]: continue
        dom = (c <= c[i]) & (e <= e[i]) & ((c < c[i]) | (e < e[i]))
        if dom.any(): nd[i] = False
    return nd

nd = pareto_mask(cost, evac)
pf = df[nd].copy().sort_values("Cost_Score")
log(f"C2: {nd.sum()} Pareto-optimal solutions")
pf_genes = np.array(pf["Solution_Widths"].apply(ast.literal_eval).tolist(), dtype=float)

# knee point: normalize both objectives on the front, min L2 distance to ideal
pc = pf["Cost_Score"].to_numpy(float); pe = pf["Evac_Score"].to_numpy(float)
nc = (pc - pc.min())/max(pc.max()-pc.min(),1e-9)
ne = (pe - pe.min())/max(pe.max()-pe.min(),1e-9)
knee_local = int(np.argmin(np.hypot(nc, ne)))
knee_idx = pf.index[knee_local]
# beta=0.1 weighted-sum optimum (the manuscript's original single solution)
beta = 0.1
w_idx = int(np.argmin(evac + beta*cost))

# Fig O1: objective space + Pareto front
fig, ax = plt.subplots(figsize=(6,5))
sc = ax.scatter(cost, evac, c=gen, cmap="viridis", s=18, alpha=0.55, edgecolors="none")
ax.plot(pf["Cost_Score"], pf["Evac_Score"], "-o", color="crimson", ms=4, lw=1.6, label="Pareto front")
ax.scatter([cost[knee_idx]],[evac[knee_idx]], marker="*", s=320, color="gold",
           edgecolors="k", zorder=6, label="Knee solution")
ax.scatter([cost[w_idx]],[evac[w_idx]], marker="D", s=70, color="royalblue",
           edgecolors="k", zorder=6, label=r"Weighted-sum ($\beta$=0.1)")
ax.set_xlabel("Cost score"); ax.set_ylabel("Evacuation score")
ax.set_title("Objective space and Pareto front")
cbar = fig.colorbar(sc, ax=ax); cbar.set_label("Generation")
ax.legend(loc="upper right", fontsize=8)
fig.savefig(os.path.join(FIG,"FigR_C2_pareto_front.png"), **SAVE); plt.close(fig)

# Hypervolume convergence (2D, ref = worst corner * 1.05)
ref_c = cost.max()*1.05; ref_e = evac.max()*1.05
def hv2d(c, e, rc, re):
    m = pareto_mask(c, e)
    pts = sorted(zip(c[m], e[m]))  # ascending cost
    hv = 0.0; prev_c = None; cur_e = re
    for cc, ee in pts:
        if cc >= rc or ee >= re: continue
        hv += (rc - cc) * (cur_e - ee)
        rc = cc  # next slab to the left
        cur_e = ee
    return hv
hv_series = []
gens = sorted(df["Generation"].unique())
for g in gens:
    sel = gen <= g
    hv_series.append(hv2d(cost[sel], evac[sel], ref_c, ref_e))
hv_series = np.array(hv_series)
hv_norm = hv_series / hv_series[-1]
fig, ax = plt.subplots(figsize=(6,5))
ax.plot(gens, hv_norm, "-o", ms=3, lw=2, color="tab:blue")
ax.set_xlabel("Generation"); ax.set_ylabel("Normalized hypervolume")
ax.set_title("Pareto-front convergence (hypervolume)")
ax.grid(True)
fig.savefig(os.path.join(FIG,"FigR_C2_hypervolume.png"), **SAVE); plt.close(fig)

# Representative solutions table
def row(tag, i):
    return dict(Type=tag, Run_ID=int(runid[i]), Evac=round(float(evac[i]),2),
               Cost=round(float(cost[i]),2),
               Widths="["+",".join(f"{v:.0f}" for v in genes[i])+"]")
reps = [
    row("Min-cost", int(pf["Cost_Score"].idxmin())),
    row("Min-evac (fastest)", int(pf["Evac_Score"].idxmin())),
    row("Knee (recommended)", int(knee_idx)),
    row(f"Weighted-sum beta={beta}", w_idx),
]
pd.DataFrame(reps).to_csv(os.path.join(TAB,"TableR_C2_representative_solutions.csv"), index=False)
pf[["Run_ID","Evac_Score","Cost_Score","Solution_Widths"]].to_csv(
    os.path.join(DAT,"pareto_front.csv"), index=False)
log("C2 done")

# ======================================================================
# C5a — global sensitivity to road-widening decisions + GA convergence
# ======================================================================
Xs = (genes - genes.mean(0)) / (genes.std(0) + 1e-9)
def std_coef(y):
    ys = (y - y.mean())/(y.std()+1e-9)
    return np.linalg.lstsq(Xs, ys, rcond=None)[0]
coef_evac = std_coef(evac); coef_cost = std_coef(cost)
seg = np.arange(1, NG+1)
order = np.argsort(np.abs(coef_evac))
fig, axes = plt.subplots(1,2, figsize=(12,6), sharey=True)
axes[0].barh(seg, coef_evac[order-0][order], color="tab:orange", alpha=0.85)
axes[0].set_yticks(seg); axes[0].set_yticklabels([f"R{order[k]+1}" for k in range(NG)])
axes[0].set_xlabel("Std. regression coef."); axes[0].set_title("Effect on evacuation score")
axes[0].axvline(0, color="k", lw=0.8)
axes[1].barh(seg, coef_cost[order], color="tab:blue", alpha=0.85)
axes[1].set_xlabel("Std. regression coef."); axes[1].set_title("Effect on cost score")
axes[1].axvline(0, color="k", lw=0.8)
fig.suptitle("Global sensitivity of objectives to road-segment widening", y=1.01)
fig.tight_layout()
fig.savefig(os.path.join(FIG,"FigR_C5_sensitivity_tornado.png"), **SAVE); plt.close(fig)

# main-effect table (mean objective per width level per segment)
rows=[]
for j in range(NG):
    rec={"Segment":f"R{j+1}", "coef_evac":round(float(coef_evac[j]),4),
         "coef_cost":round(float(coef_cost[j]),4)}
    for lvl in (0.0,2.0,4.0):
        m = genes[:,j]==lvl
        rec[f"evac@{int(lvl)}m"]=round(float(evac[m].mean()),1) if m.any() else np.nan
    rec["evac_range"]=round(rec["evac@4m"]-rec["evac@0m"],1)
    rows.append(rec)
pd.DataFrame(rows).to_csv(os.path.join(TAB,"TableR_C5_main_effects.csv"), index=False)

# GA convergence (best/mean fitness + std band) — original Fig1 style
gstats = df.groupby("Generation")["Final_Fitness"].agg(["mean","min","std"])
fig, ax = plt.subplots(figsize=(6,5))
ax.plot(gstats.index, gstats["mean"], "--", lw=2, label="Mean fitness")
ax.plot(gstats.index, gstats["min"], lw=2, label="Best fitness")
ax.fill_between(gstats.index, gstats["mean"]-gstats["std"], gstats["mean"]+gstats["std"],
                alpha=0.2, label="±1 std")
ax.set_xlabel("Generation"); ax.set_ylabel("Final fitness")
ax.set_title("GA fitness convergence"); ax.legend(); ax.grid(True)
fig.savefig(os.path.join(FIG,"FigR_C5_ga_convergence.png"), **SAVE); plt.close(fig)

# gene entropy diversity — original Fig5 style
from scipy.stats import entropy
def gene_entropy(idx):
    mat = genes[idx]
    ents=[]
    for j in range(NG):
        _,cnt=np.unique(mat[:,j], return_counts=True); ents.append(entropy(cnt))
    return np.mean(ents)
ent_by_gen = [gene_entropy(gen==g) for g in gens]
fig, ax = plt.subplots(figsize=(6,5))
ax.plot(gens, ent_by_gen, "-o", ms=3, lw=2, color="purple")
ax.set_xlabel("Generation"); ax.set_ylabel("Mean gene entropy")
ax.set_title("Population diversity (entropy)"); ax.grid(True)
fig.savefig(os.path.join(FIG,"FigR_C5_gene_entropy.png"), **SAVE); plt.close(fig)
log("C5a done")

# ======================================================================
# C4 — optimization-scale cost from the log (real GPU timing is separate)
# ======================================================================
best_so_far = np.minimum.accumulate(fit)
fig, ax = plt.subplots(figsize=(6,5))
ax.plot(np.arange(1,len(fit)+1), best_so_far, lw=2, color="tab:green")
ax.set_xlabel("Simulation evaluations"); ax.set_ylabel("Best-so-far fitness")
ax.set_title("Optimization efficiency (best-so-far vs evaluations)")
ax.grid(True)
# annotate evaluations to reach within 1% of final best
final_best = best_so_far[-1]
thr = final_best*1.01
reach = int(np.argmax(best_so_far <= thr))+1
ax.axvline(reach, color="k", ls=":", lw=1)
ax.text(reach, ax.get_ylim()[1], f" within 1% @ {reach} evals", va="top", fontsize=8)
fig.savefig(os.path.join(FIG,"FigR_C4_convergence_vs_evals.png"), **SAVE); plt.close(fig)
log(f"C4: within 1% of best after {reach}/{len(fit)} evals")

# ======================================================================
# C1 — model validation
# ======================================================================
# (a) fundamental diagram from a representative per-frame snapshot
def fundamental_diagram(csv_file, out_png, bins=25, min_count=30):
    d = pd.read_csv(csv_file, on_bad_lines="skip")
    d.columns=[c.strip() for c in d.columns]
    for c in ("State","Speed","Flow","Density"):
        d[c]=pd.to_numeric(d[c], errors="coerce")
    d=d[d["State"]==1].dropna(subset=["Speed","Flow","Density"])
    dens = d["Density"].to_numpy()*2.0   # same density scaling as original paradiam.py
    spd  = d["Speed"].to_numpy()
    flw  = d["Flow"].to_numpy()*2.0
    def binned(x,y):
        edges=np.unique(np.quantile(x,np.linspace(0,1,bins+1)))
        xb,yb=[],[]
        for a,b in zip(edges[:-1],edges[1:]):
            m=(x>=a)&(x<b) if b!=edges[-1] else (x>=a)&(x<=b)
            if m.sum()<min_count: continue
            xb.append(np.median(x[m])); yb.append(np.median(y[m]))
        return np.array(xb),np.array(yb)
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    axes[0].scatter(dens,spd,s=8,alpha=0.30,color="steelblue",edgecolors="none")
    xl,yl=binned(dens,spd)
    if len(xl): axes[0].plot(xl,yl,"k-",lw=2,label="Binned median")
    axes[0].axhline(1.34,color="tab:red",ls="--",lw=1.5,label="Weidmann free speed 1.34 m/s")
    axes[0].set_xlabel("Density (ped/m$^2$)"); axes[0].set_ylabel("Speed (m/s)")
    axes[0].set_title("Speed–Density (State=1)"); axes[0].set_xlim(0,4.5); axes[0].set_ylim(0,2.0)
    axes[0].grid(True,alpha=0.2); axes[0].legend(fontsize=8)
    axes[1].scatter(dens,flw,s=8,alpha=0.30,color="steelblue",edgecolors="none")
    xl2,yl2=binned(dens,flw)
    if len(xl2): axes[1].plot(xl2,yl2,"k-",lw=2,label="Binned median")
    axes[1].axhline(1.3,color="tab:red",ls="--",lw=1.5,label="SFPE specific-flow cap ~1.3")
    axes[1].set_xlabel("Density (ped/m$^2$)"); axes[1].set_ylabel("Flow (ped/m/s)")
    axes[1].set_title("Flow–Density (State=1)"); axes[1].set_xlim(0,4.5); axes[1].set_ylim(0,2.5)
    axes[1].grid(True,alpha=0.2); axes[1].legend(fontsize=8)
    plt.tight_layout(); fig.savefig(out_png,**SAVE); plt.close(fig)
    # macro indicators
    free_speed = float(np.nanmedian(spd[dens<0.5])) if (dens<0.5).any() else float(np.nanmax(spd))
    cap = float(np.nanmax(yl2)) if len(yl2) else float(np.nanmax(flw))
    return dict(free_speed=round(free_speed,3), max_density=round(float(np.nanmax(dens)),2),
                capacity=round(cap,3), n=len(d))

fd_csv = str(FUNDAMENTAL_FRAMES / "10.csv")
macro = fundamental_diagram(fd_csv, os.path.join(FIG,"FigR_C1_fundamental_diagram.png"))
log(f"C1 fundamental diagram: {macro}")

# (b) macroscopic evacuation curves for representative Pareto solutions
fig, ax = plt.subplots(figsize=(6,5))
curve_styles = dict(zip(["Min-cost","Min-evac (fastest)","Knee (recommended)",f"Weighted-sum beta={beta}"],
                        ["tab:blue","tab:green","gold","royalblue"]))
for r in reps:
    p = str(REPRESENTATIVE_RUNS / f"shipai_{r['Run_ID']}" / "alive_series.csv")
    if not os.path.exists(p): continue
    a = pd.read_csv(p)
    t=a["time"].to_numpy(float); al=a["alive"].to_numpy(float)
    ax.plot(t, al/al[0], lw=2, label=f"{r['Type']} (T={t[-1]:.0f}s)", color=curve_styles.get(r["Type"]))
ax.set_xlabel("Time (s)"); ax.set_ylabel("Fraction remaining")
ax.set_title("Macroscopic evacuation curves"); ax.legend(fontsize=8); ax.grid(True)
fig.savefig(os.path.join(FIG,"FigR_C1_evacuation_curves.png"), **SAVE); plt.close(fig)

# (c) distribution of total evacuation time + step counts across all runs (cached)
summ_path = str(DERIVED / "evac_summary.csv")
if not os.path.exists(summ_path):
    recs=[]
    for rid in runid:
        p=str(REPRESENTATIVE_RUNS / f"shipai_{rid}" / "alive_series.csv")
        if not os.path.exists(p): continue
        try:
            a=pd.read_csv(p)
            recs.append(dict(Run_ID=int(rid), steps=len(a),
                             T_total=float(a["time"].iloc[-1]),
                             N0=int(a["alive"].iloc[0]),
                             N_end=int(a["alive"].iloc[-1])))
        except Exception: pass
    pd.DataFrame(recs).to_csv(summ_path,index=False)
es = pd.read_csv(summ_path)
fig, axes = plt.subplots(1,2,figsize=(12,4.8))
axes[0].hist(es["T_total"], bins=40, color="tab:blue", alpha=0.85)
axes[0].set_xlabel("Total evacuation time (s)"); axes[0].set_ylabel("Number of runs")
axes[0].set_title("Distribution of total evacuation time"); axes[0].grid(True,alpha=0.25)
axes[1].hist(es["steps"], bins=40, color="tab:orange", alpha=0.85)
axes[1].set_xlabel("Simulation steps (compute proxy)"); axes[1].set_ylabel("Number of runs")
axes[1].set_title("Distribution of simulation length"); axes[1].grid(True,alpha=0.25)
plt.tight_layout(); fig.savefig(os.path.join(FIG,"FigR_C1C4_run_distributions.png"), **SAVE); plt.close(fig)

# macro indicator table vs literature
mt = pd.DataFrame([
    dict(Indicator="Free-flow speed (m/s)", Simulated=macro["free_speed"], Literature="1.2–1.4 (Weidmann)"),
    dict(Indicator="Specific flow capacity (ped/m/s)", Simulated=macro["capacity"], Literature="1.2–1.3 (SFPE/Fruin)"),
    dict(Indicator="Max observed density (ped/m^2)", Simulated=macro["max_density"], Literature="≤ ~5.5 (jam)"),
    dict(Indicator="Median total evac time (s)", Simulated=round(float(es["T_total"].median()),1), Literature="—"),
])
mt.to_csv(os.path.join(TAB,"TableR_C1_macro_validation.csv"), index=False)
log("C1 done")

# summary json
summary = dict(
    n_evals=int(len(df)), n_pareto=int(nd.sum()),
    knee_runid=int(runid[knee_idx]), knee_evac=float(evac[knee_idx]), knee_cost=float(cost[knee_idx]),
    weighted_runid=int(runid[w_idx]), weighted_evac=float(evac[w_idx]), weighted_cost=float(cost[w_idx]),
    evals_within_1pct=int(reach), macro=macro,
    median_total_time=float(es["T_total"].median()),
)
with open(os.path.join(DAT,"analysis_summary.json"),"w") as f: json.dump(summary,f,indent=2)
log("ALL DONE")
print(json.dumps(summary, indent=2))
