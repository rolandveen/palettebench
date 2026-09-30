"""Report orchestration, provenance, and comparison outputs."""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import platform
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import __version__
from .analysis import AnalysisConfig, AnalysisResult, analyse_palette
from .figures import write_figures
from .palette import Palette
from .tables import write_tables


def _versions() -> dict[str, str]:
    packages = ("numpy", "matplotlib", "PyYAML", "colorspacious", "colour-science")
    return {name: importlib.metadata.version(name) for name in packages}


def write_metadata(result: AnalysisResult, output: Path) -> None:
    palette_bytes = result.palette.path.read_bytes()
    metadata = {
        "palettebench_version": __version__,
        "python_version": platform.python_version(),
        "dependencies": _versions(),
        "input_palette": str(result.palette.path),
        "input_sha256": hashlib.sha256(palette_bytes).hexdigest(),
        "generated_utc": datetime.now(UTC).isoformat(),
        "configuration": {
            "severities": result.config.severities,
            "thresholds": result.config.thresholds,
            "curve_step": result.config.curve_step,
            "weakest_count": result.config.weakest_count,
            "simulation": "Colorspacious sRGB1+CVD (Machado et al.) with display-bound clipping",
            "metric": "CIEDE2000 via colour-science; sRGB D65 to CIE Lab",
        },
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def write_report(
    result: AnalysisResult,
    output: str | Path,
    formats: tuple[str, ...] = ("svg", "pdf", "png"),
    dpi: int = 300,
) -> Path:
    """Write a complete, self-contained single-palette audit directory."""
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    write_tables(result, destination)
    write_figures(result, destination, formats, dpi)
    write_metadata(result, destination)
    source = result.palette.source
    source_url = source.get("url", "Not supplied")
    threshold_text = ", ".join(f"ΔE00 < {value:g}" for value in result.config.thresholds)
    report = f"""# {result.palette.name}: palette audit

{result.palette.description}

![Normal palette](figures/palette_normal.svg)

## Palette metadata

- Input: `{result.palette.path.name}`
- Source: {source_url}
- Colours: {len(result.palette.colours)}
- Machine-readable provenance: [`metadata.json`](metadata.json)

## Methodology and assumptions

Input values are interpreted as six-digit, gamma-encoded sRGB. For each simulated condition, sRGB values are transformed with Colorspacious's `sRGB1+CVD` model, which implements the Machado et al. model, then clipped to the displayable sRGB gamut. Display-bound sRGB is converted through CIE XYZ to CIE Lab using the sRGB D65 reference white. Pairwise differences use CIEDE2000 (ΔE00) from Colour Science for Python. Grayscale values preserve WCAG relative luminance.

The simulated severity percentages are model parameters, not clinical measurements. Partial tritan simulations are supported by the underlying function but are omitted from the standard report because inherited tritan deficiency is rarer and severity interpolation has a less direct evidential basis than the primary red–green use case.

## Overview

![CVD overview](figures/cvd_overview.svg)

## Summary statistics

{(destination / "tables" / "summary.md").read_text(encoding="utf-8")}
Counts below the descriptive thresholds {threshold_text} are available in `data/summary.csv`. No threshold is treated as a universal accessibility pass/fail criterion.

## Palette characteristics

{(destination / "tables" / "colours.md").read_text(encoding="utf-8")}
## Pairwise comparisons

The lower half of each pair matrix places two colours in direct diagonal contact; the upper half gives their ΔE00 value.

- [Normal pair matrix](figures/pairs_normal.svg)
- [Protan 100% pair matrix](figures/pairs_protan100.svg)
- [Deutan 100% pair matrix](figures/pairs_deutan100.svg)
- [Tritan 100% pair matrix](figures/pairs_tritan100.svg)
- [All pairwise data](data/pairwise.csv)

## Weakest pairs and severity progression

![Weakest pairs](figures/weakest_pairs.svg)

![Distance versus severity](figures/minimum_distance_severity.svg)

The identity of the minimum pair at each sampled severity is recorded in `data/severity_curves.csv`.

## Grayscale and lightness

![Grayscale palette](figures/palette_grayscale.svg)

Grayscale is an additional robustness analysis; categorical palettes need not be fully discriminable by lightness alone when redundant encodings are provided.

## Caveats

Simulated CVD and perceptual-distance metrics support accessibility assessment, but they do not constitute validation with people who have CVD. Perception also depends on monitor calibration, viewing conditions, visual acuity, ageing, print reproduction, spatial context, and mark size. Colour should not be the sole carrier of critical information.

## Complete outputs

Publication-ready SVG/PDF figures and PNG previews are in `figures/`; Markdown and booktabs LaTeX tables are in `tables/`; canonical CSV/JSON data are in `data/`.
"""
    (destination / "report.md").write_text(report, encoding="utf-8")
    return destination


def write_comparison(
    palettes: list[Palette],
    output: str | Path,
    config: AnalysisConfig | None = None,
    formats: tuple[str, ...] = ("svg", "pdf", "png"),
    dpi: int = 300,
) -> Path:
    """Write transparent baseline-relative comparisons for two or more palettes."""
    if len(palettes) < 2:
        raise ValueError("Comparison requires at least two palettes")
    config = config or AnalysisConfig()
    results = [analyse_palette(palette, config) for palette in palettes]
    destination = Path(output)
    (destination / "figures").mkdir(parents=True, exist_ok=True)
    (destination / "data").mkdir(parents=True, exist_ok=True)
    keys = ("normal", "protan100", "deutan100", "tritan100", "grayscale")
    rows: list[dict[str, object]] = []
    baseline = {s.condition: s for s in results[0].summaries}
    for result in results:
        for summary in result.summaries:
            if summary.condition in keys:
                rows.append(
                    {
                        "palette": result.palette.name,
                        "condition": summary.condition,
                        "severity": summary.severity,
                        "minimum": summary.minimum,
                        "mean": summary.mean,
                        "median": summary.median,
                        "weakest_pair": "/".join(summary.minimum_pair),
                        "minimum_change_from_baseline": summary.minimum
                        - baseline[summary.condition].minimum,
                    }
                )
    with (destination / "data" / "comparison.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    fig, axes = plt.subplots(
        len(results),
        len(keys),
        figsize=(max(10, len(keys) * 2.2), len(results) * 1.7),
        squeeze=False,
    )
    for row_index, result in enumerate(results):
        for column_index, key in enumerate(keys):
            ax = axes[row_index, column_index]
            condition = next(c for c in result.conditions if c.key == key)
            for i, rgb in enumerate(condition.srgb):
                ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=rgb, ec="white", lw=0.4))
            ax.set(xlim=(0, len(condition.srgb)), ylim=(0, 1))
            ax.axis("off")
            if row_index == 0:
                ax.set_title(condition.label, fontsize=9)
            if column_index == 0:
                ax.text(
                    -0.04,
                    0.5,
                    result.palette.name,
                    transform=ax.transAxes,
                    ha="right",
                    va="center",
                    fontsize=8,
                )
    fig.savefig(destination / "figures" / "palette_comparison.svg", bbox_inches="tight")
    fig.savefig(destination / "figures" / "palette_comparison.pdf", bbox_inches="tight")
    if "png" in formats:
        fig.savefig(
            destination / "figures" / "palette_comparison.png", dpi=dpi, bbox_inches="tight"
        )
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for result in results:
        for kind, style in (("protan", "-"), ("deutan", "--")):
            points = [p for p in result.curves if p.kind == kind]
            ax.plot(
                [p.severity for p in points],
                [p.minimum for p in points],
                style,
                label=f"{result.palette.name} — {kind}",
            )
    ax.set(xlabel="Simulated severity (%)", ylabel="Minimum pairwise ΔE00", xlim=(0, 100))
    ax.grid(True, color="0.9")
    ax.legend(frameon=False, fontsize=7, ncol=2)
    for extension in formats:
        fig.savefig(
            destination / "figures" / f"minimum_distance_comparison.{extension}",
            dpi=dpi if extension == "png" else None,
            bbox_inches="tight",
        )
    plt.close(fig)
    lines = [
        "# Palette comparison",
        "",
        f"Baseline: **{results[0].palette.name}**",
        "",
        "![Palette comparison](figures/palette_comparison.svg)",
        "",
        "![Minimum distance comparison](figures/minimum_distance_comparison.svg)",
        "",
        "Results remain condition-specific; no aggregate accessibility score or ranking is computed.",
        "",
        "Full values, weakest pairs, and baseline changes are in [`data/comparison.csv`](data/comparison.csv).",
        "",
    ]
    (destination / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return destination
