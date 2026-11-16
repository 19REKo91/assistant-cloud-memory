# C-G-Z v1.0 — Partial Association Check
Date: 2026-11-16

## Scope and method
Input: `PROJECTS/C-G-Z-Test-v1.0/data/C_G_Z_unified_accountant_input_118.csv`
Only the 60 rows with active numeric G were used. No input, source, formula, or calibration limit was changed.

For a linear partial-association diagnostic, ordinary least-squares regressions were fitted:
1. C ~ intercept + density + atomic mass
2. G ~ intercept + density + atomic mass

Pearson and Spearman correlations were then calculated between the two sets of residuals. This tests whether C and G retain a linear residual association after removing their separate linear associations with density and atomic mass. It is not a causal test and does not fully control nonlinear functions.

## Results
| Diagnostic | Result |
|---|---:|
| Rows | 60 |
| Pearson correlation of residuals | -0.024942 |
| Spearman correlation of residuals | -0.137538 |

The linear residual association is effectively zero for Pearson and weakly negative for Spearman. This differs sharply from the unadjusted correlations (Spearman 0.839082; Pearson 0.662311).

## Both-inputs-within-calibration subset
For the 30 rows where density and molar volume are both inside the declared calibration limits, the residual Pearson correlation was -0.184055.

## Period subsets
Residual Pearson correlations (small samples; descriptive only):
| Period | n | Residual Pearson |
|---|---:|---:|
| 4 | 12 | 0.261872 |
| 5 | 13 | -0.333429 |
| 6 | 27 | -0.236327 |

## Interpretation
1. The strong raw C-G association largely disappears after linearly controlling for density and atomic mass in this 60-row sample.
2. This provides no evidence that C carries a separate *linear* association with G beyond those two inputs in this dataset.
3. Important mathematical limitation: C is deterministically calculated from normalized density and molar volume, and molar volume is M/density. Therefore C is itself a nonlinear deterministic transformation of density and M. Residualizing only with a linear model does not remove all information encoded by density and M. A flexible nonlinear model or a prespecified physical model would be needed to assess incremental predictive value fairly.
4. The prior LOOCV comparison remains relevant: RMSE was 35.31 GPa for density+mass and 36.03 GPa for density+mass+C. Adding C did not improve that reported linear-model prediction.
5. The available G dataset has incomplete coverage and source-condition limitations already documented in the source audit. Results are sample-specific and do not establish causality or a universal law.

## Conclusion
The unadjusted correlation is strong, but the linear partial association is approximately zero. At present, the data do not support the claim that C adds independent information about G beyond density and atomic mass. This is a bounded conclusion about the current 60-row dataset and the stated linear diagnostic, not proof that no nonlinear relation can exist.
