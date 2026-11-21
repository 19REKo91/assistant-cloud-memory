#!/usr/bin/env python3
"""Phase 3: NIST ASD neutral-atom excitation-level gaps vs 6.5.0 closure angle.

One neutral spectrum (Element I) is queried at a time, as required by the
NIST Levels form. Energies are retained in the database's native cm^-1 units.
Unmarked values are EVALUATED; [x] is SEMIEMPIRICAL; (x) is THEORETICAL.
"""
from __future__ import annotations

import argparse
import html
import re
from io import StringIO
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.stats import pearsonr, spearmanr

NIST_LEVELS_URL = "https://physics.nist.gov/cgi-bin/ASD/energy1.pl"
PERIODIC_TABLE_URL = "https://raw.githubusercontent.com/Bluegrams/periodic-table-data/master/Periodica.Data/Data/ElementData.csv"

def parse_level_value(value):
    raw = str(value).strip().replace(",", "").replace("−", "-")
    if not raw or raw.lower() in {"nan", "none", "--", "-", "—", "–"}:
        return np.nan, "MISSING"
    if "+x" in raw.lower() or "+y" in raw.lower() or "+z" in raw.lower():
        return np.nan, "UNCONNECTED"
    kind = "EVALUATED"
    if raw.startswith("[") and raw.endswith("]"):
        kind, raw = "SEMIEMPIRICAL", raw[1:-1].strip()
    elif raw.startswith("(") and raw.endswith(")"):
        kind, raw = "THEORETICAL", raw[1:-1].strip()
    if raw.endswith(("?", "†")):
        kind = "TENTATIVE"
        raw = raw[:-1].strip()
    footnote = re.fullmatch(r"([0-9][0-9.\s]*)([a-z]+)", raw, flags=re.I)
    if footnote:
        if kind == "EVALUATED":
            kind = "FOOTNOTED"
        raw = footnote.group(1)
    raw = re.sub(r"\s+", "", raw)
    try:
        return float(raw), kind
    except ValueError:
        return np.nan, "UNPARSED"

def _norm(value):
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())

def parse_levels_ascii(text, z, symbol):
    """Parse NIST ASD ASCII pipe table for one neutral spectrum."""
    plain = html.unescape(re.sub(r"<[^>]+>", "", text))
    lines = [line.rstrip("\r\n") for line in plain.splitlines() if line.strip()]
    header_idx = None
    for i, line in enumerate(lines):
        normalized = _norm(line)
        if "|" in line and "configuration" in normalized and "level" in normalized:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError(f"NIST levels table header not found for {symbol}. Response: {plain[:1200]}")
    header = [cell.strip() for cell in lines[header_idx].split("|")]
    while header and header[0] == "":
        header = header[1:]
    while header and header[-1] == "":
        header = header[:-1]
    skip_header_rows = {header_idx}
    # NIST commonly places the Level unit and Reference label on a second header line.
    if header_idx + 1 < len(lines) and "|" in lines[header_idx + 1]:
        next_header = [cell.strip() for cell in lines[header_idx + 1].split("|")]
        if len(next_header) == 2 and "cm" in next_header[0].lower() and "reference" in next_header[1].lower():
            header[-1] = header[-1] + " " + next_header[0]
            header.append(next_header[1])
            skip_header_rows.add(header_idx + 1)
    level_idx = None
    conf_idx = None
    term_idx = None
    j_idx = None
    for i, name in enumerate(header):
        n = _norm(name)
        if n.startswith("level") and level_idx is None:
            level_idx = i
        elif n.startswith("configuration") and conf_idx is None:
            conf_idx = i
        elif n == "term" and term_idx is None:
            term_idx = i
        elif n == "j" and j_idx is None:
            j_idx = i
    if level_idx is None:
        raise ValueError(f"NIST levels column missing for {symbol}; headers={header}")
    rows = []
    for line_index, line in enumerate(lines[header_idx + 1:], start=header_idx + 1):
        if line_index in skip_header_rows:
            continue
        if "|" not in line:
            if rows:
                break
            continue
        # Do not trim leading empty cells: NIST uses them to indicate repeated
        # configuration/term fields on fine-structure rows.
        cells = [cell.strip() for cell in line.split("|")]
        if not cells or all(set(cell) <= {"-", " "} for cell in cells):
            continue
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        energy, provenance = parse_level_value(cells[level_idx])
        rows.append({
            "Z": int(z), "symbol": symbol,
            "configuration": cells[conf_idx] if conf_idx is not None else "",
            "term": cells[term_idx] if term_idx is not None else "",
            "J": cells[j_idx] if j_idx is not None else "",
            "level_cm1": energy, "provenance": provenance,
            "raw_level": cells[level_idx],
        })
    result = pd.DataFrame(rows)
    if result.empty:
        raise ValueError(f"NIST returned no parseable levels for {symbol}.")
    # NIST suppresses repeated configuration/term labels on consecutive fine-structure rows.
    # Forward-fill those two grouped columns only; do not fill J, energy, or reference fields.
    for column in ("configuration", "term"):
        result[column] = result[column].replace("", np.nan).ffill().fillna("")
    return result

def fetch_levels(symbol, z):
    params = {
        "spectrum": f"{symbol} I",
        "units": "0",             # native cm^-1
        "format": "1",            # ASCII pipe-delimited
        "output": "0",            # all levels
        "page_size": "10000",
        "conf_out": "on",
        "term_out": "on",
        "level_out": "on",
        "j_out": "on",
        "submit": "Retrieve Data",
    }
    response = requests.get(
        NIST_LEVELS_URL, params=params, timeout=120,
        headers={"User-Agent": "AtomicInteriorResearch/1.0 (research data analysis)"}
    )
    response.raise_for_status()
    return parse_levels_ascii(response.text, z, symbol)

def _lowest(frame, provenance):
    d = frame[(frame["provenance"] == provenance) & frame["level_cm1"].notna() & (frame["level_cm1"] > 0)]
    return float(d["level_cm1"].min()) if len(d) else np.nan

def summarize_levels(levels):
    rows = []
    for z, group in levels.groupby("Z"):
        numeric = group[group["level_cm1"].notna()].copy()
        if numeric.empty:
            continue
        ground = numeric.loc[numeric["level_cm1"].idxmin()]
        evaluated = numeric[numeric["provenance"] == "EVALUATED"]
        semi = numeric[numeric["provenance"].isin(["EVALUATED", "SEMIEMPIRICAL"])]
        all_sources = numeric[numeric["provenance"].isin(["EVALUATED", "SEMIEMPIRICAL", "THEORETICAL", "TENTATIVE", "FOOTNOTED"])]
        def distinct_gap(source, field):
            d = source[(source["level_cm1"] > 0) & (source[field].astype(str) != str(ground[field]))]
            return float(d["level_cm1"].min()) if len(d) else np.nan
        low5 = np.sort(evaluated.loc[evaluated["level_cm1"] > 0, "level_cm1"].to_numpy())[:5]
        rows.append({
            "Z": int(z), "symbol": group["symbol"].iloc[0],
            "ground_configuration": str(ground["configuration"]),
            "ground_term": str(ground["term"]),
            "first_excited_level_gap_evaluated_cm1": _lowest(group, "EVALUATED"),
            "first_excited_level_gap_incl_semie_cm1": float(semi.loc[semi["level_cm1"] > 0, "level_cm1"].min()) if (semi["level_cm1"] > 0).any() else np.nan,
            "first_excited_level_gap_mixed_cm1": float(all_sources.loc[all_sources["level_cm1"] > 0, "level_cm1"].min()) if (all_sources["level_cm1"] > 0).any() else np.nan,
            "first_distinct_term_gap_evaluated_cm1": distinct_gap(evaluated, "term"),
            "first_distinct_configuration_gap_evaluated_cm1": distinct_gap(evaluated, "configuration"),
            "median_first5_excitation_levels_evaluated_cm1": float(np.median(low5)) if len(low5) else np.nan,
            "evaluated_level_count": int((numeric["provenance"] == "EVALUATED").sum()),
            "semie_level_count": int((numeric["provenance"] == "SEMIEMPIRICAL").sum()),
            "theoretical_level_count": int((numeric["provenance"] == "THEORETICAL").sum()),
            "tentative_level_count": int((numeric["provenance"] == "TENTATIVE").sum()),
            "footnoted_level_count": int((numeric["provenance"] == "FOOTNOTED").sum()),
            "evaluated_levels_below_10000_cm1": int(((evaluated["level_cm1"] > 0) & (evaluated["level_cm1"] <= 10000)).sum()),
            "evaluated_levels_below_20000_cm1": int(((evaluated["level_cm1"] > 0) & (evaluated["level_cm1"] <= 20000)).sum()),
            "total_numeric_level_rows": int(len(numeric)),
        })
    return pd.DataFrame(rows)

PROPERTIES = [
    "first_excited_level_gap_evaluated_cm1",
    "first_excited_level_gap_incl_semie_cm1",
    "first_distinct_term_gap_evaluated_cm1",
    "first_distinct_configuration_gap_evaluated_cm1",
    "median_first5_excitation_levels_evaluated_cm1",
    "evaluated_levels_below_10000_cm1",
    "evaluated_levels_below_20000_cm1",
]

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

def fetch_periodic_controls():
    """Independent period/block metadata; used only as statistical controls."""
    response = requests.get(PERIODIC_TABLE_URL, timeout=60)
    response.raise_for_status()
    table = pd.read_csv(StringIO(response.text))
    required = ["AtomicNumber", "Period", "Block"]
    missing = set(required) - set(table.columns)
    if missing:
        raise ValueError(f"Periodic-table control source missing columns: {sorted(missing)}")
    out = table[required].rename(columns={
        "AtomicNumber": "Z", "Period": "Period", "Block": "Block"
    })
    out["Z"] = pd.to_numeric(out["Z"], errors="coerce")
    out["Period"] = pd.to_numeric(out["Period"], errors="coerce")
    out["Block"] = out["Block"].astype(str).str.lower()
    return out.dropna(subset=["Z", "Period"]).drop_duplicates("Z")

def _partial_corr_controls(frame, ycol, xcol, numeric_controls, categorical_controls):
    cols = [ycol, xcol] + numeric_controls + categorical_controls
    d = frame[cols].dropna().copy()
    if len(d) < 8:
        return np.nan, len(d)
    matrices = [np.ones(len(d))]
    for col in numeric_controls:
        matrices.append(pd.to_numeric(d[col], errors="coerce").to_numpy())
    for col in categorical_controls:
        dummies = pd.get_dummies(d[col], drop_first=True, dtype=float)
        matrices.extend(dummies[c].to_numpy() for c in dummies.columns)
    X = np.column_stack(matrices)
    x, y = d[xcol].to_numpy(), d[ycol].to_numpy()
    rx = x - X @ np.linalg.lstsq(X, x, rcond=None)[0]
    ry = y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
    if np.std(rx) == 0 or np.std(ry) == 0:
        return np.nan, len(d)
    return float(np.corrcoef(rx, ry)[0, 1]), len(d)

def _design_with_block(train, test, include_angle):
    numeric = ["Z", "Period", "outermost_shell_electron_count"]
    train_blocks = pd.get_dummies(train["Block"], drop_first=True, dtype=float)
    test_blocks = pd.get_dummies(test["Block"], drop_first=True, dtype=float).reindex(
        columns=train_blocks.columns, fill_value=0
    )
    x_train = [np.ones(len(train))] + [train[c].astype(float).to_numpy() for c in numeric]
    x_test = [np.ones(len(test))] + [test[c].astype(float).to_numpy() for c in numeric]
    x_train.extend(train_blocks[c].to_numpy() for c in train_blocks.columns)
    x_test.extend(test_blocks[c].to_numpy() for c in train_blocks.columns)
    if include_angle:
        x_train.append(train["theta3"].astype(float).to_numpy())
        x_test.append(test["theta3"].astype(float).to_numpy())
    return np.column_stack(x_train), np.column_stack(x_test)


def reports(joined):
    measured = joined[joined["Data_Quality"].str.upper() == "MEASURED"].copy()
    corr, holdout, log_corr, block_corr, rolling = [], [], [], [], []
    for prop in PROPERTIES:
        d = measured[["Z", "theta3", prop]].dropna()
        if len(d) >= 5 and d[prop].nunique() > 1:
            corr.append({
                "property": prop, "N_elements": len(d),
                "Pearson_r": float(pearsonr(d["theta3"], d[prop]).statistic),
                "Spearman_rho": float(spearmanr(d["theta3"], d[prop]).statistic),
                "partial_r_after_Z": _partial_corr(d["theta3"], d[prop], d["Z"]),
            })
        train, test = d[d["Z"] <= 60], d[d["Z"] > 60]
        if len(train) >= 8 and len(test) >= 5:
            y_train, y_test = train[prop].to_numpy(), test[prop].to_numpy()
            for model_name, predictors in [
                ("Z_only", ["Z"]), ("theta3_only", ["theta3"]), ("Z_plus_theta3", ["Z", "theta3"])
            ]:
                X = np.column_stack([np.ones(len(train))] + [train[k].to_numpy() for k in predictors])
                Xt = np.column_stack([np.ones(len(test))] + [test[k].to_numpy() for k in predictors])
                coef = np.linalg.lstsq(X, y_train, rcond=None)[0]
                pred = Xt @ coef
                mae = float(np.mean(np.abs(y_test - pred)))
                rmse = float(np.sqrt(np.mean((y_test - pred) ** 2)))
                den = float(np.sum((y_test - y_test.mean()) ** 2))
                r2 = float(1 - np.sum((y_test - pred) ** 2) / den) if den else np.nan
                holdout.append({"property": prop, "train_n": len(train), "test_n": len(test),
                                "model": model_name, "MAE": mae, "RMSE": rmse, "R2": r2})

        # Log-energy analysis: energy gaps span orders of magnitude.
        if "gap" not in prop and "median_first5" not in prop:
            continue
        log_data = measured[["Z", "theta3", "Period", "Block",
                             "outermost_shell_electron_count", prop]].dropna().copy()
        log_data = log_data[log_data[prop] > 0]
        if len(log_data) < 10:
            continue
        log_col = "log10_" + prop
        log_data[log_col] = np.log10(log_data[prop])
        log_corr.append({
            "property": log_col, "N_elements": len(log_data),
            "Pearson_r": float(pearsonr(log_data["theta3"], log_data[log_col]).statistic),
            "Spearman_rho": float(spearmanr(log_data["theta3"], log_data[log_col]).statistic),
            "partial_r_after_Z": _partial_corr(log_data["theta3"], log_data[log_col], log_data["Z"]),
            "partial_r_after_Z_period_block_shell": _partial_corr_controls(
                log_data, log_col, "theta3",
                ["Z", "Period", "outermost_shell_electron_count"], ["Block"]
            )[0],
        })
        for block, group in log_data.groupby("Block"):
            if len(group) >= 5 and group[log_col].nunique() > 1:
                block_corr.append({
                    "property": log_col, "block": block, "N_elements": len(group),
                    "Pearson_r": float(pearsonr(group["theta3"], group[log_col]).statistic),
                    "Spearman_rho": float(spearmanr(group["theta3"], group[log_col]).statistic),
                    "partial_r_after_Z": _partial_corr(group["theta3"], group[log_col], group["Z"]),
                })
        for cutoff in (40, 50, 60, 70):
            tr, te = log_data[log_data["Z"] <= cutoff], log_data[log_data["Z"] > cutoff]
            if len(tr) < 20 or len(te) < 10:
                continue
            ytr, yte = tr[log_col].to_numpy(), te[log_col].to_numpy()
            for model_name, include_angle in (("Z_period_shell_block", False),
                                               ("Z_period_shell_block_plus_theta3", True)):
                X, Xt = _design_with_block(tr, te, include_angle)
                coef = np.linalg.lstsq(X, ytr, rcond=None)[0]
                pred = Xt @ coef
                mae = float(np.mean(np.abs(yte - pred)))
                rmse = float(np.sqrt(np.mean((yte - pred) ** 2)))
                den = float(np.sum((yte - yte.mean()) ** 2))
                r2 = float(1 - np.sum((yte - pred) ** 2) / den) if den else np.nan
                rolling.append({
                    "property": log_col, "Z_train_max": cutoff,
                    "train_n": len(tr), "test_n": len(te), "model": model_name,
                    "MAE_log10": mae, "RMSE_log10": rmse, "R2": r2
                })
    return (pd.DataFrame(corr), pd.DataFrame(holdout), pd.DataFrame(log_corr),
            pd.DataFrame(block_corr), pd.DataFrame(rolling))

def run(framework_csv: Path, output_dir: Path):
    from search import calculate_closure_angles
    output_dir.mkdir(parents=True, exist_ok=True)
    framework = pd.read_csv(framework_csv)
    angles = calculate_closure_angles(framework)
    measured = framework[framework["Data_Quality"].astype(str).str.upper() == "MEASURED"][["Z", "Sym"]]
    symbols = [(int(row.Z), str(row.Sym)) for row in measured.itertuples()]
    all_rows, errors = [], []
    for index, (z, symbol) in enumerate(symbols):
        if index:
            time.sleep(0.5)
        try:
            all_rows.append(fetch_levels(symbol, z))
        except Exception as exc:
            errors.append({"Z": z, "symbol": symbol, "error": str(exc)[:500]})
            print(f"   NIST levels missing/error for {symbol}: {type(exc).__name__}")
    if not all_rows:
        raise RuntimeError("NIST Levels returned no parseable neutral-atom data.")
    levels = pd.concat(all_rows, ignore_index=True)
    summary = summarize_levels(levels)
    periodic = fetch_periodic_controls()
    electronic_path = output_dir / "element_angle_electronic_summary.csv"
    if not electronic_path.exists():
        raise FileNotFoundError(
            "Run electronic_search.py first; its NIST neutral shell summary is required as a control."
        )
    electronic = pd.read_csv(electronic_path)
    joined = (
        angles.merge(summary, on="Z", how="left")
        .merge(periodic, on="Z", how="left")
        .merge(electronic[["Z", "outermost_shell_electron_count"]], on="Z", how="left")
    )
    corr, holdout, log_corr, block_corr, rolling = reports(joined)

    levels.to_csv(output_dir / "NIST_ASD_neutral_energy_levels.csv", index=False)
    summary.to_csv(output_dir / "NIST_ASD_neutral_level_summary.csv", index=False)
    joined.to_csv(output_dir / "element_angle_level_summary.csv", index=False)
    corr.to_csv(output_dir / "level_correlations.csv", index=False)
    holdout.to_csv(output_dir / "level_ordered_Z_holdout.csv", index=False)
    log_corr.to_csv(output_dir / "level_log_correlations.csv", index=False)
    block_corr.to_csv(output_dir / "level_block_correlations.csv", index=False)
    rolling.to_csv(output_dir / "level_rolling_Z_holdout_with_block_controls.csv", index=False)
    periodic.to_csv(output_dir / "periodic_table_block_controls.csv", index=False)
    pd.DataFrame(errors).to_csv(output_dir / "NIST_ASD_level_fetch_errors.csv", index=False)

    print(f"NIST neutral level rows parsed: {len(levels)}")
    print(f"NIST neutral elements with level data: {summary['Z'].nunique()}")
    print(f"NIST level query errors: {len(errors)}")
    print("\nNeutral excitation-level correlations:")
    print(corr.to_string(index=False) if not corr.empty else "No sufficient overlap.")
    print("\nOrdered-Z holdout: train Z<=60; test Z>60")
    print(holdout.to_string(index=False) if not holdout.empty else "No sufficient overlap.")
    print("\nLog-gap correlations, including block-adjusted partial correlations:")
    print(log_corr.to_string(index=False) if not log_corr.empty else "No sufficient overlap.")
    print("\nBlock-specific log-gap correlations:")
    print(block_corr.to_string(index=False) if not block_corr.empty else "No sufficient overlap.")
    print("\nRolling high-Z holdout with period/block/shell controls:")
    print(rolling.to_string(index=False) if not rolling.empty else "No sufficient overlap.")
    print("Only unmarked evaluated levels enter strict evaluated-gap metrics; bracketed and theoretical values remain separate.")
    print(f"Results: {output_dir.resolve()}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", default="PROJECTS/triangle-framework/6.5.0/elements_input_118.csv")
    parser.add_argument("--out", default="atomic-interior-results")
    args = parser.parse_args()
    run(Path(args.framework), Path(args.out))

if __name__ == "__main__":
    main()
