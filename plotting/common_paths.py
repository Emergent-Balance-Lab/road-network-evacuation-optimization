"""Single source of truth for every plotting script in this release."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
LEGACY = RESULTS / "legacy"
FUNDAMENTAL_FRAMES = LEGACY / "fundamental_frames"
REPRESENTATIVE_RUNS = LEGACY / "representative_runs"
C1_PAIRED_RUNS = RESULTS / "c1_macro" / "paired_runs"
DERIVED = RESULTS / "derived"
RELEASED_TABLES = RESULTS / "tables"
SIM_RUNS = RESULTS / "sim_runs"
GA_SWEEP = RESULTS / "ga_sweep"
NSGA2 = RESULTS / "nsga2"
PHYSICAL_SENSITIVITY = RESULTS / "physical_optimization_sensitivity"
GA_PHYSICAL_SENSITIVITY = RESULTS / "ga_physical_sensitivity"
COMPACT = RESULTS / "compact"

GENERATED_FIGURES = ROOT / "figures" / "generated"
GENERATED_TABLES = ROOT / "generated" / "tables"
GENERATED_DATA = ROOT / "generated" / "data"


def ensure_output_dirs() -> None:
    for directory in (GENERATED_FIGURES, GENERATED_TABLES, GENERATED_DATA):
        directory.mkdir(parents=True, exist_ok=True)


ensure_output_dirs()
