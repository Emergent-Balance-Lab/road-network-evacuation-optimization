#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage-2 plotting for the REAL GPU experiments (run by run_experiments.sh):
  C4  scaling_timing.csv   -> wall-time & throughput vs crowd size
  C5b sph_sensitivity.csv  -> evacuation metric vs SPH / speed parameters
Robust to partially-complete data. Style matches the manuscript (ggplot, dpi=600).
"""
import os, glob
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common_paths import DERIVED, GENERATED_FIGURES, GENERATED_TABLES, SIM_RUNS

FIG, TAB, DAT, SIM = map(str, (GENERATED_FIGURES, GENERATED_TABLES, DERIVED, SIM_RUNS))
plt.style.use("ggplot"); SAVE=dict(dpi=600,bbox_inches="tight")
plt.rcParams.update({
    "font.size": 9.5,
    "axes.labelsize": 10.5,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8.5,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

def evac_metric(alive_csv):
    """same metric as the manuscript: T*(1+person_time/(N0*T))"""
    a=pd.read_csv(alive_csv)
    t=a["time"].to_numpy(float); al=a["alive"].to_numpy(float)
    if len(t)<2: return np.nan
    N0=al[0]; T=t[-1]-t[0]
    if N0<=0 or T<=0: return np.nan
    pt=np.trapezoid(al,t)
    return T*(1+pt/(N0*T))

# ----------------- C4 scaling -----------------
sc_path=os.path.join(DAT,"scaling_timing.csv")
if os.path.exists(sc_path):
    sc=pd.read_csv(sc_path)
    if len(sc):
        g=sc.groupby("crowd").agg(wall_mean=("wall_s","mean"),wall_std=("wall_s","std"),
                                  steps=("steps","mean")).reset_index()
        g["wall_std"]=g["wall_std"].fillna(0)
        # throughput = agent-steps per second
        g["throughput"]=g["crowd"]*g["steps"]/g["wall_mean"]
        g.to_csv(os.path.join(TAB,"TableR_C4_scaling_timing.csv"),index=False)
        fig,axes=plt.subplots(1,2,figsize=(7.2,3.0))
        axes[0].errorbar(g["crowd"],g["wall_mean"],yerr=g["wall_std"],fmt="-o",
                         color="tab:blue",capsize=3,lw=2,label="Measured wall time")
        # linear-in-N reference anchored at the largest point
        ref=g["wall_mean"].iloc[-1]/g["crowd"].iloc[-1]*g["crowd"]
        axes[0].plot(g["crowd"],ref,"--",color="gray",label="O(N) reference")
        axes[0].set_xscale("log"); axes[0].set_yscale("log")
        axes[0].set_xlabel("Number of agents N"); axes[0].set_ylabel("Wall-clock time (s)")
        axes[0].grid(True,which="both",alpha=0.3); axes[0].legend(loc="lower right")
        axes[0].text(-0.10, 1.03, "(a)", transform=axes[0].transAxes,
                     ha="left", va="bottom", fontweight="bold", clip_on=False)
        axes[1].plot(g["crowd"],g["throughput"]/1e6,"-o",color="tab:orange",lw=2)
        axes[1].set_xscale("log")
        axes[1].set_xlabel("Number of agents N"); axes[1].set_ylabel("Throughput (M agent-steps / s)")
        axes[1].grid(True,alpha=0.3)
        axes[1].text(-0.10, 1.03, "(b)", transform=axes[1].transAxes,
                     ha="left", va="bottom", fontweight="bold", clip_on=False)
        plt.tight_layout(rect=(0, 0, 1, 0.94))
        fig.savefig(os.path.join(FIG,"FigR_C4_scaling.png"),**SAVE)
        fig.savefig(os.path.join(FIG,"FigR_C4_scaling.pdf"),bbox_inches="tight")
        plt.close(fig)
        print("[plot] C4 scaling:", g.to_dict("records"))

# ----------------- C5b SPH sensitivity -----------------
sph_path=os.path.join(DAT,"sph_sensitivity.csv")
if os.path.exists(sph_path):
    sp=pd.read_csv(sph_path)
    # recompute full evac metric from archived alive_series where available
    metrics=[]
    for _,r in sp.iterrows():
        tag = "base" if r["param"]=="baseline" else None
        # find matching sim_runs dir
        name=None
        if r["param"]=="baseline": name="rev_sph_base"
        elif r["param"]=="smoothing_length": name=f"rev_sph_h_{r['value']}"
        elif r["param"]=="density_threshold": name=f"rev_sph_rho_{r['value']}"
        elif r["param"]=="speed_cap": name=f"rev_sph_vcap_{r['value']}"
        m=np.nan
        if name:
            p=os.path.join(SIM,name,"alive_series.csv")
            if os.path.exists(p): m=evac_metric(p)
        metrics.append(m)
    sp["evac_metric"]=metrics
    sp.to_csv(os.path.join(TAB,"TableR_C5_sph_sensitivity.csv"),index=False)
    base=sp[sp["param"]=="baseline"]
    base_m=float(base["evac_metric"].iloc[0]) if len(base) and np.isfinite(base["evac_metric"].iloc[0]) else np.nan
    params=[("smoothing_length","Smoothing length h (m)",2.4),
            ("density_threshold","Density threshold ρmax",4.0),
            ("speed_cap","Speed cap (m/s)",1.6)]
    fig,axes=plt.subplots(1,3,figsize=(15,4.6))
    for ax,(pk,xlabel,default) in zip(axes,params):
        sub=sp[sp["param"]==pk].copy()
        xs=[default]; ys=[base_m]
        for _,r in sub.iterrows():
            xs.append(float(r["value"])); ys.append(float(r["evac_metric"]))
        idx=np.argsort(xs); xs=np.array(xs)[idx]; ys=np.array(ys)[idx]
        ax.plot(xs,ys,"-o",color="tab:blue",lw=2)
        ax.axvline(default,color="tab:red",ls="--",lw=1.2,label="default")
        ax.set_xlabel(xlabel); ax.set_ylabel("Evacuation metric"); ax.grid(True,alpha=0.3)
        ax.set_title(f"Sensitivity to {pk.replace('_',' ')}"); ax.legend(fontsize=8)
    fig.suptitle("SPH / speed-regulation parameter sensitivity (crowd=8000, fixed scenario)",y=1.02)
    plt.tight_layout(); fig.savefig(os.path.join(FIG,"FigR_C5_sph_sensitivity.png"),**SAVE); plt.close(fig)
    # relative sensitivity table
    if np.isfinite(base_m):
        rows=[]
        for pk,_,default in params:
            sub=sp[sp["param"]==pk]
            for _,r in sub.iterrows():
                if np.isfinite(r["evac_metric"]):
                    rows.append(dict(param=pk,value=r["value"],
                                     evac_metric=round(float(r["evac_metric"]),1),
                                     pct_change_vs_default=round(100*(r["evac_metric"]-base_m)/base_m,2)))
        pd.DataFrame(rows).to_csv(os.path.join(TAB,"TableR_C5_sph_relative.csv"),index=False)
    print("[plot] C5b SPH done; baseline metric=",base_m)
print("[plot] stage-2 done")
