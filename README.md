# PaletteBench

PaletteBench is a small Python package for reproducible perceptual and simulated colour-vision-deficiency audits of categorical scientific palettes. A YAML palette produces publication-ready SVG/PDF figures, PNG previews, Markdown and LaTeX tables, tidy CSV/JSON data, and a concise technical report.

It reports transparent, condition-specific measurements rather than an opaque accessibility score. Simulations and colour differences support an assessment; they do not replace evaluation with people who have colour-vision deficiencies.

Start with the [User manual](docs/manual.md). The complete scientific assumptions, schema, metric definitions, output contract, figure catalogue, comparison behaviour, validation strategy, and interpretation guidance are documented in [Design and methodology](docs/design-and-methodology.md). The [Okabe–Ito rationale](docs/okabe-ito-rationale.md) separates the original authors' design principles from the measurements PaletteBench can make.

![Example PaletteBench palette strip](docs/example-palette.svg)

A [complete generated Okabe–Ito audit](examples/okabe-ito-report/report.md) is included for inspection without installing the package.

## Installation

Python 3.11 or newer is required.

With Conda:

```bash
git clone https://github.com/rolandveen/palettebench.git
cd palettebench
conda env create -f environment.yml
conda activate palettebench
```

With a Python virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

Development dependencies are available through `python -m pip install -e ".[dev]"` or `requirements-dev.txt`.

An installed package can write a copy of its bundled baseline without a repository checkout:

```bash
palettebench example --output okabe-ito.yaml
```

## Single-palette audit

```bash
palettebench palettes/okabe-ito.yaml
# Equivalent:
python -m palettebench palettes/okabe-ito.yaml
```

The default output is `reports/okabe-ito/`. Choose a destination or output formats with:

```bash
palettebench palettes/okabe-ito.yaml \
  --output reports/my-audit \
  --format svg,pdf,png \
  --severity 20,40,60,80,100 \
  --dpi 300
```

The generated `report.md` links every key figure and table. `data/pairwise.csv` is the canonical long-form result, and `metadata.json` records the input SHA-256, versions, timestamp, and analysis configuration.

## Create and compare a variant

```bash
cp palettes/okabe-ito.yaml palettes/my-palette.yaml
# Edit the copied YAML, then:
palettebench compare palettes/okabe-ito.yaml palettes/my-palette.yaml \
  --output reports/comparison
```

When PaletteBench is installed without a repository checkout, use the bundled baseline directly:

```bash
palettebench compare --okabe-ito-baseline my-palette.yaml \
  --output reports/comparison
```

The first palette is the baseline. Comparisons preserve minimum, mean, and median ΔE00, weakest pairs, baseline changes, strips, and severity curves; they do not collapse these into one score.

Colours may optionally declare a `group`. PaletteBench labels each pair as within-group, between-group, or ungrouped and reports group minima without inventing a universal hierarchy score.

```yaml
name: Example
colors:
  - {id: blue, name: Blue, hex: "#0072B2", group: blue_family}
  - {id: sky_blue, name: Sky blue, hex: "#56B4E9", group: blue_family}
```

IDs and colour values must be unique, values must be six-digit sRGB hex codes, and palettes need at least two colours. Duplicate values are accepted only with top-level `allow_duplicate_colours: true`.

## Methods

PaletteBench treats YAML values as gamma-encoded sRGB. It uses Colorspacious's `sRGB1+CVD` transform (the Machado, Oliveira & Fernandes model), clips the simulated result to displayable sRGB, converts it via CIE XYZ to CIE Lab under the sRGB D65 white point with Colour Science for Python, then calculates CIEDE2000 (ΔE00). Grayscale rendering preserves WCAG relative luminance.

The standard report includes normal vision; protan and deutan simulations at 20–100%; tritan at 100%; and grayscale. Partial tritan severity remains available through the simulation function but is deliberately not emphasised. Threshold counts are descriptive only: no ΔE00 cutoff universally establishes accessibility.

Run tests with `pytest`.

## References

- Okabe, M. & Ito, K. *Color Universal Design (CUD): How to make figures and presentations that are friendly to Colorblind people*. https://jfly.uni-koeln.de/color/
- Wong, B. (2011). Color blindness. *Nature Methods*, 8, 441. https://doi.org/10.1038/nmeth.1618. See the 2023 author correction: https://doi.org/10.1038/s41592-023-01974-0. Wong presented and popularised the palette; PaletteBench retains the Okabe–Ito attribution.
- Machado, G. M., Oliveira, M. M. & Fernandes, L. A. F. (2009). A physiologically-based model for simulation of color vision deficiency. *IEEE TVCG*, 15(6), 1291–1298. https://doi.org/10.1109/TVCG.2009.113
- Sharma, G., Wu, W. & Dalal, E. N. (2005). The CIEDE2000 color-difference formula. *Color Research & Application*, 30(1), 21–30. https://doi.org/10.1002/col.20070
- Smith, N. (2015). Colorspacious. https://colorspacious.readthedocs.io/
- Mansencal, T. et al. Colour Science for Python. https://doi.org/10.5281/zenodo.1032029

## Scientific limitations

Simulation does not reproduce any particular individual's perception. Monitor calibration, viewing environment, visual acuity, ageing, print reproduction, mark size, and surrounding colours affect discriminability. Use redundant encodings—shape, line style, labels, or texture—when colour carries critical meaning.

PaletteBench is available under the BSD 3-Clause License.
