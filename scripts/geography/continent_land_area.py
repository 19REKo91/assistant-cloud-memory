#!/usr/bin/env python3
"""Calculate continent land areas using explicit continent cookie-cutter polygons.

Land geometries come from Natural Earth 1:10m; continent partitioning comes from
GBIF's continent cookie-cutter dataset. This avoids assigning all of Russia to
Europe (or another country-level category). No map or image is generated.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
import zipfile

import geopandas as gpd
import pandas as pd
import pyproj
from shapely import make_valid
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

LAND_URL = "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_land.zip"
MINOR_ISLANDS_URL = "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_minor_islands.zip"
ICE_SHELVES_URL = "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_antarctic_ice_shelves_polys.zip"
GBIF_COMMIT = "5f2aaf608f2f828bb1d03ae0d2ef3f41feacd5be"
COOKIE_CUTTER_URL = (
    "https://raw.githubusercontent.com/gbif/continents/"
    + GBIF_COMMIT + "/continent_cookie_cutter.geojson"
)
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "output/geography"))
EXPECTED = {"Africa", "Antarctica", "Asia", "Europe", "North America", "Oceania", "South America"}


def download(url: str, destination: Path) -> None:
    with urlopen(url, timeout=90) as response, destination.open("wb") as output:
        output.write(response.read())


def polygonal(geometry):
    """Repair geometry and retain polygonal components only."""
    if geometry is None or geometry.is_empty:
        return None
    geometry = geometry if geometry.is_valid else make_valid(geometry)
    stack = [geometry]
    polygons = []
    while stack:
        part = stack.pop()
        if isinstance(part, Polygon):
            polygons.append(part)
        elif isinstance(part, MultiPolygon):
            polygons.extend(list(part.geoms))
        elif hasattr(part, "geoms"):
            stack.extend(list(part.geoms))
    if not polygons:
        return None
    result = unary_union(polygons)
    if not result.is_valid:
        result = make_valid(result)
    return result


def area_km2(geometry, geod) -> float:
    """Return geodesic area while normalizing ring orientation per polygon.

    Geod's polygon area is signed; taking abs() only after measuring a whole
    MultiPolygon can let differently oriented components cancel each other.
    Orient each exterior counter-clockwise and each hole clockwise, then sum
    the absolute net area of each polygon independently.
    """
    if geometry is None or geometry.is_empty:
        return 0.0

    def polygon_area_m2(polygon) -> float:
        from shapely.geometry.polygon import orient
        normalized = orient(polygon, sign=1.0)
        area_m2, _ = geod.geometry_area_perimeter(normalized)
        return abs(float(area_m2))

    if isinstance(geometry, Polygon):
        return polygon_area_m2(geometry) / 1_000_000.0
    if isinstance(geometry, MultiPolygon):
        return sum(polygon_area_m2(part) for part in geometry.geoms) / 1_000_000.0
    if hasattr(geometry, "geoms"):
        return sum(area_km2(part, geod) for part in geometry.geoms)
    return 0.0


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="continent-land-") as temporary:
        tmp = Path(temporary)
        land_zip = tmp / "land.zip"
        islands_zip = tmp / "minor-islands.zip"
        ice_shelves_zip = tmp / "antarctic-ice-shelves.zip"
        cutter_file = tmp / "continent_cookie_cutter.geojson"
        download(LAND_URL, land_zip)
        download(MINOR_ISLANDS_URL, islands_zip)
        download(ICE_SHELVES_URL, ice_shelves_zip)
        download(COOKIE_CUTTER_URL, cutter_file)
        for archive in (land_zip, islands_zip, ice_shelves_zip):
            if not zipfile.is_zipfile(archive):
                raise RuntimeError(f"Downloaded Natural Earth archive is invalid: {archive.name}")

        land = gpd.read_file(f"zip://{land_zip}")
        islands = gpd.read_file(f"zip://{islands_zip}")
        ice_shelves = gpd.read_file(f"zip://{ice_shelves_zip}")
        cutters = gpd.read_file(cutter_file)
        if land.empty or cutters.empty:
            raise RuntimeError("Land or continent cookie-cutter dataset is empty")
        aliases = {name.casefold(): name for name in EXPECTED}
        aliases.update({
            "af": "Africa", "an": "Antarctica", "as": "Asia", "eu": "Europe",
            "na": "North America", "oc": "Oceania", "sa": "South America",
            "north_america": "North America", "north-america": "North America",
            "south_america": "South America", "south-america": "South America",
        })
        name_candidates = ("continent", "CONTINENT", "name", "NAME", "continent_name", "CONTINENT_N", "slug")
        name_field = next(
            (field for field in name_candidates if field in cutters.columns and
             any(str(value).strip().casefold() in aliases for value in cutters[field].dropna())),
            None,
        )
        if name_field is None:
            raise RuntimeError("Could not identify continent-name field. Available fields: " + repr(list(cutters.columns)) + "; values: " + repr({field: cutters[field].dropna().astype(str).unique()[:30].tolist() for field in cutters.columns if field != "geometry"}))

        cutters["continent_name"] = cutters[name_field].map(lambda value: aliases.get(str(value).strip().casefold(), str(value).strip()))
        available = set(cutters["continent_name"].dropna())
        missing = sorted(EXPECTED - available)
        if missing:
            raise RuntimeError(f"Continent cutter missing expected regions: {missing}; available={sorted(available)}")
        continent_geometries = {}
        for name in sorted(EXPECTED):
            pieces = [polygonal(g) for g in cutters.loc[cutters["continent_name"] == name, "geometry"]]
            pieces = [g for g in pieces if g is not None]
            if not pieces:
                raise RuntimeError(f"No valid cutter geometry for {name}")
            continent_geometries[name] = unary_union(pieces)
        cutter_union = unary_union(list(continent_geometries.values()))

        geod = pyproj.Geod(ellps="WGS84")
        land_features = []
        repaired_count = 0
        for source_name, frame in (("Natural Earth major land", land), ("Natural Earth minor islands", islands)):
            for index, row in frame.iterrows():
                raw = row.geometry
                if raw is None or raw.is_empty:
                    continue
                if not raw.is_valid:
                    repaired_count += 1
                geometry = polygonal(raw)
                if geometry is not None and not geometry.is_empty:
                    land_features.append((source_name, str(index), geometry))
        if not land_features:
            raise RuntimeError("No polygonal land geometries remain after validation")

        # Union clipped geometries by continent, rather than unioning all 2,800+
        # source features at once. This removes overlap double-counting while keeping
        # the remote workflow tractable on standard GitHub-hosted runners.
        clipped_parts = {name: [] for name in sorted(EXPECTED)}
        outside_parts = []
        source_feature_area_sum_km2 = sum(area_km2(feature[2], geod) for feature in land_features)
        for source_name, feature_id, geometry in land_features:
            outside = polygonal(geometry.difference(cutter_union))
            if outside is not None and not outside.is_empty:
                outside_parts.append(outside)
            for name, continent_geometry in continent_geometries.items():
                clipped = polygonal(geometry.intersection(continent_geometry))
                if clipped is not None and not clipped.is_empty:
                    clipped_parts[name].append(clipped)

        polygon_geometries = {name: unary_union(parts) for name, parts in clipped_parts.items() if parts}
        if set(polygon_geometries) != EXPECTED:
            raise RuntimeError("One or more continents have no clipped land geometry")
        assigned_by_continent = {
            name: area_km2(polygon_geometries[name], geod) for name in sorted(EXPECTED)
        }
        assigned_sum = sum(assigned_by_continent.values())
        outside_union = unary_union(outside_parts) if outside_parts else None
        unassigned_km2 = area_km2(outside_union, geod) if outside_union is not None else 0.0
        source_land_union = unary_union(
            list(polygon_geometries.values()) + ([outside_union] if outside_union is not None else [])
        )
        total_land_km2 = area_km2(source_land_union, geod)
        covered_expected = max(0.0, total_land_km2 - unassigned_km2)
        overlap_excess = assigned_sum - covered_expected
        if unassigned_km2 > 10000:
            raise RuntimeError(f"Too much land is outside continent cutters: {unassigned_km2:.3f} km²")
        if abs(overlap_excess) > max(1000.0, covered_expected * 0.0001):
            raise RuntimeError(f"Continent cutters overlap or area totals do not reconcile: excess={overlap_excess:.3f} km²")

        rows = [{
            "continent": name,
            "area_km2": assigned_by_continent[name],
            "area_million_km2": assigned_by_continent[name] / 1_000_000.0,
        } for name in sorted(EXPECTED)]
        totals = pd.DataFrame(rows).sort_values("area_km2", ascending=False)
        totals_path = OUTPUT_DIR / "continent_land_area.csv"
        polygons_path = OUTPUT_DIR / "continent_land_polygons.geojson"
        audit_path = OUTPUT_DIR / "continent_land_area_audit.json"
        polygon_frame = gpd.GeoDataFrame(
            {"continent": list(polygon_geometries.keys())},
            geometry=list(polygon_geometries.values()),
            crs="EPSG:4326",
        )
        polygon_frame.to_file(polygons_path, driver="GeoJSON")
        totals.to_csv(totals_path, index=False, float_format="%.6f")

        # Separate scenario for references that count floating Antarctic ice shelves.
        shelf_parts = []
        shelf_repaired_count = 0
        antarctica_cutter = continent_geometries["Antarctica"]
        for _, row in ice_shelves.iterrows():
            raw = row.geometry
            if raw is None or raw.is_empty:
                continue
            if not raw.is_valid:
                shelf_repaired_count += 1
            geometry = polygonal(raw)
            if geometry is None or geometry.is_empty:
                continue
            clipped_shelf = polygonal(geometry.intersection(antarctica_cutter))
            if clipped_shelf is not None and not clipped_shelf.is_empty:
                shelf_parts.append(clipped_shelf)
        if not shelf_parts:
            raise RuntimeError("No Antarctic ice-shelf polygons remain after validation")
        shelves_union = unary_union(shelf_parts)
        antarctica_land = polygon_geometries["Antarctica"]
        antarctica_land_area = area_km2(antarctica_land, geod)
        shelf_union_area = area_km2(shelves_union, geod)
        antarctica_land_plus_shelves = area_km2(unary_union([antarctica_land, shelves_union]), geod)
        shelf_increment = antarctica_land_plus_shelves - antarctica_land_area
        scenarios_path = OUTPUT_DIR / "antarctica_area_scenarios.csv"
        scenarios = pd.DataFrame([
            {"scenario": "land_only", "definition": "Natural Earth land + minor islands, clipped to GBIF Antarctica", "area_km2": antarctica_land_area, "area_million_km2": antarctica_land_area / 1_000_000.0},
            {"scenario": "land_plus_ice_shelves", "definition": "Union of land-only Antarctica and Natural Earth Antarctic ice-shelf polygons, clipped to GBIF Antarctica; overlaps counted once", "area_km2": antarctica_land_plus_shelves, "area_million_km2": antarctica_land_plus_shelves / 1_000_000.0},
        ])
        scenarios.to_csv(scenarios_path, index=False, float_format="%.6f")
        audit = {
            "status": "PRELIMINARY_PHYSICAL_LAND_AREAS_REQUIRES_REVIEW",
            "measurement": "Geodesic polygon area on WGS84 ellipsoid using pyproj.Geod",
            "land_source": "Natural Earth 1:10m land plus minor islands",
            "land_source_urls": [LAND_URL, MINOR_ISLANDS_URL],
            "antarctic_ice_shelf_source": "Natural Earth 1:10m Antarctic Ice Shelves polygons",
            "antarctic_ice_shelf_source_url": ICE_SHELVES_URL,
            "antarctic_ice_shelf_invalid_geometry_count_repaired": shelf_repaired_count,
            "antarctica_land_only_area_km2": round(antarctica_land_area, 3),
            "antarctic_ice_shelf_union_area_km2": round(shelf_union_area, 3),
            "antarctica_land_plus_ice_shelves_area_km2": round(antarctica_land_plus_shelves, 3),
            "antarctic_ice_shelf_increment_beyond_land_km2": round(shelf_increment, 3),
            "antarctic_ice_shelves_note": "Alternative scenario only; primary continent_land_area.csv remains land-only. Land/shelf overlap is unioned and counted once; this is a source-defined polygon scenario, not a time-specific ice-sheet estimate.",
            "continent_partition_source": "GBIF continents continent_cookie_cutter.geojson",
            "continent_partition_url": COOKIE_CUTTER_URL,
            "continent_partition_commit": GBIF_COMMIT,
            "partition_note": "Continental boundaries and island assignments follow the GBIF cookie-cutter polygons; marine edges are approximate and this is one documented seven-continent convention.",
            "license_note": "Natural Earth land data is public domain; GBIF continent cookie-cutter is ODbL-derived from OpenStreetMap. Review ODbL obligations before redistributing derived datasets.",
            "continent_count": len(totals),
            "land_feature_count": len(land_features),
            "source_invalid_geometry_count_repaired": repaired_count,
            "total_source_land_area_km2": round(total_land_km2, 3),
            "sum_of_individual_source_feature_areas_km2_before_deduplication": round(source_feature_area_sum_km2, 3),
            "overlap_removed_by_union_km2": round(source_feature_area_sum_km2 - total_land_km2, 3),
            "assigned_land_area_km2": round(assigned_sum, 3),
            "unassigned_land_area_km2": round(unassigned_km2, 3),
            "overlap_excess_km2": round(overlap_excess, 3),
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "python_libraries": {"geopandas": gpd.__version__, "pandas": pd.__version__, "pyproj": pyproj.__version__},
            "files": [totals_path.name, polygons_path.name, scenarios_path.name, audit_path.name],
        }
        audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if len(totals) != 7 or not totals["area_km2"].gt(0).all():
            raise RuntimeError("Continent area output validation failed")
        if not all(p.exists() and p.stat().st_size > 0 for p in (totals_path, polygons_path, scenarios_path, audit_path)):
            raise RuntimeError("One or more continent land-area outputs are missing or empty")
        print(json.dumps(audit, ensure_ascii=False, indent=2))
        print("\nPhysical land area by continent (million km²):")
        print(totals[["continent", "area_million_km2"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())