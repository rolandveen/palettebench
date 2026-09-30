"""Restrained, publication-oriented Matplotlib figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams.update(
    {"svg.fonttype": "none", "svg.hashsalt": "palettebench", "pdf.fonttype": 42}
)
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.patches import Polygon, Rectangle

from .analysis import AnalysisResult, ConditionResult


def save_figure(
    fig: plt.Figure, directory: Path, stem: str, formats: tuple[str, ...], dpi: int
) -> None:
    for extension in formats:
        metadata: dict[str, object] = {}
        if extension == "svg":
            metadata.update({"Creator": None, "Date": None})
        elif extension == "pdf":
            metadata.update({"Creator": "PaletteBench", "CreationDate": None, "ModDate": None})
        elif extension == "png":
            metadata["Software"] = "PaletteBench"
        fig.savefig(
            directory / f"{stem}.{extension}",
            dpi=dpi if extension == "png" else None,
            bbox_inches="tight",
            metadata=metadata,
        )
    plt.close(fig)


def _condition(result: AnalysisResult, key: str) -> ConditionResult:
    return next(condition for condition in result.conditions if condition.key == key)


def _text_colour(rgb: np.ndarray) -> str:
    return "black" if float(rgb @ np.array([0.2126, 0.7152, 0.0722])) > 0.52 else "white"


def palette_strip(result: AnalysisResult, condition: ConditionResult) -> plt.Figure:
    n = len(result.colours)
    fig, ax = plt.subplots(figsize=(max(7, n * 1.25), 2.5))
    for index, (colour, rgb) in enumerate(zip(result.colours, condition.srgb, strict=True)):
        ax.add_patch(Rectangle((index, 0), 1, 1, facecolor=rgb, edgecolor="white", linewidth=1))
        ax.text(
            index + 0.5,
            0.5,
            f"{colour.name}\n{colour.hex}",
            ha="center",
            va="center",
            fontsize=8,
            color=_text_colour(rgb),
        )
    ax.set(xlim=(0, n), ylim=(0, 1), title=f"{result.palette.name} — {condition.label}")
    ax.axis("off")
    return fig


def cvd_overview(result: AnalysisResult) -> plt.Figure:
    conditions = [
        _condition(result, key)
        for key in ("normal", "protan100", "deutan100", "tritan100", "grayscale")
    ]
    n = len(result.colours)
    fig, ax = plt.subplots(figsize=(max(7, n), 4.2))
    for row, condition in enumerate(conditions):
        for column, rgb in enumerate(condition.srgb):
            ax.add_patch(
                Rectangle((column, row), 1, 1, facecolor=rgb, edgecolor="white", linewidth=1)
            )
    ax.set_xlim(0, n)
    ax.set_ylim(len(conditions), 0)
    ax.set_aspect("equal")
    ax.set_xticks(
        np.arange(n) + 0.5, [c.name for c in result.colours], rotation=35, ha="left", fontsize=8
    )
    ax.xaxis.tick_top()
    ax.set_yticks(np.arange(len(conditions)) + 0.5, [c.label for c in conditions])
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return fig


def severity_progression(result: AnalysisResult, kind: str) -> plt.Figure:
    conditions = [_condition(result, "normal")] + [c for c in result.conditions if c.kind == kind]
    n = len(result.colours)
    fig, ax = plt.subplots(figsize=(max(7, n), max(3.3, len(conditions) * 0.7)))
    for row, condition in enumerate(conditions):
        for column, rgb in enumerate(condition.srgb):
            ax.add_patch(
                Rectangle((column, row), 1, 1, facecolor=rgb, edgecolor="white", linewidth=0.8)
            )
    ax.set(xlim=(0, n), ylim=(len(conditions), 0))
    ax.set_xticks(
        np.arange(n) + 0.5, [c.name for c in result.colours], rotation=35, ha="left", fontsize=8
    )
    ax.xaxis.tick_top()
    ax.set_yticks(np.arange(len(conditions)) + 0.5, [f"{c.severity}%" for c in conditions])
    ax.tick_params(length=0)
    ax.set_title(f"{kind.title()} severity progression", pad=42)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return fig


def heatmap(result: AnalysisResult, condition: ConditionResult, vmax: float) -> plt.Figure:
    n = len(result.colours)
    fig, ax = plt.subplots(figsize=(max(6, n * 0.72), max(5, n * 0.68)))
    data = np.ma.masked_where(np.eye(n, dtype=bool), condition.delta_e)
    image = ax.imshow(data, cmap="viridis", norm=Normalize(0, vmax))
    for i in range(n):
        for j in range(n):
            ax.text(
                j,
                i,
                "—" if i == j else f"{condition.delta_e[i, j]:.1f}",
                ha="center",
                va="center",
                fontsize=7,
                color="white" if i != j and condition.delta_e[i, j] < vmax * 0.55 else "black",
            )
    labels = [c.name for c in result.colours]
    ax.set_xticks(range(n), labels, rotation=40, ha="right", fontsize=8)
    ax.set_yticks(range(n), labels, fontsize=8)
    ax.set_title(f"CIEDE2000 — {condition.label}")
    fig.colorbar(image, ax=ax, label="ΔE00", shrink=0.8)
    return fig


def pair_matrix(result: AnalysisResult, condition: ConditionResult, vmax: float) -> plt.Figure:
    n = len(result.colours)
    fig, ax = plt.subplots(figsize=(max(7, n * 0.85), max(6, n * 0.8)))
    cmap, norm = plt.get_cmap("viridis"), Normalize(0, vmax)
    for row in range(n):
        for column in range(n):
            x, y = column, n - row - 1
            if row > column:
                ax.add_patch(
                    Polygon(
                        [(x, y), (x + 1, y), (x, y + 1)],
                        color=condition.srgb[row],
                        ec="white",
                        lw=0.5,
                    )
                )
                ax.add_patch(
                    Polygon(
                        [(x + 1, y + 1), (x + 1, y), (x, y + 1)],
                        color=condition.srgb[column],
                        ec="white",
                        lw=0.5,
                    )
                )
            elif row < column:
                value = condition.delta_e[row, column]
                ax.add_patch(Rectangle((x, y), 1, 1, color=cmap(norm(value)), ec="white", lw=0.5))
                ax.text(
                    x + 0.5,
                    y + 0.5,
                    f"{value:.1f}",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white" if value < vmax * 0.55 else "black",
                )
            else:
                ax.add_patch(Rectangle((x, y), 1, 1, color=condition.srgb[row], ec="white", lw=0.5))
                ax.text(
                    x + 0.5,
                    y + 0.5,
                    result.colours[row].id.replace("_", "\n"),
                    ha="center",
                    va="center",
                    fontsize=6,
                    color=_text_colour(condition.srgb[row]),
                )
    labels = [c.name for c in result.colours]
    ax.set(xlim=(0, n), ylim=(0, n), aspect="equal")
    ax.set_xticks(np.arange(n) + 0.5, labels, rotation=40, ha="left", fontsize=8)
    ax.xaxis.tick_top()
    ax.set_yticks(np.arange(n) + 0.5, labels[::-1], fontsize=8)
    ax.tick_params(length=0)
    ax.set_title(f"Pair comparison — {condition.label}", pad=48)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return fig


def weakest_pairs(result: AnalysisResult) -> plt.Figure:
    shown = [
        _condition(result, key)
        for key in ("normal", "protan100", "deutan100", "tritan100", "grayscale")
    ]
    count = min(result.config.weakest_count, len(result.colours) * (len(result.colours) - 1) // 2)
    fig, axes = plt.subplots(
        len(shown),
        count,
        figsize=(count * 2.15, len(shown) * 2.25),
        squeeze=False,
        layout="constrained",
    )
    original = _condition(result, "normal")
    id_to_index = {c.id: i for i, c in enumerate(result.colours)}
    for row, condition in enumerate(shown):
        pairs = sorted(
            (p for p in result.pairs if p.condition == condition.key), key=lambda p: p.delta_e_00
        )[:count]
        for column, pair in enumerate(pairs):
            ax = axes[row, column]
            a, b = id_to_index[pair.colour1], id_to_index[pair.colour2]
            ax.add_patch(Rectangle((0, 0.52), 0.5, 0.48, color=original.srgb[a]))
            ax.add_patch(Rectangle((0.5, 0.52), 0.5, 0.48, color=original.srgb[b]))
            ax.add_patch(Rectangle((0, 0), 0.5, 0.48, color=condition.srgb[a]))
            ax.add_patch(Rectangle((0.5, 0), 0.5, 0.48, color=condition.srgb[b]))
            ax.axhline(0.5, color="white", linewidth=1)
            ax.set_title(
                f"{result.colours[a].name} / {result.colours[b].name}\nΔE00 {pair.delta_e_00:.1f}",
                fontsize=7,
            )
            if column == 0:
                ax.text(0.02, 0.76, "Original", transform=ax.transAxes, fontsize=6, va="center")
                ax.text(0.02, 0.24, "Simulated", transform=ax.transAxes, fontsize=6, va="center")
            ax.axis("off")
        axes[row, 0].text(
            -0.08,
            0.5,
            condition.label,
            transform=axes[row, 0].transAxes,
            rotation=90,
            ha="right",
            va="center",
            fontsize=8,
        )
    fig.suptitle("Weakest simulated pairs")
    return fig


def severity_curve(result: AnalysisResult) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for kind, style in (("protan", "-"), ("deutan", "--")):
        points = [point for point in result.curves if point.kind == kind]
        ax.plot(
            [p.severity for p in points],
            [p.minimum for p in points],
            style,
            label=f"{kind.title()} minimum",
            linewidth=2,
        )
        ax.plot(
            [p.severity for p in points],
            [p.mean for p in points],
            style,
            label=f"{kind.title()} mean",
            alpha=0.45,
        )
    ax.set(xlabel="Simulated severity (%)", ylabel="Pairwise ΔE00", xlim=(0, 100))
    ax.grid(True, color="0.9", linewidth=0.8)
    ax.legend(frameon=False, ncol=2, fontsize=8)
    ax.set_title("Pairwise distance versus simulated CVD severity")
    return fig


def write_figures(
    result: AnalysisResult,
    output: Path,
    formats: tuple[str, ...] = ("svg", "pdf", "png"),
    dpi: int = 300,
) -> None:
    """Generate all standard single-palette figures."""
    directory = output / "figures"
    directory.mkdir(parents=True, exist_ok=True)
    major = [
        _condition(result, key)
        for key in ("normal", "protan100", "deutan100", "tritan100", "grayscale")
    ]
    vmax = max(float(c.delta_e.max()) for c in major)
    for condition in major:
        save_figure(
            palette_strip(result, condition), directory, f"palette_{condition.key}", formats, dpi
        )
    save_figure(cvd_overview(result), directory, "cvd_overview", formats, dpi)
    for kind in ("protan", "deutan"):
        save_figure(severity_progression(result, kind), directory, f"severity_{kind}", formats, dpi)
    for condition in major[:-1]:
        save_figure(
            heatmap(result, condition, vmax),
            directory,
            f"heatmap_{condition.key}",
            formats,
            dpi,
        )
        save_figure(
            pair_matrix(result, condition, vmax), directory, f"pairs_{condition.key}", formats, dpi
        )
    save_figure(weakest_pairs(result), directory, "weakest_pairs", formats, dpi)
    save_figure(severity_curve(result), directory, "minimum_distance_severity", formats, dpi)
