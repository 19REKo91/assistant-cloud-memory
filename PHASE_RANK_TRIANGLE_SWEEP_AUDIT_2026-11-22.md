# Phase-specific rank prototype — PubChem primary cohorts only
Date: 2026-11-22
Status: exploratory computational output; not a selected final model.

## Input cohort
The prototype includes only PubChem-listed entries labelled exactly Solid (83 elements) or Gas (11 elements), total 94. It excludes liquids (2), secondary-source entries (22), and expected-state labels (9) from this particular run. No element is treated as a calibration anchor.

## Normalization
Within each phase cohort separately, calculate midrank percentiles:
x = midrank(density)/(n-1), y = midrank(V_atom)/(n-1), both in [0,1].
Ranks are empirical and cohort-relative. A solid's x/y is not on the same absolute scale as a gas's x/y. This prototype is intended to inspect geometry response, not claim cross-phase comparability.

## Angle transformation
For each lambda in {0.25, 0.50, 1.00}:
u=2x-1, v=2y-1
wA=exp(lambda*u), wB=exp(lambda*v), wC=exp(-lambda*(u+v))
A=180wA/sum(w), B=180wB/sum(w), C=180wC/sum(w)

## Triangle and point
Set c=1, a=sin(A)/sin(C), b=sin(B)/sin(C). Vertices are A0=(0,0), B0=(1,0), C0=(b cos A,b sin A). The incenter is the side-length-weighted vertex average. It is the internal angle-bisector intersection.

## Results
The CSV contains 94 × 3 = 282 candidate triangles. All angle triples are positive and sum to 180 degrees to floating-point precision. Each element has one triangle per lambda. Incenter coordinates are expressed in the c=1 local coordinate system.

## Interpretation limits
- The cohorts are normalized separately; compare shapes/positions within a phase, not between phases.
- Midrank percentiles depend on cohort membership and will change if rows are added or reclassified.
- Lambda is a sensitivity parameter; none is selected.
- PubChem-listed status does not guarantee a common solid allotrope or row-specific condition.
- No secondary-source or predicted values enter this prototype.
- This does not satisfy the final 118-element chart; it is a controlled intermediate calculation.

## Files
`ELEMENTS_94_PUBCHEM_PHASE_RANK_TRIANGLE_SWEEP_2026-11-22.csv`
