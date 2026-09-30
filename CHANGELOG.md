# Changelog

All notable changes to PaletteBench will be documented here. The project follows semantic versioning.

## Unreleased

## 0.1.0 - 2026-09-30

Initial public release.

### Added

- YAML-defined categorical palettes with optional groups.
- Normal, simulated protan/deutan/tritan, and grayscale analysis.
- CIEDE2000, lightness, luminance, chroma, contrast, and grouped-pair measurements.
- Publication figures, Markdown/LaTeX tables, CSV/JSON data, provenance metadata, and self-contained input copies.
- Baseline-relative multi-palette comparison reports with distribution summaries, descriptive threshold changes, matched-pair diagnostics, coverage reporting, and an automatically supplied Okabe–Ito baseline.
- Command-line, Conda, pip, and Python module workflows.
- A complete generated Okabe–Ito audit and documentation of the palette's original design rationale.

### Changed

- Record condition-level and per-colour out-of-gamut clipping provenance.
- Report pair-matching coverage relative to both baseline and candidate palettes.
- Refuse non-empty output directories to prevent stale artifacts from mixed runs.
- Document population standard deviation and the percentile interpolation convention.
- Enforce static type checks and at least 90% statement coverage in continuous integration.
- Expand CIEDE2000 validation to the complete 34-pair Sharma reference dataset.
- Document non-obvious scientific conventions, comparison tolerances, coverage denominators, and figure geometry directly in the implementation.

### Fixed

- Only label genuinely positive or negative matched-pair changes as increases or decreases.
- Require `allow_duplicate_colours` to be a YAML boolean and validate analysis/render settings.
