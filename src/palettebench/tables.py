"""Markdown, LaTeX, CSV, and JSON serialisation."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Sequence
from pathlib import Path

import numpy as np

from .analysis import AnalysisResult, ConditionResult


def markdown_table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return "\n".join(lines) + "\n"


def _latex_escape(value: object) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "\n": " ",
    }
    return "".join(replacements.get(character, character) for character in str(value))


def latex_table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    rows = list(rows)
    columns = "l" + "r" * (len(headers) - 1)
    body = [
        r"\begin{tabular}{" + columns + "}",
        r"\toprule",
        " & ".join(map(_latex_escape, headers)) + r" \\",
        r"\midrule",
    ]
    body.extend(" & ".join(_latex_escape(value) for value in row) + r" \\" for row in rows)
    body.extend([r"\bottomrule", r"\end{tabular}", ""])
    return "\n".join(body)


def _matrix_rows(result: AnalysisResult, condition: ConditionResult) -> list[list[object]]:
    names = [colour.id for colour in result.palette.colours]
    return [
        [name, *(f"{value:.2f}" for value in condition.delta_e[index])]
        for index, name in enumerate(names)
    ]


def write_tables(result: AnalysisResult, output: Path) -> None:
    """Write publication tables and canonical machine-readable files."""
    data_dir, table_dir = output / "data", output / "tables"
    data_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    colour_headers = [
        "Colour",
        "HEX",
        "RGB",
        "L*",
        "Chroma",
        "Relative luminance",
        "Contrast white",
        "Contrast black",
        "Group",
    ]
    colour_rows = [
        [
            c.name,
            c.hex,
            " ".join(str(round(x * 255)) for x in c.srgb),
            f"{c.lab[0]:.2f}",
            f"{c.chroma:.2f}",
            f"{c.relative_luminance:.4f}",
            f"{c.contrast_white:.2f}",
            f"{c.contrast_black:.2f}",
            c.group or "—",
        ]
        for c in result.colours
    ]
    (table_dir / "colours.md").write_text(
        markdown_table(colour_headers, colour_rows), encoding="utf-8"
    )
    (table_dir / "colours.tex").write_text(
        latex_table(colour_headers, colour_rows), encoding="utf-8"
    )

    summary_headers = [
        "Condition",
        "Severity",
        "Minimum ΔE00",
        "Pair",
        "Maximum",
        "Mean",
        "Median",
        "SD",
        "10th percentile",
    ]
    summary_rows = [
        [
            s.condition,
            s.severity,
            f"{s.minimum:.2f}",
            " / ".join(s.minimum_pair),
            f"{s.maximum:.2f}",
            f"{s.mean:.2f}",
            f"{s.median:.2f}",
            f"{s.std:.2f}",
            f"{s.q10:.2f}",
        ]
        for s in result.summaries
    ]
    (table_dir / "summary.md").write_text(
        markdown_table(summary_headers, summary_rows), encoding="utf-8"
    )
    (table_dir / "summary.tex").write_text(
        latex_table(summary_headers, summary_rows), encoding="utf-8"
    )

    selected = {"normal", "protan100", "deutan100", "tritan100"}
    for condition in result.conditions:
        if condition.key in selected:
            headers = ["Colour", *(colour.id for colour in result.palette.colours)]
            rows = _matrix_rows(result, condition)
            (table_dir / f"deltae_{condition.key}.md").write_text(
                markdown_table(headers, rows), encoding="utf-8"
            )
            (table_dir / f"deltae_{condition.key}.tex").write_text(
                latex_table(headers, rows), encoding="utf-8"
            )

    with (data_dir / "colours.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "id",
                "name",
                "hex",
                "group",
                "srgb_r",
                "srgb_g",
                "srgb_b",
                "lab_l",
                "lab_a",
                "lab_b",
                "chroma",
                "relative_luminance",
                "contrast_white",
                "contrast_black",
            ]
        )
        for c in result.colours:
            writer.writerow(
                [
                    c.id,
                    c.name,
                    c.hex,
                    c.group or "",
                    *c.srgb,
                    *c.lab,
                    c.chroma,
                    c.relative_luminance,
                    c.contrast_white,
                    c.contrast_black,
                ]
            )

    pair_fields = [
        "condition",
        "kind",
        "severity",
        "colour1",
        "colour2",
        "group1",
        "group2",
        "relationship",
        "delta_e_00",
        "delta_l",
    ]
    pair_dicts = [{field: getattr(pair, field) for field in pair_fields} for pair in result.pairs]
    with (data_dir / "pairwise.csv").open("w", newline="", encoding="utf-8") as handle:
        pair_writer = csv.DictWriter(handle, fieldnames=pair_fields, lineterminator="\n")
        pair_writer.writeheader()
        pair_writer.writerows(pair_dicts)
    (data_dir / "pairwise.json").write_text(
        json.dumps(pair_dicts, indent=2) + "\n", encoding="utf-8"
    )

    with (data_dir / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "condition",
            "kind",
            "severity",
            "minimum",
            "minimum_pair",
            "maximum",
            "mean",
            "median",
            "std",
            "q10",
            "pair_count",
            "minimum_within_group",
            "minimum_between_group",
        ] + [
            field
            for threshold in result.config.thresholds
            for field in (f"below_{threshold:g}_count", f"below_{threshold:g}_fraction")
        ]
        summary_writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        summary_writer.writeheader()
        for s in result.summaries:
            row = {field: getattr(s, field) for field in fields if hasattr(s, field)}
            row["minimum_pair"] = "/".join(s.minimum_pair)
            for threshold in result.config.thresholds:
                row[f"below_{threshold:g}_count"] = s.below[threshold]
                row[f"below_{threshold:g}_fraction"] = s.below_fraction[threshold]
            summary_writer.writerow(row)

    relationships = ("within", "between", "ungrouped")
    grouped_table_rows: list[list[object]] = []
    with (data_dir / "group_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "condition",
                "kind",
                "severity",
                "relationship",
                "count",
                "minimum",
                "maximum",
                "mean",
                "median",
                "std",
            ]
        )
        for condition in result.conditions:
            condition_pairs = [pair for pair in result.pairs if pair.condition == condition.key]
            for relationship in relationships:
                values = np.asarray(
                    [
                        pair.delta_e_00
                        for pair in condition_pairs
                        if pair.relationship == relationship
                    ],
                    dtype=float,
                )
                if values.size:
                    data_row = [
                        condition.key,
                        condition.kind,
                        condition.severity,
                        relationship,
                        values.size,
                        values.min(),
                        values.max(),
                        values.mean(),
                        np.median(values),
                        values.std(ddof=0),
                    ]
                    writer.writerow(data_row)
                    if relationship in {"within", "between"}:
                        grouped_table_rows.append(
                            [
                                condition.key,
                                condition.severity,
                                relationship,
                                values.size,
                                f"{values.min():.2f}",
                                f"{values.mean():.2f}",
                                f"{np.median(values):.2f}",
                                f"{values.max():.2f}",
                            ]
                        )
    if grouped_table_rows:
        group_headers = [
            "Condition",
            "Severity",
            "Relationship",
            "Pairs",
            "Minimum",
            "Mean",
            "Median",
            "Maximum",
        ]
        (table_dir / "groups.md").write_text(
            markdown_table(group_headers, grouped_table_rows), encoding="utf-8"
        )
        (table_dir / "groups.tex").write_text(
            latex_table(group_headers, grouped_table_rows), encoding="utf-8"
        )

    with (data_dir / "conditions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "condition",
                "kind",
                "severity",
                "label",
                "clipped_colour_count",
                "clipped_channel_count",
                "raw_srgb_min",
                "raw_srgb_max",
            ]
        )
        writer.writerows(
            (
                c.key,
                c.kind,
                c.severity,
                c.label,
                np.count_nonzero(c.clipped_channels.any(axis=1)),
                np.count_nonzero(c.clipped_channels),
                c.raw_srgb.min(),
                c.raw_srgb.max(),
            )
            for c in result.conditions
        )

    with (data_dir / "gamut_clipping.csv").open("w", newline="", encoding="utf-8") as handle:
        # This is an exception table: header-only output means that no colour in
        # any reported condition required display-gamut clipping.
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "condition",
                "kind",
                "severity",
                "colour_id",
                "raw_srgb_r",
                "raw_srgb_g",
                "raw_srgb_b",
                "display_srgb_r",
                "display_srgb_g",
                "display_srgb_b",
                "clipped_r",
                "clipped_g",
                "clipped_b",
            ]
        )
        for condition in result.conditions:
            for colour, raw, display, clipped in zip(
                result.palette.colours,
                condition.raw_srgb,
                condition.srgb,
                condition.clipped_channels,
                strict=True,
            ):
                if clipped.any():
                    writer.writerow(
                        [
                            condition.key,
                            condition.kind,
                            condition.severity,
                            colour.id,
                            *raw,
                            *display,
                            *(bool(value) for value in clipped),
                        ]
                    )

    with (data_dir / "severity_curves.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["kind", "severity", "minimum", "mean", "median", "minimum_pair"])
        writer.writerows(
            (c.kind, c.severity, c.minimum, c.mean, c.median, "/".join(c.minimum_pair))
            for c in result.curves
        )
