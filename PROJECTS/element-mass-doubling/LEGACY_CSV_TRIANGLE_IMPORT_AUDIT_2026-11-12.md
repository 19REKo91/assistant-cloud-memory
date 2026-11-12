# Legacy CSV Triangle Import — Geometry Audit (2026-11-12)

## Decision and source

The user explicitly authorized using the historical repository dataset for the triangle-overlay work.

- Source: `PROJECTS/triangle-framework/recovery/elements_118.csv`
- Branch: `main`
- Blob SHA: `5f11780d5688a671bc667b0116de90444378d1f1`
- Rows: 118 (Z=1–118)
- Fields used for triangle eligibility/construction: `t1`, `t2`, `t3_adopted`
- `n`, `t3_calc_check`, and the source's classifications were not substituted for the user's current classifications.

## Import rule

No modulo-360 operation, subtraction of 360-degree turns, absolute-value correction, or angle replacement was applied.

A legacy CSV row was imported only when:
1. all three selected angle fields were finite and strictly positive;
2. their displayed sum was exactly 180 degrees within 0.005 degrees (floating-point tolerance only); and
3. its Z and element symbol matched one of the 118 original SVG chart points.

The 60 exact-180-degree CSV rows were imported. The CSV's Li row sums to 180.1 degrees, so it was not used. Li remains sourced from the user's newer angle table dated 2026-11-12.

## Result

- Original chart points retained: 118 / 118.
- Legacy CSV exact-180 rows imported: 60.
- Current user-table Li triangle retained: 1.
- Total displayed Euclidean triangles: 61.
- Positive numeric angle triples in CSV: 108.
- Positive triples within 0.15 degrees of 180: 78 (includes the CSV Li row, which was not imported).
- Exact-180 rows: 60.
- Near-180 but not exact rows withheld: 18.
- Positive triples outside the 0.15-degree window: 30.
- Missing/non-positive triples: 10.

Near-180 rows withheld rather than silently adjusted:
`Li, Sc, Mn, Ni, Se, Zr, Rh, Pd, Ag, Te, La, Ac, Cm, Bk, Cf, Lr, Rf, Fl`.
Li is separately drawn from the current user table, not from the legacy CSV.

## Geometry

For each imported triangle:
- `AB = c = 3`
- `alpha = t1`, `beta = t2`, `gamma = t3_adopted`
- `a = 3 sin(alpha) / sin(gamma)`
- `b = 3 sin(beta) / sin(gamma)`
- `C = (b cos(alpha), b sin(alpha))`
- `G = (a A + b B + c C) / (a+b+c)`, with `A=(0,0)`, `B=(3,0)`.

The computed incenter G is translated to the unchanged original SVG point for that element. The triangle display slider changes visual scale only; it is not a scientific conversion to chart-axis units.

## Numerical validation

The updated HTML was fetched again from GitHub after commit `f1f9098635f07880f19aaec3ddd5ec26c46b97a3`.

Checks:
- 118 original blue SVG circles remain.
- 61 triangle records are present (60 legacy CSV + current Li).
- JavaScript syntax parse: PASS.
- Maximum difference between the stored G and the independently recomputed incenter formula: approximately `3.7e-11` model units.
- Maximum spread among the three perpendicular distances from G to the triangle sides: approximately `5.4e-11` model units.

These checks validate the stored triangle geometry and SVG data structure. They do not claim a full interactive browser-session test.

## Updated workbench

`PROJECTS/element-mass-doubling/element-mass-triangle-overlay-workbench.html`

Commit: `f1f9098635f07880f19aaec3ddd5ec26c46b97a3`
Blob SHA: `89b7ed92ff3a5405edb83f1b2b363f30092041e7`
