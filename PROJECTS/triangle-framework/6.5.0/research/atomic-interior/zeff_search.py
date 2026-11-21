#!/usr/bin/env python3
"""Phase 4: independent effective-nuclear-charge estimates vs 6.5.0 theta3.

Two distinct estimates are retained:
1) hydrogenic IE1 estimate: n*sqrt(IE1/13.605693 eV), an approximation;
2) Slater screening estimate from neutral ground-state configuration.

Neither is a direct measurement of Zeff. Framework inputs remain read-only.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

RYDBERG_EV = 13.605693122994
CORE_CONFIGS = {
    "He": "1s2",
    "Ne": "1s2 2s2 2p6",
    "Ar": "1s2 2s2 2p6 3s2 3p6",
    "Kr": "1s2 2s2 2p6 3s2 3p6 4s2 3d10 4p6",
    "Xe": "1s2 2s2 2p6 3s2 3p6 4s2 3d10 4p6 5s2 4d10 5p6",
    "Rn": "1s2 2s2 2p6 3s2 3p6 4s2 3d10 4p6 5s2 4d10 5p6 6s2 4f14 5d10 6p6",
}
ORBITAL_CAPACITY = {"s": 2, "p": 6, "d": 10, "f": 14, "g": 18}
ORBITAL_ORDER = {"s": 0, "p": 1, "d": 2, "f": 3, "g": 4}

def parse_configuration(text):
    """Expand common noble-gas cores and parse subshell occupancies."""
    raw = str(text).strip()
    if not raw or raw.lower() in {"nan", "none", "--"}:
        return {}
    for core, expanded in CORE_CONFIGS.items():
        raw = re.sub(r"\[" + core + r"\]", expanded, raw, flags=re.I)
    # NIST sometimes includes parenthesized configuration labels; keep orbital tokens only.
    matches = re.findall(r"(\d+)\s*([spdfg])\s*\^?\s*\{?\s*(\d+)\s*\}?", raw, flags=re.I)
    config = {}
    for n, orbital, occupancy in matches:
        key = (int(n), orbital.lower())
        config[key] = int(occupancy)
    return config

def select_ionized_subshell(config):
    """Select the highest-n occupied subshell as the first-ionized electron proxy."""
    if not config:
        return None
    return max(config, key=lambda key: (key[0], ORBITAL_ORDER[key[1]]))

def slater_zeff(config):
    """Return Slater-rule Zeff for an electron in the selected outer subshell."""
    target = select_ionized_subshell(config)
    if target is None:
        return np.nan, np.nan, "", np.nan
    n0, l0 = target
    occupancy = config[target]
    if occupancy < 1:
        return np.nan, np.nan, f"{n0}{l0}", np.nan

    shielding = 0.0
    for (n, orbital), count in config.items():
        if n == n0 and orbital == l0:
            # Same subshell: exclude the electron being considered.
            shielding += max(count - 1, 0) * (0.30 if n0 == 1 and l0 == "s" else 0.35)
        elif l0 in {"s", "p"}:
            if n == n0:
                # Same principal shell, other subshells to the left (e.g. nd).
                shielding += count * 1.0
            elif n == n0 - 1 and orbital in {"s", "p"}:
                shielding += count * 0.85
            elif n < n0 - 1 or (n == n0 - 1 and orbital in {"d", "f", "g"}):
                shielding += count * 1.0
        else:
            # For nd/nf target electrons, all lower groups shield fully.
            if n < n0 or (n == n0 and ORBITAL_ORDER[orbital] < ORBITAL_ORDER[l0]):
                shielding += count * 1.0
    z = sum(config.values())
    zeff = z - shielding
    return float(zeff), float(shielding), f"{n0}{l0}", float(n0)

def hydrogenic_zeff(ie1_ev, n):
    if pd.isna(ie1_ev) or pd.isna(n) or ie1_ev <= 0 or n <= 0:
        return np.nan
    return float(n * np.sqrt(float(ie1_ev) / RYDBERG_EV))

def _partial_corr_controls(frame, ycol, xcol, numeric_controls, categorical_controls):
    cols = [ycol, xcol] + numeric_controls + categorical_controls
    d = frame[cols].dropna().copy()
    if len(d) < 8:
        return np.nan, len(d)
    matrices = [np.ones(len(d))]
    for col in numeric_controls:
        matrices.append(pd.to_numeric(d[col], errors="coerce").to_numpy(dtype=float))
    for col in categorical_controls:
        dummy = pd.get_dummies(d[col], drop_first=True, dtype=float)
        matrices.extend(dummy[c].to_numpy() for c in dummy.columns)
    X = np.column_stack(matrices)
    x, y = d[xcol].to_numpy(dtype=float), d[ycol].to_numpy(dtype=float)
    rx = x - X @ np.linalg.lstsq(X, x, rcond=None)[0]
    ry = y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
    if np.std(rx) == 0 or np.std(ry) == 0:
        return np.nan, len(d)
    return float(np.corrcoef(rx, ry)[0, 1]), len(d)

def _model_matrix(train, test, include_angle):
    numeric = ["Z", "Period", "outermost_shell_electron_count"]
    blocks_train = pd.get_dummies(train["Block"], drop_first=True, dtype=float)
    blocks_test = pd.get_dummies(test["Block"], drop_first=True, dtype=float).reindex(
        columns=blocks_train.columns, fill_value=0
    )
    a = [np.ones(len(train))] + [train[c].to_numpy(dtype=float) for c in numeric]
    b = [np.ones(len(test))] + [test[c].to_numpy(dtype=float) for c in numeric]
    a += [blocks_train[c].to_numpy() for c in blocks_train]
    b += [blocks_test[c].to_numpy() for c in blocks_train]
    if include_angle:
        a.append(train["theta3"].to_numpy(dtype=float))
        b.append(test["theta3"].to_numpy(dtype=float))
    return np.column_stack(a), np.column_stack(b)

def analyze(joined):
    targets = ["Zeff_IE1_hydrogenic", "Zeff_Slater"]
    correlations, holdouts, block_rows = [], [], []
    for target in targets:
        d = joined[["Z", "theta3", "Period", "Block",
                    "outermost_shell_electron_count", target]].dropna().copy()
        if len(d) >= 8 and d[target].nunique() > 1:
            r, n = _partial_corr_controls(
                d, target, "theta3",
                ["Z", "Period", "outermost_shell_electron_count"], ["Block"]
            )
            correlations.append({
                "property": target, "N_elements": len(d),
                "Pearson_r": float(pearsonr(d["theta3"], d[target]).statistic),
                "Spearman_rho": float(spearmanr(d["theta3"], d[target]).statistic),
                "partial_r_after_Z_period_shell_block": r,
                "controlled_N": n,
            })
        for block, group in d.groupby("Block"):
            if len(group) >= 5 and group[target].nunique() > 1:
                block_rows.append({
                    "property": target, "Block": block, "N_elements": len(group),
                    "Pearson_r": float(pearsonr(group["theta3"], group[target]).statistic),
                    "partial_r_after_Z": _simple_partial(group["theta3"], group[target], group["Z"]),
                })
        for cutoff in (40, 50, 60, 70):
            train, test = d[d["Z"] <= cutoff], d[d["Z"] > cutoff]
            if len(train) < 20 or len(test) < 10:
                continue
            for name, include_angle in [
                ("Z_period_shell_block_baseline", False),
                ("baseline_plus_theta3", True),
            ]:
                X, Xt = _model_matrix(train, test, include_angle)
                coef = np.linalg.lstsq(X, train[target].to_numpy(), rcond=None)[0]
                pred = Xt @ coef
                actual = test[target].to_numpy()
                den = float(np.sum((actual - actual.mean()) ** 2))
                holdouts.append({
                    "property": target, "train_Z_max": cutoff,
                    "train_n": len(train), "test_n": len(test), "model": name,
                    "MAE": float(np.mean(np.abs(actual - pred))),
                    "RMSE": float(np.sqrt(np.mean((actual - pred) ** 2))),
                    "R2": float(1 - np.sum((actual - pred) ** 2) / den) if den else np.nan,
                })
    return pd.DataFrame(correlations), pd.DataFrame(block_rows), pd.DataFrame(holdouts)

def _simple_partial(x, y, z):
    d = pd.DataFrame({"x": x, "y": y, "z": z}).dropna()
    if len(d) < 5:
        return np.nan
    X = np.column_stack([np.ones(len(d)), d["z"].to_numpy(dtype=float)])
    rx = d["x"].to_numpy(dtype=float) - X @ np.linalg.lstsq(X, d["x"].to_numpy(dtype=float), rcond=None)[0]
    ry = d["y"].to_numpy(dtype=float) - X @ np.linalg.lstsq(X, d["y"].to_numpy(dtype=float), rcond=None)[0]
    if np.std(rx) == 0 or np.std(ry) == 0:
        return np.nan
    return float(np.corrcoef(rx, ry)[0, 1])

def run(framework_csv: Path, output_dir: Path):
    from search import calculate_closure_angles
    from levels_search import fetch_periodic_controls
    output_dir.mkdir(parents=True, exist_ok=True)
    framework = pd.read_csv(framework_csv)
    angles = calculate_closure_angles(framework)
    ion_path = output_dir / "NIST_ASD_ionization_all_stages.csv"
    if not ion_path.exists():
        raise FileNotFoundError("Run electronic_search.py first; NIST ionization CSV is missing.")
    ion = pd.read_csv(ion_path)
    neutral = ion[pd.to_numeric(ion["ion_charge"], errors="coerce") == 0].copy()
    neutral = neutral.sort_values(["Z"]).drop_duplicates("Z")
    periodic = fetch_periodic_controls()
    joined = angles.merge(neutral[["Z", "energy_eV", "provenance", "ground_shells",
                                   "occupied_principal_shell_count", "outermost_shell_electron_count"]],
                          on="Z", how="left")
    joined = joined.merge(periodic, on="Z", how="left")
    joined["Zeff_IE1_hydrogenic"] = [
        hydrogenic_zeff(e, n) for e, n in zip(
            joined["energy_eV"], joined["occupied_principal_shell_count"]
        )
    ]
    parsed = joined["ground_shells"].map(parse_configuration)
    slater = parsed.map(slater_zeff)
    joined["Zeff_Slater"] = slater.map(lambda x: x[0])
    joined["Slater_shielding_S"] = slater.map(lambda x: x[1])
    joined["Slater_target_subshell"] = slater.map(lambda x: x[2])
    joined["Slater_n"] = slater.map(lambda x: x[3])
    # Main inference uses evaluated NIST IE1 only; other provenance remains visible.
    joined["IE1_is_evaluated"] = joined["provenance"].eq("EVALUATED")
    joined["Zeff_IE1_hydrogenic_evaluated_only"] = joined["Zeff_IE1_hydrogenic"].where(
        joined["IE1_is_evaluated"]
    )
    correlations, block_rows, holdouts = analyze(joined)
    joined.to_csv(output_dir / "element_angle_effective_nuclear_charge.csv", index=False)
    correlations.to_csv(output_dir / "zeff_correlations.csv", index=False)
    block_rows.to_csv(output_dir / "zeff_block_correlations.csv", index=False)
    holdouts.to_csv(output_dir / "zeff_rolling_Z_holdout.csv", index=False)
    print(f"Elements with neutral NIST configurations: {joined['ground_shells'].notna().sum()}")
    print(f"Elements with Slater Zeff: {joined['Zeff_Slater'].notna().sum()}")
    print(f"IE1 provenance counts:\n{joined['provenance'].value_counts(dropna=False).to_string()}")
    print("\nZeff correlations (exploratory approximations):")
    print(correlations.to_string(index=False) if not correlations.empty else "No sufficient overlap.")
    print("\nWithin-block correlations:")
    print(block_rows.to_string(index=False) if not block_rows.empty else "No sufficient overlap.")
    print("\nOrdered-Z holdout with period/block/shell controls:")
    print(holdouts.to_string(index=False) if not holdouts.empty else "No sufficient coverage.")
    print("\nInterpretation: both Zeff values are model-derived approximations, not direct measurements.")
    print("Hydrogenic estimate uses neutral IE1 and the outermost principal shell; Slater uses the selected outer subshell.")
    print("Primary interpretation must use evaluated IE1; semiempirical/theoretical values remain flagged.")
    print(f"Results: {output_dir.resolve()}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", default="PROJECTS/triangle-framework/6.5.0/elements_input_118.csv")
    parser.add_argument("--out", default="atomic-interior-results")
    args = parser.parse_args()
    run(Path(args.framework), Path(args.out))

if __name__ == "__main__":
    main()
