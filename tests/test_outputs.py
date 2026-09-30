import json

from palettebench import analyse_palette, load_palette
from palettebench.report import write_comparison, write_report


def test_standard_outputs(tmp_path):
    palette = load_palette("palettes/okabe-ito.yaml")
    output = write_report(analyse_palette(palette), tmp_path / "report", formats=("svg",))
    expected = [
        "report.md",
        "metadata.json",
        "data/pairwise.csv",
        "data/pairwise.json",
        "tables/summary.tex",
        "figures/pairs_normal.svg",
        "figures/weakest_pairs.svg",
    ]
    for relative in expected:
        assert (output / relative).is_file()
    assert len(json.loads((output / "metadata.json").read_text())["input_sha256"]) == 64


def test_comparison_outputs(tmp_path):
    palette = load_palette("palettes/okabe-ito.yaml")
    output = write_comparison([palette, palette], tmp_path / "comparison", formats=("svg",))
    assert (output / "data/comparison.csv").is_file()
    assert (output / "figures/minimum_distance_comparison.svg").is_file()
