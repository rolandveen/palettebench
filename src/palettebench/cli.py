"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from importlib.resources import as_file, files
from pathlib import Path


def _formats(value: str) -> tuple[str, ...]:
    result = tuple(part.strip().lower() for part in value.split(",") if part.strip())
    unknown = set(result) - {"svg", "pdf", "png"}
    if not result or unknown:
        raise argparse.ArgumentTypeError(
            f"Formats must be svg, pdf, and/or png; got {sorted(unknown)}"
        )
    return result


def _severities(value: str) -> tuple[int, ...]:
    try:
        result = tuple(dict.fromkeys(int(part.strip()) for part in value.split(",")))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Severities must be comma-separated integers") from exc
    if not result or any(item < 0 or item > 100 for item in result):
        raise argparse.ArgumentTypeError("Severities must be between 0 and 100")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="palettebench", description="Audit scientific categorical colour palettes"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit", help="audit one palette")
    audit.add_argument("palette", type=Path)
    audit.add_argument("--output", "-o", type=Path)
    example = subparsers.add_parser("example", help="write the bundled Okabe–Ito YAML example")
    example.add_argument("--output", "-o", type=Path, default=Path("okabe-ito.yaml"))
    compare = subparsers.add_parser("compare", help="compare palettes, using the first as baseline")
    compare.add_argument("palettes", nargs="+", type=Path)
    compare.add_argument(
        "--okabe-ito-baseline",
        action="store_true",
        help="prepend the bundled Okabe–Ito palette as the baseline",
    )
    compare.add_argument("--output", "-o", type=Path, default=Path("reports/comparison"))
    for target in (audit, compare):
        target.add_argument(
            "--format", type=_formats, default=("svg", "pdf", "png"), dest="formats"
        )
        target.add_argument(
            "--severity", type=_severities, default=(20, 40, 60, 80, 100), dest="severities"
        )
        target.add_argument("--dpi", type=int, default=300)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] not in {"audit", "compare", "example", "-h", "--help"}:
        arguments.insert(0, "audit")
    args = parser.parse_args(arguments)
    if args.command == "example":
        if args.output.exists():
            parser.error(f"refusing to overwrite existing file: {args.output}")
        resource = files("palettebench.data").joinpath("okabe-ito.yaml")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(resource.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Wrote example palette to {args.output}")
        return
    from .analysis import AnalysisConfig, analyse_palette
    from .palette import PaletteError, load_palette
    from .report import write_comparison, write_report

    try:
        config = AnalysisConfig(severities=args.severities)
        if args.command == "compare":
            if not args.okabe_ito_baseline and len(args.palettes) < 2:
                parser.error("compare requires at least two palette files")
            palettes = [load_palette(path) for path in args.palettes]
            if args.okabe_ito_baseline:
                resource = files("palettebench.data").joinpath("okabe-ito.yaml")
                with as_file(resource) as baseline_path:
                    palettes.insert(0, load_palette(baseline_path))
                    destination = write_comparison(
                        palettes, args.output, config, args.formats, args.dpi
                    )
            else:
                destination = write_comparison(
                    palettes, args.output, config, args.formats, args.dpi
                )
        else:
            palette = load_palette(args.palette)
            destination = args.output or Path("reports") / palette.path.stem
            write_report(analyse_palette(palette, config), destination, args.formats, args.dpi)
    except (PaletteError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Wrote report to {destination}")
