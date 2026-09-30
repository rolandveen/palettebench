"""Palette data model and YAML validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


class PaletteError(ValueError):
    """Raised when a palette definition is invalid."""


@dataclass(frozen=True)
class ColourEntry:
    id: str
    name: str
    hex: str
    group: str | None = None


@dataclass(frozen=True)
class Palette:
    name: str
    description: str
    colours: tuple[ColourEntry, ...]
    source: dict[str, Any]
    path: Path
    allow_duplicate_colours: bool = False


def load_palette(path: str | Path) -> Palette:
    """Load and validate a palette from YAML while preserving colour order."""
    source_path = Path(path)
    try:
        raw = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise PaletteError(f"Could not read palette {source_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise PaletteError("Palette YAML must contain a mapping at the top level")
    if not isinstance(raw.get("name"), str) or not raw["name"].strip():
        raise PaletteError("Palette 'name' must be a non-empty string")
    rows = raw.get("colors")
    if not isinstance(rows, list) or len(rows) < 2:
        raise PaletteError("Palette must contain at least two colours")

    colours: list[ColourEntry] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise PaletteError(f"Colour {index} must be a mapping")
        identifier, name, value = row.get("id"), row.get("name"), row.get("hex")
        if not isinstance(identifier, str) or not ID_RE.fullmatch(identifier):
            raise PaletteError(f"Colour {index} has an invalid id")
        if not isinstance(name, str) or not name.strip():
            raise PaletteError(f"Colour {identifier!r} has an invalid name")
        if not isinstance(value, str) or not HEX_RE.fullmatch(value):
            raise PaletteError(f"Colour {identifier!r} must use six-digit hexadecimal sRGB")
        group = row.get("group")
        if group is not None and (not isinstance(group, str) or not group.strip()):
            raise PaletteError(f"Colour {identifier!r} has an invalid group")
        colours.append(ColourEntry(identifier, name.strip(), value.upper(), group))

    ids = [colour.id for colour in colours]
    if len(ids) != len(set(ids)):
        raise PaletteError("Colour IDs must be unique")
    allow_duplicates = raw.get("allow_duplicate_colours", False)
    if not isinstance(allow_duplicates, bool):
        raise PaletteError("Palette 'allow_duplicate_colours' must be a boolean")
    values = [colour.hex for colour in colours]
    if not allow_duplicates and len(values) != len(set(values)):
        raise PaletteError("Colour values must be unique unless allow_duplicate_colours is true")
    source = raw.get("source", {})
    if not isinstance(source, dict):
        raise PaletteError("Palette 'source' must be a mapping")
    return Palette(
        name=raw["name"].strip(),
        description=str(raw.get("description", "")).strip(),
        colours=tuple(colours),
        source=source,
        path=source_path.resolve(),
        allow_duplicate_colours=allow_duplicates,
    )
