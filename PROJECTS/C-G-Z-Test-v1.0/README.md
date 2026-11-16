# C-G-Z Test v1.0 — Data intake

## Status
DATA TEMPLATE PREPARED — NO C-G-Z CALCULATION HAS BEEN RUN.

This is an independent test dataset. It is not a new release of the triangle geometry engine and does not modify 6.5.0 or any other framework version.

## Input file
- `data/elements_118_C_G_Z_input.csv`
- 118 element rows, preserving the source row order and original source columns from `PROJECTS/triangle-framework/6.5.0/elements_input_118.csv`.
- 60 provisional G values transcribed from the ChemReference compilation; 58 G values remain missing.
- The source input's Z, M, rho, and per-field provenance columns were carried forward without recalculation or alteration.

## C-G-Z equations fixed for this test
```
rho_n = (rho - 1.74) / (22.59 - 1.74)
Vm    = M / rho
V_n   = (Vm - 7.10) / (18.27 - 7.10)
C     = 90 + 70 * (rho_n - V_n)
```
Units:
- M: g/mol
- rho: g/cm^3
- Vm: cm^3/mol
- G: GPa
- C: degrees

Calibration limits:
- rho: 1.74 to 22.59 g/cm^3
- Vm: 7.10 to 18.27 cm^3/mol

Do not clip values outside these limits or change the limits. Flag out-of-range rows and retain the raw calculated value.

## G-field policy
New columns:
- `G_GPa`: shear modulus value.
- `G_source`: source for G, separately recorded.
- `G_structure`: crystal structure / polycrystalline designation.
- `G_direction`: measurement direction or isotropic/polycrystalline note.
- `G_temperature_C`: measurement temperature in °C.
- `G_pressure_GPa`: measurement pressure in GPa.
- `G_notes`: provenance and limitations.

Sixty G values were entered from the ChemReference compilation (which reports values for 60 of 118 elements). The five values in the user's original discovery sample are included:
- Pb = 5.6 GPa
- Al = 26 GPa
- Fe = 82 GPa
- W = 161 GPa
- Os = 222 GPa

The five original sample values (Pb, Al, Fe, W, Os) match the ChemReference compilation. The entered G values are labelled with that compilation as their source. ChemReference does not provide per-row experimental citations or measurement metadata in the retrieved table. Crystal structure/type, direction, temperature and pressure therefore remain unverified/missing for these values. The compilation is a secondary source and is suitable for provisional data intake, not yet a fully condition-harmonized scientific dataset.

Cross-source discrepancies are explicitly retained in `G_notes`: Mo is 120 GPa in ChemReference but 20 GPa in PeriodicTable.com/Wolfram ElementData; Co is 75 versus 76 GPa; Yb is 9.9 versus 10 GPa; Eu is reported as 7.9 GPa in the consulted compilations, with a prior alternate value 7.8 requiring checking. Do not silently resolve these conflicts. The other 58-element rows without a published value remain blank. Do not fill them from memory.

Reference pages:
- ChemReference: https://chemreference.com/properties/shear-modulus
- PeriodicTable.com / Wolfram ElementData: https://periodictable.com/Properties/A/ShearModulus.al.html
- WebElements literature notes and cited handbooks: https://webelements.com/periodicity/rigidity_modulus/index.html

## Source lineage for inherited fields
The inherited M and rho values and their source labels are in the CSV columns `M_source` and `rho_source`. Their documented assembly rules are in:
`PROJECTS/triangle-framework/6.5.0/SOURCES_AND_AUDIT.md`.

Important: some inherited values were user-supplied; the source audit explicitly distinguishes these from fallback dataset values. Do not treat the `MEASURED` row label as proof that every property is a direct experimental measurement.

## Prohibited actions
- Do not change the C equation or calibration constants.
- Do not silently replace missing G values.
- Do not infer crystal structure or measurement conditions.
- Do not combine G values measured under incompatible conditions without flagging them.
- Do not start statistical analysis until the G dataset and its provenance are reviewed.
- Do not treat correlation as causation.

## Current state
- Element rows: 118
- G values entered from the ChemReference compilation: 60
- G values missing from that compilation: 58
- G values with fully verified per-row measurement metadata: 0
- C-G-Z calculations performed: 0
