#!/usr/bin/env python3
"""Independent exploratory recalculation using the 20 C gas table and phase-rank coordinates.
The frozen 6.2.1 reference and all prior outputs are read-only.
"""
import csv, math
from pathlib import Path
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"PROJECTS"/"cosmic-triangle-rebalance-118"
SRC=P/"ELEMENTS_118_MASS_DENSITY_SOURCE_AUDITED_DRAFT_2026-11-22.csv"
PHASE=P/"ELEMENTS_118_PHASE_COMPATIBILITY_REGISTER_2026-11-22.csv"
GAS=P/"ELEMENTAL_GASES_11_ROOM_TEMPERATURE_20C_1ATM_2026-11-22.csv"
OUT=P/"ELEMENTS_118_PHASE_RANK_20C_RECALCULATED_EXPLORATORY_2026-11-22.csv"
SVG=P/"ELEMENTS_118_PERIODIC_TABLE_TRIANGLES_20C_EXPLORATORY_2026-11-22.svg"
PNG=P/"ELEMENTS_118_PERIODIC_TABLE_TRIANGLES_20C_EXPLORATORY_2026-11-22.png"
AUD=P/"PHASE_RANK_20C_RECALCULATION_AUDIT_2026-11-22.md"
LAMBDA=0.5
TOL=1e-8

def read(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def fnum(x):
    try:
        v=float(x)
        return v if math.isfinite(v) and v>0 else None
    except (TypeError,ValueError):
        return None

def midranks(values):
    ordered=sorted((v,i) for i,v in enumerate(values) if v is not None)
    out=[None]*len(values)
    n=len(ordered)
    if n<=1:
        return out
    k=0
    while k<n:
        j=k+1
        while j<n and ordered[j][0]==ordered[k][0]:
            j+=1
        rank=((k+1)+j)/2.0
        pct=(rank-1)/(n-1)
        for q in range(k,j):
            out[ordered[q][1]]=pct
        k=j
    return out

def angles(x,y):
    u=2*x-1; v=2*y-1
    ws=[LAMBDA*u,LAMBDA*v,-LAMBDA*(u+v)]
    m=max(ws)
    ex=[math.exp(z-m) for z in ws]
    s=sum(ex)
    return [180*z/s for z in ex]

def geometry(A,B,C):
    ar,br,cr=map(math.radians,(A,B,C))
    c=1.0
    a=math.sin(ar)/math.sin(cr)
    b=math.sin(br)/math.sin(cr)
    pts=[(0.0,0.0),(1.0,0.0),(b*math.cos(ar),b*math.sin(ar))]
    per=a+b+c
    ix=(a*pts[0][0]+b*pts[1][0]+c*pts[2][0])/per
    iy=(a*pts[0][1]+b*pts[1][1]+c*pts[2][1])/per
    return pts,(ix,iy),(a,b,c)

def rankdata(rows,field):
    groups=defaultdict(list)
    for i,r in enumerate(rows):
        if r["_phase"] in ("Gas","Solid","Liquid") and r[field] is not None:
            groups[r["_phase"]].append((i,r[field]))
    out=[None]*len(rows)
    for g,items in groups.items():
        vals=[v for _,v in items]
        ranks=midranks(vals)
        for (idx,_),rank in zip(items,ranks):
            out[idx]=rank
    return out, {g:len(v) for g,v in groups.items()}

# Standard periodic-table positions (period, group); f-block shown on rows 8 and 9.
period_groups={
1:[1,18],
2:[1,2,13,14,15,16,17,18],
3:[1,2,13,14,15,16,17,18],
4:list(range(1,19)),
5:list(range(1,19)),
6:[1,2]+list(range(4,19)),
7:[1,2]+list(range(4,19)),
}
positions={}
for period, zs in {
1:[1,2],
2:list(range(3,11)),
3:list(range(11,19)),
4:list(range(19,37)),
5:list(range(37,55)),
6:[55,56]+list(range(72,87)),
7:[87,88]+list(range(104,119)),
}.items():
    for z,g in zip(zs,period_groups[period]):
        positions[z]=(period,g)
for z in range(57,72):
    positions[z]=(8,z-54) # groups 3..17
for z in range(89,104):
    positions[z]=(9,z-86) # groups 3..17

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def render_svg(rows):
    cw,ch=270,235
    margin=70
    width=18*cw+2*margin
    height=9*ch+2*margin
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
    '<rect width="100%" height="100%" fill="#ffffff"/>',
    '<style>text{font-family:Arial,sans-serif;fill:#17202a}.sym{font-size:22px;font-weight:bold}.z{font-size:12px;fill:#59636e}.small{font-size:10px;fill:#46515c}.cell{fill:#fbfcfd;stroke:#d7dde4;stroke-width:1}.missing{fill:#f3f4f6;stroke:#9ca3af;stroke-dasharray:4 3}.dot{fill:#c62828;stroke:#fff;stroke-width:1}</style>',
    '<text x="70" y="36" font-size="24" font-weight="bold">118 Elements — 20°C gas update / phase-rank exploratory map (lambda=0.50)</text>',
    '<text x="70" y="55" font-size="12" fill="#58616b">A: green · B: blue · C: yellow · red point: incenter · periodic-table positions</text>']
    byz={int(r["Z"]):r for r in rows}
    for z in range(1,119):
        if z not in positions: continue
        per,grp=positions[z]
        x=margin+(grp-1)*cw
        y=margin+(per-1)*ch
        if per>=8: y=margin+(per-1)*ch
        r=byz[z]
        valid=r["Geometry_Status"]=="TRIANGLE"
        cls="cell" if valid else "missing"
        parts.append(f'<rect class="{cls}" x="{x+4}" y="{y+4}" width="{cw-8}" height="{ch-8}" rx="8"/>')
        parts.append(f'<text class="z" x="{x+15}" y="{y+25}">Z={z}</text>')
        parts.append(f'<text class="sym" x="{x+15}" y="{y+51}">{esc(r["Symbol"])}</text>')
        if valid:
            pts=[(float(r["P1x"]),float(r["P1y"])),(float(r["P2x"]),float(r["P2y"])),(float(r["P3x"]),float(r["P3y"]))]
            ix,iy=float(r["Incenter_x"]),float(r["Incenter_y"])
            allp=pts+[(ix,iy)]
            minx=min(p[0] for p in allp); maxx=max(p[0] for p in allp)
            miny=min(p[1] for p in allp); maxy=max(p[1] for p in allp)
            spanx=max(maxx-minx,1e-12); spany=max(maxy-miny,1e-12)
            scale=min(205/spanx,112/spany)
            ox=x+cw/2-(minx+maxx)/2*scale
            oy=y+150+(miny+maxy)/2*scale
            def tr(p): return (ox+p[0]*scale,oy-p[1]*scale)
            q=[tr(p) for p in pts]; qi=tr((ix,iy))
            colors=["#36a657","#2878d0","#f2c744"]
            for i in range(3):
                p1=q[i]; p2=q[(i+1)%3]
                poly=f'{qi[0]:.2f},{qi[1]:.2f} {p1[0]:.2f},{p1[1]:.2f} {p2[0]:.2f},{p2[1]:.2f}'
                parts.append(f'<polygon points="{poly}" fill="{colors[i]}" fill-opacity="0.78" stroke="#263238" stroke-width="1.5"/>')
            parts.append(f'<circle class="dot" cx="{qi[0]:.2f}" cy="{qi[1]:.2f}" r="4"/>')
            parts.append(f'<text class="small" x="{x+15}" y="{y+cw*0+220}">A/B/C={float(r["Angle_A_deg"]):.1f}/{float(r["Angle_B_deg"]):.1f}/{float(r["Angle_C_deg"]):.1f}°</text>')
        else:
            parts.append(f'<text x="{x+15}" y="{y+118}" font-size="14" fill="#9b1c1c">NO DATA / HELD</text>')
            parts.append(f'<text class="small" x="{x+15}" y="{y+145}">{esc(r["Geometry_Status"])}</text>')
    parts.append('</svg>')
    return "\n".join(parts)

def main():
    src=read(SRC); phase=read(PHASE); gas=read(GAS)
    if len(src)!=118 or len(phase)!=118 or len({int(r["Z"]) for r in src})!=118:
        raise SystemExit("Input coverage validation failed; expected 118 unique rows.")
    pmap={int(r["Z"]):r for r in phase}
    gmap={int(r["Z"]):r for r in gas}
    rows=[]
    for s in src:
        z=int(s["Z"]); pr=pmap[z]
        mass=fnum(s["AtomicMass_u"]); rho=fnum(s["Density_g_cm3"])
        phase_label=pr["Phase_Group"]
        ph="Gas" if phase_label in ("Gas","Expected to be Gas") else ("Liquid" if phase_label=="Liquid" else "Solid")
        gas_status="NOT_APPLICABLE"
        temp=pr["Temperature_C"]; pressure=pr["Pressure_kPa"]
        if ph=="Gas" and z in gmap:
            gr=gmap[z]
            rho20_ref=fnum(gr.get("Density_20C_reference_g_cm3"))
            rho20_derived=fnum(gr["Density_20C_derived_g_cm3"])
            if rho20_ref is not None:
                rho=rho20_ref; temp="20"; pressure="101.325"
                gas_status="DIRECT_20C_REFERENCE_VALUE_USED"
            elif rho20_derived is not None:
                rho=rho20_derived; temp="20"; pressure="101.325"
                gas_status="IDEAL_GAS_SCALED_FROM_0C_NO_DIRECT_20C_VALUE"
        vol=mass/rho if mass and rho else None
        source_class=pr["Density_Source_Class"]
        quality=pr["Data_Quality_Flag"]
        status="READY_EXPLORATORY"
        if not mass or not rho or not vol:
            status="MISSING_REQUIRED_MASS_OR_DENSITY"
        elif "predicted" in (s["Density_Status"]+" "+quality).lower() or "expected" in phase_label.lower():
            status="PREDICTED_OR_EXPECTED_INPUT"
        elif ph=="Liquid":
            status="LOW_N_LIQUID_COHORT"
        elif ph=="Gas" and gas_status.startswith("IDEAL_GAS"):
            status="GAS_IDEAL_SCALED_20C"
        elif ph=="Gas":
            status="GAS_DIRECT_20C_REFERENCE_USED"
        elif source_class!="PubChem":
            status="SECONDARY_SOURCE_INPUT"
        else:
            status="PRIMARY_LISTED_CONDITIONS_UNSPECIFIED"
        rows.append({"Z":z,"Symbol":s["Symbol"],"Element":s["Element"],"_phase":ph,
          "Phase_Source_Label":phase_label,"Source_Class":source_class,"Mass_u":mass,
          "Density_g_cm3_used":rho,"Density_Source_URL":s["Density_Source"],
          "Temperature_C":temp,"Pressure_kPa":pressure,"Gas_20C_Status":gas_status,
          "Density_Status_Source":s["Density_Status"],"Quality_Flag":quality,
          "Molar_Volume_cm3_per_mol_atoms":vol,"Input_Status":status})
    # Midrank normalization is explicitly within phase, not across phases.
    for field in ("Density_g_cm3_used","Molar_Volume_cm3_per_mol_atoms"):
        ranks,counts=rankdata(rows,field)
        for r,rank in zip(rows,ranks): r["Rank_Density" if field.startswith("Density") else "Rank_MolarVolume"]=rank
    output=[]
    for r in rows:
        x=r["Rank_Density"]; y=r["Rank_MolarVolume"]
        base=dict(r)
        base.pop("_phase")
        base["Phase_Cohort"]=r["_phase"]
        base["Cohort_N"]={"Gas":12,"Solid":104,"Liquid":2}.get(r["_phase"],0)
        base["Lambda"]=LAMBDA
        if x is None or y is None:
            base.update({"Angle_A_deg":"NA","Angle_B_deg":"NA","Angle_C_deg":"NA",
              "Incenter_x":"NA","Incenter_y":"NA","P1x":"NA","P1y":"NA","P2x":"NA","P2y":"NA","P3x":"NA","P3y":"NA",
              "Geometry_Status":"NO_NORMALIZATION_COORDINATE"})
        else:
            A,B,C=angles(x,y)
            pts,I,sides=geometry(A,B,C)
            base.update({"Angle_A_deg":A,"Angle_B_deg":B,"Angle_C_deg":C,
              "Incenter_x":I[0],"Incenter_y":I[1],
              "P1x":pts[0][0],"P1y":pts[0][1],"P2x":pts[1][0],"P2y":pts[1][1],"P3x":pts[2][0],"P3y":pts[2][1],
              "Side_a":sides[0],"Side_b":sides[1],"Side_c":sides[2],
              "Angle_Sum_deg":A+B+C,"Geometry_Status":"TRIANGLE"})
        output.append(base)
    fields=list(output[0].keys())
    with OUT.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(output)
    svg=render_svg(output); SVG.write_text(svg,encoding="utf-8")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    fig,ax=plt.subplots(figsize=(27,14),dpi=180)
    ax.set_xlim(0,18); ax.set_ylim(9,0); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("118 Elements — periodic-table triangle map (20°C gas update; exploratory)",fontsize=20,pad=18)
    byz={r["Z"]:r for r in output}
    for z,(per,grp) in positions.items():
        r=byz[z]; x=grp-1; y=per-1
        ax.add_patch(plt.Rectangle((x+0.03,y+0.03),0.94,0.94,fill=False,edgecolor="#aab2bd",linewidth=.7))
        ax.text(x+.09,y+.17,str(z),fontsize=5.5)
        ax.text(x+.09,y+.34,r["Symbol"],fontsize=9,weight="bold")
        if r["Geometry_Status"]=="TRIANGLE":
            pts=[(float(r["P1x"]),float(r["P1y"])),(float(r["P2x"]),float(r["P2y"])),(float(r["P3x"]),float(r["P3y"]))]
            ix,iy=float(r["Incenter_x"]),float(r["Incenter_y"])
            allp=pts+[(ix,iy)]
            minx=min(p[0] for p in allp); maxx=max(p[0] for p in allp)
            miny=min(p[1] for p in allp); maxy=max(p[1] for p in allp)
            scale=min(.68/max(maxx-minx,1e-12),.38/max(maxy-miny,1e-12))
            ox=x+.5-(minx+maxx)*scale/2; oy=y+.77+(miny+maxy)*scale/2
            q=[(ox+p[0]*scale,oy-p[1]*scale) for p in pts]; qi=(ox+ix*scale,oy-iy*scale)
            for i,col in enumerate(["#36a657","#2878d0","#f2c744"]):
                tri=[qi,q[i],q[(i+1)%3]]
                ax.add_patch(Polygon(tri,closed=True,facecolor=col,edgecolor="#263238",linewidth=.35,alpha=.82))
            ax.scatter([qi[0]],[qi[1]],s=4,c="#c62828",zorder=5)
        else:
            ax.text(x+.09,y+.67,"HOLD",fontsize=6,color="#a11")
    fig.tight_layout()
    fig.savefig(PNG,bbox_inches="tight")
    plt.close(fig)
    valid=[r for r in output if r["Geometry_Status"]=="TRIANGLE"]
    angleerr=max(abs(float(r["Angle_Sum_deg"])-180) for r in valid) if valid else 0
    phases=defaultdict(int); statuses=defaultdict(int)
    for r in output: phases[r["Phase_Cohort"]]+=1; statuses[r["Input_Status"]]+=1
    audit=f"""# 20°C gas update and 118-element phase-rank recalculation audit

**Status:** Independent exploratory recalculation. Not a final physical model and not a change to frozen reference 6.2.1 or prior outputs.

## Inputs and transformations
- Source mass/density table: {SRC.name}
- Phase/source compatibility register: {PHASE.name}
- Gas harmonization table: {GAS.name}
- Gas density inputs replaced with the separately audited 20°C, 101.325 kPa values where present (11 gas rows); direct-reference and ideal-scaled statuses remain distinct.
- Solid/liquid density values are carried from their source rows without an unsupported thermal correction. Their source-specific temperature/pressure/allotrope limitations remain visible in the row status and flags.
- Elemental molar volume is calculated as atomic mass / density, in cm³ per mole of atoms.
- Density and molar-volume percentiles are midranks within each phase cohort, never pooled across phases.
- Angle transformation is the existing explicitly exploratory softmax candidate with lambda={LAMBDA}; it is not a measured physical law.
- Triangle base c=1 is a normalized construction scale. The red point is the incenter.
- Display positions use standard periodic-table group/period positions, with lanthanides and actinides on separate rows.

## Coverage
- Input rows: {len(output)}; unique Z: {len(set(r["Z"] for r in output))}
- Phase cohorts: {dict(phases)}
- Valid angle-defined triangles: {len(valid)}
- Rows held without triangle: {len(output)-len(valid)}
- Maximum angle-sum numerical error: {angleerr:.3g} degrees
- Cohort sizes: {dict(counts)}

## Input quality distribution
{chr(10).join("- "+k+": "+str(v) for k,v in sorted(statuses.items()))}

## Scientific limitations
1. A common thermodynamic state for all 118 elements is not established. Solid and liquid densities are not temperature-corrected because row-level conditions/allotropes are unavailable.
2. The gas table has a mixture of direct 20°C cross-checks and ideal-gas-scaled values; the latter are explicitly flagged.
3. The liquid cohort contains only two members; its phase-relative ranks are unstable and must not be interpreted as a robust scale.
4. Expected/predicted and secondary-source entries are retained and flagged; their numeric presence does not make them measurements.
5. Phase-relative percentiles are not one shared physical scale across gas, liquid, and solid. The resulting map is a computational visualization scenario only.
6. This run does not claim pressure/stress measurements, and no old reference constants or old angle values were used.

## Outputs
- {OUT.name}
- {SVG.name}
- {PNG.name}
- {AUD.name}
"""
    AUD.write_text(audit,encoding="utf-8")
    print("INPUT_ROWS=118")
    print("UNIQUE_Z=118")
    print("PHASE_COUNTS="+str(dict(phases)))
    print("VALID_TRIANGLES="+str(len(valid)))
    print("HELD_ROWS="+str(len(output)-len(valid)))
    print("MAX_ANGLE_SUM_ERROR="+str(angleerr))
    print("COHORT_COUNTS="+str(dict(counts)))
    print("INPUT_STATUS_COUNTS="+str(dict(statuses)))
    print("OUTPUT_CSV="+str(OUT.relative_to(ROOT)))
    print("OUTPUT_SVG="+str(SVG.relative_to(ROOT)))
    print("OUTPUT_PNG="+str(PNG.relative_to(ROOT)))
    print("OUTPUT_AUDIT="+str(AUD.relative_to(ROOT)))

if __name__=="__main__":
    main()
