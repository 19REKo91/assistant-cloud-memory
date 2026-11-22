#!/usr/bin/env python3
"""Place the already-approved 118 angle-defined triangles on a Gx/inradius map.

This is a display-only transformation:
- source A_final/B_final/C_final and Status are read unchanged;
- no angle, cycle n, or triangle geometry is recalculated from new data;
- AB=3 is the common geometric construction scale used to compute the incenter;
- each plotted triangle is uniformly reduced by DISPLAY_SCALE=0.05, matching
  the visual glyph scale of the archived Triangle Framework 4.0 G Map.
The red point is the incenter location (Gx, inradius).
"""
from __future__ import annotations
import csv, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "PROJECTS" / "cosmic-triangle-rebalance-118"
SOURCE = PROJECT / "ELEMENTS_118_BC_60_CYCLE_COMPLETE_2026-11-22.csv"
OUT_SVG = PROJECT / "ELEMENTS_118_BC_60_CYCLE_G_MAP_2026-11-22.svg"
OUT_PNG = PROJECT / "ELEMENTS_118_BC_60_CYCLE_G_MAP_2026-11-22.png"
OUT_REPORT = PROJECT / "BC_60_CYCLE_G_MAP_PLACEMENT_AUDIT_2026-11-22.md"
BASE = 3.0
DISPLAY_SCALE = 0.05
TOL = 1e-7

def geom(row):
    A, B, C = (math.radians(float(row[k])) for k in ("A_final", "B_final", "C_final"))
    if min(A, B, C) <= 0 or abs(math.degrees(A+B+C)-180.0) > TOL:
        return None
    a = BASE * math.sin(A) / math.sin(C)  # BC
    b = BASE * math.sin(B) / math.sin(C)  # CA
    c = BASE                            # AB
    verts = [(0.0, 0.0), (BASE, 0.0), (b*math.cos(A), b*math.sin(A))]
    per = a+b+c
    ix = (a*verts[0][0] + b*verts[1][0] + c*verts[2][0]) / per
    iy = (a*verts[0][1] + b*verts[1][1] + c*verts[2][1]) / per
    area = 0.5*BASE*verts[2][1]
    radius = 2.0*area/per
    # Translate the uniformly reduced triangle so its incenter is at (ix, radius).
    dx = ix - DISPLAY_SCALE*ix
    dy = radius - DISPLAY_SCALE*iy
    shown = [(DISPLAY_SCALE*x+dx, DISPLAY_SCALE*y+dy) for x,y in verts]
    return {"Gx":ix, "Gy":radius, "vertices":shown, "area":area, "perimeter":per}

def main():
    with SOURCE.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 118 or len({int(r["Z"]) for r in rows}) != 118:
        raise SystemExit("Input must contain exactly 118 unique elements.")
    valid, invalid = [], []
    for row in rows:
        g = geom(row) if row["Status"] == "VALID" else None
        if g is None:
            invalid.append(row)
        else:
            valid.append({**row, **g})

    # Render with Matplotlib; all triangles use the same uniform display scale.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    from adjustText import adjust_text

    fig, ax = plt.subplots(figsize=(16, 10), dpi=180)
    ax.set_title("Triangle Framework — 118 Elements G Map (B/C 60° Cycle)", fontsize=17, weight="bold", pad=16)
    ax.set_xlabel("G_x (geometric units)", fontsize=12)
    ax.set_ylabel("G_y = inradius (geometric units)", fontsize=12)
    ax.grid(True, alpha=0.22)
    texts = []
    for r in valid:
        poly = Polygon(r["vertices"], closed=True, facecolor="#dbeafe", edgecolor="#1d4ed8",
                       linewidth=0.8, alpha=0.72, zorder=2)
        ax.add_patch(poly)
        ax.scatter(r["Gx"], r["Gy"], s=8, color="#dc2626", zorder=4)
        texts.append(ax.text(r["Gx"], r["Gy"], r["Symbol"], fontsize=5.7, zorder=5))
    if texts:
        adjust_text(texts, ax=ax, only_move={"points":"y", "texts":"xy"},
                    arrowprops=dict(arrowstyle="-", color="#777777", lw=0.35))
    if invalid:
        detail = "No Euclidean triangle (A ≤ 0): " + ", ".join(
            f'{r["Symbol"]} (A={float(r["A_final"]):.3f}°)' for r in invalid)
        fig.text(0.02, 0.015, detail, fontsize=8, color="#b3261e")
    xs = [r["Gx"] for r in valid]
    ys = [r["Gy"] for r in valid]
    if xs and ys:
        padx = max(0.08, (max(xs)-min(xs))*0.08)
        pady = max(0.08, (max(ys)-min(ys))*0.10)
        ax.set_xlim(min(0, min(xs)-padx), max(xs)+padx)
        ax.set_ylim(min(0, min(ys)-pady), max(ys)+pady)
    fig.tight_layout(rect=(0,0.04,1,1))
    fig.savefig(OUT_PNG, bbox_inches="tight")
    fig.savefig(OUT_SVG, bbox_inches="tight")
    plt.close(fig)

    report = f"""# G Map placement audit — 118 elements

**Purpose:** Reposition the existing B/C-cycle triangles into the archived G Map presentation style. This is a display-only derivative; the source angle records and triangle angle geometry are unchanged.

## Source and invariants
- Input: {SOURCE.name}
- Input rows / unique Z: {len(rows)} / {len(set(int(r["Z"]) for r in rows))}
- Final angle fields A_final, B_final, C_final are read as-is.
- Cycle index n_selected and Status are not modified.
- Geometric base used for incenter calculation: AB={BASE:g}.
- Uniform display glyph scale: {DISPLAY_SCALE:g}; all three coordinates of every triangle are multiplied by the same factor before translation. This preserves each triangle's shape.
- Placement coordinate: (Gx, Gy) = (incenter x-coordinate, inradius), matching the archived G Map axes.
- No physical side length is inferred from the display glyph size.

## Results
- Input elements: {len(rows)}
- Placed triangles: {len(valid)}
- Retained without triangle: {len(invalid)}
- Invalid elements: {", ".join(r["Symbol"] for r in invalid) if invalid else "None"}
- Gx range: {min(xs):.9f} to {max(xs):.9f}
- Inradius range: {min(ys):.9f} to {max(ys):.9f}

## Outputs
- {OUT_SVG.name}
- {OUT_PNG.name}
- {OUT_REPORT.name}

The archived reference image is used for layout/axes/presentation only. Its historical element coordinates are not copied onto the new triangles; every new position is computed from that element's unchanged current triangle geometry.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(f"INPUT_ROWS={len(rows)}")
    print(f"PLACED_TRIANGLES={len(valid)}")
    print(f"NO_TRIANGLE={len(invalid)}")
    print("INVALID_SYMBOLS=" + ",".join(r["Symbol"] for r in invalid))
    print(f"GX_RANGE={min(xs):.9f},{max(xs):.9f}")
    print(f"INRADIUS_RANGE={min(ys):.9f},{max(ys):.9f}")
    print("OUTPUT_SVG=" + str(OUT_SVG.relative_to(ROOT)))
    print("OUTPUT_PNG=" + str(OUT_PNG.relative_to(ROOT)))
    print("OUTPUT_REPORT=" + str(OUT_REPORT.relative_to(ROOT)))

if __name__ == "__main__":
    main()
