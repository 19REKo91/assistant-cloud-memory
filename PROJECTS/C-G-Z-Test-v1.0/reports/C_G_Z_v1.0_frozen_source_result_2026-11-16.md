# C-G-Z Test v1.0 — Frozen-Source Result and Decision
Date: 2026-11-16
Status: Current analysis baseline; source policy frozen by project owner

## 1. Frozen source policy

For the current C-G-Z Test v1.0 analysis, use only the active shear-modulus column `G_active_GPa` as supplied from PeriodicTable.com / Wolfram ElementData.

- Do not merge other websites or legacy compilations into the active G column.
- Do not replace a value because another website reports a different number.
- Preserve missing values as missing; do not impute.
- Preserve the existing input CSV unchanged.
- Keep `G_legacy_input_GPa` only as historical/audit information; it is not used in the analysis.
- External disagreements may be noted for a later, separately authorized review, but they do not trigger recalculation or dataset changes now.

This is a decision to keep one consistent dataset for this test. It is not a claim that every source value is experimentally verified or measured under identical conditions.

## 2. Fixed equations and calibration

```
Vm = M / rho
rho_n = (rho - 1.74) / (22.59 - 1.74)
V_n = (Vm - 7.10) / (18.27 - 7.10)
C = 90 + 70 * (rho_n - V_n)
```

Constants remain unchanged:
- RHO_MIN = 1.74
- RHO_MAX = 22.59
- VM_MIN = 7.10
- VM_MAX = 18.27

No clipping is applied. Out-of-range observations remain in the calculations and are flagged separately.

## 3. Dataset coverage and calculation validation

From the unified 118-element input and GitHub Actions run #1/#2:

- Total element rows: 118.
- Rows with recalculable M and rho: 117.
- Rows not recalculable: 1 (rho unavailable).
- Active G values: 60.
- Missing active G values: 58.
- Legacy G values were not used.
- Calculation agreement against stored derived columns passed at tolerance 1e-8:
  - Vm maximum absolute difference: approximately 4.86e-11.
  - rho_n maximum absolute difference: approximately 4.99e-11.
  - V_n maximum absolute difference: approximately 4.99e-11.
  - C maximum absolute difference: approximately 5.00e-9.

The input is a compilation with mixed M/rho provenance, not a single harmonized laboratory dataset.

## 4. Main C–G association

Using the 60 rows with active G:

| Statistic | Result |
|---|---:|
| Spearman correlation, C vs G | 0.8390818 |
| Spearman p-value | 5.7087e-17 |
| Pearson correlation, C vs G | 0.6623105 |
| Pearson p-value | 8.2437e-9 |
| n | 60 |

For the subset whose rho and Vm both fall inside the stated calibration intervals, the earlier run reported n = 30 and Spearman(C,G) = 0.7909.

Interpretation: the fixed dataset shows a strong positive rank association between calculated C and active G. This is an association within the available 60 rows; it does not establish causation or universal validity.

## 5. Predictive comparison (LOOCV)

Leave-one-out cross-validation from run #1:

| Model | n=60 RMSE (GPa) |
|---|---:|
| C alone | 42.44 |
| rho alone | 44.11 |
| Vm alone | 45.78 |
| Z alone | 54.86 |
| rho + M | 35.3108 |
| rho + M + C (exploratory) | 36.0301 |

Within the both-ranges subset (n=30), reported RMSE values:
- C: 46.37 GPa
- rho: 53.45 GPa
- Vm: 54.45 GPa
- Z: 64.68 GPa
- rho + M: 43.4551 GPa
- rho + M + C: 43.8257 GPa

Interpretation: C alone performed better than rho, Vm, or Z alone in this internal validation, but the rho+M model performed better than C alone. Adding C to rho+M did not improve performance; RMSE became slightly worse. Since C is calculated deterministically from rho and M, it is not independent input evidence.

LOOCV is internal validation only, not external validation.

## 6. Sensitivity scenarios already completed

The second GitHub Actions run tested alternatives without modifying the input CSV:

| Scenario | n | Spearman(C,G) | Pearson(C,G) |
|---|---:|---:|---:|
| Current active values | 60 | 0.8390818 | 0.6623105 |
| Mo = 120 GPa (scenario only) | 60 | 0.8494685 | 0.6764888 |
| Exclude Mo | 59 | 0.8474388 | 0.6731132 |
| Co = 75 GPa (scenario only) | 60 | 0.8390979 | 0.6621267 |
| Ta = 69 GPa (scenario only) | 60 | 0.8390818 | 0.6627341 |
| Yb = 9.9 GPa (scenario only) | 60 | 0.8390818 | 0.6623292 |
| All four alternatives together | 60 | 0.8494845 | 0.6767490 |

These were sensitivity checks only. The canonical active values remain unchanged. Under the now-frozen source policy, these scenarios are historical checks and are not a reason to repeat the test whenever another website differs.

## 7. Final assessment for this version

**Result: positive association observed; predictive and scientific validation remains limited.**

What the test supports:
1. The calculation engine reproduces the stored derived values within the specified tolerance.
2. In the fixed 60-row active-G dataset, C and G have a strong positive rank association.
3. The rank association remained strong under the limited value-change scenarios already tested.

What the test does not establish:
1. That C causes or physically determines G.
2. That C adds independent information beyond M and rho.
3. That the association generalizes to all 118 elements, because G is missing for 58 elements.
4. That all G values share harmonized phase, temperature, pressure, orientation, purity, and measurement uncertainty.
5. External predictive validity.

## 8. Reproducibility record

- Repository: `19REKo91/assistant-cloud-memory`
- Input: `PROJECTS/C-G-Z-Test-v1.0/data/C_G_Z_unified_accountant_input_118.csv`
- Engine: `PROJECTS/C-G-Z-Test-v1.0/main.py`
- Workflow: `.github/workflows/c-g-z-test.yml`
- Run #1: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/43854332627
- Run #2: https://github.com/19REKo91/assistant-cloud-memory/actions/runs/43855030020
- G source coverage audit (historical source documentation): `PROJECTS/C-G-Z-Test-v1.0/source-audit/G_active_60_source_coverage_audit_2026-11-16.md`

No input data, equation, calibration bound, or active G value was changed in preparing this decision record.
