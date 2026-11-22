# G Map placement audit — 118 elements

**Purpose:** Reposition the existing B/C-cycle triangles into the archived G Map presentation style. This is a display-only derivative; the source angle records and triangle angle geometry are unchanged.

## Source and invariants
- Input: ELEMENTS_118_BC_60_CYCLE_COMPLETE_2026-11-22.csv
- Input rows / unique Z: 118 / 118
- Final angle fields A_final, B_final, C_final are read as-is.
- Cycle index n_selected and Status are not modified.
- Geometric base used for incenter calculation: AB=3.
- Uniform display glyph scale: 0.05; all three coordinates of every triangle are multiplied by the same factor before translation. This preserves each triangle's shape.
- Placement coordinate: (Gx, Gy) = (incenter x-coordinate, inradius), matching the archived G Map axes.
- No physical side length is inferred from the display glyph size.

## Results
- Input elements: 118
- Placed triangles: 114
- Retained without triangle: 4
- Invalid elements: Bh, Hs, Mt, Ds
- Gx range: 0.301080245 to 2.728424985
- Inradius range: 0.093449368 to 1.435966251

## Outputs
- ELEMENTS_118_BC_60_CYCLE_G_MAP_2026-11-22.svg
- ELEMENTS_118_BC_60_CYCLE_G_MAP_2026-11-22.png
- BC_60_CYCLE_G_MAP_PLACEMENT_AUDIT_2026-11-22.md

The archived reference image is used for layout/axes/presentation only. Its historical element coordinates are not copied onto the new triangles; every new position is computed from that element's unchanged current triangle geometry.
