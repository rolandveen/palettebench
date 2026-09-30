"""Colour-vision-deficiency simulation using Colorspacious/Machado matrices."""

from __future__ import annotations

import numpy as np
from colorspacious import cspace_convert
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]

CVD_TYPES = {"protan": "protanomaly", "deutan": "deuteranomaly", "tritan": "tritanomaly"}


def simulate_cvd(rgb: FloatArray, deficiency: str, severity: float) -> FloatArray:
    """Simulate CVD and clip display-bound gamma-encoded sRGB to [0, 1]."""
    if deficiency not in CVD_TYPES:
        raise ValueError(f"Unknown CVD type: {deficiency}")
    if not 0 <= severity <= 100:
        raise ValueError("CVD severity must be between 0 and 100")
    spec = {"name": "sRGB1+CVD", "cvd_type": CVD_TYPES[deficiency], "severity": float(severity)}
    return np.clip(np.asarray(cspace_convert(rgb, spec, "sRGB1"), dtype=float), 0.0, 1.0)
