# Deepnote — 118-element triangle plots and geometry QA (2026-11-12)

## Notebook
- Project: **Triangle Framework 4.0 — Natural Elements G Map**
- Notebook: [Open in Deepnote](https://deepnote.com/workspace/xyzreko-a2ba0423-4e67-4be4-801e-013b6dca1755/project/Triangle-Framework-40-Natural-Elements-G-Map-96b6e06e-e874-4b07-bc6f-7cfa8637f0c9/notebook/Triangle-Framework-40-Natural-Elements-G-Map-d8e0d6d9c9b7487aad8f94047a406537?utm_content=96b6e06e-e874-4b07-bc6f-7cfa8637f0c9)
- Successful final run: `2935d74e-69ce-4011-a393-d4cfb4beb20e`
- Added notebook section: “تدقيق ورسم العناصر الـ118 — مصدر 2026-11-12”

## Input
Copied verbatim from:
`PROJECTS/element-mass-doubling/ELEMENTS_118_RESCUE_DOSAGE_GEOMETRY_DERIVED_2026-11-12.csv`

Deepnote copy:
`element_triangle_map_2026_11_12/elements_118_rescue_dosage_geometry_derived.csv`

The 118 source rows and atomic-number order 1–118 were asserted in the notebook. Source angles were not recomputed, reduced modulo 360, or silently altered.

## Outputs generated in Deepnote project root
- `elements_118_triangles_by_atomic_number_2026-11-12.png` — 118 individual panels in atomic-number order; only source rows marked `euclidean_planar_valid` receive a triangle.
- `elements_118_mass_position_triangle_overlay_2026-11-12.png`
- `elements_118_mass_position_triangle_overlay_2026-11-12.svg`
- `elements_118_geometry_quality_checks_2026-11-12.csv`

## Final run results
- Source rows: 118
- Recorded valid Euclidean triangle geometries: 76
- Classified/non-excluded rows without valid geometry: 35
- Excluded rows: 7
- Maximum midpoint-coordinate verification error: `4.965068306494546e-16`
- Maximum spread among the three perpendicular distances from stored G to the sides: `0.0006911252894682418`

## Interpretation limits
- G is the incenter (intersection of internal angle bisectors), not the centroid.
- The triangle panel uses the stored geometry with AB=3.
- The mass-position overlay keeps each original point at (Z, mass_position_percent); the triangle is a uniformly reduced display glyph centered at that point.
- The 35 rows without valid geometry and the 7 excluded rows are explicitly marked; no triangle was fabricated for them.
- The small nonzero inradius spread is retained as a QA finding. It is not concealed or called exact; it may reflect rounding in the stored coordinates and should be reviewed against the source precision.
- This notebook section is an addition; historical Framework 4.0 cells were left intact.
- The source CSV is a derived/mixed-source file; successful plotting does not independently validate every source angle or classification.
