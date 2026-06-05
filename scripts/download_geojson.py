"""
One-time script: downloads Philippine regions GeoJSON, simplifies it,
and saves a small version to data/ph_regions.geojson.

Run once from project root: python scripts/download_geojson.py
"""

import json
import math
import os
from pathlib import Path

import requests

URL = "https://raw.githubusercontent.com/macoymejia/geojsonph/master/Regions/Regions.json"
OUT = Path(__file__).parent.parent / "data" / "ph_regions.geojson"
PRECISION = 3       # decimal places (~111m resolution — enough for regional map)
MIN_RING_POINTS = 4 # drop rings with fewer points after simplification


def round_coords(obj):
    """Recursively round all coordinate values to PRECISION decimal places."""
    if isinstance(obj, list):
        if obj and isinstance(obj[0], (int, float)):
            return [round(v, PRECISION) for v in obj]
        return [round_coords(item) for item in obj]
    return obj


def ring_area(ring):
    """Approximate polygon ring area via shoelace formula — for island filtering."""
    n = len(ring)
    if n < 3:
        return 0
    area = 0
    for i in range(n):
        j = (i + 1) % n
        area += ring[i][0] * ring[j][1]
        area -= ring[j][0] * ring[i][1]
    return abs(area) / 2


def simplify_geometry(geom):
    """
    Simplify a GeoJSON geometry:
    - Round coordinates
    - Drop tiny island polygons (area < 0.001 sq degrees)
    """
    if geom is None:
        return None

    gtype = geom["type"]
    coords = round_coords(geom["coordinates"])

    if gtype == "Polygon":
        rings = [r for r in coords if len(r) >= MIN_RING_POINTS]
        if not rings:
            return None
        return {"type": "Polygon", "coordinates": rings}

    if gtype == "MultiPolygon":
        polys = []
        for poly in coords:
            rings = [r for r in poly if len(r) >= MIN_RING_POINTS]
            if rings:
                # Keep only rings with meaningful area (drops tiny islets)
                outer = rings[0]
                if ring_area(outer) >= 0.001:
                    polys.append(rings)
        if not polys:
            return None
        return {"type": "MultiPolygon", "coordinates": polys}

    return geom


# ── Region name mapping ───────────────────────────────────────────────────────
# Maps GeoJSON region names to our internal region codes
REGION_MAP = {
    "National Capital Region (NCR)":           "NCR",
    "Ilocos Region (Region I)":                "Region I",
    "Cagayan Valley (Region II)":              "Region II",
    "Central Luzon (Region III)":              "Region III",
    "CALABARZON (Region IV-A)":                "Region IV-A",
    "MIMAROPA (Region IV-B)":                  "Region IV-B",
    "Bicol Region (Region V)":                 "Region V",
    "Western Visayas (Region VI)":             "Region VI",
    "Central Visayas (Region VII)":            "Region VII",
    "Eastern Visayas (Region VIII)":           "Region VIII",
    "Zamboanga Peninsula (Region IX)":         "Region IX",
    "Northern Mindanao (Region X)":            "Region X",
    "Davao Region (Region XI)":                "Region XI",
    "SOCCSKSARGEN (Region XII)":               "Region XII",
    "CARAGA (Region XIII)":                    "Region XIII",
    "Cordillera Administrative Region (CAR)":  "CAR",
    "Bangsamoro (BARMM)":                      "BARMM",
}


def main():
    print("Downloading Philippine regions GeoJSON...")
    tmp = OUT.parent / "_tmp_regions.json"

    with requests.get(URL, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded / total * 100
                    print(f"\r  {pct:.0f}%  ({downloaded:,} / {total:,} bytes)", end="")
        print()

    print("Parsing and simplifying...")
    with open(tmp, encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    print(f"  Original: {len(features)} features")

    simplified = []
    for feat in features:
        props = feat.get("properties", {})
        # Try common property name variants for region name
        name = (
            props.get("REGION")
            or props.get("region")
            or props.get("NAME_1")
            or props.get("name")
            or props.get("REGNAME")
            or ""
        )

        geom = simplify_geometry(feat.get("geometry"))
        if geom is None:
            continue

        region_code = REGION_MAP.get(name, name)

        simplified.append({
            "type": "Feature",
            "id": region_code,
            "properties": {
                "name": name,
                "region_code": region_code,
            },
            "geometry": geom,
        })

    result = {"type": "FeatureCollection", "features": simplified}

    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, separators=(",", ":"))

    size_kb = OUT.stat().st_size / 1024
    print(f"  Simplified: {len(simplified)} features")
    print(f"  Saved to: {OUT}  ({size_kb:.0f} KB)")

    tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
