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
1. Review the meaning of Antarctic area: land polygons only versus land plus floating ice shelves.
2. Compare preliminary values with an independent reference and explain differences, especially island grouping and source scale.
3. Once the definition is approved, generate a map remotely from the real polygon data using Equal Earth for display only; keep area calculations geodesic and independent of the display projection.
4. Inspect the resulting map file for non-empty content, expected dimensions, and readable labels before calling it complete.

## Session update — 2026-10-15: remote calculation verified

### Completed and verified
- GitHub Actions run [#11](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38682861700) completed successfully, including both calculation scripts and artifact upload.
- Downloaded and inspected artifact ID `11948154828`; it contains five non-empty files: country details, country-classification totals, country audit JSON, physical-continent totals, and physical-continent audit JSON.
- The first country-based grouping is unsuitable as a final continent calculation because Natural Earth's `CONTINENT` field assigns whole countries to one group. It remains explicitly preliminary.
- Added `scripts/geography/continent_land_area.py`, using Natural Earth 1:10m land and minor-island polygons intersected with the GBIF seven-continent cookie-cutter polygons pinned to commit `5f2aaf608f2f828bb1d03ae0d2ef3f41feacd5be`.
- The script repaired no Natural Earth land geometries in this run. It processed 2,806 land/island features.
- Physical land totals (million km²): Asia 43.671567; Africa 29.848559; North America 24.252768; South America 17.708031; Antarctica 12.370083; Europe 10.057641; Oceania 8.948389.
- Audit reconciliation: source land 146,857,177.566 km²; assigned 146,857,037.717 km²; unassigned 139.817 km²; overlap excess -0.032 km².
- Added results, sources, methodology, caveats, and the artifact URL to `PROJECTS/geography/README.md`.

### Current verified Git state
- Branch: `geography-continent-area-audit`.
- Calculation code commit: `8d7b14629ec5d6ee728e9fe73107219eca8eb45a`.
- README results update commit: `d8450d8cb15a751047252aa5ae1d81360cb4e8ab`.
- Main remains unchanged; draft PR #10 is open and unmerged.
- Successful run: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38682861700
- Artifact (14-day retention): https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38682861700/artifacts/11948154828

### Still incomplete
- Values are preliminary, not final certified continent areas.
- GBIF notes that ocean boundaries are approximate and the cutter reflects one seven-continent convention. Its ODbL-derived source license must be respected.
- Antarctic total represents Natural Earth land polygons; floating ice shelves are not automatically included.
- No map image has been generated. The user explicitly prohibited creating images inside ChatGPT's environment; any future map must be rendered remotely and checked as an actual file.

## Session update — 2026-10-15: remote map generated and published

### Completed and verified
- Added scripts/geography/render_continent_map.py; it reads the calculated physical-continent polygons and area CSV, renders Equal Earth (EPSG:8857), and checks the PNG can be opened, is at least 1600×800, and exceeds 50 KB.
- Added a remote rendering step to GitHub Actions. The map is generated only on the GitHub Actions runner; no image was created in ChatGPT's local environment.
- Successful full workflow run: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38683310415
- Verified runner output: MAP_RENDERED_AND_IMAGE_FILE_VERIFIED; PNG dimensions 2769×1461; size 391,513 bytes. The workflow uploaded the audit bundle and published the PNG into the project branch.
- Verified the PNG exists in GitHub at PROJECTS/geography/generated/continent_map_equal_earth.png; GitHub's directory API reported 391,513 bytes.
- Added explicit GBIF/OpenStreetMap ODbL attribution to the map footer.
- Hardened the publishing step to fetch and rebase on the latest branch before pushing, after a first push was rejected due to concurrent branch updates.

### Direct map links
- View: https://github.com/19REKo91/assistant-cloud-memory/blob/geography-continent-area-audit/PROJECTS/geography/generated/continent_map_equal_earth.png
- Raw PNG: https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/geography-continent-area-audit/PROJECTS/geography/generated/continent_map_equal_earth.png
- Latest audit artifact (14-day retention): https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38683310415/artifacts/11949540485

### Current verified state
- Branch: geography-continent-area-audit.
- Latest README correction commit: 327cfa54b147ff6aa33da3d9f0c91737028de5c6.
- Main remains unchanged. Draft PR #10 remains open and unmerged.
- The map is programmatically verified, but still needs visual review and independent comparison of area values before the project can be called complete.

### Remaining work
1. User visually reviews the map labels and layout.
2. Decide whether Antarctic floating ice shelves should be included in the definition.
3. Compare preliminary values against an independent source and document methodological differences.
4. Re-run and update the map only if the review warrants a change.

### Final rerun after publishing the image — 2026-10-15
- Re-ran the complete workflow after adding attribution and robust branch publication; run succeeded: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38683447317
- Latest artifact: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38683447317/artifacts/11949360828
- Re-checked GitHub metadata for the published PNG: file exists at PROJECTS/geography/generated/continent_map_equal_earth.png, size 391,513 bytes, blob SHA c9953d3f13cfc17ff0059edf5d9dd9c7f83e21c0.
- The output PNG was unchanged in the rerun. Current project state remains incomplete until visual review and an independent methodology comparison are done.

### Independent comparison added — 2026-10-15
- Added a clearly qualified comparison in PROJECTS/geography/README.md against the seven-continent area table attributed to Encyclopaedia Britannica on https://en.wikipedia.org/wiki/Continent.
- The comparison shows material differences: Asia about -2.11%, Africa -1.70%, North America +0.09%, South America -0.59%, Antarctica -12.89%, Europe +0.58%, Oceania +5.14%.
- These are not treated as proof of a coding error because the references may differ in island assignment, coastline data, and whether Antarctic ice shelves are counted. They are a reason to keep the result preliminary and resolve the definitions before approval.
- The current PNG remains published but its area labels are preliminary. Next review must explain the differences before final approval.

### Latest rerun after reference comparison — 2026-10-15
- Full workflow run 41 succeeded after the reference-comparison documentation update: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38683636121
- Artifact for this run: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38683636121/artifacts/11949481092
- The remote calculation, GeoJSON export, Equal Earth rendering, PNG verification, artifact upload, and publish step all passed again.


## Session update — 2026-10-15: independent numeric audit of latest artifact

### Verified run and artifact
- Latest checked run: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/38683738886 — completed successfully.
- Run commit: 33a4449e15848b86f179cabed13620cb34c23e03; branch: `geography-continent-area-audit`.
- Artifact ID 11949351364 (6,328,091 bytes) downloaded and inspected. It contains seven files, including both CSV baselines, both JSON audit reports, GeoJSON continent polygons, and the PNG map.
- Job steps for calculate, physical land area by continent, remote Equal Earth rendering, PNG verification, and artifact upload all succeeded. The PNG publish step was skipped in this run; the already-published image is a separate branch file.

### Numeric checks completed
- `country_area_baseline.csv`: 258 country/area rows; rounded row sum 146,826,414.841 km².
- `continent_area_baseline.csv`: sum of grouped totals 146,826,414.844 km². Difference about 0.003 km², explained by detail rows rounded to 3 decimals and grouped totals to 6 decimals. No material internal summation error found.
- `area_audit.json`: one invalid source geometry, Egypt; one geometry repaired; zero null geometries. The code applies Shapely `make_valid`, retains polygonal parts, unions them, and rejects the geometry if it remains invalid.
- `continent_land_area_audit.json`: source land 146,857,177.566 km²; assigned to seven continents 146,857,037.717 km²; unassigned 139.817 km²; reported overlap excess -0.032 km².
- Country polygon total vs assigned physical land total differs by 30,622.873 km². This is not a simple arithmetic discrepancy because the inputs differ: administrative country/area polygons grouped by Natural Earth CONTINENT versus Natural Earth land/minor-island polygons partitioned with GBIF continent cookie-cutters.
- Recomputed reference percentages using (project − reference) / reference × 100. Published rounded percentages are arithmetically correct: Asia -2.1124%, Africa -1.7008%, North America +0.0940%, South America -0.5949%, Antarctica -12.8867%, Europe +0.5764%, Oceania +5.1391%.

### Interpretation / status
- The major issue is methodological/source comparability, not a meaningful summation bug. The country-classification table is not suitable as the final natural-continent area table because whole transcontinental countries inherit a single dataset classification.
- The physical-land method is more appropriate for the intended seven-continent comparison, but remains preliminary: GBIF boundary/cutter conventions, islands, 139.817 km² unassigned land, and Antarctic floating ice shelves need explicit treatment. The external reference values may use different conventions, so percentage differences alone do not prove a code error.
- Updated `PROJECTS/geography/README.md` with the audit, computed differences, and a clear incomplete status. README update commit: `0fa0ee17c043e3641b576da1029c22b44b59aeca`.
- **Project status remains INCOMPLETE.** Next exact steps: (1) visually review the published PNG, (2) decide land-only vs land plus Antarctic ice shelves, (3) document island and transcontinental-boundary rules and investigate unassigned land, (4) compare against a source with matching definitions, (5) rerun and update the map only after the area labels are justified.
