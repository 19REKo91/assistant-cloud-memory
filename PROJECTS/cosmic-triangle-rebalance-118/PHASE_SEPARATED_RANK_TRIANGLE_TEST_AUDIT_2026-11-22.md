# Phase-Separated Rank Triangle Test — 2026-11-22

## Purpose and status
Independent exploratory test of whether the extreme molar-volume scale in gases changes the triangle map when density and molar volume are ranked within each exact listed phase cohort. This is a separate experiment only. It does not modify the frozen 6.2.1 reference, the legacy B/C 60-degree cycle, or any source values.

## Input
- Source CSV: `PROJECTS/cosmic-triangle-rebalance-118/ELEMENTS_118_BC_60_CYCLE_TEST_2026-11-22.csv`
- 118 element rows.
- Density and molar volume values are reused exactly as recorded in the input; (V_m=M/\rho) is not recalculated here.
- Phase labels are kept exact; "Expected to be a Solid" and "Expected to be a Gas" are not silently merged into measured Solid/Gas cohorts.

## Method
For each exact phase cohort, independently calculate midrank percentiles:
- (x=\operatorname{midrank}(\rho)\) scaled to [0,1].
- (y=\operatorname{midrank}(V_m)\) scaled to [0,1].
- Ties receive their average rank.
- A one-row cohort has no meaningful rank and is left without a triangle.

Candidate mapping:
- (A=80-70x)
- (B=10+70y)
- (C=180-A-B)
- Base (c=3); sides are calculated by the sine rule.
- Incenter is calculated from the three vertices weighted by opposite side lengths.

This is a rank-based remapping, not a physical equation for thermal expansion or gas volume. The positive angle bounds are built into the mapping, so triangle validity alone is not evidence that the mapping is physically correct. No minimum-angle or elongation filter is applied.

## Results
- **Gas**: n=11; rankable=11; Vm range=11029.869322–22817.839671 cm³/mol; legacy-center comparisons=11; mean shift=0.989933840; median=0.936624676; max=1.950466284.
- **Solid**: n=96; rankable=96; Vm range=4.561181–76.903355 cm³/mol; legacy-center comparisons=90; mean shift=0.269689416; median=0.294517565; max=0.581367274.
- **Liquid**: n=2; rankable=2; Vm range=14.821629–25.691318 cm³/mol; legacy-center comparisons=2; mean shift=0.423612058; median=0.230048694; max=0.617175422.
- **Expected to be a Solid**: n=8; rankable=8; Vm range=10.298029–40.862639 cm³/mol; legacy-center comparisons=7; mean shift=0.825668646; median=0.778031039; max=1.240275374.
- **Expected to be a Gas**: n=1; rankable=0; Vm range=51.792281–51.792281 cm³/mol; legacy-center comparisons=0; mean shift=NA; median=NA; max=NA.

- Rankable rows: 117/118.
- No-rank rows: Og. Og is the sole "Expected to be a Gas" row; assigning it a percentile in a one-element cohort would manufacture information.
- Legacy center comparisons: 110; mean shift=0.379892949; median=0.309484718; p90=0.757450832; max=1.950466284.
- The 11 listed gases have (V_m) between 11029.869322 and 22817.839671 cm³/mol. This cohort-specific rank removes the cross-phase scale domination in the angle input, but it does not mean the gas expansion itself has been measured by triangle elongation.
- The two liquids form a cohort of only two. Their ranks necessarily become endpoints (0 and 1); resulting angles are an extreme two-point ordering artifact, not a stable liquid-phase model.
- The eight "Expected to be a Solid" rows are kept separate; their values are predicted/estimated and the small cohort makes the ranks coarse. Do not interpret their resulting shapes as measured solid-state behavior.
- Og is not ranked because its phase is only "Expected to be a Gas" and cohort size is one; its density is estimated/predicted.

## Interpretation
The test supports a narrower conclusion: the legacy global (V_m) normalization gives gases values far outside the solid-derived range, and phase-separated ranks substantially change gas triangle centers. It does **not** establish that the geometric elongation is proportional to physical expansion. The liquid result is not robust because n=2. A stronger next test needs phase-consistent density measurements with documented temperature and pressure, and more than two liquid observations (or a different independent liquid dataset).

## Integrity checks
- 118 input rows retained, in atomic-number order within each exact phase cohort as present in source.
- 117 rows received a phase rank triangle; one singleton cohort (Og) is intentionally unranked.
- No source input values overwritten; no 6.2.1 reference files changed.
- Legacy comparison uses the previously stored B/C-cycle incenter only when its original final angles are positive and sum to 180 degrees; unavailable comparisons remain NA.
- This report does not claim a physical validation or select a final normalization method.
