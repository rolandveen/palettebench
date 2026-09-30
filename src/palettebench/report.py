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
from typing import Any

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import __version__
from .analysis import AnalysisConfig, AnalysisResult, analyse_palette
from .figures import save_figure, write_figures
from .palette import Palette
from .tables import latex_table, markdown_table, write_tables

FLOAT_EQUALITY_TOLERANCE = 1e-12


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
                "original_path": palette.path.name,
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
        "standard_deviation": "population standard deviation (ddof=0)",
        "quantile_method": "NumPy percentile, method=linear",
    }


def _preview_extension(formats: tuple[str, ...]) -> str:
    for preferred in ("svg", "png", "pdf"):
        if preferred in formats:
            return preferred
    raise ValueError("At least one output format is required")


def _prepare_destination(output: str | Path) -> Path:
    destination = Path(output)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError(f"refusing to write into non-empty output directory: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def _validate_render_options(formats: tuple[str, ...], dpi: int) -> None:
    allowed = {"svg", "pdf", "png"}
    if not formats or len(formats) != len(set(formats)) or set(formats) - allowed:
        raise ValueError("Formats must be a unique non-empty selection of svg, pdf, and png")
    if isinstance(dpi, bool) or not isinstance(dpi, int) or dpi < 1:
        raise ValueError("DPI must be a positive integer")


def _clipping_metadata(result: AnalysisResult) -> list[dict[str, object]]:
    records = []
    for condition in result.conditions:
        affected = np.asarray(condition.clipped_channels.any(axis=1), dtype=bool)
        records.append(
            {
                "condition": condition.key,
                "clipped_colour_count": int(affected.sum()),
                "clipped_channel_count": int(condition.clipped_channels.sum()),
                "clipped_colour_ids": [
                    colour.id
                    for colour, is_affected in zip(result.palette.colours, affected, strict=True)
                    if is_affected
                ],
                "raw_srgb_min": float(condition.raw_srgb.min()),
                "raw_srgb_max": float(condition.raw_srgb.max()),
            }
        )
    return records


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
        "gamut_clipping": _clipping_metadata(result),
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def write_report(
    result: AnalysisResult,
    output: str | Path,
    formats: tuple[str, ...] = ("svg", "pdf", "png"),
    dpi: int = 300,
) -> Path:
    """Write a complete, self-contained single-palette audit directory."""
    _validate_render_options(formats, dpi)
    destination = _prepare_destination(output)
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

Input values are interpreted as six-digit, gamma-encoded sRGB. For each simulated condition, sRGB values are transformed with Colorspacious's `sRGB1+CVD` model, which implements the Machado et al. model, then clipped to the displayable sRGB gamut. Display-bound sRGB is converted through CIE XYZ to CIE Lab using the sRGB D65 reference white. Pairwise differences use CIEDE2000 (ΔE00) from Colour Science for Python. Grayscale values preserve WCAG relative luminance. Condition-level clipping summaries are in [`metadata.json`](metadata.json) and [`data/conditions.csv`](data/conditions.csv); affected colours and their raw and clipped RGB values are in [`data/gamut_clipping.csv`](data/gamut_clipping.csv).

The simulated severity percentages are model parameters, not clinical measurements. Partial tritan simulations are supported by the underlying function but are omitted from the standard report because inherited tritan deficiency is rarer and severity interpolation has a less direct evidential basis than the primary red–green use case.

## Overview

![CVD overview](figures/cvd_overview.{preview})

## Simulated CVD palette strips

### Protan 100%

![Protan 100% palette](figures/palette_protan100.{preview})

### Deutan 100%

![Deutan 100% palette](figures/palette_deutan100.{preview})

### Tritan 100%

![Tritan 100% palette](figures/palette_tritan100.{preview})

## Severity progressions

### Protan progression

![Protan severity progression](figures/severity_protan.{preview})

### Deutan progression

![Deutan severity progression](figures/severity_deutan.{preview})

## Summary statistics

{(destination / "tables" / "summary.md").read_text(encoding="utf-8")}
Counts below the descriptive thresholds {threshold_text} are available in `data/summary.csv`. No threshold is treated as a universal accessibility pass/fail criterion.

## Palette characteristics

{(destination / "tables" / "colours.md").read_text(encoding="utf-8")}
## Pairwise comparisons

The lower half of each pair matrix places two colours in direct diagonal contact; the upper half gives their ΔE00 value.

### Pairwise ΔE00 heatmaps

#### Normal

![Normal pairwise heatmap](figures/heatmap_normal.{preview})

#### Protan 100%

![Protan 100% pairwise heatmap](figures/heatmap_protan100.{preview})

#### Deutan 100%

![Deutan 100% pairwise heatmap](figures/heatmap_deutan100.{preview})

#### Tritan 100%

![Tritan 100% pairwise heatmap](figures/heatmap_tritan100.{preview})

### Diagonal split pair matrices

#### Normal

![Normal pair matrix](figures/pairs_normal.{preview})

#### Protan 100%

![Protan 100% pair matrix](figures/pairs_protan100.{preview})

#### Deutan 100%

![Deutan 100% pair matrix](figures/pairs_deutan100.{preview})

#### Tritan 100%

![Tritan 100% pair matrix](figures/pairs_tritan100.{preview})

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

Requested figure formats ({format_text}) are in `figures/`; Markdown and booktabs LaTeX tables are in `tables/`; canonical CSV/JSON data, including gamut-clipping provenance, are in `data/`; and an exact copy of the input palette is in `inputs/`.
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
    _validate_render_options(formats, dpi)
    results = [analyse_palette(palette, config) for palette in palettes]
    destination = _prepare_destination(output)
    (destination / "figures").mkdir(parents=True, exist_ok=True)
    (destination / "data").mkdir(parents=True, exist_ok=True)
    (destination / "tables").mkdir(parents=True, exist_ok=True)
    inputs = _copy_inputs(palettes, destination)
    preview = _preview_extension(formats)
    keys = ("normal", "protan100", "deutan100", "tritan100", "grayscale")
    rows: list[dict[str, Any]] = []
    baseline = {s.condition: s for s in results[0].summaries}
    for palette_index, result in enumerate(results):
        for summary in result.summaries:
            if summary.condition in keys:
                reference = baseline[summary.condition]
                minimum_change = summary.minimum - reference.minimum
                row: dict[str, Any] = {
                    "palette": result.palette.name,
                    "palette_index": palette_index,
                    "condition": summary.condition,
                    "severity": summary.severity,
                    "minimum": summary.minimum,
                    "minimum_change_from_baseline": minimum_change,
                    "q10": summary.q10,
                    "q10_change_from_baseline": summary.q10 - reference.q10,
                    "mean": summary.mean,
                    "mean_change_from_baseline": summary.mean - reference.mean,
                    "median": summary.median,
                    "median_change_from_baseline": summary.median - reference.median,
                    "maximum": summary.maximum,
                    "std": summary.std,
                    "weakest_pair": "/".join(summary.minimum_pair),
                    "minimum_separation_direction": (
                        "baseline"
                        if result is results[0]
                        else "increased"
                        if minimum_change > FLOAT_EQUALITY_TOLERANCE
                        else "decreased"
                        if minimum_change < -FLOAT_EQUALITY_TOLERANCE
                        else "unchanged"
                    ),
                }
                for threshold in config.thresholds:
                    label = f"below_{threshold:g}"
                    row[f"{label}_count"] = summary.below[threshold]
                    row[f"{label}_count_change_from_baseline"] = (
                        summary.below[threshold] - reference.below[threshold]
                    )
                    row[f"{label}_fraction"] = summary.below_fraction[threshold]
                    row[f"{label}_fraction_change_from_baseline"] = (
                        summary.below_fraction[threshold] - reference.below_fraction[threshold]
                    )
                rows.append(row)
    with (destination / "data" / "comparison.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (destination / "data" / "comparison.json").write_text(
        json.dumps(rows, indent=2) + "\n", encoding="utf-8"
    )
    table_headers = [
        "Palette #",
        "Palette",
        "Condition",
        "Severity",
        "Minimum ΔE00",
        "Δ minimum",
        "10th percentile",
        "Δ 10th percentile",
        "Weakest pair",
        "Mean",
        "Δ mean",
        "Median",
        "Δ median",
        "Maximum",
        "SD",
    ]
    table_rows = [
        [
            row["palette_index"] + 1,
            row["palette"],
            row["condition"],
            row["severity"],
            f"{row['minimum']:.2f}",
            f"{row['minimum_change_from_baseline']:+.2f}",
            f"{row['q10']:.2f}",
            f"{row['q10_change_from_baseline']:+.2f}",
            row["weakest_pair"],
            f"{row['mean']:.2f}",
            f"{row['mean_change_from_baseline']:+.2f}",
            f"{row['median']:.2f}",
            f"{row['median_change_from_baseline']:+.2f}",
            f"{row['maximum']:.2f}",
            f"{row['std']:.2f}",
        ]
        for row in rows
    ]
    comparison_markdown = markdown_table(table_headers, table_rows)
    (destination / "tables" / "comparison.md").write_text(comparison_markdown, encoding="utf-8")
    (destination / "tables" / "comparison.tex").write_text(
        latex_table(table_headers, table_rows), encoding="utf-8"
    )

    # Palette order must not affect matching: condition plus the sorted ID pair
    # is the stable identity shared by baseline and candidate results.
    baseline_pairs = {
        (pair.condition, *sorted((pair.colour1, pair.colour2))): pair for pair in results[0].pairs
    }
    pair_changes: list[dict[str, Any]] = []
    for palette_index, result in enumerate(results[1:], start=1):
        for pair in result.pairs:
            pair_reference = baseline_pairs.get(
                (pair.condition, *sorted((pair.colour1, pair.colour2)))
            )
            if pair_reference is None:
                continue
            change = pair.delta_e_00 - pair_reference.delta_e_00
            pair_changes.append(
                {
                    "palette": result.palette.name,
                    "palette_index": palette_index,
                    "condition": pair.condition,
                    "kind": pair.kind,
                    "severity": pair.severity,
                    "colour1": pair.colour1,
                    "colour2": pair.colour2,
                    "baseline_delta_e_00": pair_reference.delta_e_00,
                    "palette_delta_e_00": pair.delta_e_00,
                    "change_from_baseline": change,
                    "direction": (
                        "increased"
                        if change > FLOAT_EQUALITY_TOLERANCE
                        else "decreased"
                        if change < -FLOAT_EQUALITY_TOLERANCE
                        else "unchanged"
                    ),
                }
            )
    pair_change_fields = [
        "palette",
        "palette_index",
        "condition",
        "kind",
        "severity",
        "colour1",
        "colour2",
        "baseline_delta_e_00",
        "palette_delta_e_00",
        "change_from_baseline",
        "direction",
    ]
    with (destination / "data" / "pairwise_changes.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=pair_change_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(pair_changes)
    (destination / "data" / "pairwise_changes.json").write_text(
        json.dumps(pair_changes, indent=2) + "\n", encoding="utf-8"
    )
    # Report both directional denominators. Baseline coverage exposes removed or
    # renamed pairs; candidate coverage exposes added or renamed pairs; Jaccard
    # reports intersection over union without privileging either palette.
    coverage_rows: list[dict[str, object]] = []
    for palette_index, result in enumerate(results[1:], start=1):
        for condition in keys:
            baseline_pair_ids = {
                tuple(sorted((pair.colour1, pair.colour2)))
                for pair in results[0].pairs
                if pair.condition == condition
            }
            candidate_pair_ids = {
                tuple(sorted((pair.colour1, pair.colour2)))
                for pair in result.pairs
                if pair.condition == condition
            }
            matched_count = len(baseline_pair_ids & candidate_pair_ids)
            union_count = len(baseline_pair_ids | candidate_pair_ids)
            coverage_rows.append(
                {
                    "palette": result.palette.name,
                    "palette_index": palette_index,
                    "condition": condition,
                    "baseline_pair_count": len(baseline_pair_ids),
                    "candidate_pair_count": len(candidate_pair_ids),
                    "matched_pair_count": matched_count,
                    "union_pair_count": union_count,
                    "baseline_coverage_fraction": matched_count / len(baseline_pair_ids),
                    "candidate_coverage_fraction": matched_count / len(candidate_pair_ids),
                    "jaccard_pair_fraction": matched_count / union_count,
                    "baseline_only_pair_count": len(baseline_pair_ids - candidate_pair_ids),
                    "candidate_only_pair_count": len(candidate_pair_ids - baseline_pair_ids),
                }
            )
    with (destination / "data" / "pairwise_coverage.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(coverage_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(coverage_rows)
    (destination / "data" / "pairwise_coverage.json").write_text(
        json.dumps(coverage_rows, indent=2) + "\n", encoding="utf-8"
    )

    diagnostic_rows: list[list[object]] = []
    for palette_index, result in enumerate(results[1:], start=1):
        for condition in keys:
            matches = [
                row
                for row in pair_changes
                if row["palette_index"] == palette_index and row["condition"] == condition
            ]
            for label, selected in (
                (
                    "Largest increase",
                    sorted(
                        (
                            row
                            for row in matches
                            if row["change_from_baseline"] > FLOAT_EQUALITY_TOLERANCE
                        ),
                        key=lambda row: row["change_from_baseline"],
                        reverse=True,
                    )[:3],
                ),
                (
                    "Largest decrease",
                    sorted(
                        (
                            row
                            for row in matches
                            if row["change_from_baseline"] < -FLOAT_EQUALITY_TOLERANCE
                        ),
                        key=lambda row: row["change_from_baseline"],
                    )[:3],
                ),
            ):
                for row in selected:
                    diagnostic_rows.append(
                        [
                            palette_index + 1,
                            result.palette.name,
                            condition,
                            label,
                            f"{row['colour1']} / {row['colour2']}",
                            f"{row['baseline_delta_e_00']:.2f}",
                            f"{row['palette_delta_e_00']:.2f}",
                            f"{row['change_from_baseline']:+.2f}",
                        ]
                    )
    diagnostic_headers = [
        "Palette #",
        "Palette",
        "Condition",
        "Diagnostic",
        "Pair",
        "Baseline ΔE00",
        "Palette ΔE00",
        "Change",
    ]
    diagnostic_markdown = markdown_table(diagnostic_headers, diagnostic_rows)
    (destination / "tables" / "pairwise_changes.md").write_text(
        diagnostic_markdown, encoding="utf-8"
    )
    (destination / "tables" / "pairwise_changes.tex").write_text(
        latex_table(diagnostic_headers, diagnostic_rows), encoding="utf-8"
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
            rendered_condition = next(c for c in result.conditions if c.key == key)
            for i, rgb in enumerate(rendered_condition.srgb):
                ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=rgb, ec="white", lw=0.4))
            ax.set(xlim=(0, len(rendered_condition.srgb)), ylim=(0, 1))
            ax.axis("off")
            if row_index == 0:
                ax.set_title(rendered_condition.label, fontsize=9)
            if column_index == 0:
                ax.text(
                    -0.04,
                    0.5,
                    f"{row_index + 1}. {result.palette.name}",
                    transform=ax.transAxes,
                    ha="right",
                    va="center",
                    fontsize=8,
                )
    save_figure(fig, destination / "figures", "palette_comparison", formats, dpi)

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for palette_index, result in enumerate(results, start=1):
        for kind, style in (("protan", "-"), ("deutan", "--")):
            points = [p for p in result.curves if p.kind == kind]
            ax.plot(
                [p.severity for p in points],
                [p.minimum for p in points],
                style,
                label=f"{palette_index}. {result.palette.name} — {kind}",
            )
    ax.set(xlabel="Simulated severity (%)", ylabel="Minimum pairwise ΔE00", xlim=(0, 100))
    ax.grid(True, color="0.9")
    ax.legend(frameon=False, fontsize=7, ncol=2)
    save_figure(fig, destination / "figures", "minimum_distance_comparison", formats, dpi)

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    candidates = results[1:]
    positions = list(range(len(keys)))
    width = 0.8 / max(1, len(candidates))
    for candidate_index, result in enumerate(candidates):
        candidate_rows = {
            row["condition"]: row for row in rows if row["palette_index"] == candidate_index + 1
        }
        offset = (candidate_index - (len(candidates) - 1) / 2) * width
        ax.bar(
            [position + offset for position in positions],
            [candidate_rows[key]["minimum_change_from_baseline"] for key in keys],
            width=width,
            label=f"{candidate_index + 2}. {result.palette.name}",
        )
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(positions, ["Normal", "Protan 100%", "Deutan 100%", "Tritan 100%", "Grayscale"])
    ax.tick_params(axis="x", rotation=25)
    ax.set_ylabel("Change in minimum pairwise ΔE00")
    ax.set_title("Minimum-separation change relative to baseline")
    ax.grid(True, axis="y", color="0.9", linewidth=0.8)
    ax.legend(frameon=False, fontsize=8)
    save_figure(fig, destination / "figures", "minimum_change_comparison", formats, dpi)
    metadata = {
        "palettebench_version": __version__,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "dependencies": _versions(),
        "generated_utc": datetime.now(UTC).isoformat(),
        "baseline": palettes[0].name,
        "inputs": inputs,
        "configuration": {**_configuration(config), "formats": formats, "dpi": dpi},
        "gamut_clipping": {
            str(index): _clipping_metadata(result) for index, result in enumerate(results, start=1)
        },
    }
    (destination / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Palette comparison",
        "",
        f"Baseline (palette 1): **{results[0].palette.name}**",
        "",
        f"![Palette comparison](figures/palette_comparison.{preview})",
        "",
        f"![Minimum distance comparison](figures/minimum_distance_comparison.{preview})",
        "",
        f"![Minimum-separation change](figures/minimum_change_comparison.{preview})",
        "",
        "Positive Δ values mean greater modelled separation than the baseline; negative values mean reduced modelled separation. These are objective changes in the stated metric, not universal accessibility verdicts. Results remain condition-specific; no aggregate accessibility score or ranking is computed.",
        "",
        "## Condition-level results",
        "",
        comparison_markdown.rstrip(),
        "",
        "Threshold count and fraction changes are included in the full-precision comparison data.",
        "",
        "## Largest matched-pair changes",
        "",
        "Pairs are matched by colour ID. Increased ΔE00 means greater modelled separation; decreased ΔE00 means reduced modelled separation. Two-sided matching coverage is recorded in [`data/pairwise_coverage.csv`](data/pairwise_coverage.csv) and [`data/pairwise_coverage.json`](data/pairwise_coverage.json), so palettes with added, removed, or renamed IDs are not silently treated as complete pairwise comparisons.",
        "",
        diagnostic_markdown.rstrip(),
        "",
        "Full-precision summaries are in [`data/comparison.csv`](data/comparison.csv) and [`data/comparison.json`](data/comparison.json). Every matched pair is in [`data/pairwise_changes.csv`](data/pairwise_changes.csv) and [`data/pairwise_changes.json`](data/pairwise_changes.json). Reproducibility metadata is in [`metadata.json`](metadata.json), and exact input copies are in `inputs/`.",
        "",
    ]
    (destination / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return destination
