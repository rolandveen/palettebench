import csv
import json
from pathlib import Path

import pytest

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
    assert any(row["clipped_colour_count"] for row in metadata["gamut_clipping"])
    assert (output / "data/gamut_clipping.csv").is_file()
    report = (output / "report.md").read_text()
    generated_svgs = sorted((output / "figures").glob("*.svg"))
    assert len(generated_svgs) == 18
    assert all(f"figures/{figure.name}" in report for figure in generated_svgs)


def test_comparison_outputs(tmp_path):
    palette = load_palette("palettes/okabe-ito.yaml")
    output = write_comparison([palette, palette], tmp_path / "comparison", formats=("svg",))
    assert (output / "data/comparison.csv").is_file()
    assert (output / "data/comparison.json").is_file()
    assert (output / "data/pairwise_changes.csv").is_file()
    assert (output / "data/pairwise_changes.json").is_file()
    assert (output / "data/pairwise_coverage.csv").is_file()
    assert (output / "data/pairwise_coverage.json").is_file()
    assert (output / "figures/minimum_distance_comparison.svg").is_file()
    assert (output / "figures/minimum_change_comparison.svg").is_file()
    assert (output / "tables/comparison.md").is_file()
    assert (output / "tables/comparison.tex").is_file()
    assert (output / "tables/pairwise_changes.md").is_file()
    assert (output / "tables/pairwise_changes.tex").is_file()
    metadata = json.loads((output / "metadata.json").read_text())
    assert metadata["baseline"] == "Okabe-Ito"
    assert len(metadata["inputs"]) == 2


def test_comparison_reports_pairwise_regressions(tmp_path):
    baseline = load_palette("palettes/okabe-ito.yaml")
    variant_path = tmp_path / "variant.yaml"
    variant_path.write_text(
        Path("palettes/okabe-ito.yaml")
        .read_text()
        .replace("name: Okabe-Ito", "name: Near-yellow variant")
        .replace("#E69F00", "#F0D800")
    )
    output = write_comparison(
        [baseline, load_palette(variant_path)], tmp_path / "variant-comparison", formats=("svg",)
    )
    with (output / "data/pairwise_changes.csv").open(newline="") as handle:
        changes = list(csv.DictReader(handle))
    assert changes
    assert any(float(row["change_from_baseline"]) < 0 for row in changes)
    assert {row["direction"] for row in changes} <= {"increased", "decreased", "unchanged"}

    with (output / "data/comparison.csv").open(newline="") as handle:
        summaries = list(csv.DictReader(handle))
    variant_normal = next(
        row
        for row in summaries
        if row["palette"] == "Near-yellow variant" and row["condition"] == "normal"
    )
    assert float(variant_normal["minimum_change_from_baseline"]) < 0
    assert "below_10_fraction_change_from_baseline" in variant_normal

    diagnostics = (output / "tables/pairwise_changes.md").read_text()
    increase_lines = [line for line in diagnostics.splitlines() if "Largest increase" in line]
    decrease_lines = [line for line in diagnostics.splitlines() if "Largest decrease" in line]
    assert all(float(line.split("|")[-2]) > 0 for line in increase_lines)
    assert all(float(line.split("|")[-2]) < 0 for line in decrease_lines)


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


def test_report_refuses_non_empty_output_directory(tmp_path):
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_text("keep")
    result = analyse_palette(load_palette("palettes/okabe-ito.yaml"))
    with pytest.raises(ValueError, match="non-empty"):
        write_report(result, output, formats=("svg",))
    assert marker.read_text() == "keep"


def test_comparison_coverage_is_two_sided_for_added_colour(tmp_path):
    baseline = load_palette("palettes/okabe-ito.yaml")
    candidate_path = tmp_path / "expanded.yaml"
    candidate_path.write_text(
        Path("palettes/okabe-ito.yaml").read_text().replace("name: Okabe-Ito", "name: Expanded")
        + "  - {id: white, name: White, hex: '#FFFFFF'}\n"
    )
    output = write_comparison(
        [baseline, load_palette(candidate_path)], tmp_path / "expanded", formats=("svg",)
    )
    with (output / "data/pairwise_coverage.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    normal = next(row for row in rows if row["condition"] == "normal")
    assert float(normal["baseline_coverage_fraction"]) == 1.0
    assert float(normal["candidate_coverage_fraction"]) < 1.0
    assert int(normal["candidate_only_pair_count"]) == 8


def test_render_options_are_validated(tmp_path):
    result = analyse_palette(load_palette("palettes/okabe-ito.yaml"))
    with pytest.raises(ValueError, match="Formats"):
        write_report(result, tmp_path / "bad-format", formats=("svg", "svg"))
    with pytest.raises(ValueError, match="DPI"):
        write_report(result, tmp_path / "bad-dpi", formats=("png",), dpi=0)
