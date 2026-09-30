# PaletteBench 0.1.0

PaletteBench 0.1.0 is the first public release of a reproducible workbench for auditing categorical scientific colour palettes.

## Highlights

- Audit normal, simulated protan/deutan/tritan, and grayscale palette behaviour.
- Measure CIEDE2000 separation, lightness, luminance, chroma, contrast, descriptive thresholds, and grouped-pair behaviour.
- Generate publication-ready SVG, PDF, and PNG figures; Markdown and LaTeX tables; and tidy CSV and JSON data.
- Compare palette variants directly with the bundled Okabe–Ito baseline and identify condition-level and matched-pair improvements or regressions.
- Retain exact input copies, hashes, dependency versions, analysis settings, and full-precision numerical results.
- Inspect a complete generated Okabe–Ito audit without first installing the package.

## Installation

PaletteBench requires Python 3.11 or newer. Installation and first-use instructions are in the [README](../README.md) and [user manual](manual.md).

## Interpretation boundary

PaletteBench reports transparent, condition-specific measurements rather than a universal accessibility score. Simulated colour-vision deficiencies and colour-difference metrics support evaluation, but they do not replace testing with people or account for every display, print, mark-size, and semantic context.
