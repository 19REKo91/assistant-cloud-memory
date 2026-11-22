#!/usr/bin/env python3
"""Display-only periodic-table rearrangement of the existing B/C 60-cycle triangles."""
import csv, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"PROJECTS"/"cosmic-triangle-rebalance-118"
SRC=P/"ELEMENTS_118_BC_60_CYCLE_COMPLETE_2026-11-22.csv"
PNG=P/"ELEMENTS_118_BC_60_CYCLE_PERIODIC_TABLE_MAP_2026-11-22.png"
SVG=P/"ELEMENTS_118_BC_60_CYCLE_PERIODIC_TABLE_MAP_2026-11-22.svg"
REPORT=P/"BC60_PERIODIC_TABLE_MAP_AUDIT_2026-11-22.md"
BASE=3.0
DISPLAY_SCALE=0.05
CELL=3.4
# Standard periodic-table group positions; f-block is displayed on separate rows.
pos={}
periods={
 1:([1,2],[1,18]),
 2:(list(range(3,11)),[1,2,13,14,15,16,17,18]),
 3:(list(range(11,19)),[1,2,13,14,15,16,17,18]),
 4:(list(range(19,37)),list(range(1,19))),
 5:(list(range(37,55)),list(range(1,19))),
 6:([55,56]+list(range(72,87)),[1,2]+list(range(4,19))),
 7:([87,88]+list(range(104,119)),[1,2]+list(range(4,19))),
}
for period,(zs,groups) in periods.items():
    for z,g in zip(zs,groups): pos[z]=(period,g)
for z in range(57,72): pos[z]=(8,z-54)
for z in range(89,104): pos[z]=(9,z-86)

def geom(r):
    A,B,C=[math.radians(float(r[k])) for k in ("A_final","B_final","C_final")]
    if min(A,B,C)<=0 or abs(math.degrees(A+B+C)-180)>1e-6: return None
    a=BASE*math.sin(A)/math.sin(C)
    b=BASE*math.sin(B)/math.sin(C)
    v=[(0.,0.),(BASE,0.),(b*math.cos(A),b*math.sin(A))]
    perimeter=a+b+BASE
    ix=(a*v[0][0]+b*v[1][0]+BASE*v[2][0])/perimeter
    iy=(a*v[0][1]+b*v[1][1]+BASE*v[2][1])/perimeter
    # Preserve the same 0.05 uniform glyph scale used in the existing G map.
    shown=[((x-ix)*DISPLAY_SCALE,(y-iy)*DISPLAY_SCALE) for x,y in v]
    return shown

def main():
    with SRC.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    if len(rows)!=118 or len({int(r["Z"]) for r in rows})!=118: raise SystemExit("Expected 118 unique elements")
    byz={int(r["Z"]):r for r in rows}
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle
    fig,ax=plt.subplots(figsize=(27,15),dpi=180)
    ax.set_xlim(0,18*CELL); ax.set_ylim(9*CELL,0); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("Triangle Framework — 118 Elements (B/C 60° Cycle) arranged by Periodic Table",fontsize=21,weight="bold",pad=20)
    invalid=[]
    for z in range(1,119):
        period,group=pos[z]; x=(group-1)*CELL; y=(period-1)*CELL
        r=byz[z]
        ax.add_patch(Rectangle((x+.04,y+.04),CELL-.08,CELL-.08,fill=False,edgecolor="#aeb7c2",linewidth=.75))
        ax.text(x+.16,y+.38,f'Z={z}',fontsize=7,color="#536170")
        ax.text(x+.16,y+.68,r["Symbol"],fontsize=13,weight="bold",color="#17202a")
        tri=geom(r) if r["Status"]=="VALID" else None
        if tri:
            cx=x+CELL/2; cy=y+2.08
            points=[(cx+px,cy-py) for px,py in tri]
            ax.add_patch(Polygon(points,closed=True,facecolor="#dbeafe",edgecolor="#1d4ed8",linewidth=1.0,alpha=.78))
            ax.scatter([cx],[cy],s=11,color="#dc2626",zorder=5)
        else:
            invalid.append(r["Symbol"])
            ax.text(x+.16,y+1.9,"NO EUCLIDEAN",fontsize=8,color="#b3261e",weight="bold")
            ax.text(x+.16,y+2.2,"A ≤ 0",fontsize=8,color="#b3261e")
    # Lanthanide/actinide row labels
    ax.text(0.02,8*CELL-.08,"Lanthanides",fontsize=10,weight="bold",color="#46515c",ha="left",va="bottom")
    ax.text(0.02,9*CELL-.08,"Actinides",fontsize=10,weight="bold",color="#46515c",ha="left",va="bottom")
    fig.text(.01,.012,"Blue triangle = unchanged B/C 60° geometry  |  Red dot = incenter  |  Cell positions = periodic-table order",fontsize=9,color="#46515c")
    fig.tight_layout(rect=(0,.035,1,.97))
    fig.savefig(PNG,bbox_inches="tight",facecolor="white")
    fig.savefig(SVG,bbox_inches="tight",facecolor="white")
    plt.close(fig)
    report=f"""# B/C 60° cycle — periodic-table placement audit

**Operation:** display-only relocation. The source triangle geometry is unchanged.

- Source: {SRC.name}
- Input records: {len(rows)}; unique atomic numbers: {len(byz)}
- Valid Euclidean triangles: {sum(1 for r in rows if geom(r) is not None and r["Status"]=="VALID")}
- Retained without Euclidean triangle: {", ".join(invalid)}
- Angles A_final, B_final, C_final and n_selected are read unchanged.
- Construction base AB={BASE}; common glyph scale={DISPLAY_SCALE}; all triangle vertices are uniformly scaled by the same factor, preserving shape and relative display scale.
- Only each triangle's translation changes: its incenter is placed in the corresponding periodic-table cell.
- Red dot is the incenter. Blue triangle style matches the existing 118-element G map.
- Standard periods/groups are used; lanthanides and actinides occupy separate rows.
- No angle, side ratio, cycle count, source datum, or reference version is recalculated or modified.

Outputs: {PNG.name}, {SVG.name}, {REPORT.name}
"""
    REPORT.write_text(report,encoding="utf-8")
    print("INPUT_ROWS=118")
    print("UNIQUE_Z=118")
    print("VALID_TRIANGLES="+str(118-len(invalid)))
    print("NO_EUCLIDEAN="+",".join(invalid))
    print("GEOMETRY_SOURCE="+SRC.name)
    print("DISPLAY_SCALE="+str(DISPLAY_SCALE))
    print("OUTPUT_PNG="+str(PNG.relative_to(ROOT)))
    print("OUTPUT_SVG="+str(SVG.relative_to(ROOT)))
    print("OUTPUT_REPORT="+str(REPORT.relative_to(ROOT)))
if __name__=="__main__": main()
