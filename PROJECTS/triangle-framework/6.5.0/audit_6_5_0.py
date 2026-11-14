#!/usr/bin/env python3
"""Independent audit runner for Cosmic Triangle Framework 6.5.0."""
import csv
import hashlib
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "PROJECTS/triangle-framework/6.5.0/elements_input_118.csv"
OUT = ROOT / "PROJECTS/triangle-framework/6.5.0/output"

RHO_MIN, RHO_MAX = 0.534, 22.59
VM_MIN, VM_MAX = 7.0923, 18.27
R_MIN, R_MAX = 28.0, 203.0
MP_MIN, MP_MAX = -272.2, 3422.0
C_SIDE, EPS, DIAG_TOL = 3.0, 1e-12, 1e-9

L1 = ["Z","Sym","Data_Quality","M_source","rho_source","R_source","mp_source",
      "Vm","rho_n","V_n","R_n","mp_n","theta1","theta2raw","theta2end",
      "theta3","theta4","theta5","S1","S2","S3","S4","S5","a","b","c",
      "Cx","Cy","Gx","Gy","Ix","Iy","Ox","Oy","r","dIO","undefined_reasons"]
L2 = ["Z","Sym","Data_Quality","prov_M","prov_rho","prov_R","prov_mp",
      "den_abs_sin_theta3","den_a_plus_b_plus_3","den_2_sin_theta1",
      "sum_theta_expect_300","sum_theta_dev","sum_S_expect_600","sum_S_dev",
      "theta1_plus_theta2end_plus_theta3","a_coord_DIAGNOSTIC",
      "a_minus_a_coord","n_flags","flags"]

def number(raw):
    if raw is None:
        return None, "NOT_FOUND"
    s = str(raw).strip()
    if not s or s.upper() in {"NA","N/A","NULL","NONE"}:
        return None, "EMPTY"
    try:
        x = float(s)
    except (TypeError, ValueError):
        return None, "NON_NUMERIC"
    if not math.isfinite(x):
        return None, "NON_FINITE"
    return x, None

def fmt(x):
    if x is None:
        return ""
    if isinstance(x, float):
        return format(x, ".15g") if math.isfinite(x) else ""
    return str(x)

def sd(x):
    return math.sin(math.radians(x))

def cd(x):
    return math.cos(math.radians(x))

def calc(row):
    z, sym = row.get("Z",""), row.get("Sym","")
    reasons, flags = [], []
    out = {k: None for k in L1}
    out.update({"Z":z,"Sym":sym,"Data_Quality":row.get("Data_Quality","")})
    for k in ("M_source","rho_source","R_source","mp_source"):
        out[k] = row.get(k,"")

    vals, errs = {}, {}
    for field, key in (("M","M"),("rho","rho"),("R","R"),("mp_C","mp")):
        vals[key], errs[key] = number(row.get(field))
        if errs[key]:
            reasons.append(field + ":" + errs[key])
    M, rho, radius, mp = vals["M"], vals["rho"], vals["R"], vals["mp"]

    Vm = None
    if M is not None and rho is not None:
        if abs(rho) <= EPS:
            reasons.append("Vm:NUMERIC_GUARD")
        else:
            Vm = M / rho
    rho_n = (rho-RHO_MIN)/(RHO_MAX-RHO_MIN) if rho is not None else None
    V_n = (Vm-VM_MIN)/(VM_MAX-VM_MIN) if Vm is not None else None
    R_n = (radius-R_MIN)/(R_MAX-R_MIN) if radius is not None else None
    mp_n = (mp-MP_MIN)/(MP_MAX-MP_MIN) if mp is not None else None
    theta1 = 80-70*rho_n if rho_n is not None else None
    theta2raw = 10+70*V_n if V_n is not None else None
    theta2end = (theta2raw % 360.0) if theta2raw is not None else None
    if theta2end == 0.0:
        theta2end = 360.0
    theta4 = 80-70*R_n if R_n is not None else None
    theta5 = 80-70*mp_n if mp_n is not None else None
    theta3 = (300-(theta1+theta2end+theta4+theta5)
              if all(x is not None for x in (theta1,theta2end,theta4,theta5)) else None)

    derived = {"Vm":Vm,"rho_n":rho_n,"V_n":V_n,"R_n":R_n,"mp_n":mp_n,
      "theta1":theta1,"theta2raw":theta2raw,"theta2end":theta2end,
      "theta3":theta3,"theta4":theta4,"theta5":theta5}
    out.update(derived)
    for k,v in derived.items():
        if v is None:
            reasons.append(k + ":UNDEFINED")

    angles = [theta1,theta2end,theta3,theta4,theta5]
    for i,x in enumerate(angles,1):
        out["S"+str(i)] = 90+x/2 if x is not None else None
    if theta2end is not None and not 10 <= theta2end <= 370:
        flags.append("THETA2END_OUT_OF_RANGE_10_370")
    if theta3 is not None and theta3 < 0:
        flags.append("THETA3_NEGATIVE")
    if theta3 is not None and theta3 > 180:
        flags.append("THETA3_GT_180")

    # Ox is constitutionally independent of all geometry denominators.
    out["c"] = 3.0
    out["Ox"] = 1.5
    a=b=cx=cy=gx=gy=ix=iy=oy=dio=None
    den3 = abs(sd(theta3)) if theta3 is not None else None
    if all(x is not None for x in (theta1,theta2end,theta3)):
        if den3 <= EPS:
            flags.append("NUMERIC_GUARD_ABS_SIN_THETA3")
            reasons.append("a,b:NUMERIC_GUARD_ABS_SIN_THETA3")
        else:
            a = 3.0*sd(theta1)/den3
            b = 3.0*abs(sd(theta2end))/den3
            cx, cy = b*cd(theta1), b*sd(theta1)
            gx, gy = (3.0+cx)/3.0, cy/3.0
            out.update({"a":a,"b":b,"c":3.0,"Cx":cx,"Cy":cy,"Gx":gx,"Gy":gy})
            deni = a+b+3.0
            if abs(deni) <= EPS:
                flags.append("NUMERIC_GUARD_A_PLUS_B_PLUS_3")
                reasons.append("Ix,Iy:NUMERIC_GUARD_A_PLUS_B_PLUS_3")
            else:
                ix = (3*b+3*cx)/deni
                iy = 3*cy/deni
                out.update({"Ix":ix,"Iy":iy,"r":iy})
            deno = 2*sd(theta1)
            if abs(deno) <= EPS:
                flags.append("NUMERIC_GUARD_2_SIN_THETA1")
                reasons.append("Oy:NUMERIC_GUARD_2_SIN_THETA1")
            else:
                oy = (b-3*cd(theta1))/deno
                out["Oy"] = oy
            if ix is not None and iy is not None and oy is not None:
                dio = math.hypot(ix-1.5,iy-oy)
                out["dIO"] = dio
            if a < 0: flags.append("A_NEGATIVE")
            if iy is not None and iy < 0: flags.append("IY_NEGATIVE")
    else:
        reasons.append("geometry:REQUIRED_ANGLE_UNDEFINED")

    a_coord = math.hypot(cx-3.0,cy) if cx is not None and cy is not None else None
    sumtheta = sum(angles) if all(x is not None for x in angles) else None
    sums = [out["S"+str(i)] for i in range(1,6)]
    sumS = sum(sums) if all(x is not None for x in sums) else None
    sum3 = theta1+theta2end+theta3 if all(x is not None for x in (theta1,theta2end,theta3)) else None
    out["undefined_reasons"] = ";".join(dict.fromkeys(reasons))
    diag = {
      "Z":z,"Sym":sym,"Data_Quality":row.get("Data_Quality",""),
      "prov_M":row.get("M_source",""),"prov_rho":row.get("rho_source",""),
      "prov_R":row.get("R_source",""),"prov_mp":row.get("mp_source",""),
      "den_abs_sin_theta3":den3,
      "den_a_plus_b_plus_3":a+b+3 if a is not None and b is not None else None,
      "den_2_sin_theta1":2*sd(theta1) if theta1 is not None else None,
      "sum_theta_expect_300":sumtheta,
      "sum_theta_dev":sumtheta-300 if sumtheta is not None else None,
      "sum_S_expect_600":sumS,
      "sum_S_dev":sumS-600 if sumS is not None else None,
      "theta1_plus_theta2end_plus_theta3":sum3,
      "a_coord_DIAGNOSTIC":a_coord,
      "a_minus_a_coord":a-a_coord if a is not None and a_coord is not None else None,
      "n_flags":len(flags),"flags":";".join(flags)}
    return out,diag

def write_csv(path, fields, rows):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k:fmt(row.get(k)) for k in fields})

def main():
    if not SOURCE.is_file():
        raise FileNotFoundError("Canonical 6.5.0 source file not found: "+str(SOURCE))
    raw=SOURCE.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    with SOURCE.open("r",newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        required={"Z","Sym","M","rho","R","mp_C","M_source","rho_source","R_source","mp_source","Data_Quality"}
        absent=sorted(required-set(reader.fieldnames or []))
        if absent: raise ValueError("Missing CSV columns: "+", ".join(absent))
        rows=list(reader)
    OUT.mkdir(parents=True,exist_ok=True)
    l1,l2=[],[]
    for row in rows:
        a,b=calc(row); l1.append(a); l2.append(b)
    write_csv(OUT/"layer1_constitutional.csv",L1,l1)
    write_csv(OUT/"layer2_diagnostic.csv",L2,l2)
    z=[]
    for row in rows:
        try: z.append(int(row["Z"]))
        except (ValueError,TypeError): pass
    structure_ok=len(rows)==118 and sorted(z)==list(range(1,119))
    sums_ok=all(r["sum_theta_dev"] is None or abs(r["sum_theta_dev"])<=DIAG_TOL for r in l2) and all(r["sum_S_dev"] is None or abs(r["sum_S_dev"])<=DIAG_TOL for r in l2)
    undefined=sum(bool(r["undefined_reasons"]) for r in l1)
    flagged=sum(bool(r["flags"]) for r in l2)
    report=[
      "# تقرير تدقيق دستور 6.5.0","",
      "## هوية المصدر",
      "المسار: "+str(SOURCE.relative_to(ROOT)),
      "SHA-256: "+digest,
      "حجم الملف بالبايت: "+str(len(raw)),
      "عدد الصفوف: "+str(len(rows)),
      "تسلسل Z من 1 إلى 118: "+("PASS" if structure_ok else "FAIL"),"",
      "## فحوص الهويات",
      "مجموع الزوايا الخمس = 300 ضمن DIAG_TOL: "+("PASS" if sums_ok else "FAIL"),
      "صفوف تحتوي قيماً غير معرفة: "+str(undefined),
      "صفوف تحمل أعلاماً تشخيصية: "+str(flagged),"",
      "## قواعد التنفيذ",
      "theta2end = theta2raw % 360؛ والصفر يصبح 360.",
      "لا clamp للقيم المعيارية خارج [0,1].",
      "Ox=1.5 مستقل ويظل معرفاً حتى عند تعذر حساب الأضلاع.",
      "a_coord تشخيص فقط ولا يستبدل a الدستوري.",
      "لا حساب لمساحة أو أقواس كروية؛ لا توجد معادلات لها في الدستور.","",
      "نجاح الهويات لا يثبت الاتساق الإقليدي للمثلث أو صحة تفسير كروي.",
      "بصمة المصدر تثبت الملف الذي قرأه التشغيل، ولا تثبت صحة القياسات أو مصادرها العلمية."]
    (OUT/"audit_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    (OUT/"source_manifest.txt").write_text(
      "source_path="+str(SOURCE.relative_to(ROOT))+"\nsource_sha256="+digest+
      "\nsource_bytes="+str(len(raw))+"\nsource_rows="+str(len(rows))+"\n",encoding="utf-8")
    print("=== TRIANGLE FRAMEWORK 6.5.0 AUDIT ===")
    print("source_sha256: "+digest)
    print("source_bytes: "+str(len(raw)))
    print("source_rows: "+str(len(rows)))
    print("source_structure: "+("PASS" if structure_ok else "FAIL"))
    print("sum_identities: "+("PASS" if sums_ok else "FAIL"))
    print("rows_with_undefined_values: "+str(undefined))
    print("rows_with_diagnostic_flags: "+str(flagged))
    print("outputs: "+str(OUT.relative_to(ROOT)))
    if not structure_ok or not sums_ok: raise SystemExit("AUDIT FAILED")
    print("=== AUDIT COMPLETED ===")

if __name__=="__main__":
    main()
