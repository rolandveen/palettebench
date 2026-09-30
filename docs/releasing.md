# Release checklist

This checklist keeps a GitHub release, package metadata, and its Zenodo archive aligned.

## Prepare the release commit

1. Choose the version and release date.
2. Update the version in `pyproject.toml` and `CITATION.cff`.
3. Move the relevant `CHANGELOG.md` entries from **Unreleased** into a dated version section.
4. Confirm that `CITATION.cff` contains the intended creators, ORCIDs, affiliations, abstract, keywords, licence, and repository URL.
5. Regenerate committed examples if their expected output changed.
6. Run the complete local validation:

   ```bash
   ruff check .
   ruff format --check .
   pytest
   python -m build
   ```

7. Inspect both archives in `dist/` and install the wheel in a clean environment for a CLI smoke test.
8. Commit and push the release preparation. Confirm that the GitHub Actions matrix passes.

## Publish and archive

1. Make the repository public if it is not already public.
2. In Zenodo, connect the GitHub account, synchronize repositories, and enable `rolandveen/palettebench`.
3. Create an annotated tag named `vX.Y.Z` on the validated release commit and push it.
4. Create the matching GitHub release from that tag. Use the corresponding changelog section as the release notes.
5. Wait for Zenodo to ingest the GitHub release. Verify the record metadata, files, version, licence, creator identity, and Software Heritage archival status.
6. Record the assigned version DOI and concept DOI. Add the preferred DOI badge and citation identifier to the repository after checking the live Zenodo record.

Published release contents are immutable. Corrections that change files should be issued as a new version rather than silently replacing an archived release.
