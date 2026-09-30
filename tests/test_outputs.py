import json
from pathlib import Path

from palettebench import analyse_palette, load_palette
from palettebench.analysis import AnalysisConfig
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
        "inputs/01-okabe-ito.yaml",
        "data/group_summary.csv",
    ]
    for relative in expected:
        assert (output / relative).is_file()
    metadata = json.loads((output / "metadata.json").read_text())
    assert len(metadata["input_sha256"]) == 64
    assert metadata["input_palette"] == "okabe-ito.yaml"
    assert not Path(metadata["input_palette"]).is_absolute()


def test_comparison_outputs(tmp_path):
    palette = load_palette("palettes/okabe-ito.yaml")
    output = write_comparison([palette, palette], tmp_path / "comparison", formats=("svg",))
    assert (output / "data/comparison.csv").is_file()
    assert (output / "data/comparison.json").is_file()
    assert (output / "figures/minimum_distance_comparison.svg").is_file()
    assert (output / "tables/comparison.md").is_file()
    assert (output / "tables/comparison.tex").is_file()
    metadata = json.loads((output / "metadata.json").read_text())
    assert metadata["baseline"] == "Okabe-Ito"
    assert len(metadata["inputs"]) == 2


def test_custom_severity_retains_standard_endpoints(tmp_path):
    palette = load_palette("palettes/okabe-ito.yaml")
    result = analyse_palette(palette, AnalysisConfig(severities=(20, 40)))
    assert {condition.key for condition in result.conditions} >= {"protan100", "deutan100"}
    write_report(result, tmp_path / "severity", formats=("svg",))


def test_single_format_report_has_valid_links(tmp_path):
    palette = load_palette("palettes/okabe-ito.yaml")
    output = write_report(analyse_palette(palette), tmp_path / "pdf", formats=("pdf",))
    report = (output / "report.md").read_text()
    assert "figures/palette_normal.pdf" in report
    assert "figures/palette_normal.svg" not in report
    assert (output / "figures/palette_normal.pdf").is_file()
    assert not (output / "figures/palette_normal.svg").exists()


def test_single_format_comparison_has_valid_links(tmp_path):
    palette = load_palette("palettes/okabe-ito.yaml")
    output = write_comparison([palette, palette], tmp_path / "pdf-compare", formats=("pdf",))
    report = (output / "report.md").read_text()
    assert "figures/palette_comparison.pdf" in report
    assert "figures/palette_comparison.svg" not in report
    assert not (output / "figures/palette_comparison.svg").exists()


def test_grouped_palette_is_surfaced_in_report_and_data(tmp_path):
    source = tmp_path / "grouped.yaml"
    source.write_text(
        "name: Grouped\ncolors:\n"
        "  - {id: blue, name: Blue, hex: '#0072B2', group: blue}\n"
        "  - {id: sky, name: Sky, hex: '#56B4E9', group: blue}\n"
        "  - {id: orange, name: Orange, hex: '#E69F00', group: warm}\n"
    )
    output = write_report(analyse_palette(load_palette(source)), tmp_path / "grouped")
    assert "## Grouped-palette analysis" in (output / "report.md").read_text()
    group_data = (output / "data/group_summary.csv").read_text()
    assert ",within," in group_data
    assert ",between," in group_data
    assert (output / "tables/groups.md").is_file()
    assert (output / "tables/groups.tex").is_file()


def test_scientific_data_and_svg_are_deterministic(tmp_path):
    result = analyse_palette(load_palette("palettes/okabe-ito.yaml"))
    first = write_report(result, tmp_path / "first", formats=("svg",))
    second = write_report(result, tmp_path / "second", formats=("svg",))
    assert (first / "data/pairwise.csv").read_bytes() == (second / "data/pairwise.csv").read_bytes()
    assert (first / "figures/palette_normal.svg").read_bytes() == (
        second / "figures/palette_normal.svg"
    ).read_bytes()
