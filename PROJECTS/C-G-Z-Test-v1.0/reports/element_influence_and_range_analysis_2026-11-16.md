# C-G-Z Test v1.0 — Range, Period and Element-Influence Analysis
Date: 2026-11-16

## Scope
This is a secondary analysis of the existing input file:
`PROJECTS/C-G-Z-Test-v1.0/data/C_G_Z_unified_accountant_input_118.csv`

Input SHA-256 recorded by the successful GitHub Actions run:
`45acc80346a8b486997a5ff24277da5c96e933a0378b1543e4c9ba5256edc72f`

No input values, formulas, calibration limits, or source fields were changed. The 60 active G rows were used. This is an analysis of the current dataset, not an independent replication or external validation.

## 1. Overall association
- n = 60
- Spearman(C,G) = 0.8390817638
- Pearson(C,G) = 0.6623105169

These reproduce the GitHub Actions log.

## 2. Calibration-range coverage
Among the 60 active-G rows:
- Density within calibration range: 55; outside: 5.
- Molar volume within calibration range: 32; outside: 28.
- Both density and molar volume within range: 30.
- At least one of the two inputs outside range: 30.

The split by range status is:
| Subset | n | Spearman | Pearson | C minimum | C maximum |
|---|---:|---:|---:|---:|---:|
| Both inputs inside range | 30 | 0.7908738 | 0.7361936 | 36.9534 | 151.7217 |
| Density inside, Vm outside | 25 | 0.7880658 | 0.7535565 | -98.7357 | 117.3005 |
| Density outside, Vm inside | 2 | Not calculated (n<3) | Not calculated (n<3) | — | — |
| Both inputs outside | 3 | 0.5000000 | 0.7006288 | -152.6981 | -16.9338 |

The 30 rows outside at least one calibration range remain in the overall analysis because the protocol prohibits clipping or silently deleting them. However, their presence means the overall correlation includes extrapolated C values. The both-inside subset is the cleanest in-range check available in this dataset, but still only has n=30.

## 3. Period distribution
Active-G sample counts by period:
| Period | n |
|---|---:|
| 1 | 0 |
| 2 | 2 |
| 3 | 3 |
| 4 | 12 |
| 5 | 13 |
| 6 | 27 |
| 7 | 3 |

Within-period correlations:
| Period | n | Spearman | Pearson |
|---|---:|---:|---:|
| 2 | 2 | 1.0000 | 1.0000 |
| 3 | 3 | 1.0000 | 0.9949 |
| 4 | 12 | 0.8722 | 0.7277 |
| 5 | 13 | 0.7923 | 0.5582 |
| 6 | 27 | 0.7824 | 0.7410 |
| 7 | 3 | 0.5000 | 0.5783 |

Periods 2, 3 and 7 have too few observations for a stable inference. The total sample is also uneven: period 6 contributes 27/60 rows. Do not interpret these as established periodic laws.

## 4. Single-row deletion influence
Deleting one row at a time and recalculating the overall correlation:
- Largest increase in Spearman occurred after deleting Tl: 0.8601327 (from 0.8390818).
- Deleting Pb gave 0.8562743.
- Deleting Li gave 0.8556313.
- Largest decrease among the listed influential rows occurred after deleting K, Os or Ir: 0.8307562.
- Pearson was most sensitive to K: deleting K raised Pearson from 0.6623105 to 0.6925356.
- Deleting Au raised Pearson to 0.6781216; deleting Re lowered it to 0.6485970.

These are influence diagnostics only. They do not establish that any element's source value is wrong, and no element was removed from the canonical dataset.

## 5. Leave-one-out prediction errors
The existing accountant's LOOCV results:
| Model | RMSE (GPa) | MAE (GPa) |
|---|---:|---:|
| C alone | 42.442638 | 30.866024 |
| rho + M | 35.310794 | 24.933633 |
| rho + M + C | 36.030052 | 25.469130 |

The C-only model's largest absolute leave-one-out errors were:
| Element | Actual G (GPa) | Predicted G (GPa) | Error (GPa) |
|---|---:|---:|---:|
| Os | 222.0 | 93.5687 | -128.4313 |
| Ir | 210.0 | 93.8993 | -116.1007 |
| K | 1.3 | -100.7569 | -102.0569 |
| Ru | 173.0 | 78.3934 | -94.6066 |
| Re | 178.0 | 91.7682 | -86.2318 |
| W | 161.0 | 86.8866 | -74.1134 |
| Rh | 150.0 | 78.8161 | -71.1839 |
| Au | 27.0 | 90.1134 | 63.1134 |

This demonstrates that a strong rank correlation does not translate into accurate element-level prediction from C alone.

## 6. Conclusions
1. The positive association between C and active G is strong in rank terms in the 60-row available sample.
2. It remains positive in the 30-row both-in-range subset (Spearman 0.7909).
3. The total association is not attributable to one single row; single-row deletion changes Spearman only within the approximate 0.8308–0.8601 range among the most influential examples.
4. C alone predicts G less accurately under LOOCV than rho+M. Adding C to rho+M does not improve the reported LOOCV error.
5. C is deterministically derived from density and molar volume (and Vm from M/rho), so this association is not independent evidence of a new physical variable.
6. G source/measurement conditions are not harmonized, active G coverage is incomplete, and missingness may bias the sample. No causal or universal periodic conclusion is justified.

## Status
Secondary analysis completed from the current CSV. No source data or calculation engine was modified. Further inference should wait for better condition-harmonized, traceable G measurements and a pre-specified validation design.
