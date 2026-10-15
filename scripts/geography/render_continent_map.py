#!/usr/bin/env python3
"""Render the continent map remotely from audited real polygon data.

This script is intended to run in GitHub Actions, not in ChatGPT's local environment.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from PIL import Image
import pandas as pd

OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "output/geography"))
POLYGONS = OUTPUT_DIR / "continent_land_polygons.geojson"
AREAS = OUTPUT_DIR / "continent_land_area.csv"
OUTPUT = OUTPUT_DIR / "continent_map_equal_earth.png"
EXPECTED = {"Africa", "Antarctica", "Asia", "Europe", "North America", "Oceania", "South America"}


def main() -> int:
    if not POLYGONS.exists() or not AREAS.exists():
        raise RuntimeError("Required audited polygon or area file is missing")
    polygons = gpd.read_file(POLYGONS)
    areas = pd.read_csv(AREAS)
    if "continent" not in polygons.columns or "continent" not in areas.columns:
        raise RuntimeError("Required continent field is missing")
    if set(polygons["continent"]) != EXPECTED or set(areas["continent"]) != EXPECTED:
        raise RuntimeError("Expected exactly the seven documented continents")
    if polygons.geometry.isna().any() or polygons.geometry.is_empty.any():
        raise RuntimeError("Map input contains empty geometries")
    if not polygons.geometry.is_valid.all():
        raise RuntimeError("Map input contains invalid geometries")
    if not areas["area_km2"].gt(0).all():
        raise RuntimeError("Map area table contains non-positive values")

    projected = polygons.to_crs("EPSG:8857")
    area_lookup = areas.set_index("continent")["area_million_km2"].to_dict()
    order = ["North America", "South America", "Europe", "Africa", "Asia", "Oceania", "Antarctica"]
    cmap = plt.get_cmap("Set2")
    color_lookup = {name: cmap(i) for i, name in enumerate(order)}

    fig = plt.figure(figsize=(16, 9), facecolor="#f7f8fa")
    grid = fig.add_gridspec(1, 2, width_ratios=[3.8, 1.15], wspace=0.03)
    ax = fig.add_subplot(grid[0, 0])
    side = fig.add_subplot(grid[0, 1])
    ax.set_facecolor("#edf2f5")
    for _, feature in projected.iterrows():
        name = feature["continent"]
        gpd.GeoSeries([feature.geometry], crs=projected.crs).plot(
            ax=ax, color=color_lookup[name], edgecolor="#39434d", linewidth=0.28
        )
    for _, feature in projected.iterrows():
        name = feature["continent"]
        point = feature.geometry.representative_point()
        label = f"{name}\n{area_lookup[name]:.2f} million km²"
        ax.annotate(
            label, (point.x, point.y), ha="center", va="center", fontsize=8.3,
            color="#17212b", fontweight="semibold",
            bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#9aa6b2", "alpha": 0.88, "linewidth": 0.55},
        )
    ax.set_title("CONTINENTAL LAND AREAS", loc="left", fontsize=18, fontweight="bold", color="#17212b", pad=18)
    ax.set_axis_off()
    ax.set_aspect("equal", adjustable="datalim")

    side.set_facecolor("#f7f8fa")
    side.set_axis_off()
    side.text(0.02, 0.97, "PRELIMINARY", transform=side.transAxes, fontsize=12, fontweight="bold", color="#9b3d2f", va="top")
    side.text(0.02, 0.91, "Area (million km²)", transform=side.transAxes, fontsize=10, color="#4b5563", va="top")
    y = 0.83
    for name in order:
        side.add_patch(plt.Rectangle((0.02, y - 0.025), 0.09, 0.035, transform=side.transAxes, color=color_lookup[name], clip_on=False))
        side.text(0.15, y - 0.006, name, transform=side.transAxes, fontsize=9.2, color="#17212b", va="center")
        side.text(0.98, y - 0.047, f"{area_lookup[name]:.2f}", transform=side.transAxes, fontsize=10, color="#17212b", va="center", ha="right", fontweight="bold")
        y -= 0.095
    side.text(
        0.02, 0.12,
        "\\n\\n".join([
            "Method: Natural Earth 1:10m land + minor islands; GBIF seven-continent partition; geodesic WGS84 area.",
            "Boundaries and island assignments follow the cited source. Antarctica excludes floating ice shelves unless represented in the land layer.",
            "Map projection: Equal Earth (EPSG:8857). Projection affects display, not area calculation.",
        ]),
        transform=side.transAxes, fontsize=8.1, color="#4b5563", va="top", wrap=True
    )
    fig.suptitle("Seven-continent model · verified remote data pipeline", x=0.05, y=0.99, ha="left", fontsize=10, color="#52606d")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=180, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)

    with Image.open(OUTPUT) as image:
        image.verify()
    with Image.open(OUTPUT) as image:
        width, height = image.size
        if width < 1600 or height < 800:
            raise RuntimeError(f"Rendered map dimensions are unexpectedly small: {width}x{height}")
    if OUTPUT.stat().st_size < 50_000:
        raise RuntimeError("Rendered map file is unexpectedly small")
    print(json.dumps({"status": "MAP_RENDERED_AND_IMAGE_FILE_VERIFIED", "path": str(OUTPUT), "bytes": OUTPUT.stat().st_size, "width": width, "height": height, "projection": "EPSG:8857 Equal Earth", "continents": len(polygons)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())