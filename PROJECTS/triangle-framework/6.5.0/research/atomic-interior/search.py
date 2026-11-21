#!/usr/bin/env python3
"""Research-only tests of 6.5.0 closure angle against AME2020 nuclear structure.

The approved framework CSV and constitution are read-only. This script writes
all derived material to the workflow's temporary output directory.
"""
from __future__ import annotations

import argparse
import io
import math
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.stats import pearsonr, spearmanr

AME_URL = "https://www-nds.iaea.org/amdc/ame2020/mass_1.mas20.txt"
U_KEV = 931_494.10242
ME_NEUTRON_KEV = 8_071.31806
ME_HYDROGEN_KEV = 7_288.971064
MAGIC_NUMBERS = (2, 8, 20, 28, 50, 82, 126)

RHO_MIN, RHO_MAX = 0.534, 22.59
VM_MIN, VM_MAX = 7.0923, 18.27
R_MIN, R_MAX = 28.0, 203.0
MP_MIN, MP_MAX = -272.2, 3422.0

def _column(frame: pd.DataFrame, names: tuple[str, ...], required: bool = True):
    lookup = {str(c).strip().lower(): c for c in frame.columns}
    for name in names:
        if name.lower() in lookup:
            return lookup[name.lower()]
    if required:
        raise ValueError(f"Required input column missing. Tried {names}; found {list(frame.columns)}")
    return None

def _num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False)
              .str.replace("−", "-", regex=False),
        errors="coerce",
    )

def calculate_closure_angles(source: pd.DataFrame) -> pd.DataFrame:
    """Recalculate the approved 6.5.0 five-input closure, without changing source."""
    zc = _column(source, ("Z", "atomic_number"))
    sc = _column(source, ("Sym", "symbol", "Element"), required=False)
    mc = _column(source, ("M", "mass", "atomic_mass"))
    rc = _column(source, ("rho", "density", "solid_density"))
    radiusc = _column(source, ("R", "radius", "atomic_radius"))
    mpc = _column(source, ("mp_C", "mp", "melting_point", "melting"))
    qualityc = _column(source, ("Data_Quality", "data_quality"), required=False)

    out = pd.DataFrame(index=source.index)
    out["Z"] = _num(source[zc])
    out["symbol"] = source[sc].astype(str).str.strip() if sc else ""
    out["M"] = _num(source[mc])
    out["rho"] = _num(source[rc])
    out["R_pm"] = _num(source[radiusc])
    out["mp_C"] = _num(source[mpc])
    out["Data_Quality"] = source[qualityc].astype(str).str.strip() if qualityc else "UNSPECIFIED"

    out["Vm"] = out["M"] / out["rho"]
    out["rho_n"] = (out["rho"] - RHO_MIN) / (RHO_MAX - RHO_MIN)
    out["V_n"] = (out["Vm"] - VM_MIN) / (VM_MAX - VM_MIN)
    out["R_n"] = (out["R_pm"] - R_MIN) / (R_MAX - R_MIN)
    out["mp_n"] = (out["mp_C"] - MP_MIN) / (MP_MAX - MP_MIN)

    out["theta1"] = 80.0 - 70.0 * out["rho_n"]
    out["theta2_raw"] = 10.0 + 70.0 * out["V_n"]
    out["theta2_end"] = np.mod(out["theta2_raw"], 360.0)
    out.loc[np.isclose(out["theta2_end"], 0.0), "theta2_end"] = 360.0
    out["n_turns"] = np.floor(out["theta2_raw"] / 360.0)
    out["theta4"] = 80.0 - 70.0 * out["R_n"]
    out["theta5"] = 80.0 - 70.0 * out["mp_n"]
    out["theta3"] = 300.0 - (
        out["theta1"] + out["theta2_end"] + out["theta4"] + out["theta5"]
    )
    out = out.dropna(subset=["Z", "theta3"]).copy()
    out["Z"] = out["Z"].astype(int)
    return out.sort_values("Z").drop_duplicates("Z", keep="first").reset_index(drop=True)

def parse_ame2020_mass_text(text: str) -> pd.DataFrame:
    """Parse AME2020 mass_1.mas20 fixed-width records; preserve estimated flags."""
    rows = []
    for line in text.splitlines():
        # AME uses blank, 0, or 1 in the carriage-control column.
        if len(line) < 42 or line[0] not in (" ", "0", "1"):
            continue
        try:
            neutron_excess = int(line[1:4].strip())
            N = int(line[4:9].strip())
            Z = int(line[9:14].strip())
            A = int(line[14:19].strip())
        except ValueError:
            continue
        symbol = line[20:23].strip()
        mass_field = line[28:42].strip()
        estimated = "#" in mass_field
        if not mass_field or "*" in mass_field:
            mass_excess = np.nan
        else:
            try:
                mass_excess = float(mass_field.replace("#", ""))
            except ValueError:
                mass_excess = np.nan
        rows.append({
            "N_minus_Z": neutron_excess, "N": N, "Z": Z, "A": A,
            "symbol": symbol, "mass_excess_keV": mass_excess,
            "estimated": estimated,
        })
    result = pd.DataFrame(rows)
    if result.empty:
        raise ValueError("AME2020 parser found no nuclide records; fixed-width layout may have changed.")
    result = result.drop_duplicates(["Z", "N"], keep="last")
    return result

def download_ame2020() -> pd.DataFrame:
    response = requests.get(AME_URL, timeout=90)
    response.raise_for_status()
    if len(response.text) < 100_000 or "mass excess" not in response.text[:10_000].lower() or "<html" in response.text[:500].lower():
        raise ValueError("Downloaded content does not look like the official AME2020 mass table.")
    return parse_ame2020_mass_text(response.text)

def derive_separation_energies(nuclides: pd.DataFrame) -> pd.DataFrame:
    """Derive Sn, Sp, S2n and S2p from measured AME mass excesses only."""
    required = {"Z", "N", "A", "symbol", "mass_excess_keV"}
    missing = required - set(nuclides.columns)
    if missing:
        raise ValueError(f"Nuclide frame missing columns: {sorted(missing)}")
    data = nuclides.copy()
    if "estimated" not in data:
        data["estimated"] = False
    data["estimated"] = data["estimated"].fillna(False).astype(bool)
    measured = data.loc[
        (~data["estimated"]) & data["mass_excess_keV"].notna()
    ].copy()
    mass = {
        (int(row.Z), int(row.N)): float(row.mass_excess_keV)
        for row in measured.itertuples()
    }
    rows = []
    for row in data.itertuples():
        z, n = int(row.Z), int(row.N)
        me = float(row.mass_excess_keV) if pd.notna(row.mass_excess_keV) else np.nan
        usable = not bool(row.estimated) and math.isfinite(me)
        def delta(dz: int, dn: int, count: int, particle_me: float):
            if not usable:
                return np.nan
            neighbour = mass.get((z + dz, n + dn))
            if neighbour is None:
                return np.nan
            return neighbour + count * particle_me - me
        rows.append({
            "Z": z, "N": n, "A": int(row.A), "symbol": row.symbol,
            "mass_excess_keV": me, "estimated": bool(row.estimated),
            "Sn_keV": delta(0, -1, 1, ME_NEUTRON_KEV),
            "Sp_keV": delta(-1, 0, 1, ME_HYDROGEN_KEV),
            "S2n_keV": delta(0, -2, 2, ME_NEUTRON_KEV),
            "S2p_keV": delta(-2, 0, 2, ME_HYDROGEN_KEV),
            "N_over_Z": n / z if z else np.nan,
            "neutron_excess_fraction": (n - z) / (n + z) if (n + z) else np.nan,
            "binding_energy_per_A_keV": (
                (z * ME_HYDROGEN_KEV + n * ME_NEUTRON_KEV - me) / (n + z)
                if usable and (n + z) else np.nan
            ),
            "nearest_magic_N_distance": min(abs(n - m) for m in MAGIC_NUMBERS),
            "nearest_magic_Z_distance": min(abs(z - m) for m in MAGIC_NUMBERS),
        })
    return pd.DataFrame(rows)

NUCLEAR_PROPERTIES = [
    "Sn_keV", "Sp_keV", "S2n_keV", "S2p_keV", "N_over_Z",
    "neutron_excess_fraction", "binding_energy_per_A_keV",
    "nearest_magic_N_distance", "nearest_magic_Z_distance",
]

def summarize_by_element(nuclides: pd.DataFrame) -> pd.DataFrame:
    """Median over available AME nuclides per element; counts remain explicit."""
    rows = []
    for z, group in nuclides.groupby("Z"):
        row = {"Z": int(z), "symbol": group["symbol"].dropna().iloc[0]}
        for prop in NUCLEAR_PROPERTIES:
            values = group[prop].dropna()
            row[prop + "_median"] = values.median() if len(values) else np.nan
            row[prop + "_nuclide_count"] = int(len(values))
        row["AME_nuclide_count"] = int(len(group))
        row["measured_mass_count"] = int((~group["estimated"] & group["mass_excess_keV"].notna()).sum())
        rows.append(row)
    return pd.DataFrame(rows)

def _partial_corr(x: pd.Series, y: pd.Series, z: pd.Series) -> float:
    frame = pd.DataFrame({"x": x, "y": y, "z": z}).dropna()
    if len(frame) < 5 or frame["z"].nunique() < 2:
        return np.nan
    zmat = np.column_stack([np.ones(len(frame)), frame["z"].to_numpy()])
    rx = frame["x"].to_numpy() - zmat @ np.linalg.lstsq(zmat, frame["x"].to_numpy(), rcond=None)[0]
    ry = frame["y"].to_numpy() - zmat @ np.linalg.lstsq(zmat, frame["y"].to_numpy(), rcond=None)[0]
    if np.std(rx) == 0 or np.std(ry) == 0:
        return np.nan
    return float(np.corrcoef(rx, ry)[0, 1])

def correlation_report(joined: pd.DataFrame) -> pd.DataFrame:
    # Primary comparison is restricted to rows explicitly labelled MEASURED.
    frame = joined.loc[joined["Data_Quality"].str.upper() == "MEASURED"].copy()
    rows = []
    for prop in [p + "_median" for p in NUCLEAR_PROPERTIES]:
        data = frame[["Z", "theta3", prop]].dropna()
        if len(data) < 5 or data[prop].nunique() < 2:
            continue
        rows.append({
            "property": prop, "N_elements": len(data),
            "Pearson_r": float(pearsonr(data["theta3"], data[prop]).statistic),
            "Spearman_rho": float(spearmanr(data["theta3"], data[prop]).statistic),
            "partial_r_after_Z": _partial_corr(data["theta3"], data[prop], data["Z"]),
        })
    return pd.DataFrame(rows)

def holdout_report(joined: pd.DataFrame) -> pd.DataFrame:
    """Train on Z<=60, test on Z>60; predict each nuclear property from theta3."""
    frame = joined.loc[joined["Data_Quality"].str.upper() == "MEASURED"].copy()
    rows = []
    for prop in [p + "_median" for p in NUCLEAR_PROPERTIES]:
        data = frame[["Z", "theta3", prop]].dropna()
        train, test = data[data["Z"] <= 60], data[data["Z"] > 60]
        if len(train) < 8 or len(test) < 5 or train["theta3"].nunique() < 2:
            rows.append({"property": prop, "train_n": len(train), "test_n": len(test),
                         "MAE": np.nan, "RMSE": np.nan, "R2": np.nan,
                         "status": "INSUFFICIENT_COVERAGE"})
            continue
        slope, intercept = np.polyfit(train["theta3"], train[prop], 1)
        pred = slope * test["theta3"].to_numpy() + intercept
        actual = test[prop].to_numpy()
        mae = float(np.mean(np.abs(actual - pred)))
        rmse = float(np.sqrt(np.mean((actual - pred) ** 2)))
        denom = float(np.sum((actual - np.mean(actual)) ** 2))
        r2 = float(1 - np.sum((actual - pred) ** 2) / denom) if denom else np.nan
        rows.append({"property": prop, "train_n": len(train), "test_n": len(test),
                     "MAE": mae, "RMSE": rmse, "R2": r2, "status": "OK"})
    return pd.DataFrame(rows)

def run(framework_csv: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    source = pd.read_csv(framework_csv)
    angles = calculate_closure_angles(source)
    if source["Z"].nunique() != 118:
        raise ValueError(f"Expected 118 unique elements in 6.5.0 input; found {source['Z'].nunique()}.")
    print(f"Framework rows: {len(source)}; unique Z: {source['Z'].nunique()}")
    print(f"Elements with computable closure angle: {len(angles)}")
    print("Downloading official AME2020 atomic mass table...")
    raw = download_ame2020()
    print(f"AME2020 nuclide records parsed: {len(raw)}")
    nuclides = derive_separation_energies(raw)
    summary = summarize_by_element(nuclides)
    joined = angles.merge(summary, on="Z", how="left", suffixes=("", "_AME"))
    corr = correlation_report(joined)
    holdout = holdout_report(joined)

    raw.to_csv(output_dir / "AME2020_mass_records.csv", index=False)
    nuclides.to_csv(output_dir / "AME2020_nuclide_separation_energies.csv", index=False)
    joined.to_csv(output_dir / "element_angle_nuclear_summary.csv", index=False)
    corr.to_csv(output_dir / "nuclear_correlations.csv", index=False)
    holdout.to_csv(output_dir / "ordered_Z_holdout.csv", index=False)

    print("\nElement-level correlations (MEASURED framework elements):")
    print(corr.to_string(index=False) if not corr.empty else "No sufficient overlap.")
    print("\nOrdered-Z holdout: train Z<=60; test Z>60")
    print(holdout.to_string(index=False) if not holdout.empty else "No sufficient overlap.")
    print("\nInterpretation guardrails:")
    print("- AME-derived separation energies use measured mass-excess values only; '#' estimates are excluded.")
    print("- Per-element values are medians over available AME nuclides, not a selected natural-abundance isotope.")
    print("- One closure angle per element is compared with a distribution of isotopes; this is exploratory, not causal proof.")
    print("- Correlation and holdout prediction do not by themselves establish a physical law.")
    print(f"Results written to: {output_dir.resolve()}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", default="PROJECTS/triangle-framework/6.5.0/elements_input_118.csv")
    parser.add_argument("--out", default="atomic-interior-results")
    args = parser.parse_args()
    run(Path(args.framework), Path(args.out))

if __name__ == "__main__":
    main()
