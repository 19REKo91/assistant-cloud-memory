#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cumulative isotope-series analysis for the binary-box residual hypothesis.

The cumulative axis is defined within each fixed-Z isotope family, ordered by N.
It is not a sum of unrelated isotope masses and not a sum across elements.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
SOURCE_COLUMNS = [
    "Z", "N", "A", "Symbol", "Ground_state_candidate", "AME_match",
    "U_2Z_plus_N", "D_Z_plus_2N", "C_raw_u", "C_cancel_u",
    "AME_mass_defect_u_from_binding", "Binding_energy_per_A_keV",
    "Residual_signed_u", "Residual_absolute_u", "Residual_from_subtraction_u",
    "AME_estimated_or_flagged",
]

def _bool_series(series):
    return series.astype("string").str.lower().isin(["true", "1", "yes"])

def build_cumulative(data: pd.DataFrame):
    missing = [c for c in SOURCE_COLUMNS if c not in data.columns]
    if missing:
        raise ValueError(f"Cumulative analysis missing required columns: {missing}")

    frame = data.copy()
    for col in ["Z", "N", "A", "AME_mass_defect_u_from_binding",
                "Binding_energy_per_A_keV", "U_2Z_plus_N", "D_Z_plus_2N",
                "C_raw_u", "C_cancel_u", "Residual_signed_u",
                "Residual_absolute_u", "Residual_from_subtraction_u"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")

    ground = _bool_series(frame["Ground_state_candidate"])
    matched = _bool_series(frame["AME_match"])
    frame = frame[ground & matched & frame["Z"].between(1, 118)].copy()
    frame = frame.dropna(subset=[
        "Z", "N", "A", "AME_mass_defect_u_from_binding",
        "Binding_energy_per_A_keV", "Residual_signed_u",
        "Residual_absolute_u"
    ])
    if frame.empty:
        raise RuntimeError("No ground-state AME-matched isotopes available for cumulative analysis.")

    frame["Z"] = frame["Z"].astype(int)
    frame["N"] = frame["N"].astype(int)
    frame["A"] = frame["A"].astype(int)
    frame["Binding_energy_total_MeV"] = (
        frame["Binding_energy_per_A_keV"] * frame["A"] / 1000.0
    )
    frame["Quality_class"] = np.where(
        _bool_series(frame["AME_estimated_or_flagged"]), "flagged_or_estimated", "clean"
    )

    duplicate = frame.duplicated(["Z", "N"], keep=False)
    if duplicate.any():
        sample = frame.loc[duplicate, ["Z", "N", "A", "Symbol"]].head(12).to_dict("records")
        raise RuntimeError(
            "Duplicate ground-state isotope keys (Z,N); refusing silent deduplication: "
            + str(sample)
        )

    frame = frame.sort_values(["Z", "N", "A"], kind="mergesort").reset_index(drop=True)
    outputs = []
    for (z, symbol), group in frame.groupby(["Z", "Symbol"], sort=True):
        g = group.sort_values(["N", "A"], kind="mergesort").copy().reset_index(drop=True)
        first = g.iloc[0]
        g["Previous_N"] = g["N"].shift(1)
        g["Previous_A"] = g["A"].shift(1)
        g["Delta_N_from_previous"] = g["N"].diff()
        g["Has_previous_isotope"] = g["Previous_N"].notna()
        g["Gap_between_observed_N"] = g["Delta_N_from_previous"].gt(1).fillna(False)
        g["Delta_U"] = g["U_2Z_plus_N"].diff()
        g["Delta_D"] = g["D_Z_plus_2N"].diff()
        g["Delta_C_raw_u"] = g["C_raw_u"].diff()
        g["Delta_C_cancel_u"] = g["C_cancel_u"].diff()
        g["Delta_residual_from_subtraction_u"] = g["Residual_from_subtraction_u"].diff()
        g["Delta_residual_signed_u"] = g["Residual_signed_u"].diff()
        g["Delta_residual_absolute_u"] = g["Residual_absolute_u"].diff()
        g["Delta_binding_defect_u"] = g["AME_mass_defect_u_from_binding"].diff()
        g["Delta_binding_energy_MeV"] = g["Binding_energy_total_MeV"].diff()

        # Reference-relative net changes: the first observed isotope is zero.
        g["C_raw_change_from_first_u"] = g["C_raw_u"] - float(first["C_raw_u"])
        g["C_cancel_change_from_first_u"] = g["C_cancel_u"] - float(first["C_cancel_u"])
        g["Residual_subtraction_change_from_first_u"] = (
            g["Residual_from_subtraction_u"] - float(first["Residual_from_subtraction_u"])
        )
        g["Residual_signed_change_from_first_u"] = (
            g["Residual_signed_u"] - float(first["Residual_signed_u"])
        )
        g["Residual_absolute_change_from_first_u"] = (
            g["Residual_absolute_u"] - float(first["Residual_absolute_u"])
        )
        g["Binding_defect_change_from_first_u"] = (
            g["AME_mass_defect_u_from_binding"] - float(first["AME_mass_defect_u_from_binding"])
        )
        g["Binding_energy_change_from_first_MeV"] = (
            g["Binding_energy_total_MeV"] - float(first["Binding_energy_total_MeV"])
        )

        # Explicit sums of step magnitudes are kept separate from net changes.
        raw_steps = g["Delta_C_raw_u"].fillna(0.0)
        cancel_steps = g["Delta_C_cancel_u"].fillna(0.0)
        subtraction_steps = g["Delta_residual_from_subtraction_u"].fillna(0.0)
        signed_steps = g["Delta_residual_signed_u"].fillna(0.0)
        absolute_steps = g["Delta_residual_absolute_u"].abs().fillna(0.0)
        defect_steps = g["Delta_binding_defect_u"].fillna(0.0)
        g["Cumulative_raw_steps_u"] = raw_steps.cumsum()
        g["Cumulative_cancelled_steps_u"] = cancel_steps.cumsum()
        g["Cumulative_subtraction_residual_steps_u"] = subtraction_steps.cumsum()
        g["Cumulative_absolute_subtraction_step_magnitudes_u"] = subtraction_steps.abs().cumsum()
        g["Raw_minus_cancelled_step_identity_error_u"] = (
            g["Delta_C_raw_u"] - g["Delta_C_cancel_u"] - g["Delta_residual_from_subtraction_u"]
        )
        g["Cumulative_raw_minus_cancelled_identity_error_u"] = (
            g["Cumulative_raw_steps_u"] - g["Cumulative_cancelled_steps_u"]
            - g["Cumulative_subtraction_residual_steps_u"]
        )
        g["Cumulative_signed_residual_steps_u"] = signed_steps.cumsum()
        g["Cumulative_absolute_signed_step_magnitudes_u"] = signed_steps.abs().cumsum()
        g["Cumulative_absolute_residual_variation_u"] = absolute_steps.cumsum()
        g["Cumulative_absolute_mass_defect_step_variation_u"] = defect_steps.abs().cumsum()

        dn = g["Delta_N_from_previous"]
        g["Delta_R_signed_per_added_neutron_u"] = (
            g["Delta_residual_signed_u"] / dn.where(dn > 0)
        )
        g["Delta_mass_defect_per_added_neutron_u"] = (
            g["Delta_binding_defect_u"] / dn.where(dn > 0)
        )
        g["Cumulative_R_identity_expected_u"] = 0.004 * (g["N"] - int(first["N"]))
        g["Cumulative_R_identity_error_u"] = (
            g["Cumulative_signed_residual_steps_u"] - g["Cumulative_R_identity_expected_u"]
        )
        g["Step_R_identity_error_u"] = (
            g["Delta_residual_signed_u"] - 0.004 * g["Delta_N_from_previous"]
        )
        g["Residual_change_to_defect_change_ratio"] = (
            g["Residual_signed_change_from_first_u"] /
            g["Binding_defect_change_from_first_u"].where(
                g["Binding_defect_change_from_first_u"].abs() > 1e-15
            )
        )
        g["Element_reference_N"] = int(first["N"])
        g["Element_reference_A"] = int(first["A"])
        outputs.append(g)

    result = pd.concat(outputs, ignore_index=True)
    max_step_error = float(result["Step_R_identity_error_u"].abs().max(skipna=True) or 0.0)
    max_cum_error = float(result["Cumulative_R_identity_error_u"].abs().max(skipna=True) or 0.0)
    if max_step_error > 1e-10 or max_cum_error > 1e-10:
        raise AssertionError(
            f"Cumulative residual identity failed: step={max_step_error}, cumulative={max_cum_error}"
        )

    OUT.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT / "isotope_cumulative_steps_all.csv", index=False, na_rep="NA", encoding="utf-8-sig")
    clean = result[result["Quality_class"] == "clean"].copy()
    clean.to_csv(OUT / "isotope_cumulative_steps_clean.csv", index=False, na_rep="NA", encoding="utf-8-sig")

    summary_rows = []
    for (z, symbol), g in result.groupby(["Z", "Symbol"], sort=True):
        g = g.sort_values("N")
        summary_rows.append({
            "Z": int(z), "Symbol": symbol, "Isotope_records": len(g),
            "Clean_records": int((g["Quality_class"] == "clean").sum()),
            "Flagged_or_estimated_records": int((g["Quality_class"] != "clean").sum()),
            "N_first": int(g["N"].min()), "N_last": int(g["N"].max()),
            "Total_observed_delta_N": int(g["N"].max() - g["N"].min()),
            "Observed_steps": max(0, len(g) - 1),
            "Gaps_delta_N_gt_1": int(g["Gap_between_observed_N"].sum()),
            "Net_cumulative_C_raw_u": float(g["C_raw_change_from_first_u"].iloc[-1]),
            "Net_cumulative_C_cancelled_u": float(g["C_cancel_change_from_first_u"].iloc[-1]),
            "Net_cumulative_subtraction_residual_u": float(g["Residual_subtraction_change_from_first_u"].iloc[-1]),
            "Net_cumulative_R_signed_u": float(g["Residual_signed_change_from_first_u"].iloc[-1]),
            "Sum_absolute_R_step_magnitudes_u": float(g["Cumulative_absolute_signed_step_magnitudes_u"].iloc[-1]),
            "Net_binding_defect_change_u": float(g["Binding_defect_change_from_first_u"].iloc[-1]),
            "Sum_absolute_defect_step_changes_u": float(g["Cumulative_absolute_mass_defect_step_variation_u"].iloc[-1]),
            "Net_binding_energy_change_MeV": float(g["Binding_energy_change_from_first_MeV"].iloc[-1]),
            "Max_abs_R_identity_error_u": float(g["Cumulative_R_identity_error_u"].abs().max()),
        })
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT / "isotope_cumulative_element_summary.csv", index=False, na_rep="NA", encoding="utf-8-sig")

    example_symbols = ["Fe", "Ni", "Pb", "Bi", "Po", "Ra", "Th", "U"]
    examples = clean[clean["Symbol"].isin(example_symbols)].copy()
    examples.to_csv(OUT / "cumulative_Fe_Ni_Pb_Bi_Po_Ra_Th_U_families.csv", index=False, na_rep="NA", encoding="utf-8-sig")


    # Cumulative association is reported pooled and within each element.
    # Within-element statistics avoid treating unrelated Z families as one series.
    correlation_rows = []
    for (z, symbol), g in clean.groupby(["Z", "Symbol"], sort=True):
        g = g.sort_values("N")
        if len(g) < 3:
            continue
        x_signed = g["Residual_signed_change_from_first_u"]
        x_sub = g["Residual_subtraction_change_from_first_u"]
        y_defect = g["Binding_defect_change_from_first_u"]
        if x_signed.nunique() < 2 or y_defect.nunique() < 2:
            continue
        correlation_rows.append({
            "Z": int(z), "Symbol": symbol, "Clean_isotope_records": len(g),
            "Pearson_cumulative_signed_R_vs_defect_change": x_signed.corr(y_defect, method="pearson"),
            "Spearman_cumulative_signed_R_vs_defect_change": x_signed.rank(method="average").corr(y_defect.rank(method="average")),
            "Pearson_cumulative_subtraction_residual_vs_defect_change": (
                x_sub.corr(y_defect, method="pearson") if x_sub.nunique() > 1 else np.nan
            ),
            "Spearman_cumulative_subtraction_residual_vs_defect_change": (
                x_sub.rank(method="average").corr(y_defect.rank(method="average")) if x_sub.nunique() > 1 else np.nan
            ),
        })
    cumulative_corr = pd.DataFrame(correlation_rows)
    if not cumulative_corr.empty:
        cumulative_corr = cumulative_corr.sort_values("Z")
    cumulative_corr.to_csv(
        OUT / "isotope_cumulative_within_element_correlations.csv",
        index=False, na_rep="NA", encoding="utf-8-sig"
    )

    pooled_signed_pearson = clean["Residual_signed_change_from_first_u"].corr(
        clean["Binding_defect_change_from_first_u"], method="pearson"
    )
    pooled_signed_spearman = clean["Residual_signed_change_from_first_u"].rank(method="average").corr(
        clean["Binding_defect_change_from_first_u"].rank(method="average")
    )
    pooled_sub_pearson = clean["Residual_subtraction_change_from_first_u"].corr(
        clean["Binding_defect_change_from_first_u"], method="pearson"
    )
    pooled_sub_spearman = clean["Residual_subtraction_change_from_first_u"].rank(method="average").corr(
        clean["Binding_defect_change_from_first_u"].rank(method="average")
    )
    median_within_signed_pearson = (
        float(cumulative_corr["Pearson_cumulative_signed_R_vs_defect_change"].median())
        if not cumulative_corr.empty else float("nan")
    )

    plot_data = clean[clean["Has_previous_isotope"]].copy()
    if not plot_data.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(plot_data["Residual_signed_change_from_first_u"],
                   plot_data["Binding_defect_change_from_first_u"], s=13, alpha=0.45)
        ax.set_xlabel("Cumulative signed residual change from first observed isotope (u)")
        ax.set_ylabel("Binding-derived mass-defect change from first isotope (u)")
        ax.set_title("Cumulative isotope-series change: model residual vs binding-derived defect")
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(OUT / "cumulative_residual_vs_defect_change.png", dpi=180)
        plt.close(fig)

    for symbol in example_symbols:
        g = examples[examples["Symbol"] == symbol]
        if len(g) < 2:
            continue
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.plot(g["N"], g["Residual_signed_change_from_first_u"], marker="o",
                label="Cumulative signed residual change")
        ax.plot(g["N"], g["Binding_defect_change_from_first_u"], marker="s",
                label="Binding-derived defect change")
        ax.set_xlabel("Neutron number N")
        ax.set_ylabel("Change from first observed isotope (u)")
        ax.set_title(f"{symbol}: cumulative isotope-family comparison")
        ax.grid(alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(OUT / f"cumulative_{symbol}_family.png", dpi=180)
        plt.close(fig)

    clean_elements = int(clean["Z"].nunique())
    total_gaps = int(result["Gap_between_observed_N"].sum())
    report = [
        "# تقرير التراكم داخل السلاسل النظائرية",
        "",
        "## التعريف المعتمد",
        "- يثبت العدد الذري Z داخل كل عنصر، وترتب نظائره تصاعدياً حسب N.",
        "- المتبقي الفردي الموقّع: R_signed = 0.004(N-Z).",
        "- المتبقي الفردي المطلق: R_absolute = 0.004|N-Z|.",
        "- لكل نظير: U=2Z+N وD=Z+2N؛ C_raw=0.004(U+D)=0.012A، وC_cancel=0.008 min(U,D).",
        "- الفرق C_raw-C_cancel يساوي المتبقي المطلق من الطرح، ولا يساوي المتبقي الموقّع عندما N<Z.",
        "- التراكم الصافي من أول نظير مرصود: مجموع فروق R_signed بين الخطوات؛ وهو يساوي R_signed الحالي ناقص قيمة النظير المرجعي.",
        "- مجموع مقادير الخطوات المطلقة يحفظ منفصلاً عن التغير الصافي، ولا يخلط مع المتبقي المطلق الفردي.",
        "- يحسب التراكم من النظير المرجعي لكل من C_raw وC_cancel وفرق الطرح وR_signed، وتفصل مجاميع مقادير الخطوات عن صافي التغير.",
        "- المقارنة الفيزيائية تستخدم تغير نقص الكتلة المشتق من طاقة الربط من النظير المرجعي، لا جمع نقص الكتلة المطلق لكل نظير.",
        "",
        "## العلاقة بين التراكم وتغير عيب الكتلة",
        f"- ارتباط بيرسون المجمع بين تغير R الموقّع من المرجع وتغير عيب الكتلة: {pooled_signed_pearson:.5f}.",
        f"- ارتباط سبيرمان المجمع للمقدارين نفسيهما: {pooled_signed_spearman:.5f}.",
        f"- ارتباط بيرسون المجمع لتغير فرق الطرح المطلق مع تغير عيب الكتلة: {pooled_sub_pearson:.5f}.",
        f"- ارتباط سبيرمان المجمع لتغير فرق الطرح المطلق مع تغير عيب الكتلة: {pooled_sub_spearman:.5f}.",
        f"- عدد العائلات النظائرية النظيفة ذات 3 سجلات أو أكثر والقابلة لحساب الارتباط: {len(cumulative_corr)}.",
        f"- وسيط بيرسون داخل العناصر (R الموقّع التراكمي مقابل تغير عيب الكتلة): {median_within_signed_pearson:.5f}.",
        "- الارتباط المجمع وصفي وقد يتأثر بالفروق بين العناصر؛ لذلك يعرض ملف مستقل الارتباط داخل كل عنصر. لا تعني معاملات الارتباط السببية.",
        "",
        "## ضبط الفجوات والجودة",
        f"- عدد سجلات النظائر الأرضية المطابقة المتاحة: {len(result):,}.",
        f"- عدد العناصر ذات بيانات نظائرية: {result['Z'].nunique():,}.",
        f"- عدد العناصر التي لها سجلات نظيفة: {clean_elements:,}.",
        f"- عدد الانتقالات التي تتضمن فجوة N أكبر من 1: {total_gaps:,}.",
        "- لا تُفترض النظائر المفقودة ولا تُنشأ خطوات وهمية؛ يسجل Delta_N الفعلي وتوسم الفجوة صراحة.",
        "- تحفظ السجلات المقدرة/الموسومة في ملف all، ويُنشأ ملف clean منفصل بعد استبعادها.",
        "",
        "## الهوية الحسابية",
        f"- أكبر خطأ في هوية الخطوة ΔR_signed = 0.004 ΔN: {max_step_error:.3e} u.",
        f"- أكبر خطأ في هوية التراكم من النظير المرجعي: {max_cum_error:.3e} u.",
        "- هاتان هويتان جبريتان ناتجتان من تعريف R؛ لا تمثلان اكتشافاً تجريبياً.",
        "",
        "## تفسير المقارنة",
        "- تغير نقص الكتلة عبر السلسلة هو فرق بين نظيرين (أو من المرجع)، وليس مجموع كتل النقص للنظائر المختلفة.",
        "- قيمة نقص الكتلة مشتقة من طاقة الربط المنشورة في AME2020؛ ليست قياساً مستقلاً عنها.",
        "- لا يفترض أن التراكم الحسابي يساوي التغير الفيزيائي؛ المقارنة والاختلاف ظاهران في ملفات CSV والرسوم.",
        "- هذا التحليل لا يثبت أن 0.004u كتلة جسيم/كوارك أو مكوّن مادي مستقل.",
        "",
        "## الملفات",
        "- isotope_cumulative_steps_all.csv",
        "- isotope_cumulative_steps_clean.csv",
        "- isotope_cumulative_element_summary.csv",
        "- cumulative_Fe_Ni_Pb_Bi_Po_Ra_Th_U_families.csv",
        "- isotope_cumulative_within_element_correlations.csv",
        "- cumulative_residual_vs_defect_change.png",
        "- رسوم عائلات Fe وNi وPb وBi وPo وRa وTh وU",
        "- report_ar_cumulative.md",
    ]
    (OUT / "report_ar_cumulative.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"CUMULATIVE matched ground-state isotope records: {len(result)}")
    print(f"CUMULATIVE elements: {result['Z'].nunique()}")
    print(f"CUMULATIVE clean records: {len(clean)}")
    print(f"CUMULATIVE observed N gaps: {total_gaps}")
    print(f"CUMULATIVE step identity max error: {max_step_error:.3e} u")
    print(f"CUMULATIVE series identity max error: {max_cum_error:.3e} u")
    print("CUMULATIVE ANALYSIS COMPLETED")
    return result, summary
