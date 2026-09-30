from pathlib import Path

import pytest

from palettebench.cli import main


def test_version_command_reports_installed_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out.startswith("palettebench ")


def test_example_command_writes_valid_palette(tmp_path: Path, capsys):
    output = tmp_path / "example.yaml"
    main(["example", "--output", str(output)])
    assert output.is_file()
    assert "name: Okabe-Ito" in output.read_text()
    assert "Wrote example palette" in capsys.readouterr().out


def test_example_command_refuses_to_overwrite(tmp_path: Path):
    output = tmp_path / "existing.yaml"
    output.write_text("keep me")
    with pytest.raises(SystemExit):
        main(["example", "--output", str(output)])
    assert output.read_text() == "keep me"


def test_compare_can_supply_okabe_ito_baseline(tmp_path: Path, capsys):
    variant = tmp_path / "variant.yaml"
    main(["example", "--output", str(variant)])
    output = tmp_path / "comparison"

    main(
        [
            "compare",
            "--okabe-ito-baseline",
            str(variant),
            "--output",
            str(output),
            "--format",
            "svg",
        ]
    )

    assert (output / "report.md").is_file()
    metadata = (output / "metadata.json").read_text()
    assert '"name": "Okabe-Ito"' in metadata
    assert len(list((output / "inputs").glob("*.yaml"))) == 2
    assert f"Wrote report to {output}" in capsys.readouterr().out
