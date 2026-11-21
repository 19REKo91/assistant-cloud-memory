#!/usr/bin/env python3
"""Phase 1b: isotope-aware nuclear analysis using NUBASE2020 stable abundances.

The primary element-level statistic is an abundance-weighted average over
stable natural isotopes. The most abundant stable isotope is reported
separately. Elements without a stable isotope or abundance data remain NA.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.stats import pearsonr, spearmanr

NUBASE_URL = "https://www-nds.iaea.org/amdc/ame2020/nubase_4.mas20.txt"
PROPERTIES = [
    "Sn_keV", "Sp_keV", "S2n_keV", "S2p_keV",
    "N_over_Z", "neutron_excess_fraction", "binding_energy_per_A_keV",
    "nearest_magic_N_distance", "nearest_magic_Z_distance",
]

def parse_nubase2020(text: str) -> pd.DataFrame:
    """Read fixed-width NUBASE2020 ground-state rows and natural abundances."""
    rows = []
    for line in text.splitlines():
        if len(line) < 119 or line.startswith("#"):
            continue
        try:
            A = int(line[0:3].strip())
            z_and_state = line[4:8].strip()
            Z = int(z_and_state[:3])
            state = int(z_and_state[3])
        except (ValueError, IndexError):
            continue
        # Only ground states (isomer index 0); omit isomers and IAS.
        if state != 0:
            continue
        half_life = line[69:78].strip().lower()
        # Stable-only selection is intentional; do not treat long-lived radioactive nuclides as stable.
        if half_life != "stbl":
            continue
        abundance_text = line[119:209] if len(line) >= 120 else ""
        match = re.search(r"IS\s*=\s*([0-9]+(?:\.[0-9]+)?)", abundance_text)
        abundance = float(match.group(1)) if match else np.nan
        rows.append({
            "Z": Z, "A": A, "N": A - Z,
            "nubase_half_life_label": half_life,
            "isotopic_abundance_pct": abundance,
            "abundance_reported": bool(match),
        })
    result = pd.DataFrame(rows)
    if result.empty:
        raise ValueError("No NUBASE2020 stable ground-state rows parsed; fixed-width layout may have changed.")
    return result.drop_duplicates(["Z", "A"], keep="first")

def download_nubase2020():
    response = requests.get(NUBASE_URL, timeout=90,
                            headers={"User-Agent": "AtomicInteriorResearch/1.0"})
    response.raise_for_status()
    if "Nubase2020 citation" not in response.text[:2000]:
        raise ValueError("Downloaded content does not match the official NUBASE2020 table.")
    return parse_nubase2020(response.text)

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

def build_stable_isotope_summary(nubase, ame_nuclides):
    """Return abundance-weighted stable-isotope means and dominant stable isotope."""
    stable = nubase.merge(ame_nuclides, on=["Z", "A", "N"], how="left",
                          suffixes=("_NUBASE", "_AME"))
    rows = []
    for z, group in stable.groupby("Z"):
        known = group.dropna(subset=["isotopic_abundance_pct"])
        if known.empty:
            continue
        weights = known["isotopic_abundance_pct"].astype(float)
        if weights.sum() <= 0:
            continue
        dominant = known.sort_values("isotopic_abundance_pct", ascending=False).iloc[0]
        row = {
            "Z": int(z),
            "stable_isotope_count": int(len(group)),
            "stable_isotopes_with_abundance": int(len(known)),
            "abundance_sum_pct": float(weights.sum()),
            "dominant_stable_A": int(dominant["A"]),
            "dominant_stable_N": int(dominant["N"]),
            "dominant_abundance_pct": float(dominant["isotopic_abundance_pct"]),
        }
        for prop in PROPERTIES:
            valid = known[prop].notna()
            if valid.any():
                w = known.loc[valid, "isotopic_abundance_pct"].astype(float)
                row[prop + "_abundance_weighted"] = float(
                    np.average(known.loc[valid, prop].astype(float), weights=w)
                )
                row[prop + "_dominant"] = (
                    float(dominant[prop]) if pd.notna(dominant[prop]) else np.nan
                )
            else:
                row[prop + "_abundance_weighted"] = np.nan
                row[prop + "_dominant"] = np.nan
        rows.append(row)
    return stable, pd.DataFrame(rows)

def make_report(joined, suffix="_abundance_weighted"):
    measured = joined[joined["Data_Quality"].str.upper() == "MEASURED"].copy()
    rows = []
    for prop in PROPERTIES:
        col = prop + suffix
        if col not in measured:
            continue
        d = measured[["Z", "theta3", col]].dropna()
        if len(d) < 5 or d[col].nunique() < 2:
            continue
        rows.append({
            "property": col, "N_elements": len(d),
            "Pearson_r": float(pearsonr(d["theta3"], d[col]).statistic),
            "Spearman_rho": float(spearmanr(d["theta3"], d[col]).statistic),
            "partial_r_after_Z": _partial_corr(d["theta3"], d[col], d["Z"]),
        })
    return pd.DataFrame(rows)

def holdout_report(joined, suffix="_abundance_weighted"):
    """Compare angle-only, Z-only, and Z+angle predictions on unseen high-Z elements."""
    measured = joined[joined["Data_Quality"].str.upper() == "MEASURED"].copy()
    rows = []
    for prop in PROPERTIES:
        col = prop + suffix
        if col not in measured:
            continue
        data = measured[["Z", "theta3", col]].dropna()
        train, test = data[data["Z"] <= 60], data[data["Z"] > 60]
        if len(train) < 8 or len(test) < 5:
            rows.append({"property": col, "train_n": len(train), "test_n": len(test),
                         "model": "INSUFFICIENT_COVERAGE", "MAE": np.nan,
                         "RMSE": np.nan, "R2": np.nan})
            continue
        y_train = train[col].to_numpy()
        y_test = test[col].to_numpy()
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
            denominator = float(np.sum((y_test - y_test.mean()) ** 2))
            r2 = float(1 - np.sum((y_test - prediction) ** 2) / denominator) if denominator else np.nan
            rows.append({"property": col, "train_n": len(train), "test_n": len(test),
                         "model": model_name, "MAE": mae, "RMSE": rmse, "R2": r2})
    return pd.DataFrame(rows)

def run(framework_csv: Path, ame_csv: Path, output_dir: Path):
    from search import calculate_closure_angles
    output_dir.mkdir(parents=True, exist_ok=True)
    framework = pd.read_csv(framework_csv)
    angles = calculate_closure_angles(framework)
    ame = pd.read_csv(ame_csv)
    nubase = download_nubase2020()
    stable_rows, summary = build_stable_isotope_summary(nubase, ame)
    joined = angles.merge(summary, on="Z", how="left")
    corr_weighted = make_report(joined, "_abundance_weighted")
    corr_dominant = make_report(joined, "_dominant")
    holdout_weighted = holdout_report(joined, "_abundance_weighted")
    holdout_dominant = holdout_report(joined, "_dominant")

    stable_rows.to_csv(output_dir / "NUBASE2020_stable_ground_states.csv", index=False)
    summary.to_csv(output_dir / "stable_isotope_element_summary.csv", index=False)
    joined.to_csv(output_dir / "element_angle_stable_isotope_summary.csv", index=False)
    corr_weighted.to_csv(output_dir / "stable_isotope_weighted_correlations.csv", index=False)
    corr_dominant.to_csv(output_dir / "dominant_stable_isotope_correlations.csv", index=False)
    holdout_weighted.to_csv(output_dir / "stable_isotope_weighted_holdout.csv", index=False)
    holdout_dominant.to_csv(output_dir / "dominant_stable_isotope_holdout.csv", index=False)

    print(f"NUBASE2020 stable ground-state nuclides parsed: {len(nubase)}")
    print(f"Elements with stable nuclides and reported abundance: {len(summary)}")
    print("\nAbundance-weighted stable-isotope correlations:")
    print(corr_weighted.to_string(index=False) if not corr_weighted.empty else "No sufficient overlap.")
    print("\nDominant stable-isotope correlations:")
    print(corr_dominant.to_string(index=False) if not corr_dominant.empty else "No sufficient overlap.")
    print("\nElements without stable nuclides or abundance are left missing; no isotope is guessed.")
    print(f"Results: {output_dir.resolve()}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", default="PROJECTS/triangle-framework/6.5.0/elements_input_118.csv")
    parser.add_argument("--ame-nuclides", default="atomic-interior-results/AME2020_nuclide_separation_energies.csv")
    parser.add_argument("--out", default="atomic-interior-results")
    args = parser.parse_args()
    run(Path(args.framework), Path(args.ame_nuclides), Path(args.out))

if __name__ == "__main__":
    main()
