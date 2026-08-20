# EBL: Simulation-based Road-Network Optimization for Disaster Evacuation

This repository is the public reproducibility package for the published paper:

> **A Novel Simulation-based Approach to Optimizing Road Networks for Disaster Evacuation in Dense Urban Informal Settlements**

It consolidates the final manuscript, publication figures, legacy experiment results, 2026 revision results, and the complete public analysis and plotting code needed to regenerate the reported result figures directly from the released data.

Author website: **[Chun Song — https://chun-song.com](https://chun-song.com)**

## Repository scope

The complete release-ready analysis and plotting code for this paper is maintained in this **EBL** repository. All plotting scripts are collected in one directory, use a single portable path configuration, and read only from the released result data.

This public package contains:

- the final submitted manuscript and its bibliography;
- all figures used by the final manuscript;
- legacy and revision-stage result datasets needed for analysis and figure reproduction;
- all direct result-to-figure Python pipelines;
- generated figures, tables, and derived statistics;
- a SHA-256 manifest and an automated release validator.

In accordance with the release boundary for this publication, C/C++/CUDA simulator source files, native executables, compiled libraries, and build products are not included. Python scripts whose sole purpose was to invoke a local native simulator are also outside this result-to-figure release. The complete public code referred to here therefore means the complete analysis and visualization code that can run from the released results.

## Repository layout

```text
EBL/
├── manuscript/                 # Final paper, bibliography, and manuscript fig/
├── plotting/                   # All analysis and plotting Python code
│   ├── common_paths.py         # Single source of truth for repository paths
│   └── run_all.py              # One-command entry point for all pipelines
├── results/                    # Released legacy and 2026 revision results
│   ├── legacy/
│   ├── c1_macro/
│   ├── compact/
│   ├── derived/
│   ├── ga_sweep/
│   ├── nsga2/
│   ├── physical_optimization_sensitivity/
│   └── sim_runs/
├── figures/
│   ├── manuscript/             # Central copy of final manuscript figures
│   ├── revision/               # Revision-stage figure archive
│   └── generated/              # Figures regenerated directly from results
├── generated/
│   ├── tables/                 # Regenerated summary tables
│   └── data/                   # Regenerated derived statistics
├── PLOTTING_INDEX.md           # Result → script → figure mapping
├── DATA_INVENTORY.md           # Data provenance and compact-data notes
├── VALIDATION.md               # Reproduction and release validation record
├── verify_release.py           # Automated repository validation
└── MANIFEST.sha256             # File-integrity hashes
```

## Quick start

Python 3.10 or newer is recommended.

```bash
git clone https://github.com/Shyr0796/EBL.git
cd EBL

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

MPLBACKEND=Agg python3 plotting/run_all.py
```

The one-command runner executes all 23 analysis/plotting pipelines in a stable order. Outputs are written to:

- `figures/generated/` for regenerated PNG/PDF figures;
- `generated/tables/` for regenerated CSV tables;
- `generated/data/` for derived statistics and intermediate analysis data.

List all available pipelines:

```bash
python3 plotting/run_all.py --list
```

Run one or more selected pipelines:

```bash
MPLBACKEND=Agg python3 plotting/run_all.py --only \
  plot_c1_paired_macro.py \
  plot_c2_pareto_15d.py
```

## Figure reproducibility

Every direct result-to-figure script imports its paths from `plotting/common_paths.py`. No script depends on the original development-machine path, so the repository can be cloned and executed from any location.

The full mapping between released input data, plotting scripts, generated figures, and generated tables is documented in [PLOTTING_INDEX.md](PLOTTING_INDEX.md). It covers:

- legacy evacuation, fundamental-diagram, and GA results;
- C1 physical calibration, congestion, paired macro validation, and spatial analysis;
- C2 beta sweep and multi-seed NSGA-II/Pareto analysis;
- C4 runtime scaling and optimization;
- C5 GA, SPH, model, NSGA-II, and physical-optimization sensitivity analyses.

The manuscript's actual figure files remain under `manuscript/fig/`. Regenerated outputs are deliberately written to `figures/generated/`, allowing a reviewer to compare regenerated artifacts with the submitted versions without overwriting them.

## Released data

The package contains 909 result data/log files (approximately 153 MB), combining earlier experiments with the 2026 revision campaign. Details are provided in [DATA_INVENTORY.md](DATA_INVENTORY.md).

Two unusually large intermediate datasets were converted into compact, directly plottable representations:

- collision-calibration curves and statistics replacing approximately 2.43 GB of frame-level files;
- a downsampled congestion-heatmap archive replacing approximately 3.52 GB of raw binary grid layers.

These compact files preserve the data required by the corresponding public plotting pipelines while keeping every repository file below GitHub's 100 MB per-file limit.

## Validation

The complete plotting suite was executed on 2026-08-20 with a non-interactive Matplotlib backend:

```text
ALL_PLOTTING_PIPELINES_PASS count=23 elapsed_s=42.9
```

The validated release contains 53 regenerated figure files and 31 regenerated tables. Run the repository checks with:

```bash
python3 verify_release.py
sha256sum -c MANIFEST.sha256
```

The validator checks required paths, Python syntax, centralized path use, active manuscript figure references, machine-specific paths, forbidden native formats, executable signatures and permissions, per-file size, key generated artifacts, and SHA-256 hashes.

## Citation

If you use this repository, please cite the published paper:

> *A Novel Simulation-based Approach to Optimizing Road Networks for Disaster Evacuation in Dense Urban Informal Settlements.*

The journal-formatted citation and DOI should be taken from the final publisher record. They are intentionally not guessed in this repository.

## Project links

- Repository: [https://github.com/Shyr0796/EBL](https://github.com/Shyr0796/EBL)
- Author website: [https://chun-song.com](https://chun-song.com)
- Final manuscript: [`manuscript/CEUS.pdf`](manuscript/CEUS.pdf)
- Plotting index: [`PLOTTING_INDEX.md`](PLOTTING_INDEX.md)
- Data inventory: [`DATA_INVENTORY.md`](DATA_INVENTORY.md)
- Validation record: [`VALIDATION.md`](VALIDATION.md)

---

中文说明：本仓库是论文的公开复现材料。论文对应的完整结果分析与绘图代码均集中在 `plotting/`，可直接读取 `results/` 中发布的数据生成图片和表格。项目与作者信息可访问个人网页 [https://chun-song.com](https://chun-song.com)。
