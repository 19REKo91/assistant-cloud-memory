# 20°C gas update and 118-element phase-rank recalculation audit

**Status:** Independent exploratory recalculation. Not a final physical model and not a change to frozen reference 6.2.1 or prior outputs.

## Inputs and transformations
- Source mass/density table: ELEMENTS_118_MASS_DENSITY_SOURCE_AUDITED_DRAFT_2026-11-22.csv
- Phase/source compatibility register: ELEMENTS_118_PHASE_COMPATIBILITY_REGISTER_2026-11-22.csv
- Gas harmonization table: ELEMENTAL_GASES_11_ROOM_TEMPERATURE_20C_1ATM_2026-11-22.csv
- Gas calculation basis follows the prior gas audit: all 11 values use the consistently ideal-gas-scaled 0°C-to-20°C densities. Seven independent direct-20°C table values are retained only as separate cross-check columns; they do not overwrite the calculation basis. Four gases have no direct 20°C cross-check and remain ideal-scaled only.
- Solid/liquid density values are carried from their source rows without an unsupported thermal correction. Their source-specific temperature/pressure/allotrope limitations remain visible in the row status and flags.
- Elemental molar volume is calculated as atomic mass / density, in cm³ per mole of atoms.
- Density and molar-volume percentiles are midranks within each phase cohort, never pooled across phases.
- Angle transformation is the existing explicitly exploratory softmax candidate with lambda=0.5; it is not a measured physical law.
- Triangle base c=1 is a normalized construction scale. The red point is the incenter.
- Display positions use standard periodic-table group/period positions, with lanthanides and actinides on separate rows.

## Coverage
- Input rows: 118; unique Z: 118
- Phase cohorts: {'Gas': 12, 'Solid': 104, 'Liquid': 2}
- Valid angle-defined triangles: 118
- Rows held without triangle: 0
- Maximum angle-sum numerical error: 2.84e-14 degrees
- Cohort sizes: {'Gas': 12, 'Solid': 104, 'Liquid': 2}

## Input quality distribution
- GAS_IDEAL_SCALED_20C_NO_DIRECT_CROSSCHECK: 4
- GAS_IDEAL_SCALED_20C_WITH_DIRECT_CROSSCHECK: 7
- LOW_N_LIQUID_COHORT: 2
- PREDICTED_OR_EXPECTED_INPUT: 15
- PRIMARY_LISTED_CONDITIONS_UNSPECIFIED: 83
- SECONDARY_SOURCE_INPUT: 7

## Scientific limitations
1. A common thermodynamic state for all 118 elements is not established. Solid and liquid densities are not temperature-corrected because row-level conditions/allotropes are unavailable.
2. The gas table has a mixture of direct 20°C cross-checks and ideal-gas-scaled values; the latter are explicitly flagged.
3. The liquid cohort contains only two members; its phase-relative ranks are unstable and must not be interpreted as a robust scale.
4. Expected/predicted and secondary-source entries are retained and flagged; their numeric presence does not make them measurements.
5. Phase-relative percentiles are not one shared physical scale across gas, liquid, and solid. The resulting map is a computational visualization scenario only.
6. This run does not claim pressure/stress measurements, and no old reference constants or old angle values were used.

## Outputs
- ELEMENTS_118_PHASE_RANK_20C_RECALCULATED_EXPLORATORY_2026-11-22.csv
- ELEMENTS_118_PERIODIC_TABLE_TRIANGLES_20C_EXPLORATORY_2026-11-22.svg
- ELEMENTS_118_PERIODIC_TABLE_TRIANGLES_20C_EXPLORATORY_2026-11-22.png
- PHASE_RANK_20C_RECALCULATION_AUDIT_2026-11-22.md
