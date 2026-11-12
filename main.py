# =====================================================
# الإطار 6.2.2-R — v4.2 (Final Engine، مع self-test)
# =====================================================
import math
import json
import urllib.request

# ===== الثوابت =====
RHO_MIN = 1.74
RHO_MAX = 22.59
VM_MIN  = 7.10
VM_MAX  = 18.27
C_SIDE  = 3.0

EPS_R2_DEGEN     = 1e-9
EPS_R3_DEGEN     = 1e-15
EPS_CY_UNSTABLE  = 1e-4
EPS_CY_DEGEN     = 1e-9
EPS_MULT60       = 1e-9
EPS_HINGE        = 0.02
EPS_NUMERICAL    = -1e-12
EPS_TIE          = 0.05

GAS_SYMBOLS        = {"H", "He", "N", "O", "F", "Ne", "Cl", "Ar", "Kr", "Xe", "Rn"}
GAS_DIVISOR        = 1000.0
GAS_UNIT_THRESHOLD = 0.01

MODE_UNSTABLE = {"H", "K", "Rb", "Cs"}

DEEP_THRESHOLD    = 0.4
MEDIUM_THRESHOLD  = 0.2
SHALLOW_THRESHOLD = 0.05


def compute_element(Z, symbol, M, rho_original):
    rho = rho_original
    unit_fix_applied = False
    if symbol in GAS_SYMBOLS and rho > GAS_UNIT_THRESHOLD:
        rho = rho / GAS_DIVISOR
        unit_fix_applied = True

    V_m   = M / rho
    rho_n = (rho - RHO_MIN) / (RHO_MAX - RHO_MIN)
    V_n   = (V_m - VM_MIN) / (VM_MAX - VM_MIN)
    theta_1     = 80.0 - 70.0 * rho_n
    theta_2_raw = 10.0 + 70.0 * V_n
    theta_3_raw = 180.0 - theta_1 - theta_2_raw

    zip_mode = "none"
    n = 0
    if theta_2_raw < 0:
        theta_2_vis = theta_2_raw + 60.0
        theta_3_vis = theta_3_raw - 60.0
        zip_mode = "inverse"
    elif theta_2_raw > 60.0:
        n = math.floor(theta_2_raw / 60.0)
        if n > 0 and abs(theta_2_raw - 60.0 * n) < EPS_MULT60:
            n -= 1
        theta_2_vis = theta_2_raw - 60.0 * n
        theta_3_vis = 180.0 - theta_1 - theta_2_vis
        zip_mode = "extended_60f" if theta_3_raw >= 0 else "60f"
    else:
        theta_2_vis = theta_2_raw
        theta_3_vis = theta_3_raw

    if (theta_1 < 0 or theta_2_vis < 0 or theta_3_vis < 0
            or theta_3_vis > 180.0):
        return {"INVALID_TRIANGLE": True, "Z": Z, "sym": symbol,
                "reason": f"angles: th1={theta_1:.2f}, th2v={theta_2_vis:.2f}, th3v={theta_3_vis:.2f}"}

    r1 = math.radians(theta_1)
    r2 = math.radians(theta_2_vis)
    r3 = math.radians(theta_3_vis)
    s1 = math.sin(r1)
    s2 = math.sin(r2)
    s3 = math.sin(r3)

    if abs(s3) < EPS_R3_DEGEN or abs(s2) < EPS_R2_DEGEN:
        return {"INVALID_TRIANGLE": True, "Z": Z, "sym": symbol,
                "reason": f"degenerate: sin(th2)={s2:.2e}, sin(th3)={s3:.2e}"}

    a = C_SIDE * s1 / s3
    b = C_SIDE * abs(s2) / s3
    c = C_SIDE
    if a <= 0 or b <= 0:
        return {"INVALID_TRIANGLE": True, "Z": Z, "sym": symbol,
                "reason": f"side<=0: a={a:.4f}, b={b:.4f}"}

    C_x = b * math.cos(r1)
    C_y = b * math.sin(r1)

    s_perim = (a + b + c) / 2.0
    area_sq = s_perim * (s_perim - a) * (s_perim - b) * (s_perim - c)
    flags = []
    if area_sq < EPS_NUMERICAL:
        flags.append("NUMERICAL")
        area_sq = 0.0
    area = math.sqrt(area_sq)
    r = (area / s_perim) if s_perim > 0 else 0.0
    R = (a * b * c) / (4.0 * area) if area > 0 else float("inf")

    I_x = (C_SIDE * b + C_SIDE * C_x) / (a + b + c)
    I_y = (C_SIDE * C_y) / (a + b + c)

    O_x = C_SIDE / 2.0
    if abs(C_y) < EPS_CY_DEGEN:
        O_y = None
        flags.append("DEGENERATE")
    else:
        O_y = (C_x * C_x + C_y * C_y - C_SIDE * C_x) / (2.0 * C_y)
        if abs(C_y) < EPS_CY_UNSTABLE:
            flags.append("UNSTABLE")

    if O_y is None:
        d_IO = None
        delta_y = None
        classification = "-"
    else:
        d_IO = math.sqrt((O_x - I_x) ** 2 + (O_y - I_y) ** 2)
        delta_y = O_y - I_y
        classification = "UP" if delta_y > 0 else "DOWN"

    if symbol in MODE_UNSTABLE:
        flags.append("MODE-UNSTABLE")

    in_box = (RHO_MIN <= rho <= RHO_MAX) and (VM_MIN <= V_m <= VM_MAX)
    hinge_margin = min(
        abs(rho - RHO_MIN), abs(rho - RHO_MAX),
        abs(V_m - VM_MIN), abs(V_m - VM_MAX),
    )
    if hinge_margin < EPS_HINGE:
        flags.append("BOX-HINGE")
    if not in_box:
        flags.append("OUT-OF-BOX")
    if unit_fix_applied:
        flags.append("GAS")

    anomaly = None
    record = None
    if delta_y is not None:
        if theta_3_vis < 90.0 and delta_y < 0:
            anomaly = "th3_lt_90_but_down"
        elif theta_3_vis > 90.0 and delta_y > 0:
            anomaly = "th3_gt_90_but_up"
        if anomaly:
            abs_dy = abs(delta_y)
            if abs_dy < EPS_TIE:
                record = "TIE-ANOMALY"
                flags.append("TIE")
            elif in_box:
                if abs_dy > DEEP_THRESHOLD:
                    record = "A-DEEP"
                elif abs_dy > MEDIUM_THRESHOLD:
                    record = "A-MEDIUM"
                elif abs_dy > SHALLOW_THRESHOLD:
                    record = "A-SHALLOW"
                else:
                    record = "A-MARGINAL"
            else:
                record = "B-DERIVED"

    return {
        "Z": Z, "sym": symbol, "M": M,
        "rho_original": rho_original, "rho": rho, "unit_fix": unit_fix_applied,
        "V_m": V_m, "rho_n": rho_n, "V_n": V_n,
        "theta_1": theta_1,
        "theta_2_raw": theta_2_raw, "theta_3_raw": theta_3_raw,
        "zip": zip_mode, "n": n,
        "theta_2_vis": theta_2_vis, "theta_3_vis": theta_3_vis,
        "a": a, "b": b, "c": c, "s": s_perim, "area": area,
        "r": r, "R": R,
        "I_x": I_x, "I_y": I_y,
        "O_x": O_x, "O_y": O_y,
        "d_IO": d_IO, "delta_y": delta_y,
        "class": classification,
        "in_box": in_box, "hinge_margin": hinge_margin,
        "anomaly": anomaly, "record": record,
        "flags": ";".join(flags),
    }


def row_csv(d):
    if d.get("INVALID_TRIANGLE"):
        return f"{d['Z']},{d['sym']},INVALID_TRIANGLE,{d['reason']}"
    Oy = f"{d['O_y']:.4f}" if d['O_y'] is not None else "NONE"
    dy = f"{d['delta_y']:+.4f}" if d['delta_y'] is not None else "NONE"
    dio = f"{d['d_IO']:.4f}" if d['d_IO'] is not None else "NONE"
    return (f"{d['Z']},{d['sym']},{d['rho_original']:.8g},{d['rho']:.8g},"
            f"{d['V_m']:.4f},{d['rho_n']:.6f},{d['V_n']:.6f},"
            f"{d['theta_1']:.4f},{d['theta_2_raw']:.4f},{d['theta_3_raw']:.4f},"
            f"{d['zip']},{d['n']},{d['theta_2_vis']:.4f},{d['theta_3_vis']:.4f},"
            f"{d['a']:.4f},{d['b']:.4f},{d['s']:.4f},{d['area']:.6f},"
            f"{d['r']:.4f},{d['R']:.4f},"
            f"{d['I_x']:.4f},{d['I_y']:.4f},{d['O_x']:.4f},{Oy},"
            f"{dio},{dy},{d['class']},{d['anomaly'] or '-'},{d['record'] or '-'},"
            f"{d['flags']}")


HEADER = ("Z,sym,rho_orig,rho_used,V_m,rho_n,V_n,th1,th2_raw,th3_raw,"
          "zip,n,th2v,th3v,a,b,s,Area,r,R,I_x,I_y,O_x,O_y,d_IO,dy,"
          "class,anomaly,record,flags")


# =====================================================
# SELF-TEST
# =====================================================
print("=== SELF-TEST ===")
_li = compute_element(3, "Li", 6.94, 0.534)
assert abs(_li['theta_1'] - 84.0489) < 0.01, f"FAIL theta_1={_li['theta_1']}"
assert abs(_li['a'] - 3.9536) < 0.05, f"FAIL a={_li['a']}"
_lhs = _li['a'] / math.sin(math.radians(_li['theta_1']))
_rhs = 3.0 / math.sin(math.radians(_li['theta_3_vis']))
assert abs(_lhs - _rhs) < 1e-9, f"FAIL law of sines: {_lhs} vs {_rhs}"
print(f"Li: theta_1={_li['theta_1']:.4f}, a={_li['a']:.4f}, law-of-sines OK")
print("=== SELF-TEST PASSED ===")


# =====================================================
# CHECK-10
# =====================================================
ELEMENTS_10 = [
    (1,  "H",  1.008,   0.08988),
    (3,  "Li", 6.94,    0.534),
    (4,  "Be", 9.0122,  1.85),
    (11, "Na", 22.990,  0.968),
    (19, "K",  39.098,  0.862),
    (26, "Fe", 55.845,  7.874),
    (29, "Cu", 63.546,  8.96),
    (37, "Rb", 85.468,  1.532),
    (55, "Cs", 132.905, 1.93),
    (76, "Os", 190.23,  22.59),
]

print("\n" + HEADER)
print("=== CHECK-10 ===")
for Z, sym, M, rho in ELEMENTS_10:
    d = compute_element(Z, sym, M, rho)
    print(row_csv(d))
print("=== END CHECK-10 ===")


# =====================================================
# FULL-118
# =====================================================
print("\n=== FULL-118 ===")
url = "https://raw.githubusercontent.com/Bowserinator/Periodic-Table-JSON/master/PeriodicTableJSON.json"
elements = []
try:
    with urllib.request.urlopen(url, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
        elements = data.get("elements", [])
    print(f"# loaded {len(elements)} elements from Bowserinator")
except Exception as e:
    print(f"# NETWORK ERROR: {e}")

missing = []
invalid = []
valid = []
for el in elements:
    Z = el.get("number")
    sym = el.get("symbol")
    M = el.get("atomic_mass")
    rho = el.get("density")
    if Z is None or sym is None or M is None or rho is None or rho == 0:
        missing.append((Z, sym))
        continue
    d = compute_element(Z, sym, M, rho)
    if d.get("INVALID_TRIANGLE"):
        invalid.append(d)
    else:
        valid.append(d)
    print(row_csv(d))
print("=== END FULL-118 ===")


# =====================================================
# القوائم
# =====================================================
print("\n=== LIST: MISSING ===")
for Z, sym in missing:
    print(f"({Z}, '{sym}')")

print("\n=== LIST: INVALID_TRIANGLE ===")
for d in invalid:
    print(f"({d['Z']}, '{d['sym']}', '{d['reason']}')")

print("\n=== LIST: GAS ===")
for d in valid:
    if d['unit_fix']:
        print(f"({d['Z']}, '{d['sym']}')")

print("\n=== LIST: MODE-UNSTABLE ===")
for d in valid:
    if 'MODE-UNSTABLE' in d['flags']:
        print(f"({d['Z']}, '{d['sym']}')")

print("\n=== LIST: TIE-ANOMALY ===")
for d in valid:
    if d['record'] == 'TIE-ANOMALY':
        print(f"({d['Z']}, '{d['sym']}', dy={d['delta_y']:+.4f})")

for rec_name in ['A-DEEP', 'A-MEDIUM', 'A-SHALLOW', 'A-MARGINAL', 'B-DERIVED']:
    print(f"\n=== LIST: {rec_name} ===")
    for d in valid:
        if d['record'] == rec_name:
            print(f"({d['Z']}, '{d['sym']}', th3v={d['theta_3_vis']:.2f}, dy={d['delta_y']:+.4f})")


# =====================================================
# الملخص
# =====================================================
print("\n=== SUMMARY ===")
print(f"elements loaded: {len(elements)}")
print(f"valid: {len(valid)}")
print(f"invalid_triangle: {len(invalid)}")
print(f"missing: {len(missing)}")
print(f"gas_fixed: {sum(1 for d in valid if d['unit_fix'])}")
print(f"in_box: {sum(1 for d in valid if d['in_box'])}")
print(f"out_of_box: {sum(1 for d in valid if not d['in_box'])}")
print(f"anomalies_total: {sum(1 for d in valid if d['record'])}")
for rec_name in ['A-DEEP', 'A-MEDIUM', 'A-SHALLOW', 'A-MARGINAL', 'B-DERIVED', 'TIE-ANOMALY']:
    cnt = sum(1 for d in valid if d['record'] == rec_name)
    print(f"  {rec_name}: {cnt}")

law_violations = 0
for d in valid:
    lhs = d['a'] / math.sin(math.radians(d['theta_1']))
    rhs = 3.0 / math.sin(math.radians(d['theta_3_vis']))
    if abs(lhs - rhs) > 1e-6:
        law_violations += 1
print(f"law_of_sines_violations: {law_violations}")

angle_violations = 0
for d in valid:
    total = d['theta_1'] + d['theta_2_vis'] + d['theta_3_vis']
    if abs(total - 180.0) > 1e-6:
        angle_violations += 1
print(f"angle_sum_violations: {angle_violations}")
print("=== END ===")