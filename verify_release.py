#!/usr/bin/env python3
"""Validate the portable GitHub result-and-plotting release."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FORBIDDEN_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".cu", ".cuh",
    ".o", ".obj", ".a", ".so", ".dll", ".dylib", ".exe", ".bin", ".vtk", ".pyc",
}
MAGIC_PREFIXES = (
    b"\x7fELF", b"MZ", b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf",
    b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe",
)
MAX_FILE_BYTES = 100 * 1024 * 1024


def files() -> list[Path]:
    return sorted(
        path for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts
    )


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    all_files = files()

    for required in (
        ROOT / "manuscript" / "CEUS.tex",
        ROOT / "manuscript" / "CEUS.pdf",
        ROOT / "plotting" / "run_all.py",
        ROOT / "plotting" / "common_paths.py",
        ROOT / "results",
        ROOT / "figures" / "generated",
    ):
        check(required.exists(), f"missing required path: {required.relative_to(ROOT)}", errors)

    for path in all_files:
        rel = path.relative_to(ROOT)
        check(path.suffix.lower() not in FORBIDDEN_SUFFIXES, f"forbidden suffix: {rel}", errors)
        check(path.stat().st_size < MAX_FILE_BYTES, f"file is at least 100 MiB: {rel}", errors)
        check(not (path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)),
              f"executable permission bit: {rel}", errors)
        with path.open("rb") as handle:
            prefix = handle.read(4)
        check(not any(prefix.startswith(magic) for magic in MAGIC_PREFIXES),
              f"native executable/library magic: {rel}", errors)

    text_extensions = {".py", ".md", ".tex"}
    for path in (item for item in all_files if item.suffix.lower() in text_extensions):
        content = path.read_text(encoding="utf-8", errors="replace")
        developer_home = "/" + "home" + "/" + "shyr"
        mounted_root = "/" + "mnt" + "/"
        check(developer_home not in content and mounted_root not in content,
              f"machine-specific absolute path: {path.relative_to(ROOT)}", errors)

    plotting_scripts = sorted((ROOT / "plotting").glob("*.py"))
    for path in plotting_scripts:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
        if path.name not in {"common_paths.py"}:
            content = path.read_text(encoding="utf-8")
            check("common_paths" in content, f"script bypasses common_paths: {path.name}", errors)

    tex_raw = (ROOT / "manuscript" / "CEUS.tex").read_text(encoding="utf-8", errors="replace")
    tex = "\n".join(line.split("%", 1)[0] for line in tex_raw.splitlines())
    figure_refs = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", tex)
    for ref in figure_refs:
        candidate = ROOT / "manuscript" / ref
        if candidate.suffix:
            exists = candidate.exists()
        else:
            exists = any(candidate.with_suffix(suffix).exists() for suffix in (".pdf", ".png", ".jpg", ".jpeg"))
        check(exists, f"missing manuscript figure: {ref}", errors)

    generated_figures = list((ROOT / "figures" / "generated").glob("*"))
    generated_tables = list((ROOT / "generated" / "tables").glob("*.csv"))
    check(len(generated_figures) >= 50, "fewer than 50 generated figure files", errors)
    check(len(generated_tables) >= 30, "fewer than 30 generated tables", errors)
    for key in (
        ROOT / "figures" / "generated" / "FigR_C1_macro_spatial_composite.png",
        ROOT / "figures" / "generated" / "FigR_C2_pareto_15d_multiseed.png",
        ROOT / "figures" / "generated" / "FigR_C4_scaling.pdf",
        ROOT / "figures" / "generated" / "FigR_C5_physical_optimization_sensitivity.pdf",
    ):
        check(key.exists() and key.stat().st_size > 0, f"missing/empty generated artifact: {key.name}", errors)

    manifest = ROOT / "MANIFEST.sha256"
    if manifest.exists():
        for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            expected, rel_name = line.split("  ", 1)
            target = ROOT / rel_name
            check(target.exists(), f"manifest target missing at line {line_number}: {rel_name}", errors)
            if target.exists():
                actual = hashlib.sha256(target.read_bytes()).hexdigest()
                check(actual == expected, f"hash mismatch: {rel_name}", errors)

    if errors:
        print("RELEASE_VALIDATION_FAIL")
        print("\n".join(f"- {error}" for error in errors))
        return 1

    print(
        "RELEASE_VALIDATION_PASS "
        f"files={len(all_files)} plotting_scripts={len(plotting_scripts)} "
        f"manuscript_fig_refs={len(figure_refs)} generated_figures={len(generated_figures)} "
        f"generated_tables={len(generated_tables)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
