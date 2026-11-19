#!/usr/bin/env python3
"""Analyze AME2020 measured/evaluated nuclide masses and binding energy per nucleon.

Source: Atomic Mass Data Center, AME2020 mass_1.mas20 (unrounded).
The official table's '#' notation marks values partly derived from trends/systematics;
those rows are retained but flagged estimated. Rows with no numeric B/A are excluded
from plots and retained in the CSV with a status.
"""
from pathlib import Path
import csv
import math
import urllib.request

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SOURCE_URL = "https://amdc.impcas.ac.cn/masstables/Ame2020/mass_1.mas20"
OUT = Path(__file__).resolve().parent / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
MAGIC = (28, 50, 82, 126)

def get_source():
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "AME2020-nuclide-analysis/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read().decode("ascii", errors="replace")

def parse_rows(text):
    rows = []
    for line in text.splitlines():
        # AME2020 fixed-width layout documented in the source file header.
        if len(line) < 78:
            continue
        try:
            n = int(line[4:9].strip())
            z = int(line[9:14].strip())
            a = int(line[14:19].strip())
        except ValueError:
            continue
        symbol = line[20:23].strip()
        if not symbol or z < 1 or a < 1 or n < 0 or a != z + n:
            continue
        be_raw = line[54:67].strip()
        unc_raw = line[67:78].strip()
        estimated = "#" in be_raw or "#" in unc_raw
        be_clean = be_raw.replace("#", "").strip()
        unc_clean = unc_raw.replace("#", "").strip()
        try:
            be = float(be_clean)
        except ValueError:
            be = None
        try:
            unc = float(unc_clean)
        except ValueError:
            unc = None
        rows.append({
            "Z": z, "N": n, "A": a, "symbol": symbol,
            "binding_energy_per_nucleon_keV": be if be is not None else "",
            "uncertainty_keV": unc if unc is not None else "",
            "source_estimated_flag": estimated,
            "status": "estimated_or_systematics" if estimated else ("numeric_evaluated_value" if be is not None else "not_calculable"),
            "source": "AME2020 mass_1.mas20",
        })
    # Avoid accidental duplicate rows; AME ground-state mass table should have unique (Z,N).
    keyed = {}
    for row in rows:
        keyed[(row["Z"], row["N"])] = row
    return sorted(keyed.values(), key=lambda r: (r["A"], r["Z"]))

def main():
    raw = get_source()
    rows = parse_rows(raw)
    numeric = [r for r in rows if isinstance(r["binding_energy_per_nucleon_keV"], (int, float))]
    if len(numeric) < 1000:
        raise RuntimeError(f"Parsed too few numeric nuclides: {len(numeric)}")
    csv_path = OUT / "ame2020_nuclide_binding_energy.csv"
    fields = ["Z", "N", "A", "symbol", "binding_energy_per_nucleon_keV", "uncertainty_keV", "source_estimated_flag", "status", "source"]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # Chart 1: B/A against mass number A, with magic-number annotations.
    fig, ax = plt.subplots(figsize=(15, 8))
    measured = [r for r in numeric if not r["source_estimated_flag"]]
    estimated = [r for r in numeric if r["source_estimated_flag"]]
    ax.scatter([r["A"] for r in measured], [r["binding_energy_per_nucleon_keV"] for r in measured],
               s=8, alpha=.55, label="AME2020 values without # flag")
    if estimated:
        ax.scatter([r["A"] for r in estimated], [r["binding_energy_per_nucleon_keV"] for r in estimated],
                   s=8, alpha=.25, marker="x", label="AME2020 values flagged # (estimated component)")
    ax.set(title="AME2020: Binding energy per nucleon vs mass number",
           xlabel="Mass number A", ylabel="Binding energy per nucleon (keV)")
    ax.grid(alpha=.25); ax.legend()
    ax.text(.01, .02, "Magic numbers are proton/neutron shell counts (Z or N), not mass number A.",
            transform=ax.transAxes, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "ame2020_binding_energy_vs_A.png", dpi=200)
    plt.close(fig)

    # Chart 2: nuclide chart colored by B/A; show magic Z and N shell closures separately.
    fig, ax = plt.subplots(figsize=(14, 10))
    sc = ax.scatter([r["N"] for r in numeric], [r["Z"] for r in numeric],
                    c=[r["binding_energy_per_nucleon_keV"] for r in numeric],
                    s=12, cmap="viridis", alpha=.85)
    cb = fig.colorbar(sc, ax=ax); cb.set_label("Binding energy per nucleon (keV)")
    for m in MAGIC:
        ax.axvline(m, color="crimson", linestyle="--", linewidth=1, alpha=.8)
        ax.axhline(m, color="darkorange", linestyle=":", linewidth=1, alpha=.8)
    ax.set(title="AME2020 nuclide chart: binding energy per nucleon and magic shell counts",
           xlabel="Neutron number N (vertical dashed red: magic N)",
           ylabel="Proton number Z (horizontal dotted orange: magic Z)")
    ax.grid(alpha=.15)
    fig.tight_layout()
    fig.savefig(OUT / "ame2020_nuclide_map_magic_numbers.png", dpi=200)
    plt.close(fig)

    # Summary: nearest high-B/A nuclides around each magic Z/N, for inspection only.
    summary = []
    for axis_name, coord in [("N", "N"), ("Z", "Z")]:
        for magic in MAGIC:
            subset = [r for r in numeric if r[coord] == magic]
            subset.sort(key=lambda r: r["binding_energy_per_nucleon_keV"], reverse=True)
            for r in subset[:5]:
                summary.append({"tested_axis": axis_name, "magic_number": magic, **r})
    with (OUT / "ame2020_magic_number_summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields2 = ["tested_axis", "magic_number"] + fields
        w = csv.DictWriter(f, fieldnames=fields2); w.writeheader(); w.writerows(summary)

    print("=== AME2020 BINDING ENERGY ANALYSIS ===")
    print(f"source: {SOURCE_URL}")
    print(f"parsed_nuclides: {len(rows)}")
    print(f"numeric_binding_values: {len(numeric)}")
    print(f"estimated_flagged_numeric: {len(estimated)}")
    print(f"non_numeric_or_missing: {len(rows)-len(numeric)}")
    print("magic_numbers_tested_on_separate_axes: N and Z = 28, 50, 82, 126")
    print(f"CSV: {csv_path}")
    print(f"CHART_A: {OUT / 'ame2020_binding_energy_vs_A.png'}")
    print(f"CHART_NUCLIDE_MAP: {OUT / 'ame2020_nuclide_map_magic_numbers.png'}")
    print(f"SUMMARY: {OUT / 'ame2020_magic_number_summary.csv'}")
    print("=== END ===")

if __name__ == "__main__":
    main()
