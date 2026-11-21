#!/usr/bin/env python3
"""Phase 2: compare 6.5.0 closure angle with NIST ASD electronic properties.

Uses NIST Atomic Spectra Database (ASD) GSIE CGI output. The approved
framework CSV and constitution are read-only. Unmarked values are treated
as evaluated experimental values; [bracketed] semi-empirical/interpolated
and (parenthesized) theoretical values are kept separately.
"""
from __future__ import annotations

import argparse
import re
import time
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.stats import pearsonr, spearmanr

NIST_IE_URL = "https://physics.nist.gov/cgi-bin/ASD/ie.pl"
NIST_VERSION = "ASD 5.12"
SUPERSCRIPT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")

def parse_energy_token(value):
    """Return numeric eV and provenance class from NIST notation."""
    raw = str(value).strip().replace(",", "").replace("−", "-")
    if not raw or raw.lower() in {"nan", "none", "--", "unknown"}:
        return np.nan, "MISSING"
    kind = "MEASURED"
    if raw.startswith("[") and raw.endswith("]"):
        kind, raw = "SEMIEMPIRICAL", raw[1:-1].strip()
    elif raw.startswith("(") and raw.endswith(")"):
        kind, raw = "THEORETICAL", raw[1:-1].strip()
    raw = raw.replace(" ", "")
    try:
        return float(raw), kind
    except ValueError:
        return np.nan, "UNPARSED"

def parse_shells(shells):
    """Extract occupied principal shells and occupancy in the outermost n."""
    s = str(shells).translate(SUPERSCRIPT)
    core_shells = {"He": 1, "Ne": 2, "Ar": 3, "Kr": 4, "Xe": 5, "Rn": 6, "Og": 7}
    core_match = re.search(r"\[(He|Ne|Ar|Kr|Xe|Rn|Og)\]", s, flags=re.I)
    core_count = core_shells.get(core_match.group(1).title(), 0) if core_match else 0
    tokens = re.findall(r"(\d+)\s*([spdfgh])\s*\^?\s*(\d*)", s, flags=re.I)
    if not tokens and not core_match:
        return np.nan, np.nan
    ns = [int(t[0]) for t in tokens]
    outer_n = max(ns) if ns else core_count
    outer_count = sum(int(t[2]) if t[2] else 1 for t in tokens if int(t[0]) == outer_n)
    if not tokens and core_match:
        outer_count = 2 if core_match.group(1).title() == "He" else 8
    return max(core_count, outer_n), outer_count

def _norm_header(value):
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())

def parse_nist_tsv(text, energy_kind="ionization"):
    """Parse NIST ASD tab-delimited or formatted HTML output."""
    frame = None
    if "<table" in text.lower():
        try:
            tables = pd.read_html(StringIO(text))
        except ValueError as exc:
            raise ValueError(f"NIST HTML contained no readable data table: {exc}") from exc
        for candidate in tables:
            if isinstance(candidate.columns, pd.MultiIndex):
                candidate.columns = [
                    " ".join(str(part) for part in col if str(part) != "nan").strip()
                    for col in candidate.columns
                ]
            else:
                candidate.columns = [str(col).strip() for col in candidate.columns]
            normalized = [_norm_header(col) for col in candidate.columns]
            has_z = any(h in {"atnum", "atomicnumber"} or h.startswith("atnum") for h in normalized)
            energy_prefix = "totalbindingenergy" if energy_kind == "binding" else "ionizationenergy"
            has_energy = any(h.startswith(energy_prefix) for h in normalized)
            if has_z and has_energy:
                frame = candidate.copy()
                break
        if frame is None:
            raise ValueError("Could not locate NIST HTML table with atomic number and requested energy column.")
    else:
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            raise ValueError("NIST returned an empty response.")
        header_idx = None
        for i, line in enumerate(lines):
            cells = [c.strip().strip('"') for c in line.split("\t")]
            normalized = [_norm_header(c) for c in cells]
            if any(h in {"atnum", "atomicnumber"} or h.startswith("atnum") for h in normalized):
                header_idx = i
                break
        if header_idx is None:
            raise ValueError("Could not locate NIST tabular header (At. Num.).")
        header = [c.strip().strip('"') for c in lines[header_idx].split("\t")]
        records = []
        for line in lines[header_idx + 1:]:
            if not line.strip() or set(line.strip()) <= {"-", "|"}:
                continue
            cells = [c.strip().strip('"') for c in line.split("\t")]
            if len(cells) < len(header):
                cells += [""] * (len(header) - len(cells))
            records.append(dict(zip(header, cells)))
        frame = pd.DataFrame(records)

    lookup = {_norm_header(col): col for col in frame.columns}

    def col(*names):
        for name in names:
            target = _norm_header(name)
            if target in lookup:
                return lookup[target]
            for normalized, original in lookup.items():
                if normalized.startswith(target):
                    return original
        return None

    zc = col("At. Num.", "Atomic Number", "At Num")
    elc = col("El. name", "Element name", "Element")
    qcc = col("Ion Charge", "Charge")
    shellc = col("Ground Shells", "Ground-state electronic shells", "Shells")
    energy_label = "Total Binding Energy" if energy_kind == "binding" else "Ionization Energy"
    ec = col(energy_label, "Energy")
    if zc is None or ec is None:
        raise ValueError(f"NIST output lacks required columns. Found: {list(frame.columns)}")
    out = pd.DataFrame()
    out["Z"] = pd.to_numeric(frame[zc].astype(str).str.extract(r"(\d+)")[0], errors="coerce")
    out["element_name"] = frame[elc].astype(str).str.strip() if elc else ""
    out["ion_charge"] = pd.to_numeric(frame[qcc], errors="coerce") if qcc else 0
    out["ground_shells"] = frame[shellc].fillna("").astype(str) if shellc else ""
    parsed = frame[ec].map(parse_energy_token)
    out["energy_eV"] = parsed.map(lambda item: item[0])
    out["provenance"] = parsed.map(lambda item: item[1])
    shell_values = out["ground_shells"].map(parse_shells)
    out["occupied_principal_shell_count"] = shell_values.map(lambda item: item[0])
    out["outermost_shell_electron_count"] = shell_values.map(lambda item: item[1])
    out = out.dropna(subset=["Z"]).copy()
    out["Z"] = out["Z"].astype(int)
    out["ion_charge"] = pd.to_numeric(out["ion_charge"], errors="coerce")
    return out
def fetch_nist(energy_kind="ionization"):
    params = {
        "spectra": "H-Og I-III" if energy_kind == "ionization" else "H-Og I",
        "units": "1",              # eV
        "format": "0",             # formatted HTML table
        "output": "0",             # all results
        "at_num_out": "on",
        "el_name_out": "on",
        "ion_charge_out": "on",
        "seq_out": "on",
        "shells_out": "on",
        "unc_out": "on",
        "biblio": "off",
        "e_out": "1" if energy_kind == "binding" else "0",
        "submit": "Retrieve Data",
    }
    response = requests.get(
        NIST_IE_URL, params=params, timeout=120,
        headers={"User-Agent": "AtomicInteriorResearch/1.0 (academic exploratory analysis)"}
    )
    response.raise_for_status()
    if len(response.text) < 1000:
        raise ValueError(f"NIST response unexpectedly short ({len(response.text)} chars): {response.text[:500]}")
    return parse_nist_tsv(response.text, energy_kind=energy_kind)

def electronic_element_summary(ionization, binding):
    rows = []
    for z, group in ionization.groupby("Z"):
        row = {"Z": int(z)}
        neutral = group[group["ion_charge"] == 0].sort_values("ion_charge")
        for q in range(3):
            stage = group[group["ion_charge"] == q]
            measured = stage[stage["provenance"] == "MEASURED"]["energy_eV"].dropna()
            semi = stage[stage["provenance"].isin(["MEASURED", "SEMIEMPIRICAL"])]["energy_eV"].dropna()
            theoretical = stage[stage["provenance"] == "THEORETICAL"]["energy_eV"].dropna()
            row[f"IE{q+1}_measured_eV"] = measured.iloc[0] if len(measured) else np.nan
            row[f"IE{q+1}_incl_semie_eV"] = semi.iloc[0] if len(semi) else np.nan
            row[f"IE{q+1}_theoretical_eV"] = theoretical.iloc[0] if len(theoretical) else np.nan
        strict = [row.get(f"IE{i}_measured_eV", np.nan) for i in (1, 2, 3)]
        row["IE1_to_IE3_sum_measured_eV"] = sum(strict) if all(pd.notna(v) for v in strict) else np.nan
        if len(neutral):
            row["occupied_principal_shell_count"] = neutral.iloc[0]["occupied_principal_shell_count"]
            row["outermost_shell_electron_count"] = neutral.iloc[0]["outermost_shell_electron_count"]
            row["ground_shells"] = neutral.iloc[0]["ground_shells"]
        else:
            row["occupied_principal_shell_count"] = np.nan
            row["outermost_shell_electron_count"] = np.nan
            row["ground_shells"] = ""
        b = binding[(binding["Z"] == z) & (binding["ion_charge"] == 0)]
        b = b[b["provenance"] == "MEASURED"]["energy_eV"].dropna()
        row["total_binding_neutral_measured_eV"] = b.iloc[0] if len(b) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)

def _partial_corr(x, y, z):
    d = pd.DataFrame({"x": x, "y": y, "z": z}).dropna()
    if len(d) < 5 or d["z"].nunique() < 2:
        return np.nan
    X = np.column_stack([np.ones(len(d)), d["z"].to_numpy()])
    rx = d["x"].to_numpy() - X @ np.linalg.lstsq(X, d["x"].to_numpy(), rcond=None)[0]
    ry = d["y"].to_numpy() - X @ np.linalg.lstsq(X, d["y"].to_numpy(), rcond=None)[0]
    if np.std(rx) == 0 or np.std(ry) == 0:
        return np.nan
    return float(np.corrcoef(rx, ry)[0, 1])

PROPERTIES = [
    "IE1_measured_eV", "IE2_measured_eV", "IE3_measured_eV",
    "IE1_to_IE3_sum_measured_eV", "total_binding_neutral_measured_eV",
    "occupied_principal_shell_count", "outermost_shell_electron_count",
]

def make_reports(joined):
    measured = joined[joined["Data_Quality"].str.upper() == "MEASURED"].copy()
    corr_rows, holdout_rows = [], []
    for prop in PROPERTIES:
        d = measured[["Z", "theta3", prop]].dropna()
        if len(d) >= 5 and d[prop].nunique() > 1:
            corr_rows.append({
                "property": prop, "N_elements": len(d),
                "Pearson_r": float(pearsonr(d["theta3"], d[prop]).statistic),
                "Spearman_rho": float(spearmanr(d["theta3"], d[prop]).statistic),
                "partial_r_after_Z": _partial_corr(d["theta3"], d[prop], d["Z"]),
            })
        train, test = d[d["Z"] <= 60], d[d["Z"] > 60]
        if len(train) < 8 or len(test) < 5:
            holdout_rows.append({"property": prop, "train_n": len(train), "test_n": len(test),
                                 "model": "INSUFFICIENT_COVERAGE", "MAE": np.nan,
                                 "RMSE": np.nan, "R2": np.nan})
            continue
        y_train, y_test = train[prop].to_numpy(), test[prop].to_numpy()
        for model_name, predictors in [
            ("Z_only", ["Z"]),
            ("theta3_only", ["theta3"]),
            ("Z_plus_theta3", ["Z", "theta3"]),
        ]:
            x_train = np.column_stack([np.ones(len(train))] + [train[k].to_numpy() for k in predictors])
            x_test = np.column_stack([np.ones(len(test))] + [test[k].to_numpy() for k in predictors])
            coefficients = np.linalg.lstsq(x_train, y_train, rcond=None)[0]
            prediction = x_test @ coefficients
            mae = float(np.mean(np.abs(y_test - prediction)))
            rmse = float(np.sqrt(np.mean((y_test - prediction) ** 2)))
            denom = float(np.sum((y_test - y_test.mean()) ** 2))
            r2 = float(1 - np.sum((y_test - prediction) ** 2) / denom) if denom else np.nan
            holdout_rows.append({"property": prop, "train_n": len(train), "test_n": len(test),
                                 "model": model_name, "MAE": mae, "RMSE": rmse, "R2": r2})
    return pd.DataFrame(corr_rows), pd.DataFrame(holdout_rows)

def run(framework_csv: Path, output_dir: Path):
    from search import calculate_closure_angles
    output_dir.mkdir(parents=True, exist_ok=True)
    framework = pd.read_csv(framework_csv)
    angles = calculate_closure_angles(framework)
    print("Downloading NIST ASD 5.12 sequential ionization energies...")
    ionization = fetch_nist("ionization")
    time.sleep(1.0)
    print("Downloading NIST ASD 5.12 neutral total binding energies...")
    binding = fetch_nist("binding")
    summary = electronic_element_summary(ionization, binding)
    joined = angles.merge(summary, on="Z", how="left")
    correlations, holdout = make_reports(joined)

    ionization.to_csv(output_dir / "NIST_ASD_ionization_all_stages.csv", index=False)
    binding.to_csv(output_dir / "NIST_ASD_total_binding_all_stages.csv", index=False)
    joined.to_csv(output_dir / "element_angle_electronic_summary.csv", index=False)
    correlations.to_csv(output_dir / "electronic_correlations.csv", index=False)
    holdout.to_csv(output_dir / "electronic_ordered_Z_holdout.csv", index=False)

    print(f"NIST ionization records parsed: {len(ionization)}")
    print(f"NIST total-binding records parsed: {len(binding)}")
    print("\nElectronic correlations (MEASURED framework elements):")
    print(correlations.to_string(index=False) if not correlations.empty else "No sufficient overlap.")
    print("\nOrdered-Z holdout: train Z<=60; test Z>60")
    print(holdout.to_string(index=False) if not holdout.empty else "No sufficient overlap.")
    print("\nProvenance: unmarked=MEASURED; [x]=SEMIEMPIRICAL; (x)=THEORETICAL.")
    print("Total binding energy is the energy required to remove all electrons; NIST sums sequential ionization energies.")
    print(f"Results: {output_dir.resolve()}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", default="PROJECTS/triangle-framework/6.5.0/elements_input_118.csv")
    parser.add_argument("--out", default="atomic-interior-results")
    args = parser.parse_args()
    run(Path(args.framework), Path(args.out))

if __name__ == "__main__":
    main()
