#!/usr/bin/env python3
"""Cosmic Triangle Framework 6.5.0 — reconstructed calculation engine.

Implements the user's 6.5.0 constitution literally. It does not claim that
the 300-degree angle system is a Euclidean triangle; the side/coordinate
expressions are retained as prescribed and are reported as model outputs.
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INPUT = ROOT / "PROJECTS/triangle-framework/6.5.0/elements_input_118.csv"
OUTPUT_DIR = ROOT / "PROJECTS/triangle-framework/6.5.0/output"
OUTPUT = OUTPUT_DIR / "elements_6.5.0_results.csv"
SUMMARY = OUTPUT_DIR / "SUMMARY_6.5.0.txt"

RHO_MIN, RHO_MAX = 0.534, 22.59
VM_MIN, VM_MAX = 7.0923, 18.27
R_MIN, R_MAX = 28.0, 203.0
MP_MIN, MP_MAX = -272.2, 3422.0
C_SIDE = 3.0
EPS = 1e-12

GASES = {"H", "He", "N", "O", "F", "Ne", "Cl", "Ar", "Kr", "Xe", "Rn", "Og"}
LN_RANGE = set(range(57, 72))
AN_RANGE = set(range(89, 104))

OUTPUT_FIELDS = [
    "Z", "Sym", "M", "rho", "R", "mp_C", "Vm",
    "rho_n", "V_n", "R_n", "mp_n",
    "theta1_material", "theta2_raw_spacetime", "theta2_end",
    "n_turns", "theta4_atomic_volume", "theta5_melting",
    "theta3_law", "SumTheta",
    "S_A", "S_B", "S_C", "S_R", "S_M", "SumS",
    "a", "b", "c", "a_over_b",
    "Ax", "Ay", "Bx", "By", "Cx", "Cy",
    "Ix", "Iy", "Gx", "Gy", "inradius_r", "area_projected",
    "Data_Quality", "Family", "GAS", "Flags", "Notes"
]

def num(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value or value.upper() in {"NOT_FOUND", "NA", "NULL", "NONE"}:
        return None
    try:
        x = float(value)
    except ValueError:
        return None
    return x if math.isfinite(x) else None

def fmt(x):
    if x is None:
        return "NOT_FOUND"
    if isinstance(x, str):
        return x
    if math.isinf(x):
        return "INF" if x > 0 else "-INF"
    if math.isnan(x):
        return "NOT_FOUND"
    return f"{x:.10g}"

def normalize(value, low, high):
    return (value - low) / (high - low)

def add_flag(flags, flag):
    if flag not in flags:
        flags.append(flag)

def safe_div(a, b):
    if abs(b) <= EPS:
        return math.inf if a >= 0 else -math.inf
    return a / b

def compute(row):
    z = int(row["Z"])
    sym = row["Sym"].strip()
    M, rho, radius, mp = (num(row.get(k)) for k in ("M", "rho", "R", "mp_C"))
    flags = []

    quality = (row.get("Data_Quality") or "").strip().upper()
    family = (row.get("Family") or "").strip()
    gas = "YES" if sym in GASES or (row.get("GAS") or "").strip().upper() == "YES" else "NO"
    notes = (row.get("Notes") or "").strip()

    if quality == "PREDICTED":
        add_flag(flags, "PREDICTED")
    if "EST" in notes.upper() or "ESTIMATE" in notes.upper() or "THEORETICAL" in notes.upper():
        add_flag(flags, "EST")
    if any(str(row.get(k, "")).strip().upper() == "NOT_FOUND" for k in ("M", "rho", "R", "mp_C")):
        add_flag(flags, "NOT_FOUND")

    # Rho and melting point are mandatory under the 6.5.0 missing-data rule.
    # M and R are also required mathematically for Vm and theta4.
    missing = [name for name, value in (("M", M), ("rho", rho), ("R", radius), ("mp_C", mp)) if value is None]
    if missing:
        add_flag(flags, "NO_DATA")
        row_out = {k: row.get(k, "") for k in ("Z", "Sym", "M", "rho", "R", "mp_C")}
        row_out.update({k: "NOT_FOUND" for k in OUTPUT_FIELDS if k not in row_out})
        row_out.update({
            "Data_Quality": "NO_DATA", "Family": family, "GAS": gas,
            "Flags": "|".join(flags), "Notes": (notes + " | Missing required input: " + ",".join(missing)).strip(" |")
        })
        return row_out

    if rho <= 0:
        add_flag(flags, "NO_DATA")
        row_out = {k: row.get(k, "") for k in ("Z", "Sym", "M", "rho", "R", "mp_C")}
        row_out.update({k: "NOT_FOUND" for k in OUTPUT_FIELDS if k not in row_out})
        row_out.update({"Data_Quality": "NO_DATA", "Family": family, "GAS": gas,
                        "Flags": "|".join(flags + ["INVALID_RHO"]), "Notes": notes})
        return row_out

    Vm = M / rho
    rho_n = normalize(rho, RHO_MIN, RHO_MAX)
    V_n = normalize(Vm, VM_MIN, VM_MAX)
    R_n = normalize(radius, R_MIN, R_MAX)
    mp_n = normalize(mp, MP_MIN, MP_MAX)

    theta1 = 80.0 - 70.0 * rho_n
    theta2_raw = 10.0 + 70.0 * V_n
    theta2_end = theta2_raw % 360.0
    if abs(theta2_end) <= EPS:
        theta2_end = 360.0
    n_turns = math.floor(theta2_raw / 360.0)
    theta4 = 80.0 - 70.0 * R_n
    theta5 = 80.0 - 70.0 * mp_n
    theta3 = 300.0 - (theta1 + theta2_end + theta4 + theta5)
    sum_theta = theta1 + theta2_end + theta3 + theta4 + theta5

    doses = {
        "S_A": 90.0 + theta1 / 2.0,
        "S_B": 90.0 + theta2_end / 2.0,
        "S_C": 90.0 + theta3 / 2.0,
        "S_R": 90.0 + theta4 / 2.0,
        "S_M": 90.0 + theta5 / 2.0,
    }
    sum_doses = sum(doses.values())

    if not 0.0 <= rho_n <= 1.0:
        add_flag(flags, "RHO_OUT")
    if not 0.0 <= V_n <= 1.0:
        add_flag(flags, "V_OUT")
    if not 0.0 <= R_n <= 1.0:
        add_flag(flags, "R_OUT")
    if not 0.0 <= mp_n <= 1.0:
        add_flag(flags, "MP_OUT")
    if theta3 < 0:
        add_flag(flags, "THETA3_NEG")

    # Preserve the constitution's stated side expressions exactly.
    sin3 = math.sin(math.radians(theta3))
    a = safe_div(C_SIDE * math.sin(math.radians(theta1)), abs(sin3))
    b = safe_div(C_SIDE * abs(math.sin(math.radians(theta2_end))), abs(sin3))
    c = C_SIDE
    ab = safe_div(a, b)

    Ax, Ay, Bx, By = 0.0, 0.0, C_SIDE, 0.0
    Cx = b * math.cos(math.radians(theta1))
    Cy = b * math.sin(math.radians(theta1))
    perimeter_weight = a + b + c
    Ix = safe_div(C_SIDE * b + C_SIDE * Cx, perimeter_weight)
    Iy = safe_div(C_SIDE * Cy, perimeter_weight)
    Gx = (C_SIDE + Cx) / 3.0
    Gy = Cy / 3.0
    inradius = Iy
    area = abs(0.5 * C_SIDE * Cy)

    if abs(sin3) <= EPS:
        add_flag(flags, "SIDE_DENOMINATOR_ZERO")
    if not all(math.isfinite(v) for v in (a, b, Cx, Cy, Ix, Iy, Gx, Gy)):
        add_flag(flags, "NONFINITE_GEOMETRY")
    if abs(sum_theta - 300.0) > 1e-8:
        add_flag(flags, "ANGLE_SUM_CHECK_FAIL")
    if abs(sum_doses - 600.0) > 1e-8:
        add_flag(flags, "DOSE_SUM_CHECK_FAIL")

    out = {k: row.get(k, "") for k in ("Z", "Sym", "M", "rho", "R", "mp_C")}
    values = {
        "Vm": Vm, "rho_n": rho_n, "V_n": V_n, "R_n": R_n, "mp_n": mp_n,
        "theta1_material": theta1, "theta2_raw_spacetime": theta2_raw,
        "theta2_end": theta2_end, "n_turns": n_turns,
        "theta4_atomic_volume": theta4, "theta5_melting": theta5,
        "theta3_law": theta3, "SumTheta": sum_theta,
        "S_A": doses["S_A"], "S_B": doses["S_B"], "S_C": doses["S_C"],
        "S_R": doses["S_R"], "S_M": doses["S_M"], "SumS": sum_doses,
        "a": a, "b": b, "c": c, "a_over_b": ab,
        "Ax": Ax, "Ay": Ay, "Bx": Bx, "By": By, "Cx": Cx, "Cy": Cy,
        "Ix": Ix, "Iy": Iy, "Gx": Gx, "Gy": Gy,
        "inradius_r": inradius, "area_projected": area,
        "Data_Quality": quality or "UNSPECIFIED", "Family": family, "GAS": gas,
        "Flags": "|".join(flags) if flags else "OK", "Notes": notes
    }
    out.update({k: fmt(v) for k, v in values.items()})
    return out

def self_test():
    # Tests the 6.5.0 algebra, not scientific validity of the model.
    theta1, theta2, theta4, theta5 = 80.0, 46.0, 38.0, 71.0
    theta3 = 300.0 - (theta1 + theta2 + theta4 + theta5)
    angles_sum = theta1 + theta2 + theta3 + theta4 + theta5
    doses_sum = sum(90.0 + t / 2.0 for t in (theta1, theta2, theta3, theta4, theta5))
    assert abs(angles_sum - 300.0) < 1e-12, angles_sum
    assert abs(doses_sum - 600.0) < 1e-12, doses_sum
    boundary = (-360.0) % 360.0
    if abs(boundary) <= EPS:
        boundary = 360.0
    assert abs(boundary - 360.0) < 1e-12
    print("SELF-TEST: angle sum = 300 degrees")
    print("SELF-TEST: dose sum = 600 degrees")
    print("SELF-TEST: modulo boundary handled")
    print("SELF-TEST PASSED")

def main():
    self_test()
    if not INPUT.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT}")
    with INPUT.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if len(rows) != 118:
        raise ValueError(f"Expected 118 input rows; found {len(rows)}")
    zs = [int(r["Z"]) for r in rows]
    if sorted(zs) != list(range(1, 119)):
        raise ValueError("Atomic numbers must contain each integer from 1 through 118 exactly once")

    results = [compute(r) for r in rows]
    results.sort(key=lambda r: int(r["Z"]))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    complete = [r for r in results if r["Data_Quality"] != "NO_DATA"]
    no_data = [r for r in results if r["Data_Quality"] == "NO_DATA"]
    predicted = [r for r in results if r["Data_Quality"] == "PREDICTED"]
    with SUMMARY.open("w", encoding="utf-8") as f:
        f.write("COSMIC TRIANGLE FRAMEWORK 6.5.0 — RUN SUMMARY\n")
        f.write(f"Input rows: {len(rows)}\n")
        f.write(f"Calculated rows: {len(complete)}\n")
        f.write(f"NO_DATA rows: {len(no_data)}\n")
        f.write(f"PREDICTED source rows: {len(predicted)}\n")
        f.write("NO_DATA symbols: " + ", ".join(r["Sym"] for r in no_data) + "\n")
        f.write("Angle sum target: 300 degrees\nDose sum target: 600 degrees\n")
        f.write("Important: side/coordinate outputs reproduce the prescribed formulas; ")
        f.write("a 300-degree angle sum is not a Euclidean triangle angle sum.\n")
    print(f"INPUT_ROWS={len(rows)}")
    print(f"CALCULATED_ROWS={len(complete)}")
    print(f"NO_DATA_ROWS={len(no_data)}")
    print(f"OUTPUT_CSV={OUTPUT.relative_to(ROOT)}")
    print(f"SUMMARY={SUMMARY.relative_to(ROOT)}")
    print("CALCULATION COMPLETE")

if __name__ == "__main__":
    main()
