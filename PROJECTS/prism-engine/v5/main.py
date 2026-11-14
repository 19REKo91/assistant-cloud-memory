# ============================================================
# THE EYE OF THE PRISM — v5
# Independent engine. Does not modify the legacy root main.py.
# ============================================================
import csv
import json
import math
import os
import urllib.request

RHO_MIN = 1.74
RHO_MAX = 22.59
VM_MIN = 7.10
VM_MAX = 18.27
C_BASE = 3.0
C_NEUTRON_FACTOR = 0.016
EPS = 1e-10
EPS_MULT60 = 1e-9
GAS_SYMBOLS = {"H", "He", "N", "O", "F", "Ne", "Cl", "Ar", "Kr", "Xe", "Rn"}

DATA_URL = (
    "https://raw.githubusercontent.com/Bowserinator/Periodic-Table-JSON/"
    "master/PeriodicTableJSON.json"
)
OUTPUT_CSV = "outputs/v5_elements_118.csv"


def old_density_angles(M, rho):
    """Preserve the legacy v4.2 density normalization and 60-degree zipper."""
    vm = M / rho
    rho_n = (rho - RHO_MIN) / (RHO_MAX - RHO_MIN)
    vm_n = (vm - VM_MIN) / (VM_MAX - VM_MIN)
    theta1 = 80.0 - 70.0 * rho_n
    theta2_raw = 10.0 + 70.0 * vm_n
    theta3_raw = 180.0 - theta1 - theta2_raw

    n = 0
    zipper = "none"
    if theta2_raw < 0.0:
        theta2_vis = theta2_raw + 60.0
        theta3_vis = theta3_raw - 60.0
        zipper = "inverse"
    elif theta2_raw > 60.0:
        n = math.floor(theta2_raw / 60.0)
        if n > 0 and abs(theta2_raw - 60.0 * n) < EPS_MULT60:
            n -= 1
        theta2_vis = theta2_raw - 60.0 * n
        theta3_vis = 180.0 - theta1 - theta2_vis
        zipper = "extended_60f" if theta3_raw >= 0.0 else "60f"
    else:
        theta2_vis = theta2_raw
        theta3_vis = theta3_raw

    return {
        "V_m": vm, "rho_n": rho_n, "V_n": vm_n,
        "theta_1": theta1, "theta_2_raw": theta2_raw,
        "theta_3_raw": theta3_raw, "theta_2_vis": theta2_vis,
        "theta_3_vis": theta3_vis, "zip_n": n, "zip_mode": zipper,
    }


def triangle_geometry(a, b, c):
    """Construct a triangle from side lengths; return I and G coordinates."""
    if not all(math.isfinite(float(v)) for v in (a, b, c)):
        raise ValueError("NON_FINITE_SIDE")
    if min(a, b, c) <= 0:
        raise ValueError("NON_POSITIVE_SIDE")
    if (a + b <= c + EPS) or (a + c <= b + EPS) or (b + c <= a + EPS):
        raise ValueError("TRIANGLE_INEQUALITY")

    # Vertices: A=(0,0), B=(c,0), C determined by AC=b and BC=a.
    cx = (b*b + c*c - a*a) / (2.0*c)
    cy_sq = b*b - cx*cx
    if cy_sq <= EPS:
        raise ValueError("DEGENERATE_TRIANGLE")
    cy = math.sqrt(cy_sq)

    # Incenter: vertex weights are their opposite side lengths.
    perimeter = a + b + c
    ix = (a*0.0 + b*c + c*cx) / perimeter
    iy = (c*cy) / perimeter

    # Centroid: arithmetic mean of the three vertex coordinates.
    gx = (0.0 + c + cx) / 3.0
    gy = cy / 3.0

    area = 0.5 * c * cy
    return {
        "A_x": 0.0, "A_y": 0.0, "B_x": c, "B_y": 0.0,
        "C_x": cx, "C_y": cy, "I_x": ix, "I_y": iy,
        "G_x": gx, "G_y": gy, "area": area,
    }


def clock_reading(theta2_raw):
    angle = theta2_raw % 360.0
    if abs(angle) < EPS or abs(angle - 360.0) < EPS:
        sign = "BOUNDARY_0"
        charge = "BOUNDARY"
    elif abs(angle - 180.0) < EPS:
        sign = "BOUNDARY_180"
        charge = "BOUNDARY"
    elif angle < 180.0:
        sign = "POSITIVE_CONVENTION"
        charge = "POSITIVE"
    else:
        sign = "NEGATIVE_CONVENTION"
        charge = "NEGATIVE"
    return angle, sign, charge


def compute(el):
    z = el.get("number")
    sym = el.get("symbol")
    mass = el.get("atomic_mass")
    rho_original = el.get("density")

    base = {
        "Z": z, "symbol": sym, "M_atomic_mass": mass,
        "rho_original": rho_original,
    }
    if z is None or sym is None or mass is None or rho_original is None:
        return {**base, "status": "MISSING_DATA"}

    # Validate source values before applying the unchanged v5 equations.
    try:
        z_num = int(z)
        mass_num = float(mass)
        rho = float(rho_original)
    except (TypeError, ValueError, OverflowError):
        return {
            **base, "status": "INVALID_SOURCE_VALUE",
            "reason": "Z, atomic_mass, and density must be numeric",
        }

    if not all(math.isfinite(v) for v in (mass_num, rho)):
        return {
            **base, "status": "INVALID_SOURCE_VALUE",
            "reason": "Non-finite atomic_mass or density",
        }
    if z_num < 1 or z_num > 118 or mass_num <= 0.0 or rho <= 0.0:
        return {
            **base, "status": "INVALID_SOURCE_VALUE",
            "reason": "Z must be 1..118 and atomic_mass/density must be positive",
        }

    gas_unit_fix = sym in GAS_SYMBOLS and rho > 0.01
    if gas_unit_fix:
        rho /= 1000.0

    # User-defined v5 input relation; M is the source atomic-mass value.
    neutron_proxy = mass_num - float(z_num)

    try:
        angles = old_density_angles(mass_num, rho)
    except (ArithmeticError, ValueError) as exc:
        return {**base, "status": "ANGLE_CALC_ERROR", "reason": str(exc)}

    # Preserve b from the legacy density-angle sine relation.
    t2 = math.radians(angles["theta_2_vis"])
    t3 = math.radians(angles["theta_3_vis"])
    sin_t3 = math.sin(t3)
    if (angles["theta_1"] < 0.0 or angles["theta_2_vis"] < 0.0
            or angles["theta_3_vis"] < 0.0 or angles["theta_3_vis"] > 180.0
            or abs(sin_t3) < EPS):
        return {
            **base, **angles, "rho_used": rho, "N_proxy": neutron_proxy,
            "status": "INVALID_LEGACY_ANGLES",
            "reason": "Legacy adjusted angles do not define a non-degenerate triangle",
        }

    b = C_BASE * abs(math.sin(t2)) / sin_t3
    a = float(z_num) / 10.0
    c = C_BASE + C_NEUTRON_FACTOR * neutron_proxy

    theta_clock, clock_state, conventional_charge = clock_reading(
        angles["theta_2_raw"]
    )
    perimeter = a + b + c
    law_ratio = (c / perimeter) * 100.0 if perimeter > 0 else None

    result = {
        **base, **angles,
        "rho_used": rho, "gas_unit_fix": gas_unit_fix,
        "N_proxy_M_minus_Z": neutron_proxy,
        "a_material": a, "b_spacetime_legacy": b, "c_law": c,
        "perimeter": perimeter, "law_ratio_percent": law_ratio,
        "theta_clock_deg": theta_clock,
        "clock_state": clock_state,
        "conventional_charge": conventional_charge,
        "status": "PENDING_GEOMETRY",
    }

    if law_ratio > 40.0:
        result["model_class"] = "UPPER_FORTRESS"
    elif law_ratio < 30.0:
        result["model_class"] = "LOWER"
    else:
        result["model_class"] = "MIDDLE_UNRESOLVED"

    try:
        geom = triangle_geometry(a, b, c)
        result.update(geom)
        result["status"] = "VALID"
    except ValueError as exc:
        result["status"] = str(exc)

    return result


def self_test():
    # 3-4-5 triangle: known incenter and centroid coordinates.
    g = triangle_geometry(4.0, 3.0, 5.0)
    assert abs(g["area"] - 6.0) < 1e-9
    assert abs(g["I_x"] - 2.0) < 1e-9
    assert abs(g["I_y"] - 1.0) < 1e-9
    assert abs(g["G_x"] - (6.8 / 3.0)) < 1e-9
    assert abs(g["G_y"] - 0.8) < 1e-9
    assert clock_reading(190.0)[0] == 190.0
    assert clock_reading(190.0)[2] == "NEGATIVE"
    assert clock_reading(360.0)[2] == "BOUNDARY"

    # The legacy zipper must preserve the 180-degree visible-angle sum.
    inverse_case = old_density_angles(7.10, 1.74)
    assert inverse_case["zip_mode"] == "inverse"
    assert abs(
        inverse_case["theta_1"] + inverse_case["theta_2_vis"]
        + inverse_case["theta_3_vis"] - 180.0
    ) < 1e-9

    extended_case = old_density_angles(31.7898, 1.74)
    assert extended_case["zip_mode"] == "extended_60f"
    assert abs(
        extended_case["theta_1"] + extended_case["theta_2_vis"]
        + extended_case["theta_3_vis"] - 180.0
    ) < 1e-9

    invalid_case = compute({
        "number": 1, "symbol": "H", "atomic_mass": "not-a-number",
        "density": 0.00008988,
    })
    assert invalid_case["status"] == "INVALID_SOURCE_VALUE"

    print(
        "SELF-TEST PASSED: triangle geometry, incenter, centroid, "
        "clock, zipper, and source validation"
    )


def main():
    self_test()
    request = urllib.request.Request(
        DATA_URL, headers={"User-Agent": "The-Eye-of-the-Prism-v5"}
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.loads(response.read().decode("utf-8"))

    elements = payload.get("elements", [])
    by_z = {int(e["number"]): e for e in elements if e.get("number") is not None}
    rows = []
    for z in range(1, 119):
        el = by_z.get(z)
        if el is None:
            rows.append({"Z": z, "status": "ELEMENT_NOT_IN_SOURCE"})
        else:
            rows.append(compute(el))

    os.makedirs("outputs", exist_ok=True)
    fields = sorted({key for row in rows for key in row.keys()},
                    key=lambda x: (x != "Z", x))
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    counts = {}
    for row in rows:
        status = row.get("status", "UNKNOWN")
        counts[status] = counts.get(status, 0) + 1

    print("=== V5 SUMMARY ===")
    print(f"source_elements: {len(elements)}")
    print(f"rows_written: {len(rows)}")
    for status in sorted(counts):
        print(f"{status}: {counts[status]}")
    print(f"csv: {OUTPUT_CSV}")
    print("=== END ===")


if __name__ == "__main__":
    main()
