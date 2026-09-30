# Complete example output

[`okabe-ito-report/`](okabe-ito-report/) is a complete PaletteBench audit of the bundled Okabe–Ito baseline. It includes the exact copied input, provenance metadata, full-precision CSV/JSON data, Markdown and LaTeX tables, and every default SVG/PDF/PNG figure.

Start with the generated [`report.md`](okabe-ito-report/report.md).

The example is regenerated from the repository root with:

```bash
palettebench palettes/okabe-ito.yaml \
  --output examples/okabe-ito-report \
  --format svg,pdf,png
```

The generated `metadata.json` records the precise package and dependency versions, configuration, timestamp, and SHA-256 of the copied palette definition.

