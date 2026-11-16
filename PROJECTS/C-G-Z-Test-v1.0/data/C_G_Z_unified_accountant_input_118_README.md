# C-G-Z Test v1.0 — Unified 118-element input for independent accountant

This file combines the original element input table with the separately maintained PeriodicTable.com / Wolfram ElementData shear-modulus table, joined strictly by atomic number (Z).

## Active calculation fields
- `M`, `rho`: retained exactly from the original input file, including source and quality metadata.
- `G_active_GPa`: active G value from `shear_modulus_wolfram_elementdata_118.csv`. `NA` means the selected source did not list a value.
- `Vm_cm3_mol = M / rho`
- `rho_n = (rho - 1.74) / (22.59 - 1.74)`
- `V_n = (Vm - 7.10) / (18.27 - 7.10)`
- `C_deg = 90 + 70 * (rho_n - V_n))

## Important separation of sources
The former `G_GPa` and `G_source` columns in the original file have been renamed `G_legacy_input_GPa` and `G_legacy_input_source`. They are retained only for audit/history and may contain values from an earlier ChemReference compilation. They are NOT the active G dataset for this test. Use only `G_active_GPa` for the current C-G-Z analysis. Do not merge the legacy values into the active column.

## Missing data and calibration
- Missing values remain blank in calculated fields and `NA` in active G where the selected source reports no value.
- No value is clipped to calibration limits.
- `rho_range_status` and `Vm_range_status` independently mark values outside the calibration intervals.
- `C_GZ_status` is `IN_CALIBRATION_RANGE` only when both rho and Vm are within their respective intervals; otherwise it is `OUT_OF_CALIBRATION_RANGE`.
- `OUT_OF_CALIBRATION_RANGE` is a calibration flag, not a claim that the source value is false.
- The input contains mixed source provenance and quality labels. Do not describe all M/rho values as measurements from one experiment or uniform conditions.
- No imputation or inferred G values were added.

## Source files
- Original input: `PROJECTS/C-G-Z-Test-v1.0/data/elements_118_C_G_Z_input.csv`
- Active G table: `PROJECTS/C-G-Z-Test-v1.0/data/shear_modulus_wolfram_elementdata_118.csv`

## Reproducibility
The calculations are direct implementations of the equations above using the stored numeric values without rounding before calculation. Display columns are rounded only for CSV readability (Vm/rho_n/V_n to 10 decimal places; C to 8 decimal places). For independent recalculation, use original M and rho columns and the stated equations.
