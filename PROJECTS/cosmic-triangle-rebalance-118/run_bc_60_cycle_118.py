#!/usr/bin/env python3
"""Apply the documented B/C 60-degree cycle to the 118-row audited angle input.

Independent experiment only. A is never changed. The SVG uses a normalized
unit base solely to display triangle shape; no physical side lengths are output.
"""
from __future__ import annotations
import csv, math
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "PROJECTS" / "cosmic-triangle-rebalance-118"
SOURCE = PROJECT / "ELEMENTS_118_BC_60_CYCLE_TEST_2026-11-22.csv"
OUT_CSV = PROJECT / "ELEMENTS_118_BC_60_CYCLE_COMPLETE_2026-11-22.csv"
OUT_SVG = PROJECT / "ELEMENTS_118_BC_60_CYCLE_SHAPES_2026-11-22.svg"
OUT_REPORT = PROJECT / "BC_60_CYCLE_COMPLETE_AUDIT_2026-11-22.md"
TOL = 1e-7

def number(row, key):
    value = row.get(key, "")
    if value is None or value.strip() == "":
        raise ValueError("Missing required angle field: " + key)
    return float(value)

def choose_integer_cycle(b, c):
    # Strict positivity: n > -C/60 and n < B/60.
    n_min = math.floor(-c / 60.0) + 1
    n_max = math.ceil(b / 60.0) - 1
    if n_min > n_max:
        raise ValueError(f"No integer n makes B' and C' positive: B={b}, C={c}")
    # Operational policy: choose the feasible integer with minimum absolute value.
    # This is a run-specific selection convention, not an amendment to the rule file.
    if n_min <= 0 <= n_max:
        n = 0
    elif n_min > 0:
        n = n_min
    else:
        n = n_max
    return n_min, n_max, n

def triangle_points(a_deg, b_deg, c_deg):
    # AB=1 is a normalized drawing scale only, not a physical side measurement.
    ar, br, cr = map(math.radians, (a_deg, b_deg, c_deg))
    ac = math.sin(br) / math.sin(cr)
    return [(0.0, 0.0), (1.0, 0.0), (ac * math.cos(ar), ac * math.sin(ar))]

def build_svg(rows):
    cols, cell_w, cell_h = 10, 190, 150
    rows_n = math.ceil(len(rows) / cols)
    width, height = cols * cell_w, rows_n * cell_h + 35
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#202124}.sym{font-size:15px;font-weight:bold}.meta{font-size:10px}.invalid{fill:#b3261e;font-size:12px;font-weight:bold}.tri{fill:#eef3f8;stroke:#263746;stroke-width:2}</style>',
        '<text x="18" y="24" font-size="18" font-weight="bold">B/C 60-degree cycle — 118 elements (shape-only display)</text>',
    ]
    for idx, row in enumerate(rows):
        col, rr = idx % cols, idx // cols
        x0, y0 = col * cell_w, 35 + rr * cell_h
        parts.append(f'<rect x="{x0+3}" y="{y0+3}" width="{cell_w-6}" height="{cell_h-6}" rx="7" fill="#fafafa" stroke="#d7dce1"/>')
        parts.append(f'<text class="sym" x="{x0+10}" y="{y0+21}">{escape(row["Symbol"])} · Z={row["Z"]}</text>')
        if row["Status"] == "VALID":
            pts = triangle_points(row["A_final"], row["B_final"], row["C_final"])
            minx, maxx = min(p[0] for p in pts), max(p[0] for p in pts)
            miny, maxy = min(p[1] for p in pts), max(p[1] for p in pts)
            spanx, spany = max(maxx-minx, 1e-12), max(maxy-miny, 1e-12)
            scale = min(145.0/spanx, 82.0/spany)
            ox = x0 + (cell_w - spanx*scale)/2 - minx*scale
            oy = y0 + 112
            screen = [(ox+px*scale, oy-py*scale) for px,py in pts]
            points = " ".join(f"{px:.2f},{py:.2f}" for px,py in screen)
            parts.append(f'<polygon class="tri" points="{points}"/>')
            parts.append(f'<text class="meta" x="{x0+10}" y="{y0+137}">n={row["n_selected"]} · A/B/C positive</text>')
        else:
            parts.append(f'<text class="invalid" x="{x0+10}" y="{y0+65}">NO TRIANGLE</text>')
            parts.append(f'<text class="meta" x="{x0+10}" y="{y0+84}">A={row["A_final"]:.4f}° (unchanged)</text>')
            parts.append(f'<text class="meta" x="{x0+10}" y="{y0+101}">n={row["n_selected"]} · B/C adjusted</text>')
            parts.append(f'<text class="meta" x="{x0+10}" y="{y0+137}">A is non-positive</text>')
    parts.append('</svg>')
    return "\n".join(parts)

def main():
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
        source_rows = list(csv.DictReader(f))
    if len(source_rows) != 118:
        raise SystemExit(f"Expected 118 input rows, found {len(source_rows)}")
    if len({int(r["Z"]) for r in source_rows}) != 118:
        raise SystemExit("Input does not contain 118 unique atomic numbers")

    output = []
    for row in source_rows:
        a, b, c = number(row, "A_raw"), number(row, "B_raw"), number(row, "C_raw")
        n_min, n_max, n = choose_integer_cycle(b, c)
        ap, bp, cp = a, b - 60.0*n, c + 60.0*n
        angle_sum = ap + bp + cp
        if abs(angle_sum - (a+b+c)) > TOL:
            raise SystemExit("Cycle failed to conserve angle sum for " + row["Symbol"])
        if abs((a+b+c)-180.0) > TOL:
            status = "INVALID_RAW_ANGLE_SUM"
        elif ap <= 0.0:
            status = "INVALID_A_NONPOSITIVE"
        elif bp <= 0.0 or cp <= 0.0:
            status = "INVALID_BC_NONPOSITIVE"
        else:
            status = "VALID"
        output.append({
            "Z": int(row["Z"]), "Symbol": row["Symbol"], "Element": row["Element"],
            "A_raw": a, "B_raw": b, "C_raw": c,
            "n_min_feasible": n_min, "n_max_feasible": n_max,
            "feasible_integer_n_count": n_max-n_min+1, "n_selected": n,
            "A_final": ap, "B_final": bp, "C_final": cp,
            "angle_sum_final": angle_sum, "Status": status,
            "selection_policy": "minimum_absolute_integer_n_satisfying_BC_positive",
        })

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(output[0].keys()))
        writer.writeheader()
        writer.writerows(output)
    OUT_SVG.write_text(build_svg(output), encoding="utf-8")

    valid = [r for r in output if r["Status"] == "VALID"]
    invalid = [r for r in output if r["Status"] != "VALID"]
    zero = [r for r in valid if r["n_selected"] == 0]
    positive = [r for r in valid if r["n_selected"] > 0]
    negative = [r for r in valid if r["n_selected"] < 0]
    max_error = max(abs(r["angle_sum_final"]-180.0) for r in valid) if valid else 0.0
    invalid_lines = "\n".join(
        f'- {r["Symbol"]} (Z={r["Z"]}): {r["Status"]}; A remains {r["A_final"]:.9f}°.'
        for r in invalid
    ) or "- None"
    report = f"""# B/C 60° cycle — full 118-element execution audit

**Status:** Independent experimental execution; the frozen reference framework was not modified.

## Input and rule
- Input: {SOURCE.name}; 118 rows and 118 unique atomic numbers.
- Canonical rule: A'=A, B'=B-60n, C'=C+60n, with the same integer n applied to B and C.
- A is never changed.
- The operation preserves A+B+C.
- This run selects the feasible integer n with the smallest absolute value. This is an explicit operational selection policy for this run, not an amendment to the canonical rule document.
- The SVG uses AB=1 only as a normalized drawing scale to display angle-defined shape. No physical side lengths are asserted or exported.

## Results
- Input rows: {len(output)}
- Valid angle-defined triangles: {len(valid)}
- Invalid rows retained: {len(invalid)}
- Valid with n=0: {len(zero)}
- Valid with positive n: {len(positive)}
- Valid with negative n: {len(negative)}
- Maximum absolute final angle-sum error among valid triangles: {max_error:.12g}°

## Invalid rows
{invalid_lines}

## Validation
- Every input element is retained in the output CSV and SVG.
- A is copied unchanged.
- B and C use the same integer n with opposite 60° adjustments.
- The sum is conserved.
- A triangle is drawn only when all three final angles are positive and the raw angle sum is 180° within tolerance.
- Invalid entries are explicitly marked; no angle is fabricated to force a triangle.

## Outputs
- {OUT_CSV.name}
- {OUT_SVG.name}
- {OUT_REPORT.name}
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(f"INPUT_ROWS={len(output)}")
    print(f"VALID_TRIANGLES={len(valid)}")
    print(f"INVALID_ROWS={len(invalid)}")
    print(f"N_ZERO={len(zero)}")
    print(f"N_POSITIVE={len(positive)}")
    print(f"N_NEGATIVE={len(negative)}")
    print(f"MAX_ANGLE_SUM_ERROR={max_error:.12g}")
    print("INVALID_SYMBOLS=" + ",".join(r["Symbol"] for r in invalid))
    print("OUTPUT_CSV=" + str(OUT_CSV.relative_to(ROOT)))
    print("OUTPUT_SVG=" + str(OUT_SVG.relative_to(ROOT)))
    print("OUTPUT_REPORT=" + str(OUT_REPORT.relative_to(ROOT)))

if __name__ == "__main__":
    main()
