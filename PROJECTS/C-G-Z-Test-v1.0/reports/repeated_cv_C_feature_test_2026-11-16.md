# Repeated cross-validation: C feature versus rho and M

**Date:** 2026-11-16  
**Dataset:** `PROJECTS/C-G-Z-Test-v1.0/data/C_G_Z_unified_accountant_input_118.csv`  
**Scope:** the 60 rows with numeric `G_active_GPa` and numeric `rho` and `M`. No rows were added, imputed, clipped, or removed beyond the rows without active G.

## Question

Does adding the derived variable C improve out-of-sample prediction of G beyond rho and M?

C was recomputed from the approved equations:

- rho_n = (rho - 1.74) / (22.59 - 1.74)
- Vm = M / rho
- V_n = (Vm - 7.10) / (18.27 - 7.10)
- C = 90 + 70 * (rho_n - V_n)

No clipping was applied. C is a deterministic transformation of rho and M, not an independent measurement.

## Method

- Repeated 5-fold cross-validation, 20 repetitions (100 train/test folds total).
- Fixed reproducible pseudo-random seed: 20261116.
- Three ridge-regression feature sets:
  1. Linear baseline: rho, M.
  2. Nonlinear baseline: rho, M, rho², rho×M, M².
  3. Same nonlinear feature set plus C.
- Ridge penalty alpha = 1 for all models.
- Each feature was standardized using only the training fold's mean and standard deviation. Test-fold values used those training-fold parameters.
- Each fold predicted its held-out rows. RMSE and MAE were computed over the pooled out-of-fold predictions within each repetition, then summarized across the 20 repetitions.
- Paired repeat-level RMSE difference is defined as RMSE(poly2 + C) minus RMSE(poly2). Positive values mean adding C made prediction worse.

This was a direct local calculation from the retrieved repository CSV. It was **not** a GitHub Actions run.

## Results

| Model | Mean RMSE (GPa) | SD across repeats | Mean MAE (GPa) | SD across repeats |
|---|---:|---:|---:|---:|
| Linear: rho + M | 35.2960 | 0.9217 | 24.0046 | 0.6004 |
| Polynomial degree 2: rho + M | 35.8112 | 0.9106 | 24.3657 | 0.7281 |
| Polynomial degree 2: rho + M + C | 35.9606 | 0.9856 | 24.7633 | 0.8157 |

### Paired comparison: polynomial + C versus polynomial baseline

- Mean RMSE difference: **+0.1494 GPa** (C model worse).
- Median repeat-level difference: +0.1153 GPa.
- Empirical 2.5th–97.5th percentile range across the 20 repeats: -0.2260 to +0.7409 GPa.
- C model had higher RMSE in 12/20 repeats and lower RMSE in 8/20 repeats.

The percentile range describes variation across these repeated random partitions; it is **not** a formal confidence interval, because the repeats reuse the same 60 observations.

## Interpretation

In this specified cross-validation experiment, adding C did not improve prediction. Both nonlinear models were also slightly worse than the simple linear rho + M baseline. The result therefore provides no evidence that C improves out-of-sample prediction of G beyond the supplied rho and M in this dataset.

This does not prove that no alternative nonlinear model or a better independently sourced dataset could show a benefit. The sample is small (n=60), coverage is uneven, and the active G values have the source/measurement limitations documented in the existing source-audit report.

Most importantly, C is computed deterministically from rho and M. It contains no new raw measurement information. It can only help as a feature representation for a particular model class; here, with the stated degree-2 ridge model and validation design, it did not help.

## Reproducibility record

- Seed: 20261116
- Repeats: 20
- Folds per repeat: 5
- Ridge alpha: 1
- Eligible rows: 60
- Source CSV blob SHA at retrieval: `dc2e80fa743c1f744bd4683f61b8c9111efb117c`
- No source CSV, engine, or workflow files were modified.
