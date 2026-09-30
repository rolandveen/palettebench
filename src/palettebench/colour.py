"""Centralised colour transformations and display characteristics."""

from __future__ import annotations

import colour
import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def hex_to_srgb(value: str) -> FloatArray:
    """Convert #RRGGBB to gamma-encoded sRGB in [0, 1]."""
    return np.array([int(value[i : i + 2], 16) for i in (1, 3, 5)], dtype=float) / 255.0


def srgb_to_hex(rgb: FloatArray) -> str:
    """Convert gamma-encoded sRGB in [0, 1] to canonical #RRGGBB."""
    channels = np.rint(np.clip(rgb, 0.0, 1.0) * 255).astype(int)
    return "#" + "".join(f"{channel:02X}" for channel in channels)


def srgb_to_lab(rgb: FloatArray) -> FloatArray:
    """Convert sRGB to CIE Lab using the sRGB D65 white point."""
    xyz = colour.sRGB_to_XYZ(np.asarray(rgb, dtype=float))
    return np.asarray(colour.XYZ_to_Lab(xyz), dtype=float)


def relative_luminance(rgb: FloatArray) -> FloatArray:
    """WCAG relative luminance for one colour or an (..., 3) array."""
    values = np.asarray(rgb, dtype=float)
    linear = np.where(values <= 0.04045, values / 12.92, ((values + 0.055) / 1.055) ** 2.4)
    return np.asarray(linear @ np.array([0.2126, 0.7152, 0.0722]), dtype=float)


def contrast_ratio(luminance_a: FloatArray | float, luminance_b: float) -> FloatArray:
    """WCAG contrast ratio between luminances."""
    a = np.asarray(luminance_a, dtype=float)
    lighter = np.maximum(a, luminance_b)
    darker = np.minimum(a, luminance_b)
    return np.asarray((lighter + 0.05) / (darker + 0.05), dtype=float)


def grayscale_srgb(rgb: FloatArray) -> FloatArray:
    """Render colours as neutral sRGB values with matched relative luminance."""
    luminance = relative_luminance(rgb)
    encoded = np.where(
        luminance <= 0.0031308,
        12.92 * luminance,
        1.055 * np.power(luminance, 1 / 2.4) - 0.055,
    )
    return np.repeat(np.asarray(encoded)[..., None], 3, axis=-1)
