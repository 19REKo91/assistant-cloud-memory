# All-118 phase-rank exploratory scenario — 2026-11-22
Status: illustrative full-coverage scenario, NOT a final physical model.

## Purpose
A full 118-row geometry pass was made to test the mechanics of generating one independent triangle per element while preserving visible source-quality flags. It does not settle the data comparability problem.

## Cohorts
Source phase labels were grouped as:
- Solid cohort: Solid + Expected to be a Solid
- Gas cohort: Gas + Expected to be a Gas
- Liquid cohort: Liquid

Cohort sizes: solid 104, gas 12, liquid 2 (total 118). The liquid cohort has only two members and therefore produces unstable endpoint ranks; it is explicitly marked low-N.

## Rank normalization
Within each phase cohort, midrank percentiles are computed separately for density and raw elemental molar volume. This means each element's coordinates are relative to its phase cohort. The ranks are not a common physical scale across phases.

## Angle map and triangle
Uses the previously documented candidate softmax angle map at lambda=0.50. Side c=1; a and b are obtained by the sine rule. The incenter is computed by side-length weighting. The CSV contains one triangle and incenter per element (118 rows).

## Sensitivity to adding secondary/expected entries
The 94 PubChem solid/gas entries were compared against their ranks in the PubChem-only 94-element prototype. Inclusion of secondary and expected entries changes the percentile coordinates of the PubChem elements. This is expected because the cohort membership changes; it demonstrates that source inclusion decisions materially affect geometry.

Summary:
- PubChem baseline comparison rows: 94
- Mean absolute shift in density percentile: 0.064295
- Maximum absolute shift in density percentile: 0.116090
- Mean absolute shift in molar-volume percentile: 0.023652
- Maximum absolute shift in molar-volume percentile: 0.090909

## Interpretation
This scenario completes the computational coverage requirement (118 separate triangles), but not the data-validation requirement. Secondary and predicted values are included only as clearly flagged illustrative inputs. The liquid cohort's n=2 is insufficient for stable percentile normalization. The full map must not be called final, physically calibrated, or validated.

## File
`ELEMENTS_118_PHASE_RANK_TRIANGLES_LAMBDA_0_50_EXPLORATORY_2026-11-22.csv`
