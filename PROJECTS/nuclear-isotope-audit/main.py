#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuclear Isotope Audit
Sources: NUBASE2020 and AME2020 (Atomic Mass Data Center / IAEA-NDS).
This is a reproducible comparison tool, not a validation of the proposed model.
"""

from __future__ import annotations

import csv
import math
import re
import sys
import time
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs"
RAW_DIR = DATA_DIR / "raw"
NUBASE_URL = "https://www-nds.iaea.org/amdc/ame2020/nubase_4.mas20.txt"
AME_URL = "https://www-nds.iaea.org/amdc/ame2020/mass_1.mas20.txt"
U_PER_KEV = 1.0 / 931_494.10242
TIMEOUT = 60

ELEMENTS = [
"H","He","Li","Be","B","C","N","O","F","Ne","Na","Mg","Al","Si","P","S","Cl","Ar",
"K","Ca","Sc","Ti","V","Cr","Mn","Fe","Co","Ni","Cu","Zn","Ga","Ge","As","Se","Br","Kr",
"Rb","Sr","Y","Zr","Nb","Mo","Tc","Ru","Rh","Pd","Ag","Cd","In","Sn","Sb","Te","I","Xe",
"Cs","Ba","La","Ce","Pr","Nd","Pm","Sm","Eu","Gd","Tb","Dy","Ho","Er","Tm","Yb","Lu",
"Hf","Ta","W","Re","Os","Ir","Pt","Au","Hg","Tl","Pb","Bi","Po","At","Rn","Fr","Ra","Ac",
"Th","Pa","U","Np","Pu","Am","Cm","Bk","Cf","Es","Fm","Md","No","Lr","Rf","Db","Sg","Bh",
"Hs","Mt","Ds","Rg","Cn","Nh","Fl","Mc","Lv","Ts","Og"
]

def say(message: str) -> None:
    print(message, flush=True)

def parse_number(value: str) -> tuple[Optional[float], bool, bool]:
    """Return numeric value, estimated-marker flag (#), and noncalculable flag (*)."""
    s = (value or "").strip()
    if not s or "*" in s:
        return None, False, "*" in s
    estimated = "#" in s
    s = s.replace("#", "")
    try:
        return float(s), estimated, False
    except ValueError:
        return None, estimated, False

def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 20_000:
        say(f"Using cached source: {destination.name} ({destination.stat().st_size:,} bytes)")
        return
    say(f"Downloading {url}")
    headers = {"User-Agent": "Nuclear-Isotope-Audit/1.0 (reproducible research script)"}
    response = requests.get(url, timeout=TIMEOUT, headers=headers)
    response.raise_for_status()
    if len(response.content) < 20_000:
        raise RuntimeError(f"Downloaded file is unexpectedly small: {len(response.content)} bytes")
    destination.write_bytes(response.content)
    say(f"Saved {destination.name}: {len(response.content):,} bytes")

def read_text(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()

def parse_nubase(path: Path) -> pd.DataFrame:
    """Parse documented NUBASE2020 fixed-width columns (1-based positions in source header)."""
    rows = []
    rejected = []
    for line_no, line in enumerate(read_text(path), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if len(line) < 80:
            continue
        try:
            a_text = line[0:3].strip()
            zzi_text = line[4:8].strip()
            if not a_text.isdigit() or len(zzi_text) != 4 or not zzi_text.isdigit():
                continue
            a = int(a_text)
            z = int(zzi_text[:3])
            state_index = int(zzi_text[3])
            symbol_field = line[11:16].strip()
            state_suffix = line[16:17].strip()
            mass_excess, mass_estimated, mass_noncalc = parse_number(line[18:31])
            excitation, exc_estimated, exc_noncalc = parse_number(line[42:54])
            half_life_text = line[69:78].strip()
            half_life_unit = line[78:80].strip()
            spin_parity = line[88:102].strip() if len(line) >= 102 else ""
            discovery = line[114:118].strip() if len(line) >= 118 else ""
            decay_modes = line[119:209].strip() if len(line) >= 120 else ""
            if z < 0 or z > 118 or a < z:
                rejected.append((line_no, line[:100], "invalid Z/A"))
                continue
            symbol_match = re.match(r"^\d+([A-Z][a-z]?)", symbol_field)
            symbol = symbol_match.group(1) if symbol_match else ""
            rows.append({
                "A": a, "Z": z, "N": a-z, "Symbol": symbol,
                "NUBASE_symbol_field": symbol_field,
                "State_index": state_index, "State_suffix": state_suffix,
                "NUBASE_mass_excess_keV": mass_excess,
                "NUBASE_mass_excess_estimated": mass_estimated,
                "NUBASE_mass_excess_noncalculable": mass_noncalc,
                "Excitation_energy_keV": excitation,
                "Excitation_estimated": exc_estimated,
                "Excitation_noncalculable": exc_noncalc,
                "Half_life_text": half_life_text, "Half_life_unit": half_life_unit,
                "Spin_parity": spin_parity, "Discovery_year_field": discovery,
                "Decay_modes": decay_modes, "NUBASE_source_line": line_no,
                "NUBASE_raw_line": line
            })
        except Exception as exc:
            rejected.append((line_no, line[:100], str(exc)))
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError("NUBASE parser returned zero records. Inspect diagnostics and source layout.")
    frame["State_class"] = frame.apply(classify_state, axis=1)
    frame["Ground_state_candidate"] = (
        (frame["State_index"] == 0) & (frame["State_suffix"] == "")
    )
    frame["Element_symbol_valid"] = frame["Symbol"].isin(ELEMENTS)
    frame.attrs["rejected"] = rejected
    return frame

def classify_state(row: pd.Series) -> str:
    idx = int(row["State_index"])
    suffix = str(row["State_suffix"])
    if idx == 0 and not suffix:
        return "ground_state_candidate"
    if idx in (1, 2) or suffix in ("m", "n"):
        return "isomer"
    if idx in (3, 4) or suffix in ("p", "q"):
        return "excited_level_or_special_state"
    if idx == 5 or suffix in ("r", "x"):
        return "resonance_or_special_state"
    if idx in (8, 9) or suffix in ("i", "j"):
        return "isobaric_analogue_state"
    return "other_or_unresolved_state"

def parse_ame(path: Path) -> pd.DataFrame:
    """
    Parse AME2020 using the documented Fortran fixed-width layout.
    # and * are retained as flags; starred/non-numeric quantities become NA.
    """
    rows = []
    rejected = []
    for line_no, line in enumerate(read_text(path), start=1):
        if len(line) < 135:
            continue
        try:
            # AME2020: columns 1-4 NZ, 5-9 N, 10-14 Z, 15-19 A.
            z_text = line[9:14].strip()
            a_text = line[14:19].strip()
            if not z_text.isdigit() or not a_text.isdigit():
                continue
            z, a = int(z_text), int(a_text)
            symbol = line[20:23].strip()
            mass_excess, mass_estimated, mass_noncalc = parse_number(line[28:42])
            binding_per_a, be_estimated, be_noncalc = parse_number(line[54:67])
            atomic_mass_integer = line[106:109].strip()
            atomic_mass_fraction = line[110:123].strip()
            atomic_mass, atomic_estimated, atomic_noncalc = parse_number(
                (atomic_mass_integer + atomic_mass_fraction) if atomic_mass_integer else atomic_mass_fraction
            )
            mass_unc, _, _ = parse_number(line[42:54])
            be_unc, _, _ = parse_number(line[67:78])
            atomic_unc, _, _ = parse_number(line[123:135])
            if not (0 <= z <= 118 and a >= z):
                rejected.append((line_no, line[:135], "invalid Z/A"))
                continue
            rows.append({
                "Z": z, "A": a, "N": a-z, "AME_symbol": symbol,
                "AME_mass_excess_keV": mass_excess,
                "AME_mass_excess_unc_keV": mass_unc,
                "AME_mass_excess_estimated": mass_estimated,
                "AME_mass_excess_noncalculable": mass_noncalc,
                "Binding_energy_per_A_keV": binding_per_a,
                "Binding_energy_per_A_unc_keV": be_unc,
                "Binding_energy_estimated": be_estimated,
                "Binding_energy_noncalculable": be_noncalc,
                "AME_atomic_mass_micro_u": atomic_mass,
                "AME_atomic_mass_unc_micro_u": atomic_unc,
                "AME_atomic_mass_estimated": atomic_estimated,
                "AME_atomic_mass_noncalculable": atomic_noncalc,
                "AME_source_line": line_no, "AME_raw_line": line
            })
        except Exception as exc:
            rejected.append((line_no, line[:135], str(exc)))
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError("AME parser returned zero records. Inspect diagnostics and source layout.")
    # Duplicate keys are not expected in AME mass table; keep all evidence and stop if found.
    duplicates = frame.duplicated(["Z", "A"], keep=False)
    if duplicates.any():
        sample = frame.loc[duplicates, ["Z", "A", "AME_source_line"]].head(10).to_dict("records")
        raise RuntimeError(f"Duplicate (Z,A) keys in AME parser; refusing silent merge: {sample}")
    frame["AME_atomic_mass_u"] = frame["AME_atomic_mass_micro_u"] / 1_000_000.0
    frame["AME_binding_energy_MeV"] = frame["Binding_energy_per_A_keV"] * frame["A"] / 1000.0
    frame["AME_mass_defect_u_from_binding"] = (
        frame["AME_binding_energy_MeV"] / 931.49410242
    )
    frame.attrs["rejected"] = rejected
    return frame

def build_analysis(nubase: pd.DataFrame, ame: pd.DataFrame) -> pd.DataFrame:
    merged = nubase.merge(ame, on=["Z", "A"], how="left", validate="many_to_one")
    merged["AME_match"] = merged["AME_mass_excess_keV"].notna()
    merged["U_2Z_plus_N"] = 2 * merged["Z"] + merged["N"]
    merged["D_Z_plus_2N"] = merged["Z"] + 2 * merged["N"]
    merged["C_raw_u"] = 0.012 * merged["A"]
    merged["C_cancel_u"] = 0.008 * merged[["U_2Z_plus_N", "D_Z_plus_2N"]].min(axis=1)
    merged["Residual_from_subtraction_u"] = merged["C_raw_u"] - merged["C_cancel_u"]
    merged["Residual_signed_u"] = 0.004 * (merged["N"] - merged["Z"])
    merged["Residual_absolute_u"] = 0.004 * (merged["N"] - merged["Z"]).abs()
    merged["Residual_identity_check"] = (
        (merged["Residual_from_subtraction_u"] - merged["Residual_absolute_u"]).abs() < 1e-10
    )
    merged["Model_residual_vs_binding_defect_u"] = (
        merged["Residual_absolute_u"] - merged["AME_mass_defect_u_from_binding"]
    )
    merged["Residual_to_binding_defect_percent"] = (
        100 * merged["Residual_absolute_u"] / merged["AME_mass_defect_u_from_binding"]
    )
    merged.loc[merged["AME_mass_defect_u_from_binding"].isna() |
               (merged["AME_mass_defect_u_from_binding"] == 0),
               "Residual_to_binding_defect_percent"] = pd.NA
    merged["AME_estimated_or_flagged"] = (
        merged["AME_mass_excess_estimated"].fillna(False) |
        merged["Binding_energy_estimated"].fillna(False) |
        merged["AME_atomic_mass_estimated"].fillna(False)
    )
    merged["NUBASE_and_AME_mass_excess_difference_keV"] = (
        merged["NUBASE_mass_excess_keV"] - merged["AME_mass_excess_keV"]
    )
    return merged

def save_diagnostics(nubase: pd.DataFrame, ame: pd.DataFrame) -> None:
    diag = OUT_DIR / "parser_diagnostics.txt"
    with diag.open("w", encoding="utf-8") as f:
        f.write("NUCLEAR ISOTOPE AUDIT — PARSER DIAGNOSTICS\n")
        f.write("Source format: NUBASE2020 and AME2020 published fixed-width ASCII.\n\n")
        for label, frame in (("NUBASE2020", nubase), ("AME2020", ame)):
            f.write(f"{label}: parsed records = {len(frame)}\n")
            rejected = frame.attrs.get("rejected", [])
            f.write(f"{label}: rejected candidate rows = {len(rejected)}\n")
            for item in rejected[:30]:
                f.write(f"REJECTED: {item}\n")
            f.write("\n")
        f.write("NUBASE raw sample:\n")
        for line in nubase["NUBASE_raw_line"].head(5):
            f.write(line + "\n")
        f.write("\nAME raw sample:\n")
        for line in ame["AME_raw_line"].head(5):
            f.write(line + "\n")
        f.write("\nParser note: an empty/NA value is not replaced by an estimate.\n")

def make_outputs(data: pd.DataFrame, nubase: pd.DataFrame, ame: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Preserve complete source records and all markers/flags.
    data.to_csv(OUT_DIR / "isotope_model_comparison.csv", index=False, na_rep="NA", encoding="utf-8-sig")
    nubase.drop(columns=["NUBASE_raw_line"], errors="ignore").to_csv(
        OUT_DIR / "nubase2020_parsed.csv", index=False, na_rep="NA", encoding="utf-8-sig")
    ame.drop(columns=["AME_raw_line"], errors="ignore").to_csv(
        OUT_DIR / "ame2020_parsed.csv", index=False, na_rep="NA", encoding="utf-8-sig")

    element_counts = (data[data["Z"].between(1,118)]
                      .groupby(["Z","Symbol"], dropna=False)
                      .agg(Isotope_and_state_records=("A","size"),
                           Unique_mass_numbers=("A","nunique"),
                           AME_matched_records=("AME_match","sum"))
                      .reset_index())
    expected = pd.DataFrame({"Z": range(1,119), "Symbol": ELEMENTS})
    element_counts = expected.merge(element_counts, on=["Z","Symbol"], how="left")
    element_counts.to_csv(OUT_DIR / "element_coverage_118.csv", index=False, na_rep="NA", encoding="utf-8-sig")

    ground = data[data["Ground_state_candidate"]].copy()
    ground.to_csv(OUT_DIR / "ground_state_candidates.csv", index=False, na_rep="NA", encoding="utf-8-sig")
    data[data["State_class"] != "ground_state_candidate"].to_csv(
        OUT_DIR / "non_ground_states_isomers_levels.csv", index=False, na_rep="NA", encoding="utf-8-sig")

    matched = data[data["AME_match"] & data["AME_mass_defect_u_from_binding"].notna()].copy()
    if not matched.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(matched["A"], matched["AME_mass_defect_u_from_binding"], s=9, alpha=0.45,
                   label="AME2020 binding-derived mass defect")
        ax.scatter(matched["A"], matched["Residual_absolute_u"], s=9, alpha=0.45,
                   label="Model residual (absolute)")
        ax.set_xlabel("Mass number A")
        ax.set_ylabel("Mass equivalent (u)")
        ax.set_title("Model residual vs AME2020 binding-derived mass defect")
        ax.grid(True, alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(OUT_DIR / "residual_vs_binding_defect.png", dpi=180)
        plt.close(fig)

        valid = matched[matched["Residual_to_binding_defect_percent"].notna()]
        if not valid.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.scatter(valid["A"], valid["Residual_to_binding_defect_percent"], s=10, alpha=0.5)
            ax.set_xlabel("Mass number A")
            ax.set_ylabel("Residual / binding-derived mass defect (%)")
            ax.set_title("Ratio is not assumed to be constant")
            ax.grid(True, alpha=0.25)
            fig.tight_layout()
            fig.savefig(OUT_DIR / "residual_to_binding_defect_ratio.png", dpi=180)
            plt.close(fig)

    # Four illustrative nuclei, when present in ground-state candidates.
    examples = [(26,56),(28,62),(82,208),(92,238)]
    selected = ground[ground.apply(lambda r: (int(r["Z"]),int(r["A"])) in examples, axis=1)]
    selected.to_csv(OUT_DIR / "illustrative_nuclei_Fe56_Ni62_Pb208_U238.csv",
                    index=False, na_rep="NA", encoding="utf-8-sig")

    matched_ground = ground[ground["AME_match"]]
    report_lines = [
        "# تقرير تدقيق النظائر النووية",
        "",
        "## نطاق البيانات",
        f"- سجلات NUBASE2020 المحللة: {len(nubase):,}",
        f"- سجلات AME2020 المحللة: {len(ame):,}",
        f"- سجلات NUBASE المطابقة مع AME2020 بالمفتاح (Z,A): {int(data['AME_match'].sum()):,}",
        f"- مرشحو الحالة الأرضية في NUBASE: {len(ground):,}",
        f"- مرشحو الحالة الأرضية المطابقون مع AME: {len(matched_ground):,}",
        f"- عدد العناصر ذات Z من 1 إلى 118 الموجودة في التغطية: {int(element_counts['Isotope_and_state_records'].notna().sum())}",
        "",
        "## تعريفات النموذج المختبرة",
        "- U = 2Z + N",
        "- D = Z + 2N",
        "- C_raw = 0.012 A",
        "- C_cancel = 0.008 min(U,D)",
        "- Residual_signed = 0.004 (N-Z)",
        "- Residual_absolute = 0.004 |N-Z|",
        "",
        "## فحوصات الاتساق",
        f"- عدد الصفوف التي تحقق Raw - Cancelled = 0.004|N-Z| ضمن السماحية: {int(data['Residual_identity_check'].sum()):,} / {len(data):,}",
        f"- عدد مخالفات الهوية الحسابية: {int((~data['Residual_identity_check']).sum()):,}",
        "- الهوية الجبرية تعني أن الطرح يعطي القيمة المطلقة، وليس المتبقي الموقّع عندما N < Z.",
        "",
        "## المقارنة مع AME2020",
        "- حُسب مكافئ نقص الكتلة من طاقة الربط المنشورة: (BE/A × A) / 931.49410242 MeV/u.",
        "- هذا اشتقاق من عمود طاقة الربط في AME2020، وليس عموداً مستقلاً مقاساً باسم mass defect.",
        f"- السجلات المتاحة للمقارنة العددية: {len(matched):,}",
        "",
        "## قيود وتفسير",
        "- NUBASE2020 يشمل حالات أرضية ومتزامرات ومستويات وحالات خاصة؛ لا تُعامل كل السجلات كنظائر أرضية.",
        "- State index ووسم الحالة محفوظان؛ تصنيف ground_state_candidate ترشيح آلي لا إثبات مستقل لترتيب الحالة.",
        "- علامات # و * محفوظة في أعلام مستقلة؛ القيم غير القابلة للحساب تبقى NA.",
        "- لا يُستبدل المفقود بتخمين ولا تُخلط بيانات المصدر بالقيم المشتقة.",
        "- النموذج الحسابي فرضية قيد الاختبار. لا يثبت هذا البرنامج وجود طاقة ربط جديدة أو كتلة كوارك أو آلية QCD.",
        "- لا تُفسّر النسب المئوية على أنها ثابت فيزيائي؛ افحص التوزيع الكامل ومصادر عدم اليقين.",
        "",
        "## الملفات الناتجة",
        "- isotope_model_comparison.csv: السجلات المدمجة وكل أعمدة النموذج والمقارنة.",
        "- nubase2020_parsed.csv و ame2020_parsed.csv: الجداول المصدرية بعد التحليل.",
        "- ground_state_candidates.csv و non_ground_states_isomers_levels.csv.",
        "- element_coverage_118.csv و parser_diagnostics.txt.",
        "- الرسوم البيانية PNG عند توافر سجلات مطابقة.",
        "",
        "## المصادر",
        "- NUBASE2020: F.G. Kondev et al., Chinese Physics C 45 (2021) 030001.",
        "- AME2020: W.J. Huang et al. / M. Wang et al., Chinese Physics C 45 (2021) 030002 and 030003.",
        f"- NUBASE source: {NUBASE_URL}",
        f"- AME source: {AME_URL}",
    ]
    (OUT_DIR / "report_ar.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    try:
        download(NUBASE_URL, RAW_DIR / "nubase_4.mas20.txt")
        download(AME_URL, RAW_DIR / "mass_1.mas20.txt")
        say("Parsing NUBASE2020...")
        nubase = parse_nubase(RAW_DIR / "nubase_4.mas20.txt")
        say(f"NUBASE2020 parsed records: {len(nubase):,}")
        say("Parsing AME2020...")
        ame = parse_ame(RAW_DIR / "mass_1.mas20.txt")
        say(f"AME2020 parsed records: {len(ame):,}")
        data = build_analysis(nubase, ame)
        save_diagnostics(nubase, ame)
        make_outputs(data, nubase, ame)
        bad = int((~data["Residual_identity_check"]).sum())
        say(f"Combined records: {len(data):,}")
        say(f"AME matched records: {int(data['AME_match'].sum()):,}")
        say(f"Ground-state candidates: {int(data['Ground_state_candidate'].sum()):,}")
        say(f"Algebraic identity failures: {bad}")
        if bad:
            say("WARNING: identity check failed for one or more rows; inspect CSV.")
        say(f"Outputs written to: {OUT_DIR}")
        say("PROCESS COMPLETED — inspect parser_diagnostics.txt and report_ar.md before interpreting.")
        return 0
    except Exception as exc:
        error = f"FATAL: {type(exc).__name__}: {exc}"
        say(error)
        (OUT_DIR / "fatal_error.txt").write_text(error + "\n", encoding="utf-8")
        return 1

if __name__ == "__main__":
    sys.exit(main())
