# Geometric Concentration Pilot: Gas vs Solid
Date: 2026-11-22
Status: Exploratory only; not a pressure measurement and not part of the frozen reference framework.

## Question
Does the existing phase-separated triangle dataset show a geometric pattern consistent with the hypothesis that gas effects are more distributed while solid effects are more localized?

## Input
Repository file:
`ELEMENTS_118_PHASE_SEPARATED_RANK_TRIANGLE_TEST_2026-11-22.csv`

Included cohorts:
- Gas: 11 recorded gas elements.
- Solid: 96 recorded solid elements.

Excluded:
- Liquids (n=2), expected solids (n=8), expected gas singleton Og (n=1), and rows without valid geometry.

## Geometric proxies
For each triangle, using side lengths a, b, c and perimeter P=a+b+c:

1. Side-share concentration (Herfindahl proxy):
   `H = (a/P)^2 + (b/P)^2 + (c/P)^2`
   Higher H means side length is more unevenly distributed among the three sides. It does **not** measure physical pressure concentration.

2. Incenter-to-centroid displacement:
   Calculate the triangle centroid G and incenter I, then use `|I-G|/c` to remove overall scale dependence. A larger value means the incenter is more eccentric relative to the centroid; it does not establish a pressure focus.

3. Relative inradius:
   `r/c`, where `r=2*Area/P`. This is a dimensionless measure of the inscribed-circle size relative to the fixed base.

4. Largest side share and longest/shortest side ratio are reported as supporting shape descriptors.

The incenter is computed from the side-length-weighted vertex average. The centroid is the arithmetic average of the three vertices. The base is c=3 in the source dataset.

## Results

| Metric | Gas mean | Gas median | Solid mean | Solid median |
|---|---:|---:|---:|---:|
| Side-share concentration H | 0.369712 | 0.370283 | 0.360458 | 0.355893 |
| Incenter-centroid offset / c | 0.121822 | 0.135849 | 0.103642 | 0.084156 |
| Relative inradius r/c | 0.177001 | 0.165124 | 0.196364 | 0.193009 |
| Largest side share | 0.429966 | 0.439871 | 0.424355 | 0.415975 |
| Longest / shortest side | 2.568582 | 2.440268 | 2.112860 | 1.912279 |

Ranges:

| Metric | Gas min–max | Solid min–max |
|---|---:|---:|
| H | 0.336264–0.429283 | 0.333485–0.428004 |
| Incenter-centroid offset / c | 0.048671–0.249954 | 0.008579–0.388817 |
| Relative inradius r/c | 0.066507–0.324703 | 0.062538–0.406023 |
| Largest side share | 0.355433–0.487869 | 0.343355–0.490961 |
| Longest / shortest side | 1.229297–5.758770 | 1.047555–5.690331 |

## Interpretation
- The gas cohort has slightly higher mean side-share concentration and a somewhat larger mean incenter-centroid offset.
- The gas cohort also has a smaller mean relative inradius and a larger mean longest/shortest side ratio.
- These differences are modest and the ranges overlap substantially. They do not show a clean separation between gases and solids.
- In particular, the incenter-centroid offset is not a physical pressure-centre measurement. The side-share concentration is a shape statistic, not a stress or pressure field.

## Critical circularity / limitation
The source triangle angles were constructed using both density rank and molar-volume rank; specifically, angle B depends on the molar-volume rank. Therefore, this pilot is descriptive of the existing constructed geometry, not an independent test of a relationship between geometry and molar volume, and still less a direct test of pressure distribution.

The source dataset contains no matched pressure-field measurements, no stress tensors, and no pressure-dependent states for the same material. A static gas-versus-solid comparison cannot establish how pressure redistributes.

## Next valid test
Use measured states for the same gas and/or solid across multiple controlled pressures (and recorded temperatures). Define a pressure-distribution statistic from measured or physically modelled pressure/stress fields independently of the triangle. Only then compare that independent statistic with triangle geometry generated without using pressure or molar volume as an input. Keep gas, liquid, solid, and predicted phase cohorts separate.

## Conclusion
This pilot does not confirm the proposed pressure-distribution rule. It shows small geometric differences in the expected direction for some proxies, but with substantial overlap and a circular input dependency. The hypothesis remains open and requires independent pressure data.
