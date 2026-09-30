# User manual

This manual covers installation, palette creation, single-palette audits, comparisons, outputs, interpretation, and troubleshooting. The deeper scientific rationale is documented in [Design and methodology](design-and-methodology.md).

## 1. Installation

PaletteBench requires Python 3.11 or newer. Conda is recommended for an isolated scientific environment, but an ordinary virtual environment works equally well.

### Conda

From the repository root:

```bash
conda env create -f environment.yml
conda activate palettebench
```

To update an existing environment after dependency changes:

```bash
conda env update -n palettebench -f environment.yml --prune
```

### Python virtual environment and requirements.txt

```bash
python3.11 -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

For development and testing, replace the final two install commands with:

```bash
python -m pip install -e ".[dev]"
# Equivalent: python -m pip install -r requirements-dev.txt
```

Verify the installation:

```bash
palettebench --help
python -c "import palettebench; print(palettebench.__version__)"
```

If PaletteBench was installed from a wheel rather than a repository checkout, write the bundled example to the current directory:

```bash
palettebench example --output okabe-ito.yaml
```

The command refuses to overwrite an existing file.

## 2. First audit

Run the bundled Okabe–Ito baseline:

```bash
palettebench palettes/okabe-ito.yaml
```

The report is written to `reports/okabe-ito/`. Open `report.md` in a Markdown viewer or repository browser. The report directory also contains exact input, data, tables, figures, and provenance.

Equivalent module invocation:

```bash
python -m palettebench palettes/okabe-ito.yaml
```

Choose an output directory:

```bash
palettebench palettes/okabe-ito.yaml --output reports/baseline
```

## 3. Define a palette

Copy the baseline or create a YAML file:

```yaml
name: Example palette
description: Six categorical colours for an example analysis.
source:
  authors:
    - Example Author
  url: https://example.org/palette
colors:
  - id: dark_blue
    name: Dark blue
    hex: "#0072B2"
    group: blue_family
  - id: light_blue
    name: Light blue
    hex: "#56B4E9"
    group: blue_family
  - id: orange
    name: Orange
    hex: "#E69F00"
  - id: vermillion
    name: Vermillion
    hex: "#D55E00"
  - id: green
    name: Bluish green
    hex: "#009E73"
  - id: black
    name: Black
    hex: "#000000"
```

Rules:

- at least two colours;
- unique IDs;
- non-empty names;
- six-digit hexadecimal sRGB values;
- unique colour values unless top-level `allow_duplicate_colours: true` is deliberately set;
- optional `group` values for related colour families.

Input order is preserved in every table and figure.

## 4. Audit options

```text
palettebench PALETTE.yaml [--output DIRECTORY]
                         [--format svg,pdf,png]
                         [--severity 20,40,60,80,100]
                         [--dpi 300]
```

`--format` accepts one or more of `svg`, `pdf`, and `png`. Report links automatically use an available requested format. SVG and PDF are preferable for manuscripts; PNG is convenient for slides and repository previews.

`--severity` controls the discrete protan and deutan progression rows. The standard 100% conditions are always retained because the main comparison figures and matrices require them. The diagnostic curve independently samples 0–100% at five-point increments.

`--dpi` affects raster PNG output only.

Example:

```bash
palettebench palettes/example.yaml \
  --output reports/example \
  --format svg,pdf \
  --severity 25,50,75 \
  --dpi 300
```

## 5. Compare palettes

The first file is the baseline:

```bash
palettebench compare \
  palettes/okabe-ito.yaml \
  palettes/variant-a.yaml \
  palettes/variant-b.yaml \
  --output reports/comparison
```

The comparison report contains condition-level minimum, maximum, mean, median, standard deviation, weakest pair, and minimum-distance change from baseline. It also includes aligned palette strips and severity curves. Full-precision CSV/JSON, Markdown/LaTeX tables, copied inputs, and metadata are retained.

Comparison does not calculate a single accessibility score. Review changes condition by condition and in relation to the palette's category semantics.

## 6. Report contents

Each single-palette directory contains:

```text
report.md                 technical summary and navigation
metadata.json             versions, hashes, configuration, and timestamp
inputs/                   exact copy of the analysed YAML
data/colours.csv          normal-vision colour characteristics
data/conditions.csv       simulated conditions
data/pairwise.csv         canonical tidy pairwise result
data/pairwise.json        JSON representation of pairwise results
data/summary.csv          condition summaries and threshold counts/fractions
data/group_summary.csv    within/between/ungrouped distributions
data/severity_curves.csv  sampled protan/deutan diagnostic curves
tables/                   Markdown and booktabs LaTeX fragments
figures/                  requested publication and preview formats
```

Use `data/pairwise.csv` for independent statistical analysis. It has one row per unique colour pair and condition. Use `metadata.json` to verify the exact input SHA-256, software versions, and configuration.

## 7. Reading the figures

- **Palette strips** show the complete palette in each major condition.
- **CVD overview** keeps colours in fixed columns for rapid comparison.
- **Severity progressions** show discrete simulated protan and deutan changes.
- **Heatmaps** show all pairwise ΔE00 values on a shared scale.
- **Pair matrices** put colours in direct diagonal contact below the diagonal and show numerical ΔE00 above it.
- **Weakest-pair figure** shows original colours above simulated colours for the closest pairs in each condition.
- **Severity curve** shows how the minimum and mean pairwise distance evolve and records the changing weakest pair in CSV.

## 8. Interpreting results

ΔE00 is evidence about modelled perceptual difference, not an accessibility verdict. Counts below 5, 10, 15, and 20 are descriptive and include both counts and fractions. They support comparison and prioritisation without defining a universal threshold.

Simulated CVD is not a substitute for evaluation with people who have CVD. Viewing environment, display calibration, print process, mark size, spatial context, ageing, acuity, and individual variation matter. Critical information should also use shape, texture, line style, position, or direct labels.

Grouped palettes require two complementary questions: are related colours recognisably related, and do they remain distinguishable? `group_summary.csv` and the relationship column in `pairwise.csv` expose the relevant distributions without hiding the trade-off in one score.

## 9. Reproducing an audit

Keep the entire report directory. To rerun it:

1. inspect `metadata.json` for the PaletteBench, Python, and dependency versions;
2. verify the YAML in `inputs/` against the recorded SHA-256;
3. recreate a compatible environment;
4. rerun the command with the recorded severities, thresholds, curve step, formats, and DPI as applicable.

The source YAML and machine-readable data remain sufficient to regenerate presentation artifacts. Generation timestamps and environment metadata intentionally differ between runs.

## 10. Quality checks for contributors

```bash
ruff check .
ruff format --check .
pytest
python -m build
```

Before release, also run a default audit, a non-default severity audit, a single-format audit, and a multi-palette comparison. Continuous integration runs these checks on supported Python versions.

## 11. Troubleshooting

### `palettebench: command not found`

Activate the environment in which the package was installed, or use `python -m palettebench`.

### Matplotlib cannot create its cache directory

Set a writable cache location:

```bash
export MPLCONFIGDIR=/tmp/palettebench-matplotlib
```

### A palette is rejected

Check the validation rules in section 3. The error identifies the colour or field that failed validation.

### Figures look different on another system

Numerical results should remain stable within normal floating-point tolerance, but font availability and rendering backends can cause small layout differences. Use the recorded versions and prefer the generated vector files for publication.
