#!/usr/bin/env python3
"""Create two display-only G-map derivatives from the existing B/C 60-cycle CSV.

Map 1: atomic-number sequence H (Z=1) through Og (Z=118).
Map 2: periodic-table groups 1-18, with lanthanides and actinides in separate bands.
The source angles and triangle construction are not changed.
"""
from __future__ import annotations
import csv, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "PROJECTS" / "cosmic-triangle-rebalance-118"
SOURCE = PROJECT / "ELEMENTS_118_BC_60_CYCLE_COMPLETE_2026-11-22.csv"
BASE = 3.0
DISPLAY_SCALE = 0.05
TOL = 1e-7

def triangle(row):
    A, B, C = (math.radians(float(row[k])) for k in ("A_final", "B_final", "C_final"))
    if min(A, B, C) <= 0 or abs(math.degrees(A+B+C)-180.0) > TOL:
        return None
    a = BASE * math.sin(A) / math.sin(C)
    b = BASE * math.sin(B) / math.sin(C)
    verts = [(0.0, 0.0), (BASE, 0.0), (b*math.cos(A), b*math.sin(A))]
    perimeter = a+b+BASE
    ix = (a*verts[0][0] + b*verts[1][0] + BASE*verts[2][0]) / perimeter
    iy = (a*verts[0][1] + b*verts[1][1] + BASE*verts[2][1]) / perimeter
    radius = (BASE*verts[2][1]) / perimeter
    # The triangle's incenter is translated to the chosen display coordinate.
    return [(DISPLAY_SCALE*x, DISPLAY_SCALE*y) for x,y in verts], (ix, iy, radius)

# Standard group placement. Lanthanides and actinides are kept in distinct bands.
GROUP = {
1:[1,3,11,19,37,55,87], 2:[4,12,20,38,56,88],
3:[21,39], 4:[22,40,72,104], 5:[23,41,73,105], 6:[24,42,74,106],
7:[25,43,75,107], 8:[26,44,76,108], 9:[27,45,77,109],
10:[28,46,78,110], 11:[29,47,79,111], 12:[30,48,80,112],
13:[5,13,31,49,81,113], 14:[6,14,32,50,82,114],
15:[7,15,33,51,83,115], 16:[8,16,34,52,84,116],
17:[9,17,35,53,85,117], 18:[2,10,18,36,54,86,118]
}
GROUP_OF = {z:g for g,zs in GROUP.items() for z in zs}
LANTH = list(range(57,72))
ACT = list(range(89,104))

def main():
    with SOURCE.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r:int(r["Z"]))
    if len(rows) != 118 or [int(r["Z"]) for r in rows] != list(range(1,119)):
        raise SystemExit("Expected exactly one source row for each Z=1..118.")
    by_z = {int(r["Z"]):r for r in rows}
    prepared = {}
    invalid = []
    for row in rows:
        result = triangle(row) if row["Status"] == "VALID" else None
        if result is None:
            invalid.append(row)
        else:
            prepared[int(row["Z"])] = (row, result[0], result[1])

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    from adjustText import adjust_text

    def draw_map(kind):
        if kind == "sequence":
            png = PROJECT / "ELEMENTS_118_BC_60_CYCLE_G_MAP_ATOMIC_SEQUENCE_2026-11-22.png"
            svg = PROJECT / "ELEMENTS_118_BC_60_CYCLE_G_MAP_ATOMIC_SEQUENCE_2026-11-22.svg"
            title = "Triangle Framework — G Map in Atomic-Number Sequence (H → Og)"
            xlabel = "Atomic-number sequence (Z): H=1 through Og=118"
            ylabel = "G_y = inradius (geometric units)"
            fig, ax = plt.subplots(figsize=(34, 12), dpi=180)
            label_points = []
            for z in range(1,119):
                row = by_z[z]
                # Sequential x is a display coordinate; preserve the original G_y.
                x = z * 0.22
                item = prepared.get(z)
                if item:
                    _, verts, (ix,iy,radius) = item
                    # Put the incenter at (sequence coordinate, original inradius).
                    shifted = [(0.05*vx + x - 0.05*ix, 0.05*vy + radius - 0.05*iy) for vx,vy in
                               [(0.0,0.0),(BASE,0.0),(verts[2][0]/DISPLAY_SCALE,verts[2][1]/DISPLAY_SCALE)]]
                    ax.add_patch(Polygon(shifted, closed=True, facecolor="#dbeafe",
                                         edgecolor="#1d4ed8", linewidth=0.65, alpha=0.72))
                    ax.scatter(x, radius, s=7, color="#dc2626", zorder=4)
                    label_points.append(ax.text(x, radius, row["Symbol"], fontsize=5.0, ha="center"))
                else:
                    ax.scatter(x, 0.04, marker="x", s=18, color="#b3261e", zorder=5)
                    label_points.append(ax.text(x, 0.055, row["Symbol"]+"*", fontsize=4.5, color="#b3261e", ha="center"))
            ax.set_xlim(0, 26.4)
            ax.set_ylim(-0.02, 1.25)
            ax.set_xticks([z*0.22 for z in range(1,119,5)])
            ax.set_xticklabels([str(z) for z in range(1,119,5)], fontsize=7)
            ax.grid(True, alpha=0.22)
            if label_points:
                adjust_text(label_points, ax=ax, only_move={"points":"y","texts":"y"},
                            arrowprops=dict(arrowstyle="-", color="#777777", lw=0.25))
            fig.text(0.015,0.012,"* Bh, Hs, Mt and Ds have no Euclidean triangle because A ≤ 0.",fontsize=8,color="#b3261e")
        else:
            png = PROJECT / "ELEMENTS_118_BC_60_CYCLE_G_MAP_BY_PERIODIC_GROUP_2026-11-22.png"
            svg = PROJECT / "ELEMENTS_118_BC_60_CYCLE_G_MAP_BY_PERIODIC_GROUP_2026-11-22.svg"
            title = "Triangle Framework — G Map Grouped by Periodic-Table Group"
            xlabel = "Periodic-table group (1–18); separate f-block bands below"
            ylabel = "Element order within group (increasing atomic number)"
            fig, ax = plt.subplots(figsize=(22, 14), dpi=180)
            label_points = []
            # Group columns: members ascend vertically by Z. Coordinates are layout-only.
            for g in range(1,19):
                zs = sorted(GROUP[g])
                for rank,z in enumerate(zs, start=1):
                    row = by_z[z]
                    x, y = float(g), -float(rank)
                    item = prepared.get(z)
                    if item:
                        _, verts, (ix,iy,radius) = item
                        raw = [(0.0,0.0),(BASE,0.0),(verts[2][0]/DISPLAY_SCALE,verts[2][1]/DISPLAY_SCALE)]
                        shifted = [(0.05*vx + x - 0.05*ix, 0.05*vy + y - 0.05*iy) for vx,vy in raw]
                        ax.add_patch(Polygon(shifted, closed=True, facecolor="#dbeafe",
                                             edgecolor="#1d4ed8", linewidth=0.7, alpha=0.72))
                        ax.scatter(x,y,s=8,color="#dc2626",zorder=4)
                        label_points.append(ax.text(x,y,row["Symbol"],fontsize=6.2,ha="center"))
                    else:
                        ax.scatter(x,y,marker="x",s=22,color="#b3261e",zorder=5)
                        label_points.append(ax.text(x,y,row["Symbol"]+"*",fontsize=5.8,color="#b3261e",ha="center"))
            # f-blocks are deliberately separate, in atomic-number order.
            for band, zs, ybase in (("Lanthanides",LANTH,-9.0),("Actinides",ACT,-11.2)):
                for rank,z in enumerate(zs):
                    row = by_z[z]
                    x, y = 4.0 + rank*0.72, ybase
                    item = prepared.get(z)
                    if item:
                        _, verts, (ix,iy,radius) = item
                        raw = [(0.0,0.0),(BASE,0.0),(verts[2][0]/DISPLAY_SCALE,verts[2][1]/DISPLAY_SCALE)]
                        shifted = [(0.05*vx + x - 0.05*ix, 0.05*vy + y - 0.05*iy) for vx,vy in raw]
                        ax.add_patch(Polygon(shifted, closed=True, facecolor="#dbeafe",
                                             edgecolor="#1d4ed8", linewidth=0.7, alpha=0.72))
                        ax.scatter(x,y,s=8,color="#dc2626",zorder=4)
                        label_points.append(ax.text(x,y,row["Symbol"],fontsize=6.0,ha="center"))
                    else:
                        ax.scatter(x,y,marker="x",s=22,color="#b3261e",zorder=5)
                        label_points.append(ax.text(x,y,row["Symbol"]+"*",fontsize=5.8,color="#b3261e",ha="center"))
                ax.text(2.7,ybase,band,fontsize=9,weight="bold",ha="right",va="center")
            ax.set_xlim(0.3,18.7)
            ax.set_ylim(-13.0,0.8)
            ax.set_xticks(range(1,19))
            ax.set_xticklabels([str(g) for g in range(1,19)])
            ax.grid(True,alpha=0.22)
            if label_points:
                adjust_text(label_points, ax=ax, only_move={"points":"y","texts":"xy"},
                            arrowprops=dict(arrowstyle="-",color="#777777",lw=0.25))
            fig.text(0.015,0.012,"* Bh, Hs, Mt and Ds have no Euclidean triangle because A ≤ 0. Group columns use standard 1–18 placement; f-block series are shown separately.",fontsize=8,color="#b3261e")
        ax.set_title(title,fontsize=17,weight="bold",pad=15)
        ax.set_xlabel(xlabel,fontsize=11)
        ax.set_ylabel(ylabel,fontsize=11)
        fig.tight_layout(rect=(0,0.035,1,1))
        fig.savefig(png,bbox_inches="tight")
        fig.savefig(svg,bbox_inches="tight")
        plt.close(fig)
        return png.name,svg.name

    seq_png,seq_svg = draw_map("sequence")
    grp_png,grp_svg = draw_map("groups")
    report = f"""# Two G-map display arrangements — atomic sequence and periodic groups

## Source and invariants
- Source CSV: {SOURCE.name}
- Input rows: {len(rows)}; atomic numbers: 1–118 exactly once.
- Source angle fields A_final/B_final/C_final and n_selected are read unchanged.
- Construction base: AB={BASE:g}; uniform triangle glyph scale: {DISPLAY_SCALE:g}.
- Each valid triangle is reconstructed from its existing final angles; the glyph is uniformly scaled and translated only.
- Red point: incenter. Blue outline/fill: same G-map triangle style.
- This is a display-only rearrangement. The new horizontal/vertical layout coordinates are not new physical Gx/Gy measurements.

## Map 1 — atomic-number sequence
- Horizontal order: Z=1 H through Z=118 Og.
- Vertical coordinate: source-derived inradius (G_y) retained.
- X coordinate is a sequential display slot, not the original geometric G_x.

## Map 2 — periodic-table groups
- Main columns: groups 1–18; elements within each group ascend by atomic number.
- Lanthanides (Z=57–71) and actinides (Z=89–103) are shown in separate bands.
- Both axes in this second image are layout coordinates, not measured geometric G coordinates.

## Coverage
- Total elements: 118
- Elements with valid Euclidean triangles: {len(prepared)}
- Elements shown without triangles: {", ".join(r["Symbol"] for r in invalid)}
- Invalid entries are marked with a red cross and an asterisk; no triangle is fabricated for them.

## Output files
- {seq_png}
- {seq_svg}
- {grp_png}
- {grp_svg}

No source angles, side ratios, cycle counts, or reference versions were modified.
"""
    audit = PROJECT / "BC60_G_MAP_SEQUENCE_AND_GROUPS_AUDIT_2026-11-22.md"
    audit.write_text(report,encoding="utf-8")
    print("INPUT_ROWS=118")
    print(f"VALID_TRIANGLES={len(prepared)}")
    print("NO_TRIANGLE=" + ",".join(r["Symbol"] for r in invalid))
    for name in (seq_png,seq_svg,grp_png,grp_svg,audit.name):
        print("OUTPUT=" + name)

if __name__ == "__main__":
    main()
