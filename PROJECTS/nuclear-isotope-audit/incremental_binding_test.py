#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test incremental binding-defect changes against 0.004-u lattice multiples.

Runs after cumulative.py has produced isotope_cumulative_steps_clean.csv.
Only clean, adjacent ground-state isotope transitions with Delta_N == 1
are used for the primary per-added-neutron comparison.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
MEV_PER_U = 931.49410242
UNITS = (0.004, 0.008, 0.012, 0.016)


def _bool(s):
    return s.astype("string").str.lower().isin(["true", "1", "yes"])


def run_incremental_binding_test():
    source = OUT / "isotope_cumulative_steps_clean.csv"
    if not source.exists():
        raise FileNotFoundError(
            f"Missing {source.name}; run build_cumulative(data) before this test."
        )

    df = pd.read_csv(source, low_memory=False)
    required = [
        "Z", "Symbol", "A", "N", "Quality_class", "Has_previous_isotope",
        "Delta_N_from_previous", "Delta_binding_defect_u",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    for c in ("Z", "A", "N", "Delta_N_from_previous", "Delta_binding_defect_u"):
        df[c] = pd.to_numeric(df[c], errors="coerce")

    clean = df[df["Quality_class"].astype("string").str.lower().eq("clean")].copy()
    adjacent = clean[
        _bool(clean["Has_previous_isotope"])
        & (clean["Delta_N_from_previous"] == 1)
        & clean["Delta_binding_defect_u"].notna()
    ].copy()
    if adjacent.empty:
        raise RuntimeError("No clean adjacent isotope transitions (Delta_N=1) were found.")

    adjacent["Delta_defect_per_added_neutron_u"] = adjacent["Delta_binding_defect_u"]
    adjacent["Delta_defect_MeV"] = adjacent["Delta_binding_defect_u"] * MEV_PER_U
    adjacent["Defect_over_0p004"] = adjacent["Delta_binding_defect_u"] / 0.004
    nearest_integer = np.rint(adjacent["Defect_over_0p004"]).astype(int)
    adjacent["Nearest_0p004_multiple"] = nearest_integer
    adjacent["Nearest_multiple_parity"] = np.where(nearest_integer % 2 == 0, "even", "odd")
    x = adjacent["Defect_over_0p004"].to_numpy(float)
    adjacent["Distance_to_even_0p008_lattice_u"] = (
        np.abs(x - 2.0 * np.rint(x / 2.0)) * 0.004
    )
    adjacent["Distance_to_odd_offset_lattice_u"] = (
        np.abs(x - (2.0 * np.rint((x - 1.0) / 2.0) + 1.0)) * 0.004
    )

    metrics = []
    values = adjacent["Delta_binding_defect_u"].to_numpy(float)
    for unit in UNITS:
        error = np.abs(values - unit)
        metrics.append({
            "Candidate_unit_u": unit,
            "N_transitions": len(values),
            "Mean_abs_error_u": float(np.mean(error)),
            "Median_abs_error_u": float(np.median(error)),
            "Within_0p001_u": int(np.sum(error <= 0.001)),
            "Within_0p002_u": int(np.sum(error <= 0.002)),
        })
    metrics_df = pd.DataFrame(metrics)

    element_rows = []
    for (z, symbol), g in adjacent.groupby(["Z", "Symbol"], sort=True):
        vals = g["Delta_binding_defect_u"].to_numpy(float)
        even_n = int((g["Nearest_multiple_parity"] == "even").sum())
        odd_n = int((g["Nearest_multiple_parity"] == "odd").sum())
        element_rows.append({
            "Z": int(z),
            "Symbol": str(symbol),
            "Adjacent_clean_transitions": len(g),
            "Mean_delta_defect_u": float(np.mean(vals)),
            "Median_delta_defect_u": float(np.median(vals)),
            "Mean_delta_defect_MeV": float(np.mean(vals) * MEV_PER_U),
            "Nearest_0p008_lattice_mean_distance_u": float(
                g["Distance_to_even_0p008_lattice_u"].mean()
            ),
            "Even_nearest_multiple_count": even_n,
            "Odd_nearest_multiple_count": odd_n,
        })
    element_df = pd.DataFrame(element_rows)

    n_even = int((adjacent["Nearest_multiple_parity"] == "even").sum())
    n_odd = int((adjacent["Nearest_multiple_parity"] == "odd").sum())
    mean_even = float(adjacent["Distance_to_even_0p008_lattice_u"].mean())
    mean_odd = float(adjacent["Distance_to_odd_offset_lattice_u"].mean())
    mean_delta = float(values.mean())

    adjacent.to_csv(
        OUT / "incremental_binding_transition_results.csv",
        index=False, na_rep="NA", encoding="utf-8-sig"
    )
    metrics_df.to_csv(
        OUT / "incremental_binding_unit_comparison.csv",
        index=False, na_rep="NA", encoding="utf-8-sig"
    )
    element_df.to_csv(
        OUT / "incremental_binding_element_summary.csv",
        index=False, na_rep="NA", encoding="utf-8-sig"
    )

    lines = [
        "# اختبار تغير نقص الكتلة بين النظائر المتجاورة",
        "",
        "## العينة والمنهج",
        f"- سجلات النظائر النظيفة في ملف الإدخال: {len(clean):,}.",
        f"- الانتقالات النظيفة المتجاورة المستخدمة (Delta_N=1): {len(adjacent):,}.",
        f"- عدد العناصر ذات انتقال واحد على الأقل: {len(element_df):,}.",
        "- تُستبعد الانتقالات ذات فجوة نيوترونية أو بيانات نقص كتلة غير متاحة من المقارنة الأساسية.",
        "- نقص الكتلة هنا مشتق من طاقة الربط المنشورة في AME2020، وليس قياساً مستقلاً عنها.",
        "",
        "## مقارنة الوحدات المرشحة",
        "| الوحدة (u) | متوسط الخطأ المطلق (u) | الوسيط (u) | ضمن 0.001u | ضمن 0.002u |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in metrics:
        lines.append(
            f"| {row['Candidate_unit_u']:.3f} | {row['Mean_abs_error_u']:.8f} | "
            f"{row['Median_abs_error_u']:.8f} | {row['Within_0p001_u']} | "
            f"{row['Within_0p002_u']} |"
        )
    lines += [
        "",
        "## اختبار الزوجي والفردي داخل شبكة 0.004u",
        f"- أقرب مضاعف زوجي (شبكة 0.008u): {n_even:,}.",
        f"- أقرب مضاعف فردي (الشبكة المزاحة بمقدار 0.004u): {n_odd:,}.",
        f"- متوسط البعد عن شبكة 0.008u: {mean_even:.8f} u.",
        f"- متوسط البعد عن الشبكة الفردية المزاحة: {mean_odd:.8f} u.",
        "- هذا فحص وصفي؛ لا يُفسر كدلالة إحصائية مستقلة لأن الانتقالات متجمعة داخل العناصر.",
        "",
        "## التفسير الفيزيائي الضروري",
        f"- متوسط تغير نقص الكتلة لكل نيوترون مضاف: {mean_delta:.8f} u = {mean_delta * MEV_PER_U:.6f} MeV.",
        f"- 0.004u = {0.004 * MEV_PER_U:.6f} MeV؛ 0.008u = {0.008 * MEV_PER_U:.6f} MeV؛ 0.016u = {0.016 * MEV_PER_U:.6f} MeV.",
        "- عند ثبات Z وإضافة نيوترون واحد، فرق نقص الكتلة المشتق من طاقة الربط يساوي طاقة فصل النيوترون مقسومة على 931.49410242 MeV/u.",
        "- لذلك فإن اقتراب التغير من 0.008u قد يعكس مقياس طاقة فصل نيوترون نووي شائعاً، ولا يثبت أن 0.004u كتلة كوارك أو أن نقص الكتلة مكمّم بهذه الوحدة.",
        "- يلزم تحليل التكتل حسب العنصر، وعدم اليقين، ومقارنة نماذج مرجعية قبل استنتاج أي أفضلية عامة.",
        "",
        "## الملفات",
        "- incremental_binding_transition_results.csv",
        "- incremental_binding_unit_comparison.csv",
        "- incremental_binding_element_summary.csv",
        "- report_ar_incremental_binding_test.md",
    ]
    (OUT / "report_ar_incremental_binding_test.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(
        "INCREMENTAL BINDING TEST COMPLETED — "
        f"transitions={len(adjacent)}, elements={len(element_df)}, "
        f"mean_delta_defect={mean_delta:.8f} u ({mean_delta * MEV_PER_U:.6f} MeV), "
        f"nearest_even={n_even}, nearest_odd={n_odd}"
    )
    return metrics_df, element_df


if __name__ == "__main__":
    run_incremental_binding_test()
