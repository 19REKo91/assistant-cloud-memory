# C-G-Z Test v1.0 — Shear Modulus (G) Source Audit
Date: 2026-11-16
Dataset: `data/C_G_Z_unified_accountant_input_118.csv`
Scope: provenance and coverage of the active `G_active_GPa` column. No input values were changed.

## 1. What the current file actually contains

- 118 element rows.
- 60 numeric active G values; 58 are missing.
- All 60 active values carry the common source label `PeriodicTable.com / Wolfram ElementData`.
- The PeriodicTable.com shear-modulus page states that its curated data are provided by Mathematica's ElementData function.
- The file does not contain an individual primary experimental citation for each of the 60 G values.
- The file does not establish per-value crystal structure/phase, sample purity, measurement direction, temperature, pressure, or uncertainty.
- The general `Data_Quality` field says `MEASURED` on the 60 rows with G, but this is not enough to prove that each active G entry has a traceable primary measurement under harmonized conditions. Do not interpret this label as a complete G-specific experimental provenance record.

## 2. Coverage is not uniform

| Group in dataset | Total rows | Rows with active G |
|---|---:|---:|
| Blank / other family label | 88 | 42 |
| Lanthanides (Ln) | 15 | 15 |
| Actinides (An) | 15 | 3 |
| **Total** | **118** | **60** |

The 58 missing values are not shown to be missing at random. In particular, all 15 lanthanides have values while only 3 of 15 actinides do. Correlations based on the 60 available entries may therefore reflect selection/coverage effects as well as material relationships.

## 3. Known source conflicts retained

| Element | Active PeriodicTable.com / Wolfram value (GPa) | Legacy compilation value (GPa) | Audit note |
|---|---:|---:|---|
| Co | 76 | 75 | Both values are published in the two compilations; primary condition-specific record not attached. |
| Mo | 20 | 120 | Major discrepancy. NASA material handbooks give approximately 120 GPa near room temperature; see references below. The active 20 GPa value must be treated as unresolved and flagged, not silently accepted. |
| Yb | 10 | 9.9 | Small difference; likely precision/rounding scale, but original measurement metadata are absent. |
| Ta | 67 | 69 | Both compilation values retained; source-level experimental traceability is not yet established. |

These differences were not merged or overwritten. The source CSV remains unchanged.

## 4. Mo — high-priority discrepancy

Independent NASA references support a room-temperature molybdenum shear modulus close to 120 GPa:
- NASA Space Nuclear Propulsion Material Property Handbook (2020 revision): at 293 K, listed values are 117.80 GPa (minimum curve) and 121.08 GPa (high curve).
- NASA handbook table: at 25 °C, G = 120 GPa.
- Liu et al. (2009), *Experimental and theoretical studies on the elasticity of molybdenum to 12 GPa*, reports ambient-pressure shear modulus G0 = 125.1(2) GPa.

This evidence makes 20 GPa a serious likely source/data error for ordinary solid molybdenum near room temperature. It does not authorize an automatic replacement in the canonical input file. Keep the alternative 120 GPa as a sensitivity scenario until the dataset owner explicitly approves a correction and the source policy is settled.

## 5. Sensitivity test already run in GitHub Actions

Workflow run #2 completed successfully:
https://github.com/19REKo91/assistant-cloud-memory/actions/runs/43855030020

The engine compared the current values with source-conflict scenarios. Results:

| Scenario | n | Spearman(C,G) | Pearson(C,G) |
|---|---:|---:|---:|
| Current active values | 60 | 0.83908 | 0.66231 |
| Mo changed to 120 GPa (scenario only) | 60 | 0.84947 | 0.67649 |
| Mo excluded | 59 | 0.84744 | 0.67311 |
| Co changed to 75 GPa | 60 | 0.83910 | 0.66213 |
| Ta changed to 69 GPa | 60 | 0.83908 | 0.66273 |
| Yb changed to 9.9 GPa | 60 | 0.83908 | 0.66233 |
| All four alternatives together | 60 | 0.84948 | 0.67675 |

The positive rank association remains high under these tested scenarios. This only demonstrates robustness to these four value changes in this particular 60-row dataset. It does not solve the broader provenance, measurement-condition, or missing-data problems and does not establish causality or independent information in C.

## 6. References checked

1. PeriodicTable.com, “Shear Modulus of the elements” — identifies the table as curated data provided by Mathematica's ElementData:
   https://periodictable.com/Properties/A/ShearModulus.html
2. Wolfram, “ElementData Source Information” — describes ElementData as assembled from a wide range of sources; it does not identify the exact source for each specific shear-modulus entry:
   https://reference.wolfram.com/language/note/ElementDataSourceInformation.html
3. Wolfram, “ElementData” — describes the ShearModulus property and standard-condition conventions for macroscopic properties:
   https://reference.wolfram.com/language/ref/ElementData.html
4. NASA, *Space Nuclear Propulsion Material Property Handbook*, molybdenum section:
   https://ntrs.nasa.gov/api/citations/20240004217/downloads/SNP-HDBK-0008_SNP-Material-Handbook.pdf
5. NASA handbook table of elastic and shear moduli of molybdenum:
   https://ntrs.nasa.gov/api/citations/19770007251/downloads/19770007251.pdf
6. Liu et al. (2009), *Experimental and theoretical studies on the elasticity of molybdenum to 12 GPa*:
   https://mattwhitaker.net/docs/liu2009a.pdf

## 7. Current audit decision

- Keep all original active and legacy values unchanged.
- Mark Mo (20 vs 120 GPa) as a high-priority unresolved discrepancy.
- Do not describe the 60 G values as fully source-verified experimental measurements.
- Treat the current C–G association as promising but provisional.
- The next meaningful improvement is to obtain per-element primary references and comparable conditions for the 60 populated values, then examine the 58 missing entries and selection bias.
