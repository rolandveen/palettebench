"""Scientific colour-palette auditing."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("palettebench")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0+unknown"

from .analysis import AnalysisConfig, AnalysisResult, analyse_palette
from .palette import ColourEntry, Palette, load_palette

__all__ = [
    "AnalysisConfig",
    "AnalysisResult",
    "ColourEntry",
    "Palette",
    "analyse_palette",
    "load_palette",
]
