#!/usr/bin/env python3
"""Create C1 macro metrics and a 5 m median evacuation-time heatmap."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common_paths import C1_PAIRED_RUNS, GENERATED_DATA


def clearance_time(completed_times: np.ndarray, population: int, fraction: float):
    rank = math.ceil(population * fraction)
    if rank > completed_times.size:
        return None
    return float(np.partition(completed_times, rank - 1)[rank - 1])


def load_run_record(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame.columns = [column.strip() for column in frame.columns]
    required = {"ID", "time", "distance", "start_x", "start_y", "state"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing run-record columns: {sorted(missing)}")
    for column in required.difference({"ID"}):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def write_heatmap(done: pd.DataFrame, output_dir: Path, cell_size: float, min_count: int):
    valid = done.dropna(subset=["start_x", "start_y", "time"]).copy()
    valid = valid[(valid["time"] >= 0) & (valid["start_x"] >= 0) & (valid["start_y"] >= 0)]
    valid["grid_x"] = np.floor(valid["start_x"] / cell_size).astype(int)
    valid["grid_y"] = np.floor(valid["start_y"] / cell_size).astype(int)

    grouped = (
        valid.groupby(["grid_y", "grid_x"], as_index=False)
        .agg(median_evacuation_time=("time", "median"), completed_count=("time", "size"))
    )
    grouped["x_min"] = grouped["grid_x"] * cell_size
    grouped["y_min"] = grouped["grid_y"] * cell_size
    grouped.to_csv(output_dir / "initial_position_evacuation_time_median_5m.csv", index=False)

    if grouped.empty:
        raise ValueError("No completed rows are available for the heatmap")
    nx = int(grouped["grid_x"].max()) + 1
    ny = int(grouped["grid_y"].max()) + 1
    raster = np.full((ny, nx), np.nan, dtype=float)
    shown = grouped[grouped["completed_count"] >= min_count]
    raster[shown["grid_y"].to_numpy(), shown["grid_x"].to_numpy()] = shown[
        "median_evacuation_time"
    ].to_numpy()

    figure, axis = plt.subplots(figsize=(8, 9))
    image = axis.imshow(
        raster,
        origin="lower",
        extent=(0, nx * cell_size, 0, ny * cell_size),
        interpolation="nearest",
        cmap="viridis",
        aspect="equal",
    )
    axis.set_title(f"Median evacuation time by initial position ({cell_size:g} m grid)")
    axis.set_xlabel("x (m)")
    axis.set_ylabel("y (m)")
    colorbar = figure.colorbar(image, ax=axis, shrink=0.8)
    colorbar.set_label("Median evacuation time (s)")
    figure.tight_layout()
    figure.savefig(output_dir / "initial_position_evacuation_time_median_5m.png", dpi=300)
    plt.close(figure)


def write_alive_plot(alive_path: Path, output_dir: Path, population: int):
    if not alive_path.exists():
        return
    alive = pd.read_csv(alive_path)
    alive.columns = [column.strip() for column in alive.columns]
    alive["time"] = pd.to_numeric(alive["time"], errors="coerce")
    alive["alive"] = pd.to_numeric(alive["alive"], errors="coerce")
    alive = alive.dropna(subset=["time", "alive"])
    alive["remaining_fraction"] = alive["alive"] / population
    alive.to_csv(output_dir / "overall_evacuation_process.csv", index=False)

    figure, axis = plt.subplots(figsize=(7.5, 4.8))
    axis.plot(alive["time"], alive["remaining_fraction"], linewidth=2)
    for remaining, label in ((0.5, "t50"), (0.2, "t80"), (0.05, "t95")):
        axis.axhline(remaining, color="0.5", linestyle="--", linewidth=0.8)
        axis.text(alive["time"].max(), remaining, f" {label}", va="center")
    axis.set_xlabel("Time (s)")
    axis.set_ylabel("Remaining population fraction")
    axis.set_ylim(0, 1)
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_dir / "overall_evacuation_process.png", dpi=300)
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "run_record",
        type=Path,
        nargs="?",
        default=C1_PAIRED_RUNS / "baseline" / "seed_11" / "run_record.csv",
    )
    parser.add_argument("--alive-series", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--cell-size", type=float, default=5.0)
    parser.add_argument("--min-count", type=int, default=5)
    args = parser.parse_args()

    output_dir = args.output_dir or GENERATED_DATA / "c1_macro_metrics_single_run"
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = load_run_record(args.run_record)
    population = len(frame)
    done = frame[frame["state"] == 0].copy()
    completed_times = done["time"].dropna().to_numpy(dtype=float)

    metrics = {
        "population": population,
        "completed": int(len(done)),
        "completed_fraction": float(len(done) / population),
        "t50_s": clearance_time(completed_times, population, 0.50),
        "t80_s": clearance_time(completed_times, population, 0.80),
        "t95_s": clearance_time(completed_times, population, 0.95),
        "heatmap_cell_size_m": args.cell_size,
        "heatmap_statistic": "median",
        "heatmap_min_completed_count": args.min_count,
    }

    if "free_flow_time_lower_bound" in done.columns:
        valid = done[(done["free_flow_time_lower_bound"] > 0) & done["time"].notna()]
        metrics.update(
            free_flow_samples=int(len(valid)),
            median_delay_above_free_flow_s=float(
                (valid["time"] - valid["free_flow_time_lower_bound"]).median()
            ),
            p90_delay_above_free_flow_s=float(
                (valid["time"] - valid["free_flow_time_lower_bound"]).quantile(0.90)
            ),
            median_time_to_free_flow_ratio=float(
                (valid["time"] / valid["free_flow_time_lower_bound"]).median()
            ),
            free_flow_bound_violations=int(
                (valid["time"] + 0.2 < valid["free_flow_time_lower_bound"]).sum()
            ),
        )

    (output_dir / "macro_metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_heatmap(done, output_dir, args.cell_size, args.min_count)
    alive_path = args.alive_series or args.run_record.parent / "alive_series.csv"
    write_alive_plot(alive_path, output_dir, population)
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
