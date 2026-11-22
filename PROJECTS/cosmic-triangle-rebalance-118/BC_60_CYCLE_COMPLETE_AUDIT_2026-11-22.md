# B/C 60° cycle — full 118-element execution audit

**Status:** Independent experimental execution; the frozen reference framework was not modified.

## Input and rule
- Input: ELEMENTS_118_BC_60_CYCLE_TEST_2026-11-22.csv; 118 rows and 118 unique atomic numbers.
- Canonical rule: A'=A, B'=B-60n, C'=C+60n, with the same integer n applied to B and C.
- A is never changed.
- The operation preserves A+B+C.
- This run selects the feasible integer n with the smallest absolute value. This is an explicit operational selection policy for this run, not an amendment to the canonical rule document.
- The SVG uses AB=1 only as a normalized drawing scale to display angle-defined shape. No physical side lengths are asserted or exported.

## Results
- Input rows: 118
- Valid angle-defined triangles: 114
- Invalid rows retained: 4
- Valid with n=0: 82
- Valid with positive n: 29
- Valid with negative n: 3
- Maximum absolute final angle-sum error among valid triangles: 1.01834984889e-09°

## Invalid rows
- Bh (Z=107): INVALID_A_NONPOSITIVE; A remains -5.477218225°.
- Hs (Z=108): INVALID_A_NONPOSITIVE; A remains -10.177458034°.
- Mt (Z=109): INVALID_A_NONPOSITIVE; A remains -8.834532374°.
- Ds (Z=110): INVALID_A_NONPOSITIVE; A remains -6.148681055°.

## Validation
- Every input element is retained in the output CSV and SVG.
- A is copied unchanged.
- B and C use the same integer n with opposite 60° adjustments.
- The sum is conserved.
- A triangle is drawn only when all three final angles are positive and the raw angle sum is 180° within tolerance.
- Invalid entries are explicitly marked; no angle is fabricated to force a triangle.

## Outputs
- ELEMENTS_118_BC_60_CYCLE_COMPLETE_2026-11-22.csv
- ELEMENTS_118_BC_60_CYCLE_SHAPES_2026-11-22.svg
- BC_60_CYCLE_COMPLETE_AUDIT_2026-11-22.md
