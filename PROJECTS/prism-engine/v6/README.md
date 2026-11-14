# Prism Engine v6 — Truth-first prototype

This is a new, independent successor prototype copied conceptually from the latest v5 engine. It does not edit or replace v5 or the historical v4.2 engine.

## Design rules

1. Preserve original source values in separate fields. Derived values are labeled as derived.
2. Keep the v4.2/v5 density normalization and 60-degree zipper unchanged for comparison.
3. Construct the primary Euclidean triangle from the adjusted angle set only when all three angles are positive, below 180 degrees, and sum to 180 degrees.
4. Do not clip invalid angles, scale sides, or silently rescue a failed triangle. Failed cases remain visible with a reason.
5. Keep the v5 side definitions as a separate comparison lane:
   - a = Z / 10
   - b = 3 * abs(sin(theta_2_vis)) / sin(theta_3_vis)
   - c = 3 + 0.016 * (M - Z)
6. Predictions are separate from source data and are never presented as measurements.

## Geometry interpretation

The primary triangle is a mathematically valid Euclidean construction from the model's adjusted angles and a reference side c=3. It is not a claim that an atom is physically shaped like a triangle.

The v5 side-based construction is retained only as a comparison. Its failure does not get silently repaired by the primary lane, and vice versa.

## Prediction layer

The prototype currently attempts an atomic-mass-only scenario for Z=119..126 using the median of recent adjacent mass increments from Z=104..118. It also performs a chronological holdout check.

The pinned source contains a Z=119 Uue entry with atomic_mass=315. The increment model gives a Z=119 scenario of 296, a difference of 19 mass units. The recent holdout MAE is 1.8, so the operational comparison limit is 3.6. Because the source value's scientific quality is not specified in that dataset, this is not treated as experimental ground truth; it is recorded as an unresolved disagreement. The prototype therefore withholds Z=120..126 mass extrapolations rather than extending a model that fails this comparator.

No density is forecast, so no future-element triangle is fabricated. A future density predictor requires a separately validated method and backtesting.

## Pinned input source

- Repository: `Bowserinator/Periodic-Table-JSON`
- Commit: `a78c7a48fe7235cebd6153161a9e7fa70f0cfb30`
- File: `PeriodicTableJSON.json`
- Expected Git blob SHA-1: `2424af6ef572dd52325697570c4dc79578d5b7be`

The engine verifies the downloaded file's Git blob SHA before calculation. If the content differs, the run stops.

The source dataset does not specify a complete measured/predicted quality classification for every property. The engine marks source quality as `NOT_SPECIFIED_IN_PINNED_SOURCE`; it does not infer experimental status.

## Outputs

- `outputs/v6_elements_118_plus_extensions.csv`: baseline Z=1..118 plus any source extension rows (such as Uue) clearly marked outside the baseline.
- `outputs/v6_mass_predictions_119_126.csv`: mass-only scenarios, comparator diagnostics, or suppressed predictions.
- `outputs/v6_run_audit.json`: pinned source identity, checksum, run timestamp, counts, and methodological rules.

## Running

GitHub Actions workflow: `.github/workflows/run-prism-v6.yml`

It is manual-only (`workflow_dispatch`). Creating this version does not run it automatically. The v5 workflow and source files remain untouched.
