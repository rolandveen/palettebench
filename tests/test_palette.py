from importlib.resources import files
from pathlib import Path

import pytest

from palettebench.palette import PaletteError, load_palette


def test_loads_baseline_in_order():
    palette = load_palette("palettes/okabe-ito.yaml")
    assert [colour.id for colour in palette.colours][:3] == ["orange", "sky_blue", "bluish_green"]
    assert palette.colours[-1].hex == "#000000"


def test_packaged_baseline_matches_repository_copy():
    packaged = files("palettebench.data").joinpath("okabe-ito.yaml").read_text(encoding="utf-8")
    assert packaged.strip() == Path("palettes/okabe-ito.yaml").read_text(encoding="utf-8").strip()


@pytest.mark.parametrize(
    "body",
    [
        "name: x\ncolors: [{id: a, name: A, hex: '#000000'}]\n",
        "name: x\ncolors: [{id: a, name: A, hex: '#000000'}, {id: a, name: B, hex: '#FFFFFF'}]\n",
        "name: x\ncolors: [{id: a, name: A, hex: red}, {id: b, name: B, hex: '#FFFFFF'}]\n",
        "name: x\ncolors: [{id: a, name: A, hex: '#000000'}, {id: b, name: B, hex: '#000000'}]\n",
    ],
)
def test_invalid_palettes(tmp_path: Path, body: str):
    path = tmp_path / "invalid.yaml"
    path.write_text(body)
    with pytest.raises(PaletteError):
        load_palette(path)


def test_explicit_duplicate_permission(tmp_path: Path):
    path = tmp_path / "duplicates.yaml"
    path.write_text(
        "name: x\nallow_duplicate_colours: true\n"
        "colors: [{id: a, name: A, hex: '#000000'}, {id: b, name: B, hex: '#000000'}]\n"
    )
    assert len(load_palette(path).colours) == 2
