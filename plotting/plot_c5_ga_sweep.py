#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C5 GA meta-parameter sensitivity + robustness — analysis of the sweep produced by
ga_sweep/run_sweep.sh. Robust to PARTIAL data (only processes logs present).
Outputs (manuscript style: ggplot, dpi=600):
  FigR_C5_ga_robustness.png        convergence band + best-fitness boxplot over seeds
  FigR_C5_ga_param_sensitivity.png OFAT: final best fitness vs Pop / Cx / Mut
  TableR_C5_ga_sensitivity.csv     per-config summary
  TableR_C5_ga_robustness.csv      baseline seed-wise stats
"""
import os, glob, re, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common_paths import GA_SWEEP, GENERATED_FIGURES, GENERATED_TABLES

FIG, TAB = str(GENERATED_FIGURES), str(GENERATED_TABLES)
SWP = str(GA_SWEEP)
LOGDIR = os.environ.get("GA_SWEEP_LOGS", SWP)  # runner writes logs into ga_sweep/ root
plt.style.use("ggplot"); SAVE = dict(dpi=600, bbox_inches="tight")

BASE = dict(pop=24, cx=0.80, mut=0.08)


def classify(tag):
    """tag -> (family, pop, cx, mut, seed)"""
    m = re.match(r"([a-z]+\d*)_s(\d+)", tag)
    seed = int(m.group(2)) if m else 0
    pop, cx, mut, fam = BASE["pop"], BASE["cx"], BASE["mut"], "baseline"
    if tag.startswith("pop"):
        pop = int(re.match(r"pop(\d+)", tag).group(1)); fam = "pop"
    elif tag.startswith("cx"):
        v = re.match(r"cx(\d+)", tag).group(1); cx = float("0." + v) if len(v) <= 2 else float(v)/100; fam = "cx"
        cx = {"06": 0.60, "095": 0.95}.get(v, cx)
    elif tag.startswith("mut"):
        v = re.match(r"mut(\d+)", tag).group(1); mut = {"04": 0.04, "16": 0.16}.get(v, float(v)/100); fam = "mut"
    return fam, pop, cx, mut, seed


def per_log(path):
    d = pd.read_csv(path)
    d.columns = [c.strip() for c in d.columns]
    g = d.groupby("Generation")["Final_Fitness"].min()
    bsf = np.minimum.accumulate(g.to_numpy(float))          # best-so-far by generation
    final = float(bsf[-1])
    thr = final * 1.01
    conv_gen = int(np.argmax(bsf <= thr)) + 1
    best_row = d.loc[d["Final_Fitness"].idxmin()]
    return dict(gens=g.index.to_numpy(), bsf=bsf, final=final, conv_gen=conv_gen,
                evac=float(best_row["Evac_Score"]), cost=float(best_row["Cost_Score"]),
                n_eval=int(len(d)))


logs = sorted(glob.glob(os.path.join(LOGDIR, "log_*.csv")))
if not logs:
    print("[ga_sweep] no logs yet"); raise SystemExit(0)

rows, series = [], {}
for p in logs:
    tag = re.match(r"log_(.+)\.csv", os.path.basename(p)).group(1)
    try:
        r = per_log(p)
    except Exception as e:
        print(f"[ga_sweep] skip {tag}: {e}"); continue
    fam, pop, cx, mut, seed = classify(tag)
    rows.append(dict(tag=tag, family=fam, pop=pop, cx=cx, mut=mut, seed=seed,
                     final_best=round(r["final"], 2), conv_gen=r["conv_gen"],
                     best_evac=round(r["evac"], 1), best_cost=round(r["cost"], 1),
                     n_eval=r["n_eval"]))
    series[tag] = r
S = pd.DataFrame(rows).sort_values(["family", "pop", "cx", "mut", "seed"])
S.to_csv(os.path.join(TAB, "TableR_C5_ga_sensitivity.csv"), index=False)
print(f"[ga_sweep] {len(S)} configs processed")

# ---------- robustness: baseline seeds ----------
base_tags = [t for t in series if t.startswith("base")]
if base_tags:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    # (a) convergence band across seeds
    maxg = max(len(series[t]["bsf"]) for t in base_tags)
    M = np.full((len(base_tags), maxg), np.nan)
    for i, t in enumerate(base_tags):
        b = series[t]["bsf"]; M[i, :len(b)] = b
        axes[0].plot(range(1, len(b) + 1), b, color="tab:blue", alpha=0.35, lw=1)
    mean = np.nanmean(M, 0); lo = np.nanmin(M, 0); hi = np.nanmax(M, 0)
    gx = np.arange(1, maxg + 1)
    axes[0].plot(gx, mean, color="crimson", lw=2.2, label="Mean best-so-far")
    axes[0].fill_between(gx, lo, hi, color="tab:blue", alpha=0.18, label="Min–max over seeds")
    axes[0].set_xlabel("Generation"); axes[0].set_ylabel("Best-so-far fitness")
    axes[0].set_title(f"Convergence robustness across {len(base_tags)} seeds")
    axes[0].legend(fontsize=8); axes[0].grid(True, alpha=0.3)
    # (b) boxplot of final best fitness
    finals = [series[t]["final"] for t in base_tags]
    axes[1].boxplot([finals], tick_labels=["baseline\n(Pop24,Cx0.8,Mut0.08)"], widths=0.5)
    axes[1].scatter(np.ones(len(finals)), finals, color="tab:orange", zorder=5, s=30)
    axes[1].set_ylabel("Final best fitness")
    axes[1].set_title("Final-solution robustness")
    axes[1].grid(True, alpha=0.3)
    fig.suptitle("GA robustness to random seed (multi-seed repeats)", y=1.02)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "FigR_C5_ga_robustness.png"), **SAVE); plt.close(fig)
    cv = float(np.std(finals) / np.mean(finals)) if len(finals) > 1 else 0.0
    pd.DataFrame(dict(seed=[classify(t)[4] for t in base_tags], final_best=finals)).to_csv(
        os.path.join(TAB, "TableR_C5_ga_robustness.csv"), index=False)
    print(f"[ga_sweep] baseline final-best CV={cv:.4f} over {len(finals)} seeds")

# ---------- OFAT sensitivity: Pop / Cx / Mut ----------
def agg(values_key, fixed_ok):
    """collect (xval -> [finals]) for a family, baseline counts at its default x."""
    out = {}
    for t, r in series.items():
        fam, pop, cx, mut, seed = classify(t)
        x = {"pop": pop, "cx": cx, "mut": mut}[values_key]
        # baseline belongs to every panel at its default x
        if fam == "baseline" or fam == values_key:
            out.setdefault(x, []).append(r["final"])
    return out

panels = [("pop", "Population size", BASE["pop"]),
          ("cx", "Crossover rate", BASE["cx"]),
          ("mut", "Per-gene mutation prob.", BASE["mut"])]
fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
for ax, (key, xlabel, default) in zip(axes, panels):
    data = agg(key, default)
    xs = sorted(data)
    if xs:
        mean = [np.mean(data[x]) for x in xs]
        lo = [np.min(data[x]) for x in xs]; hi = [np.max(data[x]) for x in xs]
        ax.errorbar(xs, mean, yerr=[np.subtract(mean, lo), np.subtract(hi, mean)],
                    fmt="-o", color="tab:blue", lw=2, capsize=3)
        ax.axvline(default, color="tab:red", ls="--", lw=1.2, label="default")
    ax.set_xlabel(xlabel); ax.set_ylabel("Final best fitness")
    ax.set_title(f"Sensitivity to {xlabel.lower()}"); ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
fig.suptitle(f"GA meta-parameter sensitivity (OFAT, crowd-controlled study)", y=1.02)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "FigR_C5_ga_param_sensitivity.png"), **SAVE); plt.close(fig)
print("[ga_sweep] sensitivity figure done")
print(json.dumps(S.to_dict("records"), indent=1)[:800])
