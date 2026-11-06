# Group C — Acceptance tests for the redesigned TriangleApp engine

These are specification-level requirements. They are not executable against the current
TriangleSolver API until the new data model and solver interfaces are implemented.

## 1. Geometry and input state
1. `inputs` stores exactly what the user entered, including invalid drafts.
2. `lastValidGeometry` stores the most recent valid vertex geometry and derived measurements.
3. `validity` describes current inputs, not the retained previous geometry.
4. Invalid inputs do not overwrite or erase `lastValidGeometry`.
5. The render state marks retained geometry as stale when current inputs are invalid.
6. "Editing" is UI state, not a third geometric validity classification.

## 2. Reference side
7. Any of `a`, `b`, or `c` can be selected as reference.
8. The selected side identity remains stable across editing modes.
9. In angle mode, the selected side and its opposite angle determine scale.
10. Changing reference adopts the current length of the newly selected side.
11. Entering free mode suspends reference enforcement but preserves its identity.
12. Returning to angle mode adopts the then-current length of that same side.
13. Default reference: side opposite the first edited angle; if no angle was edited, the
    longest side; ties resolve in order `a`, then `b`, then `c`.

## 3. Input conversion and editing modes
14. Two positive angles whose sum is below 180 degrees determine the third angle.
15. One edited angle alone does not trigger automatic reconstruction.
16. Two angles plus a positive selected reference side yield one unique triangle.
17. A zero or negative reference side is rejected as a reference.
18. A second locked side is an additional constraint; incompatible constraints are reported,
    never silently changed.
19. Mode switching preserves geometry unless the newly selected constraints require solving.
20. Dragging respects active locks, or is explicitly disabled when constraints conflict.

## 4. Round-trip consistency
21. For each reference side a, b, and c:
    original sides -> derive angles -> enter two angles plus selected reference side ->
    rebuild -> compare all original side lengths using absolute and relative tolerance.

## 5. Numeric policy
22. Geometry calculations use Double.
23. Display rounding never feeds back into calculations.
24. Comparisons are numeric, never string-based.
25. NaN and Infinity are rejected before geometry construction.
26. Numeric comparisons use combined absolute and relative tolerances.

## 6. Required cases
- Equilateral, 3-4-5 right, acute, and obtuse triangles.
- Degenerate and near-degenerate triangles.
- Very large and very small valid scales.
- NaN and positive/negative Infinity in every numeric input position.
- All three reference-side identities.
- Mode transitions in both directions.
- Invalid inputs while retaining last valid geometry.
- JSON export/import round-trip and schema-version rejection.
