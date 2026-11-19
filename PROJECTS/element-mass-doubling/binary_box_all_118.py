#!/usr/bin/env python3
"""Binary-box mass-position test for all 118 confirmed elements.

Model:
    L_n = BRICK * 2**n
    n   = floor(log2(mass / BRICK))
    P   = 100 * (mass - L_n) / L_n

This is a numerical mapping only; it does not establish a physical law.
"""
import csv
import html
import json
import math
import urllib.request
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BRICK = 0.016
DATA_URL = (
    "https://raw.githubusercontent.com/Bowserinator/"
    "Periodic-Table-JSON/master/PeriodicTableJSON.json"
)
OUT = Path(__file__).resolve().parent / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

PREDICTIONS = [
    {"Z": 114, "symbol": "Fl-298 (hypothesis)", "name": "Flerovium-298",
     "mass": 298.0, "record_type": "prediction"},
    {"Z": 126, "symbol": "E126 (hypothesis)", "name": "Element 126",
     "mass": 310.0, "record_type": "prediction"},
]

def calculate_position(mass):
    if mass is None or not math.isfinite(float(mass)) or float(mass) <= 0:
        return None, None, None
    mass = float(mass)
    n = math.floor(math.log2(mass / BRICK))
    lower = BRICK * (2 ** n)
    position = ((mass - lower) / lower) * 100.0
    return n, lower, position

def load_elements():
    request = urllib.request.Request(
        DATA_URL, headers={"User-Agent": "binary-box-mass-position/1.0"}
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.loads(response.read().decode("utf-8"))
    elements = payload.get("elements", [])
    if len(elements) != 118:
        raise RuntimeError(f"Expected 118 elements; received {len(elements)}")
    elements.sort(key=lambda item: int(item["number"]))
    if [int(item["number"]) for item in elements] != list(range(1, 119)):
        raise RuntimeError("Atomic numbers are incomplete or duplicated")
    return elements

def main():
    elements = load_elements()
    rows = []
    real_for_plot = []
    missing = []

    for element in elements:
        z = int(element["number"])
        symbol = str(element["symbol"])
        name = str(element["name"])
        mass_value = element.get("atomic_mass")
        try:
            mass = float(mass_value)
        except (TypeError, ValueError):
            mass = None

        n, lower, position = calculate_position(mass)
        if position is None:
            missing.append((z, symbol))
        else:
            real_for_plot.append((z, position, symbol))
        rows.append({
            "record_type": "real_element",
            "Z": z,
            "symbol": symbol,
            "name": name,
            "mass_u": mass if mass is not None else "",
            "box_n": n if n is not None else "",
            "box_lower_limit_u": lower if lower is not None else "",
            "position_P_percent": round(position, 6) if position is not None else "",
            "data_source": DATA_URL,
            "status": "source_mass" if position is not None else "mass_missing",
        })

    prediction_for_plot = []
    for item in PREDICTIONS:
        n, lower, position = calculate_position(item["mass"])
        prediction_for_plot.append((item["Z"], position, item["symbol"]))
        rows.append({
            "record_type": "prediction_not_observed",
            "Z": item["Z"],
            "symbol": item["symbol"],
            "name": item["name"],
            "mass_u": item["mass"],
            "box_n": n,
            "box_lower_limit_u": lower,
            "position_P_percent": round(position, 6),
            "data_source": "User-supplied hypothesis; not an observed atomic mass",
            "status": "hypothesis_only",
        })

    csv_path = OUT / "binary_box_mass_position_all_118.csv"
    fields = [
        "record_type", "Z", "symbol", "name", "mass_u", "box_n",
        "box_lower_limit_u", "position_P_percent", "data_source", "status"
    ]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    # Plot all real elements, keeping predictions visually separate.
    real_for_plot.sort()
    x = [item[0] for item in real_for_plot]
    y = [item[1] for item in real_for_plot]
    plt.figure(figsize=(16, 8))
    plt.plot(x, y, color="#2563eb", marker="o", linewidth=1.2,
             markersize=4, label="118 confirmed elements (source masses)")
    px = [item[0] + (0.35 if item[0] == 114 else 0.0) for item in prediction_for_plot]
    py = [item[1] for item in prediction_for_plot]
    plt.scatter(px, py, color="#dc2626", marker="*", s=190,
                label="User-supplied hypotheses (not observed)")
    for z in [28, 50, 82, 114, 126]:
        plt.axvline(z, color="gray", linestyle="--", alpha=0.35, linewidth=1)
        plt.text(z, 101, f"Z={z}", rotation=90, va="top", ha="right",
                 fontsize=8, color="gray")
    plt.title("Binary-Box Model: Mass Position Across Elements")
    plt.xlabel("Atomic number (Z)")
    plt.ylabel("Position inside current doubling box, P (%)")
    plt.xlim(1, 130)
    plt.ylim(-2, 105)
    plt.xticks(range(0, 131, 5))
    plt.yticks(range(0, 101, 10))
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()
    png_path = OUT / "binary_box_mass_position_all_118.png"
    plt.savefig(png_path, dpi=220, bbox_inches="tight")
    plt.close()

    html_path = OUT / "binary_box_mass_position_all_118.html"
    table_rows = []
    for row in rows:
        table_rows.append(
            "<tr>" + "".join(
                f"<td>{html.escape(str(row[field]))}</td>" for field in fields
            ) + "</tr>"
        )
    headers = "".join(f"<th>{html.escape(field)}</th>" for field in fields)
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Binary-box mass position — all 118 elements</title>
<style>
body{{font-family:Arial,sans-serif;margin:24px;color:#172033}}
h1{{font-size:1.5rem}}p{{line-height:1.6}}
img{{max-width:100%;height:auto}}.wrap{{overflow-x:auto}}
table{{border-collapse:collapse;font-size:13px;white-space:nowrap}}
th,td{{border:1px solid #d0d5dd;padding:6px 8px;text-align:left}}
th{{background:#f2f4f7;position:sticky;top:0}}
tr:nth-child(even){{background:#f9fafb}}
</style></head><body>
<h1>Binary-box mass position — all 118 elements</h1>
<p>BRICK = {BRICK}. Formula: n = floor(log2(M/BRICK)); L = BRICK × 2^n;
P = 100 × (M − L) / L. Predictions are separate from the 118 source records.</p>
<p>This numerical mapping is not, by itself, evidence of a physical law.
For radioactive/synthetic elements, the source's listed atomic-mass values
must be interpreted according to that source's conventions.</p>
<img src="binary_box_mass_position_all_118.png" alt="Mass position plot">
<div class="wrap"><table><thead><tr>{headers}</tr></thead>
<tbody>{''.join(table_rows)}</tbody></table></div>
</body></html>"""
    html_path.write_text(document, encoding="utf-8")

    print("=== BINARY BOX ALL-118 ===")
    print(f"source_elements: {len(elements)}")
    print(f"elements_with_mass: {len(real_for_plot)}")
    print(f"elements_missing_mass: {len(missing)}")
    print(f"predictions_separate: {len(PREDICTIONS)}")
    print(f"BRICK: {BRICK}")
    print(f"CSV: {csv_path}")
    print(f"PNG: {png_path}")
    print(f"HTML: {html_path}")
    if missing:
        print("MISSING:", ", ".join(f"{z}:{sym}" for z, sym in missing))
    print("=== END ===")

if __name__ == "__main__":
    main()
