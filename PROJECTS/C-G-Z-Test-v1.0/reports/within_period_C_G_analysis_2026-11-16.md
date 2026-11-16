# Within-period and atomic-number control analysis: C versus G

**Date:** 2026-11-16  
**Dataset:** `PROJECTS/C-G-Z-Test-v1.0/data/C_G_Z_unified_accountant_input_118.csv`  
**Eligible sample:** 60 rows with numeric active G, density, and atomic mass. C recomputed using the approved C-G-Z equations; no clipping or imputation.

## Purpose

Check whether the observed C-G association is only a between-period / atomic-number trend, or whether it is also visible among elements within the same period.

## Method

- Periods assigned by standard atomic-number intervals: 1–2, 3–10, 11–18, 19–36, 37–54, 55–86, 87–118.
- Within each period, calculate Pearson and Spearman correlations between C and active G.
- As pooled diagnostics, calculate Pearson correlation between OLS residuals after separately regressing C and G on:
  1. atomic number Z;
  2. period fixed effects (period indicators);
  3. Z plus period fixed effects.
- These are descriptive linear controls, not causal estimates. Small period samples are not treated as reliable inferential tests.

## Within-period results

| Period | n | Elements with active G | Pearson C-G | Spearman C-G |
|---|---:|---|---:|---:|
| 1 | 0 | — | — | — |
| 2 | 2 | Li, Be | — | — |
| 3 | 3 | Na, Mg, Al | 0.9949 | 1.0000 |
| 4 | 12 | K through Se (available subset) | 0.7277 | 0.8722 |
| 5 | 13 | Sr through Te (available subset) | 0.5582 | 0.7923 |
| 6 | 27 | Ba through Bi (available subset) | 0.7410 | 0.7824 |
| 7 | 3 | Th, U, Pu | 0.5783 | 0.5000 |

The period-3 and period-7 results have only three observations each and should not be interpreted as stable evidence. Period 2 has only two observations, so no correlation is reported.

## Pooled linear-control diagnostics

| Control variables removed from both C and G | Pearson correlation of residuals |
|---|---:|
| None (raw C and G) | 0.6623 |
| Atomic number Z | 0.6565 |
| Period fixed effects | 0.6584 |
| Z + period fixed effects | 0.6290 |

The association remains positive after these simple linear controls, although it is weaker after controlling jointly for Z and period. This suggests that the raw association is not explained solely by a linear atomic-number trend or by differences in period means.

## Interpretation and limits

1. Positive C-G association is visible within the adequately populated periods 4, 5, and 6; it is not merely an artifact of comparing period averages.
2. Strength varies by period: period 5 is weaker than periods 4 and 6. This is compatible with heterogeneity across periodic structure and does not establish one universal relationship.
3. The period-3 and period-7 values are too small to support stable conclusions.
4. This analysis does **not** establish that C is an independent physical property. C remains a deterministic function of density and atomic mass. The previous repeated cross-validation found no predictive improvement from adding C to rho and M.
5. The active G column has the provenance and measurement-condition limitations documented in the existing source audit. Uneven coverage and possible source/condition inconsistencies remain important constraints.
6. The CSV's `Family` field only distinguishes a small number of labels (notably Ln and An); it does not provide a complete element-family classification. Therefore, this report uses periods rather than pretending that the current family labels support a full family-by-family test.

## Conclusion

The C-G association persists within periods and under simple linear controls for Z and period. This is a useful descriptive observation, but it does not override the failed out-of-sample feature-addition test and does not show that C contributes information independent of rho and M. The next stronger test would require better-documented, condition-matched G measurements and a pre-specified analysis that accounts for element-family structure without overfitting the 60-row sample.

## Reproducibility

- Eligible rows: 60
- C formula: `C = 90 + 70 * (rho_n - V_n)`
- `rho_n = (rho - 1.74) / 20.85`
- `Vm = M / rho`
- `V_n = (Vm - 7.10) / 11.17`
- Source CSV blob SHA at retrieval: `dc2e80fa743c1f744bd4683f61b8c9111efb117c`
- Analysis performed directly on retrieved CSV; no GitHub Actions run was triggered.
- No input, engine, or workflow files were modified.
