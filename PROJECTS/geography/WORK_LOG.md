# Geography project work log

**Status: INCOMPLETE.** No final continent map or validated final continent-area figures have been approved.

## Session — 2026-10-15

### Completed and verified in GitHub
- Created branch: `geography-continent-area-audit` (based on `main`).
- Added `PROJECTS/geography/README.md` documenting the fresh start, source, calculation method, limitations, and acceptance checks.
- Added `scripts/geography/continent_area.py` to download Natural Earth Admin 0 Countries 1:10m, calculate polygon areas geodesically on WGS84 with pyproj, export country and grouped CSVs plus an audit JSON, and reject invalid/missing geometries or empty outputs.
- Added `.github/workflows/geography-continent-area.yml` to run the calculation remotely and upload outputs as a 14-day GitHub Actions artifact.
- Removed pip caching from the workflow because the repository path has no dependency manifest for setup-python to cache against.
- Re-fetched all three files from the new branch and confirmed they exist and are non-empty.

### Current verified references
- Latest known commit on this branch: `fd53ef98a1706437de324f6dd8097a708e8295ae` (workflow correction).
- Branch: `geography-continent-area-audit`.
- Main branch has not been changed.
- The workflow's actual run result and artifact have **not yet been verified** from available GitHub Actions results.

### Important limitation
The calculation groups country polygons by Natural Earth's `CONTINENT` field. This is a reproducible baseline, not a final natural-continent partition: transcontinental countries inherit the dataset's classification. Do not present its totals as definitive natural continent areas without a separately documented rule for cross-continent countries and islands.

### Next exact steps
1. Run `.github/workflows/geography-continent-area.yml` on branch `geography-continent-area-audit` using GitHub Actions → Run workflow.
2. Inspect the run logs and download artifact `geography-area-audit`.
3. Verify CSV/JSON contents, totals, feature counts, and audit metadata; record the actual run URL and result here.
4. Only after the baseline is verified, define explicit geographic rules for transcontinental countries and island groups.
5. Build the coastlines/map from real geographic polygons remotely via GitHub Actions; do not generate images inside ChatGPT's local environment.
