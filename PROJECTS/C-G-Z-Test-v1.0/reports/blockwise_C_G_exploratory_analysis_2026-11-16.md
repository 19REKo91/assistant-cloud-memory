# C-G-Z Test v1.0 — Exploratory C–G Analysis by Periodic-Table Block
Date: 2026-11-16

## Scope and source
- Input: `data/C_G_Z_unified_accountant_input_118.csv`
- The source file contains 118 element rows and no complete, authoritative `Block` or chemical-family classification column.
- The `Family` field is sparse (not a complete classification for all elements), so it was not treated as a full block map.
- The block labels below are derived from atomic number (Z) using the explicit convention stated below. They are analytical labels, not source-provided measurements or classifications.
- Only rows with numeric `G_active_GPa` and numeric `C_deg` were included. No values were imputed, clipped, or replaced. The 60 active G values in the current source file were retained.

## Classification convention
- s-block: H, He, and the group-1/group-2 positions: Z = 1–4, 11–12, 19–20, 37–38, 55–56, 87–88.
- p-block: groups 13–18, excluding He: Z = 5–10, 13–18, 31–36, 49–54, 81–86, 113–118.
- d-block: transition-block positions excluding the two detached f-series: Z = 21–30, 39–48, 72–80, 104–112.
- f-block: the detached lanthanide/actinide series under the broad layout convention: Z = 57–71 and 89–103. This convention assigns La–Lu and Ac–Lr to f-block for this analysis; alternative group-3 placements exist and would change the classification of boundary elements.
- Helium is assigned to s-block by electron configuration/position convention, although it is chemically a noble gas.

## Coverage of active G values
| Block | Elements in block (118 total) | Numeric active G and C | Missing active G/C |
|---|---:|---:|---:|
| s | 14 | 8 | 6 |
| p | 36 | 8 | 28 |
| d | 38 | 26 | 12 |
| f | 30 | 18 | 12 |
| **Total** | **118** | **60** | **58** |

## Descriptive results within each block
Pearson and Spearman correlations are computed between derived C and active G (GPa) within each block. Mean G is the arithmetic mean of the available active G values in that block.

| Block | n | Mean G (GPa) | Mean C (degrees) | Pearson r(C,G) | Spearman rho(C,G) |
|---|---:|---:|---:|---:|---:|
| s | 8 | 22.0250 | -20.8674 | 0.6384 | 0.5476 |
| p | 8 | 13.0125 | 45.8506 | 0.1249 | -0.0238 |
| d | 26 | 78.8077 | 105.4464 | 0.6652 | 0.7611 |
| f | 18 | 26.7167 | 36.2184 | 0.8018 | 0.9809 |

### Included symbols
- s (n=8): Li, Be, Na, Mg, K, Ca, Sr, Ba
- p (n=8): Al, Se, Sn, Sb, Te, Tl, Pb, Bi
- d (n=26): Sc, Ti, V, Cr, Fe, Co, Ni, Cu, Zn, Y, Zr, Nb, Mo, Ru, Rh, Pd, Ag, Cd, Hf, Ta, W, Re, Os, Ir, Pt, Au
- f (n=18): La, Ce, Pr, Nd, Pm, Sm, Eu, Gd, Tb, Dy, Ho, Er, Tm, Yb, Lu, Th, U, Pu

## Pooled within-block association
To remove differences in block means descriptively, C and G were separately demeaned within each block and the Pearson correlation was calculated across the pooled residuals:
- n = 60
- Pearson correlation of within-block demeaned values = 0.5542

This is a descriptive block-adjusted linear association, not proof that C is an independent physical variable. It does not remove all nonlinear dependence on density and atomic mass, because C is deterministically calculated from density and molar volume (and molar volume is M/rho).

## Interpretation and limitations
1. The C–G association is not uniform across blocks. It is strongest in the available f-block sample by both Pearson and Spearman, moderate in d and s, and near zero in p.
2. The f-block estimate is especially fragile: the available sample contains 15 lanthanides but only 3 actinides (Th, U, Pu). It should not be generalized to the entire actinide series.
3. Coverage is strongly unbalanced: only 8 of 36 p-block elements have active G values, compared with 26 of 38 d-block elements. Differences between block correlations may therefore reflect selection and coverage as well as chemistry.
4. Each block has a small sample (n=8, 8, 26, 18). These are exploratory descriptive statistics; no causal or robust inferential claim is made.
5. This analysis does not reverse the earlier repeated cross-validation result: adding C to models already using rho and M did not improve prediction of G. A within-block correlation does not establish independent predictive information.
6. The G values are still largely sourced from a secondary compilation (PeriodicTable.com / Wolfram ElementData) without per-entry primary experimental traceability and uniform measurement-condition metadata, as documented in the existing source audit.

## Conclusion
A positive descriptive C–G association remains within the s-, d-, and f-block samples, while the p-block sample shows almost no association. The pooled within-block Pearson correlation is 0.5542. This supports further source-quality and coverage work, but does not establish that C is a new independent physical property or a useful additional predictor beyond rho and M.

No input CSV or calculation engine was modified. This report was generated as a separate exploratory analysis from the current CSV values; it was not run through GitHub Actions.
