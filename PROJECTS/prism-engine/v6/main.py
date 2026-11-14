# THE EYE OF THE PRISM — v6 (Truth-first)
# Independent copy; v5 is not modified.
import csv
import hashlib
import json
import math
import os
import statistics
import urllib.request
from datetime import datetime, timezone

SOURCE_COMMIT = "a78c7a48fe7235cebd6153161a9e7fa70f0cfb30"
SOURCE_BLOB_SHA = "2424af6ef572dd52325697570c4dc79578d5b7be"
DATA_URL = "https://raw.githubusercontent.com/Bowserinator/Periodic-Table-JSON/" + SOURCE_COMMIT + "/PeriodicTableJSON.json"
RHO_MIN, RHO_MAX = 1.74, 22.59
VM_MIN, VM_MAX = 7.10, 18.27
C_BASE, V5_FACTOR = 3.0, 0.016
EPS, EPS_MULT60 = 1e-10, 1e-9
GASES = {"H", "He", "N", "O", "F", "Ne", "Cl", "Ar", "Kr", "Xe", "Rn"}
OUT = "outputs"
ELEMENTS_CSV = OUT + "/v6_elements_118_plus_extensions.csv"
PREDICTIONS_CSV = OUT + "/v6_mass_predictions_119_126.csv"
AUDIT_JSON = OUT + "/v6_run_audit.json"


def legacy_angles(mass, rho):
    vm = mass / rho
    rn = (rho - RHO_MIN) / (RHO_MAX - RHO_MIN)
    vn = (vm - VM_MIN) / (VM_MAX - VM_MIN)
    t1 = 80.0 - 70.0 * rn
    t2r = 10.0 + 70.0 * vn
    t3r = 180.0 - t1 - t2r
    n, mode = 0, "none"
    if t2r < 0:
        t2, t3, mode = t2r + 60.0, t3r - 60.0, "inverse"
    elif t2r > 60:
        n = math.floor(t2r / 60.0)
        if n > 0 and abs(t2r - 60.0*n) < EPS_MULT60:
            n -= 1
        t2 = t2r - 60.0*n
        t3 = 180.0 - t1 - t2
        mode = "extended_60f" if t3r >= 0 else "60f"
    else:
        t2, t3 = t2r, t3r
    return {"V_m": vm, "rho_n": rn, "V_n": vn, "theta_1": t1,
            "theta_2_raw": t2r, "theta_3_raw": t3r,
            "theta_2_vis": t2, "theta_3_vis": t3, "zip_n": n, "zip_mode": mode}


def triangle(a, b, c):
    a, b, c = map(float, (a, b, c))
    if not all(map(math.isfinite, (a, b, c))):
        raise ValueError("NON_FINITE_SIDE")
    if min(a, b, c) <= 0:
        raise ValueError("NON_POSITIVE_SIDE")
    if a+b <= c+EPS or a+c <= b+EPS or b+c <= a+EPS:
        raise ValueError("TRIANGLE_INEQUALITY")
    # A=(0,0), B=(c,0), AC=b, BC=a.
    x = (b*b + c*c - a*a)/(2*c)
    y2 = b*b - x*x
    if y2 <= EPS:
        raise ValueError("DEGENERATE_TRIANGLE")
    y = math.sqrt(y2)
    p = a+b+c
    ix, iy = (b*c+c*x)/p, c*y/p
    gx, gy = (c+x)/3.0, y/3.0
    area = 0.5*c*y
    A = math.degrees(math.acos(max(-1.0, min(1.0, (b*b+c*c-a*a)/(2*b*c)))))
    B = math.degrees(math.acos(max(-1.0, min(1.0, (a*a+c*c-b*b)/(2*a*c)))))
    C = 180.0-A-B
    return {"a":a,"b":b,"c":c,"perimeter":p,"area":area,
            "C_x":x,"C_y":y,"I_x":ix,"I_y":iy,"G_x":gx,"G_y":gy,
            "angle_A_from_sides":A,"angle_B_from_sides":B,
            "angle_C_from_sides":C,"angle_sum_check":A+B+C}


def angle_triangle(angles, base_side=3.0):
    t1,t2,t3 = angles
    if not all(math.isfinite(x) for x in angles):
        raise ValueError("NON_FINITE_ANGLE")
    if any(x <= EPS or x >= 180.0-EPS for x in angles):
        raise ValueError("ANGLES_OUTSIDE_EUCLIDEAN_DOMAIN")
    if abs(sum(angles)-180.0) > 1e-7:
        raise ValueError("ANGLE_SUM_NOT_180")
    s3 = math.sin(math.radians(t3))
    if abs(s3) <= EPS:
        raise ValueError("DEGENERATE_SINE")
    g = triangle(base_side*math.sin(math.radians(t1))/s3,
                 base_side*math.sin(math.radians(t2))/s3, base_side)
    g.update({"angle_input_A":t1,"angle_input_B":t2,"angle_input_C":t3})
    return g


def compute_element(el):
    z, sym = el.get("number"), el.get("symbol")
    mass, rho0 = el.get("atomic_mass"), el.get("density")
    base = {"Z":z,"symbol":sym,"atomic_mass_source":mass,"density_source":rho0,
            "source_category":el.get("category"),"source_group":el.get("group"),
            "source_period":el.get("period"),"source_quality":"NOT_SPECIFIED_IN_PINNED_SOURCE"}
    if z is None or sym is None or mass is None or rho0 is None:
        return {**base,"source_status":"MISSING_REQUIRED_SOURCE_VALUE",
                "angle_triangle_status":"NOT_COMPUTED","v5_side_status":"NOT_COMPUTED"}
    try:
        z, mass, rho = int(z), float(mass), float(rho0)
    except (TypeError,ValueError,OverflowError):
        return {**base,"source_status":"INVALID_SOURCE_VALUE",
                "angle_triangle_status":"NOT_COMPUTED","v5_side_status":"NOT_COMPUTED"}
    if not all(math.isfinite(v) for v in (mass,rho)) or mass <= 0 or rho <= 0:
        return {**base,"source_status":"INVALID_SOURCE_VALUE",
                "angle_triangle_status":"NOT_COMPUTED","v5_side_status":"NOT_COMPUTED"}
    rho_used = rho/1000.0 if sym in GASES and rho > 0.01 else rho
    ang = legacy_angles(mass,rho_used)
    row = {**base,**ang,"rho_used":rho_used,"gas_unit_fix_applied":rho_used != rho,
           "source_status":"VALID_SOURCE_NUMERIC","angle_triangle_status":"NOT_COMPUTED",
           "v5_side_status":"NOT_COMPUTED"}
    # Primary lane: true Euclidean triangle only when the inherited angles qualify.
    try:
        g = angle_triangle((ang["theta_1"],ang["theta_2_vis"],ang["theta_3_vis"]))
        row.update({"angle_"+k:v for k,v in g.items()})
        row["angle_triangle_status"] = "VALID_EUCLIDEAN_TRIANGLE"
    except ValueError as exc:
        row["angle_triangle_status"] = str(exc)
        row["primary_geometry"] = "NO_TRIANGLE_NO_FORCED_RESCUE"
    # v5 side definitions remain visible as a separate, unchanged comparison lane.
    t2,t3 = math.radians(ang["theta_2_vis"]),math.radians(ang["theta_3_vis"])
    s3 = math.sin(t3)
    if abs(s3) <= EPS:
        row["v5_side_status"] = "LEGACY_SINE_DEGENERATE"
    else:
        a5, b5 = z/10.0, 3.0*abs(math.sin(t2))/s3
        c5 = 3.0 + V5_FACTOR*(mass-z)
        row.update({"v5_a_Z_over_10":a5,"v5_b_legacy_angle":b5,
                    "v5_c_3_plus_0016_M_minus_Z":c5,
                    "v5_neutron_proxy_M_minus_Z":mass-z})
        try:
            row.update({"v5_"+k:v for k,v in triangle(a5,b5,c5).items()})
            row["v5_side_status"] = "VALID_EUCLIDEAN_TRIANGLE"
        except ValueError as exc:
            row["v5_side_status"] = str(exc)
    return row


def mad(values):
    m = statistics.median(values)
    return statistics.median([abs(x-m) for x in values])


def predict_masses(elements, first_z=119, last_z=126):
    # Exploratory mass-only extrapolation. Never predicts density or a triangle.
    byz = {}
    for el in elements:
        try:
            z,m = int(el.get("number")),float(el.get("atomic_mass"))
            if math.isfinite(m) and m > 0: byz[z] = m
        except (TypeError,ValueError,OverflowError):
            pass
    inc = [byz[z]-byz[z-1] for z in range(105,119) if z in byz and z-1 in byz][-10:]
    if len(inc) < 5 or first_z-1 not in byz:
        return [{"Z":z,"prediction_status":"INSUFFICIENT_TRAINING_DATA"} for z in range(first_z,last_z+1)]
    step, spread = statistics.median(inc), mad(inc)
    errors = []
    for target in sorted(z for z in byz if 114 <= z <= 118):
        prior = [byz[k]-byz[k-1] for k in range(105,target) if k in byz and k-1 in byz][-10:]
        if len(prior) >= 5 and target-1 in byz:
            errors.append(abs(byz[target-1]+statistics.median(prior)-byz[target]))
    backtest_mae = statistics.mean(errors) if errors else None
    guess = byz[first_z-1] + step
    comparator = byz.get(first_z)
    error = abs(guess-comparator) if comparator is not None else None
    limit = max(3.0,2.0*backtest_mae) if backtest_mae is not None else 3.0
    passed = error is None or error <= limit
    out = [{"Z":first_z,"predicted_atomic_mass_scenario":guess,
            "increment_median_training":step,"increment_MAD_training":spread,
            "backtest_MAE_last_5":backtest_mae,"source_atomic_mass_comparator":comparator,
            "comparator_source_quality":"NOT_SPECIFIED_IN_PINNED_SOURCE",
            "comparator_absolute_error":error,"operational_validation_limit":limit,
            "prediction_method":"median of last 10 adjacent mass increments, Z=104..118",
            "prediction_status":"PROVISIONAL_SCENARIO" if comparator is None else
                ("SCENARIO_WITHIN_OPERATIONAL_LIMIT" if passed else
                 "SCENARIO_DISAGREES_WITH_UNVERIFIED_SOURCE_COMPARATOR"),
            "triangle_prediction_status":"NOT_PREDICTED_NO_DENSITY_MODEL"}]
    if not passed:
        out.extend({"Z":z,"prediction_status":"SUPPRESSED_UNRESOLVED_Z119_COMPARATOR",
                    "reason":"Z=119 source value is unverified and differs beyond the operational limit; downstream extrapolation is withheld.",
                    "triangle_prediction_status":"NOT_PREDICTED"} for z in range(first_z+1,last_z+1))
        return out
    prev = guess
    for z in range(first_z+1,last_z+1):
        prev += step
        out.append({"Z":z,"predicted_atomic_mass_scenario":prev,
                    "increment_median_training":step,"increment_MAD_training":spread,
                    "backtest_MAE_last_5":backtest_mae,
                    "prediction_method":"median of last 10 adjacent mass increments, Z=104..118",
                    "prediction_status":"SCENARIO_EXTRAPOLATION_NOT_MEASURED",
                    "triangle_prediction_status":"NOT_PREDICTED_NO_DENSITY_MODEL"})
    return out


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path),exist_ok=True)
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with open(path,"w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def self_test():
    g=triangle(4,3,5)
    assert abs(g["area"]-6)<1e-9 and abs(g["I_x"]-2)<1e-9 and abs(g["I_y"]-1)<1e-9
    q=angle_triangle((30.0,60.0,90.0),2.0)
    assert abs(q["a"]-1)<1e-8 and abs(q["b"]-math.sqrt(3))<1e-8
    for bad in [(-5.0,80.0,105.0),(20.0,20.0,20.0)]:
        try: angle_triangle(bad)
        except ValueError: pass
        else: raise AssertionError("invalid angle set accepted")
    try: triangle(1,1,3)
    except ValueError as exc: assert str(exc)=="TRIANGLE_INEQUALITY"
    else: raise AssertionError("invalid side set accepted")
    synthetic=[{"number":z,"atomic_mass":2.5*z+0.1*(z%3)} for z in range(100,119)]
    assert predict_masses(synthetic,119,120)[0]["prediction_status"]=="PROVISIONAL_SCENARIO"
    print("SELF-TEST PASSED: Euclidean geometry, angle gate, v5 comparison, prediction separation")


def main():
    self_test()
    req=urllib.request.Request(DATA_URL,headers={"User-Agent":"Prism-Engine-v6"})
    with urllib.request.urlopen(req,timeout=45) as response: raw=response.read()
    actual=hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()
    if actual != SOURCE_BLOB_SHA:
        raise RuntimeError("SOURCE_CHECKSUM_MISMATCH: expected "+SOURCE_BLOB_SHA+", got "+actual)
    elements=json.loads(raw.decode("utf-8")).get("elements",[])
    byz={int(e["number"]):e for e in elements if e.get("number") is not None}
    rows=[]
    for z in range(1,119):
        el=byz.get(z)
        rows.append(compute_element(el) if el else {"Z":z,"source_status":"ELEMENT_NOT_IN_SOURCE",
                     "angle_triangle_status":"NOT_COMPUTED","v5_side_status":"NOT_COMPUTED"})
    extension=[compute_element(e) for z,e in sorted(byz.items()) if z>118]
    for r in extension: r["scope_note"]="SOURCE_EXTENSION_OUTSIDE_118_ELEMENT_BASELINE"
    predictions=predict_masses(elements,119,126)
    write_csv(ELEMENTS_CSV,rows+extension)
    write_csv(PREDICTIONS_CSV,predictions)
    counts={}
    for r in rows:
        k=r.get("angle_triangle_status","UNKNOWN"); counts[k]=counts.get(k,0)+1
    audit={"engine":"Prism Engine v6 — Truth-first","run_utc":datetime.now(timezone.utc).isoformat(),
           "source_repository":"Bowserinator/Periodic-Table-JSON","source_path":"PeriodicTableJSON.json",
           "source_commit":SOURCE_COMMIT,"expected_source_git_blob_sha":SOURCE_BLOB_SHA,
           "actual_source_git_blob_sha":actual,"source_elements_loaded":len(elements),
           "baseline_rows_1_to_118":len(rows),"extension_source_rows_over_118":len(extension),
           "angle_triangle_status_counts_1_to_118":counts,"prediction_rows":len(predictions),
           "prediction_scope":"mass-only scenario; Z=119 comparator gate; no density/future triangle invented",
           "rules":["source and derived values are separate","primary triangle requires valid positive angles summing to 180",
                    "no clipping, scaling, or silent rescue","v5 sides retained only as comparison",
                    "predictions are not measurements","failed/unverified Z=119 comparison suppresses later forecasts",
                    "no future triangle without a density model"]}
    os.makedirs(OUT,exist_ok=True)
    with open(AUDIT_JSON,"w",encoding="utf-8") as f: json.dump(audit,f,ensure_ascii=False,indent=2)
    print("=== PRISM V6 SUMMARY ===")
    print("source_elements_loaded:",len(elements))
    print("baseline_rows_1_to_118:",len(rows))
    print("extension_source_rows_over_118:",len(extension))
    for k in sorted(counts): print("angle_triangle::"+k+":",counts[k])
    print("prediction_rows_119_to_126:",len(predictions))
    print("elements_csv:",ELEMENTS_CSV)
    print("predictions_csv:",PREDICTIONS_CSV)
    print("audit_json:",AUDIT_JSON)
    print("=== END PRISM V6 ===")


if __name__ == "__main__":
    main()
