"""Scientific colour-palette auditing."""

from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, Any

try:
    __version__ = version("palettebench")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0+unknown"

if TYPE_CHECKING:
    from .analysis import AnalysisConfig, AnalysisResult
    from .palette import ColourEntry, Palette

__all__ = [
    "AnalysisConfig",
    "AnalysisResult",
    "ColourEntry",
    "Palette",
    "analyse_palette",
    "load_palette",
]


def __getattr__(name: str) -> Any:
    """Load the scientific stack only when a public analysis object is requested."""
    if name in {"AnalysisConfig", "AnalysisResult", "analyse_palette"}:
        from . import analysis

        return getattr(analysis, name)
    if name in {"ColourEntry", "Palette", "load_palette"}:
        from . import palette

        return getattr(palette, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
