#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent isotope validation: within-element trends and element-held-out prediction."""
from pathlib import Path
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
SOURCE = OUT / "isotope_model_comparison.csv"
RNG_SEED = 20261117
MEV_U = 931.49410242

def design_matrix(frame, kind):
    A = frame["A"].to_numpy(float)
    Z = frame["Z"].to_numpy(float)
    N = frame["N"].to_numpy(float)
    R = frame["Residual_absolute_u"].to_numpy(float)
    RS = frame["Residual_signed_u"].to_numpy(float)
    if kind == "mean":
        return np.ones((len(frame), 1))
    if kind == "A":
        return np.column_stack([np.ones(len(frame)), A])
    if kind == "R":
        return np.column_stack([np.ones(len(frame)), R])
    if kind == "R_plus_A":
        return np.column_stack([np.ones(len(frame)), R, A])
    if kind == "R_signed":
        return np.column_stack([np.ones(len(frame)), RS])
    if kind == "R_signed_plus_A":
        return np.column_stack([np.ones(len(frame)), RS, A])
    if kind in ("SEMF", "SEMF_plus_R_signed", "SEMF_plus_R_absolute"):
        pair = np.where((Z.astype(int) % 2 == 0) & (N.astype(int) % 2 == 0), 1.0,
               np.where((Z.astype(int) % 2 == 1) & (N.astype(int) % 2 == 1), -1.0, 0.0))
        semf = np.column_stack([
            A, -np.power(A, 2/3), -Z*(Z-1)/np.power(A, 1/3),
            -np.square(A-2*Z)/A, pair/np.power(A, 0.75)
        ])
        if kind == "SEMF_plus_R_signed":
            return np.column_stack([semf, RS])
        if kind == "SEMF_plus_R_absolute":
            return np.column_stack([semf, R])
        return semf
    raise ValueError(kind)

def fit_predict(train, test, kind, ycol):
    Xtr = design_matrix(train, kind)
    Xte = design_matrix(test, kind)
    y = train[ycol].to_numpy(float)
    if kind.startswith("SEMF"):
        coef = np.linalg.lstsq(Xtr, y, rcond=None)[0]
        return Xte @ coef
    if kind == "mean":
        return np.full(len(test), float(np.mean(y)))
    coef = np.linalg.lstsq(Xtr, y, rcond=None)[0]
    return Xte @ coef

def spearman_corr(x, y):
    """Spearman correlation via average ranks; avoids an optional SciPy dependency."""
    xr = pd.Series(np.asarray(x)).rank(method="average")
    yr = pd.Series(np.asarray(y)).rank(method="average")
    return float(xr.corr(yr))

def metrics(y, pred):
    err = pred-y
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    denom = float(np.sum((y-np.mean(y))**2))
    r2 = float(1-np.sum(err**2)/denom) if denom > 0 else float("nan")
    return mae, rmse, r2


def _bool_for_validation(series):
    return series.astype("string").str.lower().isin(["true", "1", "yes"])

def validate_cumulative_outputs():
    """Independently recompute cumulative isotope-series identities."""
    path = OUT / "isotope_cumulative_steps_all.csv"
    if not path.exists():
        raise FileNotFoundError(
            "Cumulative output missing. Run main.py first; validation must not silently skip it."
        )
    c = pd.read_csv(path, low_memory=False)
    required = [
        "Z", "N", "Symbol", "U_2Z_plus_N", "D_Z_plus_2N", "C_raw_u", "C_cancel_u",
        "Residual_from_subtraction_u", "Residual_signed_u", "Residual_absolute_u",
        "AME_mass_defect_u_from_binding", "Cumulative_signed_residual_steps_u",
        "Cumulative_absolute_signed_step_magnitudes_u",
        "Binding_defect_change_from_first_u", "Gap_between_observed_N",
        "C_raw_change_from_first_u", "C_cancel_change_from_first_u",
        "Residual_subtraction_change_from_first_u", "Cumulative_raw_steps_u",
        "Cumulative_cancelled_steps_u", "Cumulative_subtraction_residual_steps_u",
        "Cumulative_absolute_subtraction_step_magnitudes_u"
    ]
    missing = [x for x in required if x not in c.columns]
    if missing:
        raise ValueError(f"Cumulative output missing columns: {missing}")
    numeric_columns = [
        "Z", "N", "U_2Z_plus_N", "D_Z_plus_2N", "C_raw_u", "C_cancel_u",
        "Residual_from_subtraction_u", "Residual_signed_u", "Residual_absolute_u",
        "AME_mass_defect_u_from_binding", "Cumulative_signed_residual_steps_u",
        "Cumulative_absolute_signed_step_magnitudes_u", "Binding_defect_change_from_first_u",
        "C_raw_change_from_first_u", "C_cancel_change_from_first_u",
        "Residual_subtraction_change_from_first_u", "Cumulative_raw_steps_u",
        "Cumulative_cancelled_steps_u", "Cumulative_subtraction_residual_steps_u",
        "Cumulative_absolute_subtraction_step_magnitudes_u"
    ]
    for col in numeric_columns:
        c[col] = pd.to_numeric(c[col], errors="coerce")
    if c.duplicated(["Z", "N"]).any():
        raise AssertionError("Cumulative output contains duplicate (Z,N) isotope keys.")

    summaries = []
    max_net_error = max_step_error = max_abs_step_sum_error = max_defect_error = 0.0
    max_raw_cancel_error = max_subtraction_identity_error = max_cumulative_raw_error = 0.0
    total_gaps = 0
    for z, g in c.groupby("Z", sort=True):
        g = g.sort_values("N").copy()
        n0 = int(g["N"].iloc[0])
        d0 = float(g["AME_mass_defect_u_from_binding"].iloc[0])
        expected_net = 0.004 * (g["N"] - n0)
        net_error = float((g["Cumulative_signed_residual_steps_u"] - expected_net).abs().max())
        max_net_error = max(max_net_error, net_error)

        delta_n = g["N"].diff()
        delta_r = g["Residual_signed_u"].diff()
        step_error = float((delta_r - 0.004 * delta_n).abs().max())
        max_step_error = max(max_step_error, step_error)

        expected_abs_steps = delta_r.abs().fillna(0).cumsum()
        abs_step_error = float((
            g["Cumulative_absolute_signed_step_magnitudes_u"] - expected_abs_steps
        ).abs().max())
        max_abs_step_sum_error = max(max_abs_step_sum_error, abs_step_error)

        # Recompute the raw/cancelled/subtraction ledger independently.
        expected_subtraction = g["C_raw_u"] - g["C_cancel_u"]
        subtraction_error = float((g["Residual_from_subtraction_u"] - expected_subtraction).abs().max())
        max_subtraction_identity_error = max(max_subtraction_identity_error, subtraction_error)
        raw_cancel_steps = g["C_raw_u"].diff().fillna(0) - g["C_cancel_u"].diff().fillna(0)
        expected_cumulative_subtraction = raw_cancel_steps.cumsum()
        expected_cumulative_raw = g["C_raw_u"].diff().fillna(0).cumsum()
        expected_cumulative_cancelled = g["C_cancel_u"].diff().fillna(0).cumsum()
        cumulative_raw_error = max(
            float((g["Cumulative_raw_steps_u"] - expected_cumulative_raw).abs().max()),
            float((g["Cumulative_cancelled_steps_u"] - expected_cumulative_cancelled).abs().max()),
            float((g["Cumulative_subtraction_residual_steps_u"] - expected_cumulative_subtraction).abs().max())
        )
        max_cumulative_raw_error = max(max_cumulative_raw_error, cumulative_raw_error)
        raw_cancel_error = float((
            g["C_raw_change_from_first_u"] - g["C_cancel_change_from_first_u"]
            - g["Residual_subtraction_change_from_first_u"]
        ).abs().max())
        max_raw_cancel_error = max(max_raw_cancel_error, raw_cancel_error)
        if not np.allclose(g["Residual_from_subtraction_u"], g["Residual_absolute_u"], atol=1e-10, rtol=0):
            raise AssertionError(f"Subtraction residual does not equal absolute residual for Z={z}.")

        expected_defect_change = g["AME_mass_defect_u_from_binding"] - d0
        defect_error = float((
            g["Binding_defect_change_from_first_u"] - expected_defect_change
        ).abs().max())
        max_defect_error = max(max_defect_error, defect_error)

        expected_gap = delta_n.gt(1).fillna(False).to_numpy()
        actual_gap = _bool_for_validation(g["Gap_between_observed_N"]).to_numpy()
        if not np.array_equal(expected_gap, actual_gap):
            raise AssertionError(f"Incorrect N-gap flags for Z={z}.")
        gaps = int(expected_gap.sum())
        total_gaps += gaps
        summaries.append({
            "Z": int(z), "Symbol": str(g["Symbol"].iloc[0]),
            "Isotope_records": len(g), "N_first": n0, "N_last": int(g["N"].iloc[-1]),
            "Observed_N_gaps": gaps, "Net_R_from_first_u": float(expected_net.iloc[-1]),
            "Observed_net_defect_change_u": float(expected_defect_change.iloc[-1]),
            "Max_net_identity_error_u": net_error,
            "Max_step_identity_error_u": step_error,
            "Max_absolute_step_sum_error_u": abs_step_error,
            "Max_defect_change_error_u": defect_error,
            "Max_raw_cancel_identity_error_u": raw_cancel_error,
            "Max_cumulative_raw_cancel_error_u": cumulative_raw_error,
            "Max_subtraction_absolute_identity_error_u": subtraction_error
        })

    tol = 1e-10
    if max(max_net_error, max_step_error, max_abs_step_sum_error, max_defect_error,
           max_raw_cancel_error, max_subtraction_identity_error, max_cumulative_raw_error) > tol:
        raise AssertionError(
            "Independent cumulative validation failed: "
            f"net={max_net_error}, step={max_step_error}, "
            f"abs_steps={max_abs_step_sum_error}, defect={max_defect_error}, "
            f"raw_cancel={max_raw_cancel_error}, subtraction={max_subtraction_identity_error}, "
            f"cumulative_raw={max_cumulative_raw_error}"
        )
    summary = pd.DataFrame(summaries)
    summary.to_csv(OUT / "cumulative_independent_validation.csv", index=False)
    report = [
        "INDEPENDENT CUMULATIVE VALIDATION",
        f"Elements tested: {len(summary)}",
        f"Isotope records tested: {len(c)}",
        f"Observed N gaps (not interpolated): {total_gaps}",
        f"Maximum net cumulative identity error (u): {max_net_error:.12g}",
        f"Maximum step identity error (u): {max_step_error:.12g}",
        f"Maximum absolute-step-sum error (u): {max_abs_step_sum_error:.12g}",
        f"Maximum reference-relative mass-defect error (u): {max_defect_error:.12g}",
        f"Maximum raw-cancelled-subtraction identity error (u): {max_subtraction_identity_error:.12g}",
        f"Maximum cumulative raw-cancelled identity error (u): {max_cumulative_raw_error:.12g}",
        f"Maximum net raw/cancelled change identity error (u): {max_raw_cancel_error:.12g}",
        "PASS: cumulative columns independently recomputed from isotope records."
    ]
    (OUT / "cumulative_independent_validation.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    return summary



def run_binary_box_tests(clean):
    """Direct tests of the user's 0.016-u brick, binary mass boxes, and 42% loss hypothesis."""
    d = clean.copy()
    required = ["AME_atomic_mass_u", "Binding_defect_u", "Binding_energy_per_nucleon_MeV"]
    missing = [c for c in required if c not in d.columns]
    if missing:
        raise ValueError(f"Binary-box test missing columns: {missing}")

    b = 0.016
    mass = pd.to_numeric(d["AME_atomic_mass_u"], errors="coerce")
    d = d[mass.notna() & (mass > 0)].copy()
    mass = pd.to_numeric(d["AME_atomic_mass_u"], errors="coerce")
    A = d["A"].astype(float)
    Z = d["Z"].astype(float)
    N = d["N"].astype(float)

    # Test 1: binary boxes on mass number A: [2^k, 2^(k+1)].
    k = np.floor(np.log2(A)).astype(int)
    lower_A = np.power(2.0, k)
    upper_A = 2.0 * lower_A
    d["Binary_box_k"] = k
    d["Binary_box_lower_A"] = lower_A
    d["Binary_box_upper_A"] = upper_A
    d["Binary_box_position_pct"] = 100.0 * (A - lower_A) / (upper_A - lower_A)
    d["Binary_box_remaining_to_upper_pct"] = 100.0 * (upper_A - A) / upper_A

    # Test 2: 0.016-u brick lattice and brick-scaled binary box.
    brick_count = mass / b
    nearest_bricks = np.rint(brick_count)
    d["Brick_count_0p016"] = brick_count
    d["Nearest_integer_bricks"] = nearest_bricks
    d["Brick_lattice_residual_u"] = mass - nearest_bricks * b
    d["Brick_lattice_error_pct_of_brick"] = (
        100.0 * d["Brick_lattice_residual_u"].abs() / b
    )
    brick_k = np.floor(np.log2(brick_count)).astype(int)
    brick_lower = b * np.power(2.0, brick_k)
    brick_upper = 2.0 * brick_lower
    d["Brick_binary_box_k"] = brick_k
    d["Brick_box_lower_u"] = brick_lower
    d["Brick_box_upper_u"] = brick_upper
    d["Brick_box_position_pct"] = 100.0 * (mass - brick_lower) / (brick_upper - brick_lower)
    d["Brick_box_remaining_to_upper_pct"] = 100.0 * (brick_upper - mass) / brick_upper

    # Test 3: is the proposed 42% loss explained by neutron excess?
    d["Neutron_excess_fraction_pct"] = 200.0 * (N - Z) / A
    d["Proposed_loss_42pct_u"] = 0.42 * A
    d["Proposed_effective_mass_58pct_u"] = 0.58 * A
    d["Observed_binding_defect_fraction_pct"] = (
        100.0 * d["Binding_defect_u"] / mass
    )
    d["Neutron_excess_minus_42pct_points"] = d["Neutron_excess_fraction_pct"] - 42.0
    d["Effective_mass_vs_A_minus_2excess_u"] = (
        d["Proposed_effective_mass_58pct_u"] - (A - 2.0 * (N - Z))
    )
    d["Residual_in_0p016_bricks"] = d["Residual_absolute_u"] / b
    d["Residual_is_integer_bricks"] = np.isclose(
        d["Residual_in_0p016_bricks"],
        np.rint(d["Residual_in_0p016_bricks"]),
        atol=1e-9, rtol=0
    )

    # Distinguish neutral-atom mass from approximate nuclear mass.
    # Electron binding energy is omitted here; this is a first-order correction only.
    electron_mass_u = 0.000548579909065
    d["Approx_nuclear_mass_u"] = mass - Z * electron_mass_u
    d["Approx_nuclear_brick_count"] = d["Approx_nuclear_mass_u"] / b
    d["Approx_nuclear_brick_error_pct"] = (
        100.0 * (d["Approx_nuclear_brick_count"] -
                 np.rint(d["Approx_nuclear_brick_count"])).abs()
    )
    d["Binding_defect_in_0p016_bricks"] = d["Binding_defect_u"] / b
    d["Binding_defect_brick_error_pct"] = (
        100.0 * (d["Binding_defect_in_0p016_bricks"] -
                 np.rint(d["Binding_defect_in_0p016_bricks"])).abs()
    )
    d["Binding_energy_per_nucleon_u"] = (
        d["Binding_energy_per_nucleon_MeV"] / MEV_U
    )
    d["Binding_energy_per_nucleon_vs_0p008_ratio"] = (
        d["Binding_energy_per_nucleon_u"] / 0.008
    )

    d.to_csv(OUT / "binary_box_test_isotope_results.csv", index=False, na_rep="NA")

    # Element-level medians; do not treat isotopes of one element as independent elements.
    element_rows = []
    for (z, symbol), g in d.groupby(["Z", "Symbol"], sort=True):
        element_rows.append({
            "Z": int(z), "Symbol": str(symbol), "Clean_isotope_records": len(g),
            "A_median": float(g["A"].median()),
            "N_over_Z_median": float((g["N"] / g["Z"]).median()),
            "Neutron_excess_fraction_pct_median": float(g["Neutron_excess_fraction_pct"].median()),
            "Binding_defect_fraction_pct_median": float(g["Observed_binding_defect_fraction_pct"].median()),
            "Binding_energy_per_nucleon_MeV_median": float(g["Binding_energy_per_nucleon_MeV"].median()),
            "Binary_box_k_mode": int(g["Binary_box_k"].mode().iloc[0]),
            "Binary_box_position_pct_median": float(g["Binary_box_position_pct"].median()),
            "Brick_lattice_error_pct_median": float(g["Brick_lattice_error_pct_of_brick"].median()),
            "Approx_nuclear_brick_error_pct_median": float(g["Approx_nuclear_brick_error_pct"].median()),
            "Binding_defect_bricks_median": float(g["Binding_defect_in_0p016_bricks"].median()),
            "Binding_defect_brick_error_pct_median": float(g["Binding_defect_brick_error_pct"].median()),
            "Binding_energy_per_nucleon_MeV_median": float(g["Binding_energy_per_nucleon_MeV"].median()),
            "Binding_energy_per_nucleon_vs_0p008_ratio_median": float(g["Binding_energy_per_nucleon_vs_0p008_ratio"].median()),
            "Effective_mass_0p58A_median": float(g["Proposed_effective_mass_58pct_u"].median())
        })
    elements = pd.DataFrame(element_rows).sort_values("Z")
    elements.to_csv(OUT / "binary_box_test_element_summary.csv", index=False, na_rep="NA")

    # Compare a fixed 42% with the measured neutron-excess fraction in mass regions.
    region_rows = []
    regions = [
        ("Z_1_28", d["Z"].between(1, 28)),
        ("Z_29_81", d["Z"].between(29, 81)),
        ("Z_82_118", d["Z"].between(82, 118)),
        ("All_clean", d["Z"].between(1, 118))
    ]
    for label, mask in regions:
        g = d[mask]
        x = g["Neutron_excess_fraction_pct"].dropna()
        region_rows.append({
            "Region": label, "Records": len(g), "Elements": int(g["Z"].nunique()),
            "Neutron_excess_fraction_median_pct": float(x.median()) if len(x) else np.nan,
            "Neutron_excess_fraction_mean_pct": float(x.mean()) if len(x) else np.nan,
            "Neutron_excess_fraction_q25_pct": float(x.quantile(.25)) if len(x) else np.nan,
            "Neutron_excess_fraction_q75_pct": float(x.quantile(.75)) if len(x) else np.nan,
            "MAE_from_fixed_42pct_points": float(np.mean(np.abs(x - 42.0))) if len(x) else np.nan,
            "Binding_defect_fraction_median_pct": float(g["Observed_binding_defect_fraction_pct"].median()) if len(g) else np.nan
        })
    regions_df = pd.DataFrame(region_rows)
    regions_df.to_csv(OUT / "binary_box_test_regions.csv", index=False, na_rep="NA")

    # Search for a data-driven change point in element-level median neutron excess.
    xz = elements["Z"].to_numpy(float)
    yy = elements["Neutron_excess_fraction_pct_median"].to_numpy(float)
    def line_sse(xv, yv):
        X = np.column_stack([np.ones(len(xv)), xv])
        coef = np.linalg.lstsq(X, yv, rcond=None)[0]
        residual = yv - X @ coef
        return float(np.sum(residual ** 2))
    candidates = []
    unique_z = np.unique(xz)
    for cut in unique_z:
        left = xz <= cut
        right = xz > cut
        if int(left.sum()) < 10 or int(right.sum()) < 10:
            continue
        sse = line_sse(xz[left], yy[left]) + line_sse(xz[right], yy[right])
        candidates.append((float(sse), int(cut), int(left.sum()), int(right.sum())))
    candidates.sort()
    best = candidates[0] if candidates else (np.nan, -1, 0, 0)
    cu_candidate = next((v for v in candidates if v[1] == 29), None)
    one_line_sse = line_sse(xz, yy)
    change_report = {
        "Best_break_after_Z": best[1],
        "Best_piecewise_RMSE": float(np.sqrt(best[0] / len(xz))) if candidates else np.nan,
        "Z29_piecewise_RMSE": float(np.sqrt(cu_candidate[0] / len(xz))) if cu_candidate else np.nan,
        "Single_line_RMSE": float(np.sqrt(one_line_sse / len(xz))),
        "Element_count": len(elements)
    }

    # Target nuclides include the examples discussed: Fe/Ni/Cu/Zn/Pb/U.
    targets = {(26,56), (28,62), (29,63), (29,65), (30,64), (30,66), (82,208), (92,238)}
    examples = d[d.apply(lambda r: (int(r["Z"]), int(r["A"])) in targets, axis=1)].copy()
    examples.to_csv(OUT / "binary_box_test_key_nuclides.csv", index=False, na_rep="NA")

    brick_error = d["Brick_lattice_error_pct_of_brick"]
    nuclear_brick_error = d["Approx_nuclear_brick_error_pct"]
    defect_brick_error = d["Binding_defect_brick_error_pct"]
    residual_brick_share = float(d["Residual_is_integer_bricks"].mean())
    half_brick_mev = 0.008 * MEV_U
    full_brick_mev = 0.016 * MEV_U
    summary = [
        "# اختبار الصندوق الثنائي والفاقد الطوبي — AME2020",
        "",
        "## النطاق",
        f"- السجلات النظائرية النظيفة المستخدمة: {len(d):,}.",
        f"- العناصر: {d['Z'].nunique():,}.",
        "- المصدر: سجلات AME2020 المطابقة مع مرشحي الحالة الأرضية في NUBASE2020؛ استُبعدت القيم المقدرة/الموسومة من عينة الاختبار.",
        "",
        "## 1) الطوبة الخام b = 0.016 u",
        f"- وسيط خطأ أقرب عدد صحيح من الطوبات، كنسبة من الطوبة: {brick_error.median():.3f}%.",
        f"- متوسط خطأ شبكة الطوبات: {brick_error.mean():.3f}%.",
        f"- نسبة السجلات التي تقع ضمن 1% من طوبة صحيحة: {(brick_error <= 1.0).mean()*100:.2f}%.",
        f"- نسبة السجلات التي تقع ضمن 5% من طوبة صحيحة: {(brick_error <= 5.0).mean()*100:.2f}%.",
        f"- بعد طرح كتل الإلكترونات (تقريب أولي يهمل طاقة ارتباطها): وسيط خطأ شبكة الكتلة النووية {nuclear_brick_error.median():.3f}%؛ ضمن 1%: {(nuclear_brick_error <= 1.0).mean()*100:.2f}%، وضمن 5%: {(nuclear_brick_error <= 5.0).mean()*100:.2f}%.",
        f"- اختبار عيب الكتلة نفسه بوحدة الطوبة: وسيط خطأ أقرب عدد صحيح من 0.016u هو {defect_brick_error.median():.3f}%; ضمن 1%: {(defect_brick_error <= 1.0).mean()*100:.2f}%، وضمن 5%: {(defect_brick_error <= 5.0).mean()*100:.2f}%.",
        f"- 0.016u تعادل {full_brick_mev:.3f} MeV، ونصفها 0.008u يعادل {half_brick_mev:.3f} MeV؛ وسيط طاقة الربط لكل نيوكليون {d['Binding_energy_per_nucleon_MeV'].median():.3f} MeV، أي {d['Binding_energy_per_nucleon_vs_0p008_ratio'].median():.3f} مرة من 0.008u.",
        f"- نسبة المتبقي النموذجي الذي يساوي عدداً صحيحاً من طوبات 0.016u: {residual_brick_share*100:.2f}% (هذه نتيجة جبرية من كون |N-Z| من مضاعفات 4، وليست قياساً مستقلاً).",
        "- فحص الهيدروجين-1: كتلة الذرة تقارن بـ 63×0.016u=1.008u، بينما 64×0.016u=1.024u؛ الفارق بين الكتلة و63 طوبة يظهر في ملف النظائر.",
        "- كتلة AME الذرية تشمل الإلكترونات؛ لذلك عُرض فحص ذري وفحص كتلة نووية تقريبي منفصل. تصحيح الكتلة النووية هنا يطرح Z كتلة إلكترونات فقط ويهمل طاقة ارتباطها الإلكترونية.",
        "",
        "## 2) الصناديق الثنائية على عدد الكتلة A",
        "- لكل نظير استُخدم الصندوق [2^k, 2^(k+1)] الذي يحتوي A، والموقع P=100(A−2^k)/(2^(k+1)−2^k).",
        "- حُفظت المسافة إلى الحد الأعلى منفصلة؛ الانتقال عند A=64 يغيّر رقم الصندوق حسابياً ولا يثبت انهياراً فيزيائياً.",
        f"- وسيط موقع الصندوق: {d['Binary_box_position_pct'].median():.3f}%.",
        f"- وسيط المسافة النسبية إلى الحد الأعلى: {d['Binary_box_remaining_to_upper_pct'].median():.3f}%.",
        "",
        "## 3) اختبار فرضية الفاقد 42% / الكتلة الفعالة 58%",
        "- اختُبرت نسبة فائض النيوترونات المعرّفة هنا بـ 2(N−Z)/A، لأنها تمثل نسبة عددية يمكن مقارنتها مباشرة بفرضية 42%؛ لا تُساوى تلقائياً بعيب الكتلة أو طاقة الربط.",
        f"- وسيط 2(N−Z)/A في كل العينة: {d['Neutron_excess_fraction_pct'].median():.3f}%.",
        f"- وسيط عيب الكتلة المشتق من طاقة الربط كنسبة من الكتلة الذرية: {d['Observed_binding_defect_fraction_pct'].median():.3f}%.",
        f"- وسيط الفرق بين 0.58A و[A−2(N−Z)]: {d['Effective_mass_vs_A_minus_2excess_u'].median():.4f} u.",
        "- إذا اقتربت 2(N−Z)/A من 42% في النوى الثقيلة فقط، فهذا يدعم وصفاً عددياً محدوداً لتلك العينة، ولا يجعل 42% ثابتاً عاماً أو فاقداً مادياً.",
        "",
        "## 4) هل النحاس Z=29 نقطة تحول؟",
        f"- أفضل نقطة انكسار إحصائية عند السماح بقطعتين خطيتين على وسيط فائض النيوترونات لكل عنصر: بعد Z={change_report['Best_break_after_Z']}.",
        f"- RMSE القطعتين عند هذه النقطة: {change_report['Best_piecewise_RMSE']:.4f} نقطة مئوية.",
        f"- RMSE إذا فُرضت نقطة الانكسار بعد Z=29: {change_report['Z29_piecewise_RMSE']:.4f} نقطة مئوية.",
        f"- RMSE الخط الواحد دون انكسار: {change_report['Single_line_RMSE']:.4f} نقطة مئوية.",
        "- هذا بحث استكشافي عن نقطة انكسار، وليس اختباراً سببياً؛ لا تُقبل نقطة النحاس إلا إذا تفوقت بوضوح وبثبات على نقاط الانكسار البديلة.",
        "",
        "## 5) التقسيمات والبيانات التفصيلية",
    ]
    for _, r in regions_df.iterrows():
        summary.append(
            f"- {r['Region']}: n={int(r['Records'])}, العناصر={int(r['Elements'])}, "
            f"وسيط 2(N−Z)/A={r['Neutron_excess_fraction_median_pct']:.3f}%, "
            f"وسيط عيب الكتلة/الكتلة={r['Binding_defect_fraction_median_pct']:.3f}%."
        )
    summary += [
        "",
        "## ملفات النتائج",
        "- binary_box_test_isotope_results.csv",
        "- binary_box_test_element_summary.csv",
        "- binary_box_test_regions.csv",
        "- binary_box_test_key_nuclides.csv",
        "",
        "ملاحظة: الكتلة الذرية المستخدمة في اختبار الطوبات هي AME atomic mass؛ أما الصناديق الثنائية الأساسية فاختُبرت على عدد الكتلة A. لا تخلط المحورين."
    ]
    (OUT / "report_ar_binary_box_test.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n".join(summary[:38]))
    return d, elements, regions_df, examples


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Required prior audit output not found: {SOURCE}")
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SOURCE, low_memory=False)
    required = ["Z","N","A","Symbol","AME_match","AME_mass_defect_u_from_binding",
                "Residual_absolute_u","Residual_signed_u","AME_estimated_or_flagged"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    for c in ["Z","N","A","AME_mass_defect_u_from_binding","Residual_absolute_u","Residual_signed_u"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    matched = df[df["AME_match"].astype(str).str.lower().isin(["true","1"])].copy()
    matched = matched.dropna(subset=["Z","N","A","AME_mass_defect_u_from_binding","Residual_absolute_u"])
    flagged = matched["AME_estimated_or_flagged"].astype(str).str.lower().isin(["true","1","yes"])
    clean = matched[~flagged].copy()
    if len(clean) < 100:
        raise RuntimeError(f"Too few clean matched ground-state records: {len(clean)}")
    clean["Z"] = clean["Z"].astype(int)
    clean = clean[clean["Z"].between(1,118)].copy()  # Exclude free neutron (Z=0) from element/isotope tests.
    clean["N"] = clean["N"].astype(int)
    clean["A"] = clean["A"].astype(int)
    clean["Symbol"] = clean["Symbol"].replace("", np.nan).fillna(clean["AME_symbol"]).fillna("Unknown").astype(str)
    clean["Binding_defect_u"] = clean["AME_mass_defect_u_from_binding"]
    clean["Binding_energy_per_nucleon_MeV"] = (
        pd.to_numeric(clean["Binding_energy_per_A_keV"], errors="coerce")/1000.0
    )
    clean = clean.dropna(subset=["Binding_energy_per_nucleon_MeV"])
    run_binary_box_tests(clean)
    clean["Residual_to_defect_ratio"] = np.where(clean["Binding_defect_u"] > 0, clean["Residual_absolute_u"]/clean["Binding_defect_u"], np.nan)

    # Isotope-by-isotope trend within each element (Z fixed).
    rows = []
    for (z, sym), g in clean.groupby(["Z","Symbol"]):
        g = g.sort_values("N")
        if len(g) < 3 or g["Residual_absolute_u"].nunique() < 2:
            continue
        pearson_r = g["Residual_absolute_u"].corr(g["Binding_defect_u"], method="pearson")
        spearman_r = spearman_corr(g["Residual_absolute_u"], g["Binding_defect_u"])
        signed_pearson_r = g["Residual_signed_u"].corr(g["Binding_defect_u"], method="pearson")
        signed_spearman_r = spearman_corr(g["Residual_signed_u"], g["Binding_defect_u"])
        rows.append({
            "Z": z, "Symbol": sym, "Isotopes_n": len(g),
            "N_min": int(g["N"].min()), "N_max": int(g["N"].max()),
            "Pearson_R_vs_defect": pearson_r, "Spearman_R_vs_defect": spearman_r,
            "Signed_Pearson_R_vs_defect": signed_pearson_r, "Signed_Spearman_R_vs_defect": signed_spearman_r,
            "Residual_min_u": g["Residual_absolute_u"].min(),
            "Residual_max_u": g["Residual_absolute_u"].max(),
            "Defect_min_u": g["Binding_defect_u"].min(),
            "Defect_max_u": g["Binding_defect_u"].max(),
            "Mean_ratio_percent": 100*g["Residual_to_defect_ratio"].mean()
        })
    within = pd.DataFrame(rows).sort_values("Z") if rows else pd.DataFrame()
    within.to_csv(OUT/"isotope_within_element_correlations.csv", index=False)

    # Hold out entire elements, preventing isotopes of a test element leaking into training.
    elements = np.array(sorted(clean["Z"].unique()))
    rng = np.random.default_rng(RNG_SEED)
    shuffled = rng.permutation(elements)
    n_test = max(1, int(round(0.25*len(shuffled))))
    test_z = set(shuffled[:n_test].tolist())
    train = clean[~clean["Z"].isin(test_z)].copy()
    test = clean[clean["Z"].isin(test_z)].copy()
    if len(train) < 100 or len(test) < 20:
        raise RuntimeError("Holdout split produced too few train/test records.")
    ycol = "Binding_defect_u"
    model_names = ["mean","A","R","R_plus_A","R_signed","R_signed_plus_A",
                   "SEMF","SEMF_plus_R_signed","SEMF_plus_R_absolute"]
    metric_rows, pred_rows = [], []
    y = test[ycol].to_numpy(float)
    for kind in model_names:
        pred = fit_predict(train, test, kind, ycol)
        mae, rmse, r2 = metrics(y, pred)
        metric_rows.append({
            "Model": kind, "Train_records": len(train), "Test_records": len(test),
            "Held_out_elements": len(test_z), "MAE_u": mae, "RMSE_u": rmse, "R2": r2
        })
        for (_, row), p in zip(test.iterrows(), pred):
            pred_rows.append({
                "Z": int(row["Z"]), "Symbol": row["Symbol"], "A": int(row["A"]),
                "N": int(row["N"]), "Model": kind,
                "Observed_binding_defect_u": float(row[ycol]),
                "Predicted_binding_defect_u": float(p),
                "Absolute_error_u": abs(float(p)-float(row[ycol]))
            })
    metrics_df = pd.DataFrame(metric_rows).sort_values("MAE_u")
    metrics_df.to_csv(OUT/"element_holdout_model_metrics.csv", index=False)

    # Repeated group holdout: repeat 30 times with different held-out element sets.
    repeated_rows = []
    for split_seed in range(30):
        split_rng = np.random.default_rng(20261117 + split_seed)
        split_elements = split_rng.permutation(elements)
        split_test_z = set(split_elements[:n_test].tolist())
        split_train = clean[~clean["Z"].isin(split_test_z)].copy()
        split_test = clean[clean["Z"].isin(split_test_z)].copy()
        split_y = split_test[ycol].to_numpy(float)
        for kind in model_names:
            split_pred = fit_predict(split_train, split_test, kind, ycol)
            mae, rmse, r2 = metrics(split_y, split_pred)
            repeated_rows.append({
                "Split": split_seed + 1, "Model": kind,
                "Train_records": len(split_train), "Test_records": len(split_test),
                "Held_out_elements": len(split_test_z),
                "MAE_u": mae, "RMSE_u": rmse, "R2": r2
            })
    repeated = pd.DataFrame(repeated_rows)
    repeated.to_csv(OUT/"repeated_element_holdout_metrics.csv", index=False)
    repeated_summary = (repeated.groupby("Model")
        .agg(Splits=("Split","count"),
             MAE_median_u=("MAE_u","median"), MAE_mean_u=("MAE_u","mean"),
             MAE_min_u=("MAE_u","min"), MAE_max_u=("MAE_u","max"),
             RMSE_median_u=("RMSE_u","median"), R2_median=("R2","median"))
        .reset_index().sort_values("MAE_median_u"))
    repeated_summary.to_csv(OUT/"repeated_element_holdout_summary.csv", index=False)
    predictions = pd.DataFrame(pred_rows)
    predictions.to_csv(OUT/"element_holdout_predictions.csv", index=False)

    # Global descriptive statistics; these are association checks, not causal evidence.
    pearson = clean["Residual_absolute_u"].corr(clean["Binding_defect_u"], method="pearson")
    spearman = spearman_corr(clean["Residual_absolute_u"], clean["Binding_defect_u"])
    signed_pearson = clean["Residual_signed_u"].corr(clean["Binding_defect_u"], method="pearson")
    signed_spearman = spearman_corr(clean["Residual_signed_u"], clean["Binding_defect_u"])
    ratio = clean["Residual_to_defect_ratio"].replace([np.inf,-np.inf], np.nan).dropna()
    ratio_stats = {
        "n": int(len(ratio)), "median_pct": float(100*ratio.median()),
        "q10_pct": float(100*ratio.quantile(.10)), "q90_pct": float(100*ratio.quantile(.90)),
        "min_pct": float(100*ratio.min()), "max_pct": float(100*ratio.max()),
        "std_pct": float(100*ratio.std())
    }

    # Illustrative isotopic families requested in the discussion.
    examples = clean[clean["Symbol"].isin(["Fe","Ni","Pb","U"])].copy()
    examples.to_csv(OUT/"selected_element_isotope_families.csv", index=False)

    fig, ax = plt.subplots(figsize=(9,6))
    ax.scatter(clean["Residual_absolute_u"], clean["Binding_defect_u"], s=10, alpha=.35)
    ax.set_xlabel("Model residual absolute (u)")
    ax.set_ylabel("AME binding-derived mass defect (u)")
    ax.set_title("Residual vs binding-derived mass defect — clean ground-state matches")
    ax.grid(alpha=.25); fig.tight_layout()
    fig.savefig(OUT/"validation_residual_vs_defect.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9,6))
    ax.bar(metrics_df["Model"], metrics_df["MAE_u"])
    ax.set_ylabel("Holdout MAE (u)")
    ax.set_title("Prediction error by model — entire elements held out")
    ax.grid(axis="y", alpha=.25); fig.tight_layout()
    fig.savefig(OUT/"validation_holdout_mae.png", dpi=180); plt.close(fig)

    lines = [
        "# تقرير التحقق المستقل من فرضية المتبقي",
        "",
        "## البيانات المستخدمة",
        f"- السجلات المطابقة مع AME2020 قبل التنقية: {len(matched):,}",
        f"- السجلات النظيفة بعد استبعاد أي علامة تقدير/تحذير: {len(clean):,}",
        f"- العناصر الموجودة في العينة النظيفة: {clean['Z'].nunique()}",
        f"- عناصر التدريب: {train['Z'].nunique()}، سجلات التدريب: {len(train):,}",
        f"- عناصر الاختبار المحجوبة بالكامل: {len(test_z)}، سجلات الاختبار: {len(test):,}",
        f"- العناصر المحجوبة: {', '.join(sorted(set(clean.loc[clean['Z'].isin(test_z),'Symbol'].unique())))}",
        "",
        "## الارتباط العام",
        f"- Pearson بين المتبقي المطلق ونقص الكتلة المشتق من طاقة الربط: {pearson:.5f}",
        f"- Spearman: {spearman:.5f}",
        f"- Pearson للمتبقي الموقّع: {signed_pearson:.5f}، وSpearman: {signed_spearman:.5f}.",
        f"- نسبة المتبقي إلى نقص الكتلة: الوسيط {ratio_stats['median_pct']:.3f}%، والانحراف المعياري {ratio_stats['std_pct']:.3f} نقطة مئوية.",
        f"- المجال من {ratio_stats['min_pct']:.3f}% إلى {ratio_stats['max_pct']:.3f}%، والربيعان العشريان والتسعيني: {ratio_stats['q10_pct']:.3f}% و{ratio_stats['q90_pct']:.3f}%.",
        "",
        "## اختبار النظائر داخل العنصر الواحد",
        f"- عدد العناصر التي لديها 3 نظائر نظيفة على الأقل وتغير في المتبقي: {len(within)}.",
        "- التفاصيل الكاملة في isotope_within_element_correlations.csv.",
        f"- توزيع Pearson داخل العناصر: الوسيط {within['Pearson_R_vs_defect'].median():.4f}، الأدنى {within['Pearson_R_vs_defect'].min():.4f}، الأعلى {within['Pearson_R_vs_defect'].max():.4f}.",
        f"- توزيع Spearman المطلق داخل العناصر: الوسيط {within['Spearman_R_vs_defect'].median():.4f}، الأدنى {within['Spearman_R_vs_defect'].min():.4f}، الأعلى {within['Spearman_R_vs_defect'].max():.4f}.",
        f"- وسيط Pearson للمتبقي الموقّع داخل العناصر: {within['Signed_Pearson_R_vs_defect'].median():.4f}.",
        f"- وسيط Spearman للمتبقي الموقّع داخل العناصر: {within['Signed_Spearman_R_vs_defect'].median():.4f}.",
        "- هذا الاختبار يثبت/ينفي وجود انتظام إحصائي داخل العائلة النظائرية؛ لا يكفي وحده لإثبات تفسير فيزيائي.",
        "",
        "## اختبار التنبؤ بعناصر محجوبة",
        "- حُجبت عناصر كاملة، وليس نظائر عشوائية من العناصر نفسها، لمنع تسرب معلومات العنصر إلى الاختبار.",
        "- النماذج: متوسط التدريب، A فقط، المتبقي المطلق أو الموقّع منفرداً، كل منهما مع A، وصيغة شبه تجريبية للكتلة النووية (SEMF) بمعاملات ملائمة على التدريب فقط.",
        "- معاملات SEMF ملائمة على بيانات التدريب، ثم اختبرت على عناصر لم تدخل التدريب.",
        "",
        "### نتائج الاختبار (الأقل MAE أفضل)",
    ]
    for _, r in metrics_df.iterrows():
        lines.append(f"- {r['Model']}: MAE={r['MAE_u']:.6f} u، RMSE={r['RMSE_u']:.6f} u، R²={r['R2']:.5f}")
    lines += [
        "",
        "## ثبات النتيجة عبر 30 تقسيمًا مستقلاً",
        "- في كل تقسيم حُجبت 25% من العناصر بالكامل، وأعيد ملاءمة النماذج على بقية العناصر.",
    ]
    for _, r in repeated_summary.iterrows():
        lines.append(f"- {r['Model']}: وسيط MAE={r['MAE_median_u']:.6f} u، المتوسط={r['MAE_mean_u']:.6f} u، المجال={r['MAE_min_u']:.6f}–{r['MAE_max_u']:.6f} u، وسيط R²={r['R2_median']:.5f}")
    best = metrics_df.iloc[0]
    lines += [
        "",
        f"## النتيجة العددية الأولية",
        f"- أقل خطأ في هذا التقسيم كان للنموذج {best['Model']} (MAE={best['MAE_u']:.6f} u).",
        "- لا يُعد هذا وحده إثباتاً؛ يجب فحص استقرار النتيجة بتقسيمات متعددة وبمصادر/إصدارات أحدث قبل أي ادعاء.",
        "- المتبقي المطلق معرف جبرياً من |N-Z|؛ لذلك ارتباطه بنقص الكتلة لا يثبت أنه سبب نقص الكتلة أو مكوّن مادي مستقل.",
        "- المقارنة مع SEMF هنا خط أساس إحصائي قابل لإعادة الإنتاج، وليست حكماً بأن SEMF هو النموذج النووي الوحيد أو الأفضل.",
        "",
        "## الملفات",
        "- isotope_within_element_correlations.csv",
        "- element_holdout_model_metrics.csv",
        "- element_holdout_predictions.csv",
        "- selected_element_isotope_families.csv",
        "- validation_residual_vs_defect.png",
        "- validation_holdout_mae.png",
        ""
    ]
    (OUT/"report_ar_validation.md").write_text("\n".join(lines), encoding="utf-8")
    validate_cumulative_outputs()
    print(f"Matched records: {len(matched)}")
    print(f"Clean records: {len(clean)}")
    print(f"Within-element groups tested: {len(within)}")
    print(f"Train records/elements: {len(train)}/{train['Z'].nunique()}")
    print(f"Test records/elements: {len(test)}/{test['Z'].nunique()}")
    print(f"Global Pearson/Spearman: {pearson:.6f}/{spearman:.6f}")
    print("HOLDOUT METRICS:")
    print(metrics_df.to_string(index=False))
    print("VALIDATION COMPLETED")

if __name__ == "__main__":
    main()
