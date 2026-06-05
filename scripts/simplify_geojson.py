"""
Aggressively simplify the saved ph_regions.geojson to < 300KB.
Reads data/ph_regions.geojson, writes data/ph_regions_simple.geojson.
Run: python scripts/simplify_geojson.py
"""

import json
from pathlib import Path

SRC = Path("data/ph_regions.geojson")
OUT = Path("data/ph_regions_simple.geojson")
PRECISION = 2       # 0.01 deg ≈ 1 km — enough for a regional overview map
STEP = 8            # keep every Nth coordinate point
# MIN_AREA is only applied to sub-polygons within MultiPolygon features
# (removes tiny islets) but the LARGEST polygon per feature is ALWAYS kept.
# NCR (Metro Manila) is ~0.003 sq degrees — previous 0.04 threshold deleted it entirely.
MIN_SUBPOLY_AREA = 0.01


def ring_area(ring):
    n = len(ring)
    if n < 3:
        return 0
    area = 0
    for i in range(n):
        j = (i + 1) % n
        area += ring[i][0] * ring[j][1]
        area -= ring[j][0] * ring[i][1]
    return abs(area) / 2


def thin(ring):
    """Keep every STEP-th point plus always keep first and last."""
    if len(ring) <= 10:
        return ring
    thinned = ring[::STEP]
    if thinned[-1] != ring[-1]:
        thinned.append(ring[-1])
    return thinned


def round_ring(ring):
    return [[round(c, PRECISION) for c in pt] for pt in ring]


def simplify_geometry(geom):
    if geom is None:
        return None
    gtype = geom["type"]

    if gtype == "Polygon":
        rings = [round_ring(thin(r)) for r in geom["coordinates"] if len(r) >= 4]
        return {"type": "Polygon", "coordinates": rings} if rings else None

    if gtype == "MultiPolygon":
        # Score each polygon by its outer ring area
        scored = []
        for poly in geom["coordinates"]:
            rings = [round_ring(thin(r)) for r in poly if len(r) >= 4]
            if rings:
                scored.append((ring_area(rings[0]), rings))

        if not scored:
            return None

        # Always keep the largest polygon (prevents deleting tiny regions like NCR)
        scored.sort(key=lambda x: x[0], reverse=True)
        polys = [rings for area, rings in scored
                 if area >= MIN_SUBPOLY_AREA or area == scored[0][0]]

        return {"type": "MultiPolygon", "coordinates": polys} if polys else None

    return geom


def main():
    print(f"Reading {SRC} ({SRC.stat().st_size / 1024:.0f} KB)...")
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)

    # Print first feature's properties so we know the field names
    if data["features"]:
        print("Sample properties:", data["features"][0].get("properties"))

    # Fix region codes that didn't map correctly
    code_overrides = {
        "Metropolitan Manila":                          "NCR",
        "Autonomous Region of Muslim Mindanao (ARMM)":  "BARMM",
        "Caraga (Region XIII)":                         "Region XIII",
    }

    simplified = []
    for feat in data["features"]:
        geom = simplify_geometry(feat.get("geometry"))
        if geom is None:
            continue
        props = feat.get("properties", {})
        name = props.get("name", "")
        region_code = code_overrides.get(name, props.get("region_code", name))
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
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, separators=(",", ":"))

    print(f"Simplified: {len(simplified)} features")
    print(f"Saved: {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
