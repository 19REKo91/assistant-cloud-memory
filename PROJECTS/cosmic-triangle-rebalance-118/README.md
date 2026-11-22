# Cosmic Triangle Rebalance — 118 elements

Independent experimental workspace. The frozen reference framework is not modified by any file in this directory.

## Current state
- 118 element rows assembled in a source-audited draft.
- Phase/condition compatibility overlay created.
- Secondary density conflicts recorded separately.
- Cohort selection and normalization gates documented.
- One mathematical angle-map candidate tested over the normalized input square.
- No element-specific angles or triangles calculated yet.
- No final unified image generated.

## Data and audit files
- `ELEMENTS_118_MASS_DENSITY_SOURCE_AUDITED_DRAFT_2026-11-22.csv` — original working mass/density table; draft only.
- `MASS_DENSITY_SOURCE_AUDIT_2026-11-22.md` — source coverage and limitations.
- `ELEMENTS_118_PHASE_COMPATIBILITY_REGISTER_2026-11-22.csv` — 118-row phase/source/condition overlay.
- `PHASE_AND_MOLAR_VOLUME_COMPATIBILITY_AUDIT_2026-11-22.md` — phase and molar-volume basis audit.
- `SECONDARY_DENSITY_SOURCE_CONFLICTS_2026-11-22.csv` — row-level source comparisons.
- `SECONDARY_DENSITY_CONFLICT_AUDIT_2026-11-22.md` — unresolved conflict rules.
- `COHORT_MAP_AND_NORMALIZATION_GATES_2026-11-22.md` — source/phase cohort counts and normalization tracks.

## Experimental design
- `EXPERIMENT_PROTOCOL_DRAFT.md` — project scope and staged workflow.
- `ANGLE_MAP_CANDIDATE_MATHEMATICAL_TEST_2026-11-22.md` — independent positive-angle transformation candidate and mathematical sensitivity sweep.

## Control rules
1. Do not use legacy angles, element calibration anchors, or old normalization limits.
2. Do not merge measured, secondary, estimated, and predicted values silently.
3. Do not treat different phases or undocumented conditions as one homogeneous population.
4. Keep raw source values separate from derived values.
5. Do not promote any experimental result to the reference framework without explicit user approval.

- `ELEMENTS_118_RAW_MOLAR_VOLUME_SCREENING_NOT_FOR_NORMALIZATION_2026-11-22.csv` — raw M/rho derivative, explicitly held from normalization.
- `RAW_MOLAR_VOLUME_SCREENING_AUDIT_2026-11-22.md` — grouped distribution diagnostic and phase-scale warning.
- `ELEMENTS_118_CIAAW_MASS_BASIS_AUDIT_2026-11-22.csv` — CIAAW 2024 mass-basis coverage overlay.
- `CIAAW_MASS_BASIS_AUDIT_2026-11-22.md` — standard atomic weight vs nuclide-specific mass distinction.

## Latest data conclusions
- CIAAW 2024 publishes standard atomic weights for 84 elements in the current table; 34 elements have no CIAAW standard atomic weight entry and need nuclide-specific mass identity.
- Raw M/rho values are calculated for all 118 rows as a diagnostic only. The PubChem gas subset is about 11,030–22,818 cm³/mol atoms, while the PubChem solid subset is about 4.56–68.86 cm³/mol atoms. A single pooled min-max scale would be dominated by phase.
- No normalization cohort, angle parameter, or element geometry has been approved or computed.

- `ELEMENTS_94_PUBCHEM_PHASE_RANK_TRIANGLE_SWEEP_2026-11-22.csv` — 282 exploratory triangle rows (94 PubChem solid/gas elements × 3 lambda values), with incenter coordinates.
- `PHASE_RANK_TRIANGLE_SWEEP_AUDIT_2026-11-22.md` — method and interpretation limits for the 94-element prototype.

## Prototype calculation status
- Calculated a phase-specific empirical-rank prototype for 83 PubChem solid entries and 11 PubChem gas entries.
- Each element was computed at lambda = 0.25, 0.50, and 1.00; 282 triangles total.
- Every triangle has three positive interior angles summing to 180 degrees within floating-point error.
- The incenter coordinates are included using side-length weighting and a normalized base side c=1.
- This is not yet the final 118-element map. Two liquid entries, 22 secondary-source entries, and nine expected-state entries are not in this controlled prototype.

- `ELEMENTS_118_PHASE_RANK_TRIANGLES_LAMBDA_0_50_EXPLORATORY_2026-11-22.csv` — one independent exploratory triangle and incenter for each of the 118 elements.
- `ALL_118_PHASE_RANK_SCENARIO_AUDIT_2026-11-22.md` — full-coverage scenario, cohort sizes, and sensitivity to secondary/expected entries.

## Full-coverage exploratory run
- All 118 elements now have a separate triangle in the exploratory CSV.
- Phase cohorts: 104 solid/expected-solid, 12 gas/expected-gas, 2 liquid.
- The two-member liquid cohort is explicitly low-N and its rank-based triangle is unstable.
- Secondary and expected values are included only as flagged illustrative inputs.
- Adding secondary/expected rows shifts PubChem-only percentile ranks: mean absolute shift 0.0643 for density and 0.0237 for molar volume; maximum shifts 0.1161 and 0.0909 respectively.
- The run uses lambda=0.50 only as a demonstration setting. It is not approved as the final model and does not resolve cross-phase comparability.
