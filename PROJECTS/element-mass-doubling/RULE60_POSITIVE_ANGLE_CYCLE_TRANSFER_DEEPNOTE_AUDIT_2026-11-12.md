# Corrected 60-degree cycle transfer and Deepnote plot — 2026-11-12

## Correction
The prior plotting pass incorrectly treated Rule 60 only as adding cycles to a negative theta3 while leaving a large positive theta2 untouched. GitHub contains a separate documented cycle-transfer rule:

```
A' = A
B' = B - 60n
C' = C + 60n
```

Reference:
`PROJECTS/triangle-framework/rules/60-degree-angle-cycle.md`

The same n is used on B and C. The operation preserves the sum of the three angles. It is not the 360-degree dosage rule.

## Deepnote work
Notebook: Triangle Framework 4.0 — Natural Elements G Map
Notebook URL:
https://deepnote.com/workspace/xyzreko-a2ba0423-4e67-4be4-801e-013b6dca1755/project/Triangle-Framework-40-Natural-Elements-G-Map-96b6e06e-e874-4b07-bc6f-7cfa8637f0c9/notebook/Triangle-Framework-40-Natural-Elements-G-Map-d8e0d6d9c9b7487aad8f94047a406537?utm_content=96b6e06e-e874-4b07-bc6f-7cfa8637f0c9

Added section: "تصحيح تطبيق دورة 60° على زاوية B الموجبة الكبيرة".
Successful run: `840554cd-7043-40d6-a3e8-a8948900fb73`.

Generated outputs in the Deepnote project:
- `elements_118_rule60_cycle_transfer_overlay_2026-11-12.png`
- `elements_118_rule60_cycle_transfer_overlay_2026-11-12.svg`
- `elements_118_rule60_cycle_transfer_audit_2026-11-12.csv`

## Results on the currently archived derived CSV
- Total rows: 118
- Existing recorded valid geometries with n=0: 76
- Additional rows passing B−60n / C+60n, positive-angle, and 180° sum checks: 21
- Total rows with a valid Euclidean triangle in this pass: 97
- Cycle rows still unresolved: 11
- Excluded rows: 7

## Important unresolved source conflicts
The following 11 rows do not pass the checks using the archived n and reverse-reconstructed theta3:
H, He, N, O, F, Ne, Ar, Kr, In, Sn, Xe.

Their calculated transformed values are retained in the audit table; they are not silently repaired. Examples:
- H: A=85.8, B'=88.0, C'=5.8; sum=179.6°.
- He: A=85.8, B'=48.0, C'=47.6; sum=181.4°.
- Ar: A=85.8, B'=60.0, C'=47.0; sum=192.8°.
- Kr: B'=-40.0°; invalid.
- In: A=61.3, B'=3.9, C'=54.8; sum=120°.
- Sn: A=61.3, B'=7.3, C'=51.4; sum=120°.
- Xe: B'=260°; invalid.

## Source caveat
The input was copied from:
`PROJECTS/element-mass-doubling/ELEMENTS_118_RESCUE_DOSAGE_GEOMETRY_DERIVED_2026-11-12.csv`.
Its `theta3_raw_reverse_estimate` is reconstructed backwards from adopted theta3 and archived n, not an independently supplied raw measurement. The repository's angle-table audit says the latest complete user table is authoritative, while the historical CSV is not a substitute. Therefore the 97/11 result is an audit of the currently archived derived CSV, not final approval of all 118 geometries. The 11 conflicting rows must be reconciled against the exact latest user table/source rows before being changed.
