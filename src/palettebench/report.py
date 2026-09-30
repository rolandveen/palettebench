"""Report orchestration, provenance, and comparison outputs."""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import platform
import shutil
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import __version__
from .analysis import AnalysisConfig, AnalysisResult, analyse_palette
from .figures import save_figure, write_figures
from .palette import Palette
from .tables import latex_table, markdown_table, write_tables


def _versions() -> dict[str, str]:
    packages = ("numpy", "matplotlib", "PyYAML", "colorspacious", "colour-science", "scipy")
    return {name: importlib.metadata.version(name) for name in packages}


def _copy_inputs(palettes: list[Palette], output: Path) -> list[dict[str, str]]:
    input_dir = output / "inputs"
    input_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for index, palette in enumerate(palettes, start=1):
        copied_name = f"{index:02d}-{palette.path.name}"
        copied_path = input_dir / copied_name
        shutil.copyfile(palette.path, copied_path)
        digest = hashlib.sha256(copied_path.read_bytes()).hexdigest()
        records.append(
            {
                "name": palette.name,
                "original_path": str(palette.path),
                "copied_file": f"inputs/{copied_name}",
                "sha256": digest,
            }
        )
    return records


def _configuration(config: AnalysisConfig) -> dict[str, object]:
    return {
        "severities": config.severities,
        "standard_100_percent_conditions_included": True,
        "thresholds": config.thresholds,
        "curve_step": config.curve_step,
        "weakest_count": config.weakest_count,
        "simulation": "Colorspacious sRGB1+CVD (Machado et al.) with display-bound clipping",
        "metric": "CIEDE2000 via colour-science; sRGB D65 to CIE Lab",
    }


def _preview_extension(formats: tuple[str, ...]) -> str:
    for preferred in ("svg", "png", "pdf"):
        if preferred in formats:
            return preferred
    raise ValueError("At least one output format is required")


def write_metadata(
    result: AnalysisResult,
    output: Path,
    inputs: list[dict[str, str]],
    formats: tuple[str, ...],
    dpi: int,
) -> None:
    palette_record = inputs[0]
    metadata = {
        "palettebench_version": __version__,
        "python_version": platform.python_version(),
        "dependencies": _versions(),
        "platform": platform.platform(),
        "input_palette": palette_record["original_path"],
        "input_copy": palette_record["copied_file"],
        "input_sha256": palette_record["sha256"],
        "inputs": inputs,
        "generated_utc": datetime.now(UTC).isoformat(),
        "configuration": {**_configuration(result.config), "formats": formats, "dpi": dpi},
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
    inputs = _copy_inputs([result.palette], destination)
    write_tables(result, destination)
    write_figures(result, destination, formats, dpi)
    write_metadata(result, destination, inputs, formats, dpi)
    preview = _preview_extension(formats)
    source = result.palette.source
    source_url = source.get("url", "Not supplied")
    threshold_text = ", ".join(f"ΔE00 < {value:g}" for value in result.config.thresholds)
    grouped_section = ""
    if any(colour.group is not None for colour in result.palette.colours):
        group_table = (destination / "tables" / "groups.md").read_text(encoding="utf-8")
        grouped_section = f"""## Grouped-palette analysis

Pairs are classified as within-group, between-group, or ungrouped. Condition-level distributions are in [`data/group_summary.csv`](data/group_summary.csv), and each individual relationship is retained in [`data/pairwise.csv`](data/pairwise.csv). Minimum within-group and between-group distances are included in `data/summary.csv`.

{group_table}
"""
    format_text = ", ".join(extension.upper() for extension in formats)
    report = f"""# {result.palette.name}: palette audit

{result.palette.description}

![Normal palette](figures/palette_normal.{preview})

## Palette metadata

- Input: [`{result.palette.path.name}`]({inputs[0]["copied_file"]})
- Source: {source_url}
- Colours: {len(result.palette.colours)}
- Machine-readable provenance: [`metadata.json`](metadata.json)

## Methodology and assumptions

Input values are interpreted as six-digit, gamma-encoded sRGB. For each simulated condition, sRGB values are transformed with Colorspacious's `sRGB1+CVD` model, which implements the Machado et al. model, then clipped to the displayable sRGB gamut. Display-bound sRGB is converted through CIE XYZ to CIE Lab using the sRGB D65 reference white. Pairwise differences use CIEDE2000 (ΔE00) from Colour Science for Python. Grayscale values preserve WCAG relative luminance.

The simulated severity percentages are model parameters, not clinical measurements. Partial tritan simulations are supported by the underlying function but are omitted from the standard report because inherited tritan deficiency is rarer and severity interpolation has a less direct evidential basis than the primary red–green use case.

## Overview

![CVD overview](figures/cvd_overview.{preview})

## Summary statistics

{(destination / "tables" / "summary.md").read_text(encoding="utf-8")}
Counts below the descriptive thresholds {threshold_text} are available in `data/summary.csv`. No threshold is treated as a universal accessibility pass/fail criterion.

## Palette characteristics

{(destination / "tables" / "colours.md").read_text(encoding="utf-8")}
## Pairwise comparisons

The lower half of each pair matrix places two colours in direct diagonal contact; the upper half gives their ΔE00 value.

- [Normal pair matrix](figures/pairs_normal.{preview})
- [Protan 100% pair matrix](figures/pairs_protan100.{preview})
- [Deutan 100% pair matrix](figures/pairs_deutan100.{preview})
- [Tritan 100% pair matrix](figures/pairs_tritan100.{preview})
- [All pairwise data](data/pairwise.csv)

{grouped_section}## Weakest pairs and severity progression

![Weakest pairs](figures/weakest_pairs.{preview})

![Distance versus severity](figures/minimum_distance_severity.{preview})

The identity of the minimum pair at each sampled severity is recorded in `data/severity_curves.csv`.

## Grayscale and lightness

![Grayscale palette](figures/palette_grayscale.{preview})

Grayscale is an additional robustness analysis; categorical palettes need not be fully discriminable by lightness alone when redundant encodings are provided.

## Caveats

Simulated CVD and perceptual-distance metrics support accessibility assessment, but they do not constitute validation with people who have CVD. Perception also depends on monitor calibration, viewing conditions, visual acuity, ageing, print reproduction, spatial context, and mark size. Colour should not be the sole carrier of critical information.

## Complete outputs

Requested figure formats ({format_text}) are in `figures/`; Markdown and booktabs LaTeX tables are in `tables/`; canonical CSV/JSON data are in `data/`; and an exact copy of the input palette is in `inputs/`.
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
    (destination / "tables").mkdir(parents=True, exist_ok=True)
    inputs = _copy_inputs(palettes, destination)
    preview = _preview_extension(formats)
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
                        "maximum": summary.maximum,
                        "mean": summary.mean,
                        "median": summary.median,
                        "std": summary.std,
                        "q10": summary.q10,
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
    (destination / "data" / "comparison.json").write_text(
        json.dumps(rows, indent=2) + "\n", encoding="utf-8"
    )
    table_headers = [
        "Palette",
        "Condition",
        "Severity",
        "Minimum ΔE00",
        "Weakest pair",
        "Change from baseline",
        "Mean",
        "Median",
        "Maximum",
        "SD",
        "10th percentile",
    ]
    table_rows = [
        [
            row["palette"],
            row["condition"],
            row["severity"],
            f"{row['minimum']:.2f}",
            row["weakest_pair"],
            f"{row['minimum_change_from_baseline']:+.2f}",
            f"{row['mean']:.2f}",
            f"{row['median']:.2f}",
            f"{row['maximum']:.2f}",
            f"{row['std']:.2f}",
            f"{row['q10']:.2f}",
        ]
        for row in rows
    ]
    comparison_markdown = markdown_table(table_headers, table_rows)
    (destination / "tables" / "comparison.md").write_text(comparison_markdown, encoding="utf-8")
    (destination / "tables" / "comparison.tex").write_text(
        latex_table(table_headers, table_rows), encoding="utf-8"
    )

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
    save_figure(fig, destination / "figures", "palette_comparison", formats, dpi)

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
    save_figure(fig, destination / "figures", "minimum_distance_comparison", formats, dpi)
    metadata = {
        "palettebench_version": __version__,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "dependencies": _versions(),
        "generated_utc": datetime.now(UTC).isoformat(),
        "baseline": palettes[0].name,
        "inputs": inputs,
        "configuration": {**_configuration(config), "formats": formats, "dpi": dpi},
    }
    (destination / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Palette comparison",
        "",
        f"Baseline: **{results[0].palette.name}**",
        "",
        f"![Palette comparison](figures/palette_comparison.{preview})",
        "",
        f"![Minimum distance comparison](figures/minimum_distance_comparison.{preview})",
        "",
        "Results remain condition-specific; no aggregate accessibility score or ranking is computed.",
        "",
        "## Condition-level results",
        "",
        comparison_markdown.rstrip(),
        "",
        "Full-precision values are in [`data/comparison.csv`](data/comparison.csv) and [`data/comparison.json`](data/comparison.json). Reproducibility metadata is in [`metadata.json`](metadata.json), and exact input copies are in `inputs/`.",
        "",
    ]
    (destination / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return destination
