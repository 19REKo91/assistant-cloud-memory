# Incenter and side-midpoint table — recovery checkpoint (2026-11-12)

## Scope
The requested deliverable is one 118-element table containing the incenter (intersection of the three internal angle bisectors) and the three side midpoints M_AB, M_BC, and M_CA for each element with a valid triangle.

## Binding source constraints
- The authoritative current input is the user's 118-row angle table sent on 2026-11-12, with columns: Z, element, θ1, θ2, θ3, n, S_C, B, d(C), status.
- Do not substitute `PROJECTS/triangle-framework/recovery/elements_118.csv`; it is historical and not the user's current table.
- Preserve all 118 original points and axes in `element-mass-position-z1-118.html/.svg`.
- Preserve raw angles; do not silently apply modulo 360, absolute-value sign changes, or alter source values.
- The available current-table verbatim rows are not present in the repository or retrievable from the conversation context in this session. The old CSV is therefore not used to fill the gap.
- Hydrogen's modulo-360 step was documented as a one-case test only; the repository explicitly says not to generalize it to all elements without an approved rule.
- The current workbench's historical CSV-derived triangles are not accepted as replacements for the user's current angle table.

## Geometry convention already implemented for the verified Li case
Set A=(0,0), B=(3,0), c=AB=3. For a valid Euclidean angle triple:
- a=BC=3 sin(θ1)/sin(θ3)
- b=CA=3 sin(θ2)/sin(θ3)
- C=(b cos(θ1), b sin(θ1))
- G=(a A+b B+c C)/(a+b+c), the incenter (not centroid).
- M_AB=(A+B)/2; M_BC=(B+C)/2; M_CA=(C+A)/2.

## Verified result currently sourced from the user's 2026-11-12 table
Li (Z=3):
- Angles: θ1=84.05°, θ2=46.95°, θ3=49.00°; sum=180.00°.
- A=(0,0), B=(3,0), C=(0.3011123678, 2.8891437102).
- Incenter G=(0.9755841031, 0.8791909634).
- M_AB=(1.5000000000, 0.0000000000).
- M_BC=(1.6505561839, 1.4445718551).
- M_CA=(0.1505561839, 1.4445718551).

## Current completion state
- Verified current-user-source geometry rows: 1 (Li).
- Remaining current-user-source rows: 117; source rows are not currently recoverable here.
- No all-118 table is claimed complete.
- Next operation once the exact current 118-row table is available: construct only elements whose approved geometry rule yields a valid triangle; calculate G and all three midpoints; retain explicit status/blank markers for anomalous, gas, excluded, or unresolved cases; independently validate incenter-to-side distances and midpoint definitions.
