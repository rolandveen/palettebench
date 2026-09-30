from pathlib import Path

import pytest

from palettebench.cli import main


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
