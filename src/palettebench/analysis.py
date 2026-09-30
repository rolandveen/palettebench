"""Pure analysis pipeline for palette metrics."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import combinations

import colour
import numpy as np
from numpy.typing import NDArray

from .colour import contrast_ratio, grayscale_srgb, hex_to_srgb, relative_luminance, srgb_to_lab
from .cvd import simulate_cvd
from .palette import Palette

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class AnalysisConfig:
    severities: tuple[int, ...] = (20, 40, 60, 80, 100)
    thresholds: tuple[float, ...] = (5.0, 10.0, 15.0, 20.0)
    curve_step: int = 5
    weakest_count: int = 5

    def __post_init__(self) -> None:
        if any(not 0 <= value <= 100 for value in self.severities):
            raise ValueError("Severities must be between 0 and 100")
        if self.curve_step < 1 or self.curve_step > 100:
            raise ValueError("curve_step must be between 1 and 100")


@dataclass(frozen=True)
class ConditionResult:
    key: str
    kind: str
    severity: int
    label: str
    srgb: FloatArray
    lab: FloatArray
    delta_e: FloatArray
    delta_l: FloatArray


@dataclass(frozen=True)
class PairResult:
    condition: str
    kind: str
    severity: int
    colour1: str
    colour2: str
    group1: str | None
    group2: str | None
    relationship: str
    delta_e_00: float
    delta_l: float


@dataclass(frozen=True)
class SummaryResult:
    condition: str
    kind: str
    severity: int
    minimum: float
    minimum_pair: tuple[str, str]
    maximum: float
    mean: float
    median: float
    std: float
    q10: float
    below: dict[float, int]
    pair_count: int
    minimum_within_group: float | None
    minimum_between_group: float | None


@dataclass(frozen=True)
class ColourResult:
    id: str
    name: str
    hex: str
    group: str | None
    srgb: tuple[float, float, float]
    lab: tuple[float, float, float]
    chroma: float
    relative_luminance: float
    contrast_white: float
    contrast_black: float


@dataclass(frozen=True)
class CurvePoint:
    kind: str
    severity: int
    minimum: float
    mean: float
    median: float
    minimum_pair: tuple[str, str]


@dataclass(frozen=True)
class AnalysisResult:
    palette: Palette
    config: AnalysisConfig
    colours: tuple[ColourResult, ...]
    conditions: tuple[ConditionResult, ...]
    pairs: tuple[PairResult, ...]
    summaries: tuple[SummaryResult, ...]
    curves: tuple[CurvePoint, ...]


def _pairwise(lab: FloatArray) -> tuple[FloatArray, FloatArray]:
    n = len(lab)
    delta_e = np.zeros((n, n), dtype=float)
    for i, j in combinations(range(n), 2):
        value = float(colour.delta_E(lab[i], lab[j], method="CIE 2000"))
        delta_e[i, j] = delta_e[j, i] = value
    delta_l = np.abs(lab[:, None, 0] - lab[None, :, 0])
    return delta_e, delta_l


def _condition(key: str, kind: str, severity: int, label: str, rgb: FloatArray) -> ConditionResult:
    lab = srgb_to_lab(rgb)
    delta_e, delta_l = _pairwise(lab)
    return ConditionResult(key, kind, severity, label, rgb, lab, delta_e, delta_l)


def _iter_pairs(palette: Palette, condition: ConditionResult) -> Iterable[PairResult]:
    for i, j in combinations(range(len(palette.colours)), 2):
        a, b = palette.colours[i], palette.colours[j]
        relationship = "ungrouped"
        if a.group is not None and b.group is not None:
            relationship = "within" if a.group == b.group else "between"
        yield PairResult(
            condition.key,
            condition.kind,
            condition.severity,
            a.id,
            b.id,
            a.group,
            b.group,
            relationship,
            float(condition.delta_e[i, j]),
            float(condition.delta_l[i, j]),
        )


def _summarise(
    condition: ConditionResult, pairs: tuple[PairResult, ...], thresholds: tuple[float, ...]
) -> SummaryResult:
    values = np.array([pair.delta_e_00 for pair in pairs], dtype=float)
    weakest = pairs[int(np.argmin(values))]
    within = [pair.delta_e_00 for pair in pairs if pair.relationship == "within"]
    between = [pair.delta_e_00 for pair in pairs if pair.relationship == "between"]
    return SummaryResult(
        condition.key,
        condition.kind,
        condition.severity,
        float(values.min()),
        (weakest.colour1, weakest.colour2),
        float(values.max()),
        float(values.mean()),
        float(np.median(values)),
        float(values.std(ddof=0)),
        float(np.percentile(values, 10)),
        {threshold: int(np.count_nonzero(values < threshold)) for threshold in thresholds},
        len(values),
        min(within) if within else None,
        min(between) if between else None,
    )


def analyse_palette(palette: Palette, config: AnalysisConfig | None = None) -> AnalysisResult:
    """Run deterministic colour, CVD, grayscale, pairwise, and severity analyses."""
    config = config or AnalysisConfig()
    rgb = np.stack([hex_to_srgb(colour.hex) for colour in palette.colours])
    lab = srgb_to_lab(rgb)
    luminance = relative_luminance(rgb)
    colours = tuple(
        ColourResult(
            entry.id,
            entry.name,
            entry.hex,
            entry.group,
            tuple(float(x) for x in rgb[index]),
            tuple(float(x) for x in lab[index]),
            float(np.hypot(lab[index, 1], lab[index, 2])),
            float(luminance[index]),
            float(contrast_ratio(luminance[index], 1.0)),
            float(contrast_ratio(luminance[index], 0.0)),
        )
        for index, entry in enumerate(palette.colours)
    )

    conditions = [_condition("normal", "normal", 0, "Normal", rgb)]
    for kind in ("protan", "deutan"):
        for severity in config.severities:
            conditions.append(
                _condition(
                    f"{kind}{severity}",
                    kind,
                    severity,
                    f"{kind.title()} {severity}%",
                    simulate_cvd(rgb, kind, severity),
                )
            )
    conditions.append(
        _condition("tritan100", "tritan", 100, "Tritan 100%", simulate_cvd(rgb, "tritan", 100))
    )
    conditions.append(_condition("grayscale", "grayscale", 0, "Grayscale", grayscale_srgb(rgb)))

    all_pairs: list[PairResult] = []
    summaries: list[SummaryResult] = []
    for condition in conditions:
        condition_pairs = tuple(_iter_pairs(palette, condition))
        all_pairs.extend(condition_pairs)
        summaries.append(_summarise(condition, condition_pairs, config.thresholds))

    curves: list[CurvePoint] = []
    severities = list(range(0, 101, config.curve_step))
    if severities[-1] != 100:
        severities.append(100)
    for kind in ("protan", "deutan"):
        for severity in severities:
            curve_condition = _condition(
                "curve", kind, severity, "", simulate_cvd(rgb, kind, severity)
            )
            curve_pairs = tuple(_iter_pairs(palette, curve_condition))
            summary = _summarise(curve_condition, curve_pairs, ())
            curves.append(
                CurvePoint(
                    kind,
                    severity,
                    summary.minimum,
                    summary.mean,
                    summary.median,
                    summary.minimum_pair,
                )
            )
    return AnalysisResult(
        palette,
        config,
        colours,
        tuple(conditions),
        tuple(all_pairs),
        tuple(summaries),
        tuple(curves),
    )
