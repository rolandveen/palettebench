import hashlib
import json
import re
from pathlib import Path


def test_committed_example_is_complete_and_self_consistent():
    root = Path("examples/okabe-ito-report")
    metadata = json.loads((root / "metadata.json").read_text())
    input_copy = root / metadata["input_copy"]
    assert input_copy.is_file()
    assert hashlib.sha256(input_copy.read_bytes()).hexdigest() == metadata["input_sha256"]

    links = re.findall(r"\]\(([^):]+)\)", (root / "report.md").read_text())
    assert links
    assert all((root / target).is_file() for target in links)

    report = (root / "report.md").read_text()
    generated_svgs = sorted((root / "figures").glob("*.svg"))
    assert len(generated_svgs) == 18
    assert all(f"figures/{figure.name}" in report for figure in generated_svgs)

    for stem in ("palette_normal", "cvd_overview", "pairs_normal", "weakest_pairs"):
        for extension in ("svg", "pdf", "png"):
            assert (root / "figures" / f"{stem}.{extension}").is_file()
