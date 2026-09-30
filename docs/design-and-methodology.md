# Design and methodology

This document defines PaletteBench's scientific scope, data model, analysis conventions, and output contract. It is intended both for users interpreting an audit and for contributors extending the implementation.

## Purpose and scope

PaletteBench is a reproducible workbench for designing and auditing categorical colour palettes used in scientific figures. Its immediate reference case is the Okabe–Ito palette and derivatives of it, but every analysis is driven by a user-supplied YAML file. No proposed or branded derivative palette is built into the software.

The package is designed to support publication and long-term archiving. A complete audit therefore contains human-readable reports and figures alongside the machine-readable data and provenance needed to regenerate them.

PaletteBench prioritises:

- correct and explicit colour processing;
- deterministic analysis;
- transparent, condition-specific measurements;
- publication-quality vector output;
- a small dependency set built on established colour-science libraries;
- readable typed Python and small, testable functions;
- straightforward addition and comparison of palette variants.

The package deliberately avoids notebooks as its primary implementation, graphical interfaces, framework-style architecture, hidden global state, and bespoke reimplementations of established colour transforms.

Python 3.11 or newer is required. Ordinary analysis never needs network access.

## Palette definition

Palettes use human-editable YAML and preserve input ordering in every output:

```yaml
name: Example palette
description: A short description of the palette and its intended use.
source:
  authors:
    - Example Author
  url: https://example.org/palette
colors:
  - id: blue
    name: Blue
    hex: "#0072B2"
    group: blue_family
  - id: sky_blue
    name: Sky blue
    hex: "#56B4E9"
    group: blue_family
```

Each palette must contain at least two colours. IDs must be unique identifiers, names must be non-empty, and values must be six-digit hexadecimal sRGB. Colour values must also be unique unless the file explicitly sets `allow_duplicate_colours: true`. The optional `group` field describes a visual family or hierarchy without changing the colour itself.

The included [`palettes/okabe-ito.yaml`](../palettes/okabe-ito.yaml) is intended as both a baseline and a copyable example.

## Analysis conditions

The standard audit evaluates:

1. normal colour vision;
2. simulated protan deficiency at 20%, 40%, 60%, 80%, and 100% severity;
3. simulated deutan deficiency at 20%, 40%, 60%, 80%, and 100% severity;
4. simulated tritan deficiency at 100% severity;
5. a grayscale, luminance-preserving rendering.

The simulation function accepts other valid severities, including partial tritan severity. The standard report only emphasises 100% tritan because interpolation of partial tritanomaly has a less direct evidential basis and should be interpreted cautiously.

All such conditions are described as simulations. They are not presented as reproductions of any particular person's vision.

## Colour-processing pipeline

Every colour follows the same explicit pipeline:

```text
six-digit HEX
→ gamma-encoded sRGB in [0, 1]
→ requested CVD simulation, when applicable
→ clipping to displayable sRGB
→ CIE XYZ
→ CIE Lab under the sRGB D65 reference white
→ pairwise perceptual and lightness measurements
```

PaletteBench uses Colorspacious's `sRGB1+CVD` transform, based on Machado, Oliveira, and Fernandes, for colour-vision-deficiency simulation. It uses Colour Science for Python for the sRGB/XYZ/Lab transformation and CIEDE2000 calculation. Transformations are centralised in `colour.py` and `cvd.py` so that assumptions remain independently testable and replaceable.

Display-bound clipping is recorded in generated metadata because out-of-gamut handling affects subsequent measurements. Input RGB channels are normalised to `[0, 1]`; exported RGB columns remain unambiguous about their representation.

Grayscale is derived from WCAG relative luminance and re-encoded to neutral sRGB. This makes grayscale a useful robustness analysis, but not a categorical-palette requirement.

## Measurements

### Pairwise CIEDE2000

CIEDE2000 (ΔE00) is the primary perceptual-distance metric. For an `N`-colour palette, PaletteBench calculates the full symmetric matrix and all `N choose 2` unique pairs under every reported condition.

Each condition records:

- minimum ΔE00 and the pair producing it;
- maximum, mean, median, and population standard deviation;
- the 10th percentile;
- the number and fraction of pairs below configured descriptive thresholds;
- the complete pairwise matrix;
- absolute pairwise L* differences.

The default descriptive thresholds are 5, 10, 15, and 20. They help locate and compare close pairs; none is treated as a universal accessibility criterion. Accessibility conclusions require interpretation in the intended graphical and viewing context.

### Per-colour characteristics

For every colour under normal vision, the audit records:

- hexadecimal and normalised sRGB values;
- CIE L*a*b* values and L*;
- Lab chroma, `sqrt(a*² + b*²)`;
- WCAG relative luminance;
- WCAG contrast ratio against white and black.

### Hierarchical palettes

If colours declare groups, pairwise results identify comparisons as `within`, `between`, or `ungrouped`. Summaries expose minimum within-group and between-group ΔE00 values, while the tidy pairwise output supports fuller distributional analysis.

This addresses the design problem in which related categories should look related while remaining distinguishable. PaletteBench intentionally does not turn that relationship into a universal scalar score.

## Severity analysis

The standard report tables use the configured discrete severities. A separate diagnostic samples protan and deutan severity from 0 to 100, in 5-point steps by default. For each point it records:

- minimum pairwise ΔE00;
- the identity of the minimum pair;
- mean and median pairwise ΔE00.

This reveals non-linear degradation and changes in the weakest pair that a single endpoint can obscure.

## Output contract

A single-palette command creates a self-contained directory:

```text
report/
├── report.md
├── metadata.json
├── data/
│   ├── colours.csv
│   ├── conditions.csv
│   ├── pairwise.csv
│   ├── pairwise.json
│   ├── severity_curves.csv
│   └── summary.csv
├── tables/
│   ├── colours.md
│   ├── colours.tex
│   ├── summary.md
│   ├── summary.tex
│   └── deltae_<condition>.{md,tex}
└── figures/
    └── ...
```

`data/pairwise.csv` is the canonical tidy result. Each row identifies the condition and severity, both colour IDs and groups, their within/between relationship, ΔE00, and absolute ΔL*. This format is suitable for independent analysis without parsing presentation tables.

Markdown tables are intended for reports and repository previews. LaTeX fragments use `booktabs` conventions, escape names, and omit a standalone document wrapper so they can be included directly in manuscripts.

The generated report reads as a compact technical appendix. It contains palette metadata, methodology and assumptions, normal and simulated results, grayscale analysis, weakest pairs, summary statistics, links to complete outputs, and explicit interpretive limits.

## Standard figures

Figures are generated with Matplotlib and restrained scientific styling. SVG and PDF are the primary publication formats; PNG supports repository previews and presentations.

The standard figure set contains:

1. **Palette strips** for normal vision, major 100% simulated CVD conditions, and grayscale. Each swatch includes its name and original hexadecimal value.
2. **CVD overview**, with palette entries in fixed columns and normal, protan, deutan, tritan, and grayscale rows.
3. **Severity progressions** for protan and deutan simulations at the configured report severities.
4. **ΔE00 heatmaps** for normal, protan 100%, deutan 100%, and tritan 100%, using a common scale and visibly distinct diagonals.
5. **Diagonal split pair matrices** for the same four conditions. Lower-triangle cells put the two colours in direct diagonal contact, upper-triangle cells show ΔE00, and diagonal cells identify individual colours.
6. **Weakest-pair overview**, showing the five closest pairs by default across the major conditions.
7. **Minimum-distance severity curves**, with minimum and mean ΔE00 across protan and deutan severity.

The data driving each figure is retained separately. Tests therefore verify numerical and structural inputs rather than relying on fragile pixel-perfect comparisons.

## Comparing palettes

Comparison mode treats the first palette as the baseline:

```bash
palettebench compare \
  palettes/okabe-ito.yaml \
  palettes/variant-a.yaml \
  palettes/variant-b.yaml \
  --output reports/comparison
```

It reports, by palette and condition:

- minimum, mean, and median ΔE00;
- the weakest pair;
- change in minimum ΔE00 relative to the baseline;
- side-by-side normal, simulated CVD, and grayscale strips;
- overlaid minimum-distance-versus-severity curves.

PaletteBench does not combine these into a single accessibility score or an unconditional ranking. Different conditions, category semantics, intended media, and graphical contexts remain visible in the evidence.

## Reproducibility and provenance

Every audit includes `metadata.json` with:

- PaletteBench and Python versions;
- relevant dependency versions;
- the resolved input filename;
- SHA-256 of the exact palette YAML bytes;
- UTC generation timestamp;
- metric thresholds and severity configuration;
- severity-curve sampling;
- named simulation, clipping, colour-space, and metric assumptions.

The input palette remains the authoritative definition. Generated data and presentation artifacts are derived from it without network access.

Determinism is expected for numerical data given the same input, configuration, package versions, and platform. Timestamps and environment-version fields are intentionally provenance-specific.

## Validation strategy

The test suite covers:

- YAML parsing, input ordering, and invalid definitions;
- hexadecimal/sRGB round trips;
- reference black and white Lab and luminance values;
- CIEDE2000 against the Sharma, Wu, and Dalal supplementary test data;
- symmetric ΔE00 matrices and zero diagonals;
- CVD simulation shapes, valid output ranges, and zero-severity behaviour;
- generation of the standard data, table, report, and figure artifacts;
- baseline comparison output.

Graphical tests focus on the data and successful vector rendering rather than platform-sensitive pixel identity.

## Interpretation and limitations

PaletteBench measures properties relevant to accessibility; it does not certify a palette as accessible. In particular:

- simulated CVD is not equivalent to human-subject validation;
- ΔE00 is evidence about modelled perceptual difference, not a universal pass/fail threshold;
- spatial separation, mark size, adjacent colours, and background alter discriminability;
- monitor calibration, ambient light, print reproduction, ageing, visual acuity, and individual vision affect perception;
- grayscale separation is useful evidence but is not mandatory for every categorical palette;
- critical information should use redundant encodings such as labels, shapes, textures, or line styles.

Claims made from an audit should stay proportional to the conditions and measurements actually evaluated.

## Baseline provenance

The bundled baseline uses the canonical eight-colour sequence:

1. orange `#E69F00`;
2. sky blue `#56B4E9`;
3. bluish green `#009E73`;
4. yellow `#F0E442`;
5. blue `#0072B2`;
6. vermillion `#D55E00`;
7. reddish purple `#CC79A7`;
8. black `#000000`.

The palette is attributed to Masataka Okabe and Kei Ito's Color Universal Design work. Bang Wong later presented and popularised it for scientific graphics in *Nature Methods*. It should therefore not be described simply as the “Wong palette.”

## References

- Okabe, M. & Ito, K. *Color Universal Design (CUD): How to make figures and presentations that are friendly to Colorblind people*. <https://jfly.uni-koeln.de/color/>
- Wong, B. (2011). Color blindness. *Nature Methods*, 8, 441. <https://doi.org/10.1038/nmeth.1618>. Author correction: <https://doi.org/10.1038/s41592-023-01974-0>.
- Machado, G. M., Oliveira, M. M. & Fernandes, L. A. F. (2009). A physiologically-based model for simulation of color vision deficiency. *IEEE Transactions on Visualization and Computer Graphics*, 15(6), 1291–1298. <https://doi.org/10.1109/TVCG.2009.113>.
- Sharma, G., Wu, W. & Dalal, E. N. (2005). The CIEDE2000 color-difference formula: Implementation notes, supplementary test data, and mathematical observations. *Color Research & Application*, 30(1), 21–30. <https://doi.org/10.1002/col.20070>.
- Smith, N. (2015). Colorspacious. <https://colorspacious.readthedocs.io/>.
- Mansencal, T. et al. Colour Science for Python. <https://doi.org/10.5281/zenodo.1032029>.

## Licensing

PaletteBench uses the permissive BSD 3-Clause License to support scientific reuse, redistribution, publication, and archiving.

