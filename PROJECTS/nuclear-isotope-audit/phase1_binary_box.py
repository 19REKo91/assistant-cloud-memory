#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 1 only: audit the binary U/D count box and powers-of-two coordinates.

Deliberately excludes the 0.016-u brick, mass defect, binding energy,
42% proposal, and isotope accumulation. Those belong to later phases.
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"
sys.path.insert(0, str(ROOT))
from main import parse_nubase, parse_ame

def add_binary_box(frame, column, prefix):
    values = frame[column].astype(int)
    k = np.floor(np.log2(values)).astype(int)
    lower = np.power(2, k)
    upper = 2 * lower
    frame[f"{prefix}_box_k"] = k
    frame[f"{prefix}_box_lower"] = lower
    frame[f"{prefix}_box_upper"] = upper
    frame[f"{prefix}_box_position_pct"] = (
        100.0 * (values - lower) / (upper - lower)
    )
    frame[f"{prefix}_is_power_of_two"] = (
        values & (values - 1)
    ) == 0

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    nubase_path = RAW / "nubase_4.mas20.txt"
    ame_path = RAW / "mass_1.mas20.txt"
    if not nubase_path.exists() or not ame_path.exists():
        raise FileNotFoundError("AME2020/NUBASE2020 raw source files are missing.")

    nubase = parse_nubase(nubase_path)
    ame = parse_ame(ame_path)

    ground = nubase[nubase["Ground_state_candidate"]].copy()
    merged = ground.merge(
        ame[["Z", "A", "AME_N", "AME_symbol"]],
        on=["Z", "A"], how="inner", validate="one_to_one"
    )
    merged = merged[
        merged["Z"].between(1, 118)
        & (merged["A"] >= merged["Z"])
        & (merged["A"] > 0)
    ].copy()
    if merged.empty:
        raise RuntimeError("No matched ground-state nuclides available.")

    merged["N_direct"] = merged["A"] - merged["Z"]
    merged["U_2Z_plus_N"] = 2 * merged["Z"] + merged["N_direct"]
    merged["D_Z_plus_2N"] = merged["Z"] + 2 * merged["N_direct"]
    merged["U_plus_D"] = merged["U_2Z_plus_N"] + merged["D_Z_plus_2N"]
    merged["D_minus_U"] = merged["D_Z_plus_2N"] - merged["U_2Z_plus_N"]
    merged["Min_U_D"] = merged[["U_2Z_plus_N", "D_Z_plus_2N"]].min(axis=1)
    merged["Max_U_D"] = merged[["U_2Z_plus_N", "D_Z_plus_2N"]].max(axis=1)

    # Direct arithmetic identities, checked independently from the derived columns.
    checks = {
        "N_equals_A_minus_Z": merged["N"].astype(int).eq(merged["N_direct"]),
        "AME_N_equals_A_minus_Z": merged["AME_N"].astype(int).eq(merged["N_direct"]),
        "U_identity": merged["U_2Z_plus_N"].eq(2 * merged["Z"] + merged["N_direct"]),
        "D_identity": merged["D_Z_plus_2N"].eq(merged["Z"] + 2 * merged["N_direct"]),
        "U_plus_D_equals_3A": merged["U_plus_D"].eq(3 * merged["A"]),
        "D_minus_U_equals_N_minus_Z": merged["D_minus_U"].eq(merged["N_direct"] - merged["Z"]),
        "min_plus_max_equals_3A": (
            merged["Min_U_D"] + merged["Max_U_D"]
        ).eq(3 * merged["A"]),
    }
    for name, ok in checks.items():
        merged[f"check_{name}"] = ok

    # Binary doubling intervals are evaluated separately on A, U and D.
    for column, prefix in [
        ("A", "A"), ("U_2Z_plus_N", "U"), ("D_Z_plus_2N", "D")
    ]:
        add_binary_box(merged, column, prefix)

    merged = merged.sort_values(["Z", "N_direct", "A"]).reset_index(drop=True)
    merged.to_csv(OUT / "phase1_binary_box_nuclides.csv", index=False, na_rep="NA")

    # Per-coordinate occupancy and position summaries.
    summaries = []
    for prefix, value_col in [
        ("A", "A"), ("U", "U_2Z_plus_N"), ("D", "D_Z_plus_2N")
    ]:
        for k, group in merged.groupby(f"{prefix}_box_k", sort=True):
            p = group[f"{prefix}_box_position_pct"]
            summaries.append({
                "Coordinate": prefix, "Box_k": int(k),
                "Lower_boundary": int(2 ** int(k)),
                "Upper_boundary": int(2 ** (int(k) + 1)),
                "Nuclide_records": len(group),
                "Elements": int(group["Z"].nunique()),
                "Position_median_pct": float(p.median()),
                "Position_q25_pct": float(p.quantile(.25)),
                "Position_q75_pct": float(p.quantile(.75)),
                "Within_5pct_lower_boundary": int((p <= 5).sum()),
                "Within_5pct_upper_boundary": int((p >= 95).sum()),
                "Exactly_on_power_of_two": int(group[f"{prefix}_is_power_of_two"].sum()),
            })
    box_summary = pd.DataFrame(summaries)
    box_summary.to_csv(OUT / "phase1_binary_box_occupancy.csv", index=False, na_rep="NA")

    # Per-element summaries avoid presenting thousands of related isotopes as independent elements.
    element_rows = []
    for (z, symbol), group in merged.groupby(["Z", "Symbol"], sort=True):
        row = {"Z": int(z), "Symbol": str(symbol), "Nuclide_records": len(group)}
        for prefix in ("A", "U", "D"):
            row[f"{prefix}_position_median_pct"] = float(
                group[f"{prefix}_box_position_pct"].median()
            )
            row[f"{prefix}_box_k_mode"] = int(
                group[f"{prefix}_box_k"].mode().iloc[0]
            )
        row["N_minus_Z_min"] = int((group["N_direct"] - group["Z"]).min())
        row["N_minus_Z_max"] = int((group["N_direct"] - group["Z"]).max())
        element_rows.append(row)
    pd.DataFrame(element_rows).to_csv(
        OUT / "phase1_binary_box_elements.csv", index=False, na_rep="NA"
    )

    # Inspect the integer boundary around A=64 without asserting a physical transition.
    boundary = merged[merged["A"].between(60, 68)].copy()
    boundary.to_csv(OUT / "phase1_A60_A68_boundary.csv", index=False, na_rep="NA")
    boundary_counts = (
        merged[merged["A"].between(60, 68)]
        .groupby("A").agg(
            Nuclide_records=("A", "size"),
            Elements=("Z", "nunique"),
            Symbols=("Symbol", lambda s: ";".join(sorted(set(s))))
        ).reset_index()
    )
    boundary_counts.to_csv(
        OUT / "phase1_A60_A68_boundary_counts.csv", index=False, na_rep="NA"
    )

    total_checks = int(len(checks))
    failed = {
        name: int((~ok).sum()) for name, ok in checks.items() if (~ok).any()
    }
    report = [
        "# المرحلة الأولى — تدقيق الصندوق الثنائي فقط",
        "",
        "## حدود المرحلة",
        "- يشمل هذا التقرير عدّ U/D والصناديق الثنائية ذات حدود قوى العدد 2.",
        "- لا يشمل طوبة 0.016u أو عيب الكتلة أو طاقة الربط أو نسبة 42% أو التراكم النظائري.",
        "",
        "## عينة البيانات",
        f"- سجلات NUBASE2020 المرشحة للحالة الأرضية: {len(ground):,}.",
        f"- سجلات AME2020: {len(ame):,}.",
        f"- النوى الأرضية المطابقة المستخدمة: {len(merged):,}.",
        f"- العناصر الممثلة: {merged['Z'].nunique():,}.",
        "",
        "## تعريف الصندوق الثنائي",
        "- البروتون: U=2 وD=1.",
        "- النيوترون: U=1 وD=2.",
        "- للنواة ذات Z بروتوناً وN نيوتروناً: U=2Z+N، وD=Z+2N.",
        "- U+D=3A، وD−U=N−Z.",
        "- حُسب موضع A وU وD كلٌّ على حدة داخل [2^k, 2^(k+1)]؛ لم نفترض أن المحاور الثلاثة متكافئة.",
        "",
        "## التحقق الحسابي",
        f"- عدد الهويات المختبرة: {total_checks}.",
        f"- إجمالي مخالفات الهويات: {sum(int((~ok).sum()) for ok in checks.values())}.",
        f"- تفاصيل المخالفات: {failed if failed else 'لا توجد'}.",
        "",
        "## نتائج مواضع الصناديق",
    ]
    for prefix in ("A", "U", "D"):
        sub = merged[f"{prefix}_box_position_pct"]
        report += [
            f"- {prefix}: وسيط الموقع {sub.median():.3f}%، الربع الأول {sub.quantile(.25):.3f}%، الربع الثالث {sub.quantile(.75):.3f}%.",
            f"  - ضمن أول 5% من الصندوق: {(sub <= 5).sum():,} ({(sub <= 5).mean()*100:.2f}%).",
            f"  - ضمن آخر 5% من الصندوق: {(sub >= 95).sum():,} ({(sub >= 95).mean()*100:.2f}%).",
            f"  - على قوة للعدد 2 تماماً: {merged[f'{prefix}_is_power_of_two'].sum():,}.",
        ]
    a64 = merged[merged["A"] == 64]
    report += [
        "",
        "## فحص الحد A=64",
        f"- سجلات النظائر عند A=64: {len(a64):,}.",
        f"- العناصر الموجودة عند A=64: {a64['Z'].nunique():,}.",
        f"- عدد سجلات النظائر ضمن A=60 إلى 68: {len(boundary):,}.",
        "- تغيير k عند عبور 64 نتيجة مباشرة لتعريف الصندوق [2^k,2^(k+1)]؛ لا يُعد وحده دليلاً على انتقال فيزيائي.",
        "",
        "## الحكم المرحلي",
        "- هويات U/D الحسابية تُختبر كتعريفات عدّية؛ نجاحها لا يثبت تفسيراً فيزيائياً لكتلة النيوكليون.",
        "- توزيعات المواقع وصفية لعينة AME/NUBASE، وليست اختباراً لانتظام طبيعي قبل تحديد نموذج صفري مستقل.",
        "- لا يُستنتج من هذه المرحلة شيء عن 0.016u أو 42% أو عيب الكتلة؛ تلك مراحل لاحقة.",
        "",
        "## ملفات المرحلة",
        "- phase1_binary_box_nuclides.csv",
        "- phase1_binary_box_occupancy.csv",
        "- phase1_binary_box_elements.csv",
        "- phase1_A60_A68_boundary.csv",
        "- phase1_A60_A68_boundary_counts.csv",
    ]
    (OUT / "report_ar_phase1_binary_box.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    print("\n".join(report))
    if failed:
        raise RuntimeError(f"Phase 1 identity checks failed: {failed}")
    print("PHASE 1 BINARY BOX TEST PASSED")

if __name__ == "__main__":
    main()
