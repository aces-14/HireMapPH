"""
Philippine geocoder.
Strategy: hardcoded lookup for all major PH employment hubs first,
geopy Nominatim as fallback for anything not in the table.

Why hardcoded: Generic geocoders mishandle PH aliases like "BGC",
"Fort Bonifacio", "Ortigas", "NCR", etc. The handcrafted table is
more accurate for this domain and costs nothing.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Optional

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# canonical_name → (lat, lng, region)
PH_CITY_LOOKUP: dict[str, tuple[float, float, str]] = {
    # NCR
    "manila": (14.5995, 120.9842, "NCR"),
    "quezon city": (14.6760, 121.0437, "NCR"),
    "makati": (14.5547, 121.0244, "NCR"),
    "bgc": (14.5509, 121.0486, "NCR"),
    "bonifacio global city": (14.5509, 121.0486, "NCR"),
    "fort bonifacio": (14.5209, 121.0509, "NCR"),
    "taguig": (14.5243, 121.0792, "NCR"),
    "pasig": (14.5764, 121.0851, "NCR"),
    "ortigas": (14.5876, 121.0603, "NCR"),
    "mandaluyong": (14.5794, 121.0359, "NCR"),
    "san juan": (14.6019, 121.0355, "NCR"),
    "marikina": (14.6507, 121.1029, "NCR"),
    "pasay": (14.5378, 120.9970, "NCR"),
    "paranaque": (14.4793, 121.0198, "NCR"),
    "las pinas": (14.4453, 120.9833, "NCR"),
    "muntinlupa": (14.4081, 121.0415, "NCR"),
    "caloocan": (14.6488, 120.9664, "NCR"),
    "malabon": (14.6628, 120.9571, "NCR"),
    "navotas": (14.6667, 120.9417, "NCR"),
    "valenzuela": (14.6942, 120.9900, "NCR"),
    "novaliches": (14.7148, 121.0341, "NCR"),
    "eastwood": (14.6097, 121.0810, "NCR"),
    "alabang": (14.4200, 121.0400, "NCR"),
    "metro manila": (14.5995, 120.9842, "NCR"),
    "ncr": (14.5995, 120.9842, "NCR"),
    "national capital region": (14.5995, 120.9842, "NCR"),

    # Region III — Central Luzon
    "angeles city": (15.1450, 120.5887, "Region III"),
    "clark": (15.1857, 120.5603, "Region III"),
    "san fernando pampanga": (15.0289, 120.6900, "Region III"),
    "olongapo": (14.8385, 120.2840, "Region III"),
    "malolos": (14.8527, 120.8108, "Region III"),
    "balanga": (14.6752, 120.5383, "Region III"),

    # Region IV-A — CALABARZON
    "antipolo": (14.6286, 121.1764, "Region IV-A"),
    "cainta": (14.5778, 121.1228, "Region IV-A"),
    "taytay": (14.5567, 121.1328, "Region IV-A"),
    "binan": (14.3419, 121.0820, "Region IV-A"),
    "santa rosa": (14.3122, 121.1114, "Region IV-A"),
    "cabuyao": (14.2741, 121.1244, "Region IV-A"),
    "calamba": (14.2116, 121.1653, "Region IV-A"),
    "lucena": (13.9373, 121.6170, "Region IV-A"),
    "batangas city": (13.7565, 121.0584, "Region IV-A"),
    "lipa": (13.9411, 121.1636, "Region IV-A"),

    # Region VII — Central Visayas
    "cebu city": (10.3157, 123.8854, "Region VII"),
    "cebu": (10.3157, 123.8854, "Region VII"),
    "mandaue": (10.3236, 123.9223, "Region VII"),
    "lapu-lapu": (10.3103, 123.9494, "Region VII"),
    "talisay cebu": (10.2447, 123.8494, "Region VII"),

    # Region XI — Davao
    "davao city": (7.1907, 125.4553, "Region XI"),
    "davao": (7.1907, 125.4553, "Region XI"),

    # Region X — Northern Mindanao
    "cagayan de oro": (8.4822, 124.6472, "Region X"),
    "cdo": (8.4822, 124.6472, "Region X"),

    # Region VI — Western Visayas
    "iloilo city": (10.7202, 122.5621, "Region VI"),
    "iloilo": (10.7202, 122.5621, "Region VI"),
    "bacolod": (10.6765, 122.9509, "Region VI"),

    # Region I — Ilocos
    "dagupan": (16.0430, 120.3328, "Region I"),
    "san fernando la union": (16.6159, 120.3166, "Region I"),

    # CAR
    "baguio": (16.4023, 120.5960, "CAR"),
    "baguio city": (16.4023, 120.5960, "CAR"),

    # Remote / nationwide
    "remote": (12.8797, 121.7740, "Remote"),
    "work from home": (12.8797, 121.7740, "Remote"),
    "wfh": (12.8797, 121.7740, "Remote"),
    "nationwide": (12.8797, 121.7740, "Nationwide"),
    "philippines": (12.8797, 121.7740, "Nationwide"),
}

# Aliases that map to canonical keys
ALIASES: dict[str, str] = {
    "bgc": "bgc",
    "bonifacio global city": "bgc",
    "fort bonifacio": "fort bonifacio",
    "ortigas center": "ortigas",
    "ortigas centre": "ortigas",
    "eastwood city": "eastwood",
    "alabang muntinlupa": "alabang",
    "paranaque city": "paranaque",
    "las piñas": "las pinas",
    "las piñas": "las pinas",
    "quezon city metro manila": "quezon city",
    "qc": "quezon city",
    "makati city": "makati",
    "taguig city": "taguig",
    "pasig city": "pasig",
    "mandaluyong city": "mandaluyong",
    "cebu city cebu": "cebu city",
    "davao city davao del sur": "davao city",
    "cagayan de oro city": "cagayan de oro",
    "clark freeport zone": "clark",
    "clark special economic zone": "clark",
    "angeles": "angeles city",
}

_geolocator = Nominatim(user_agent="hiremap_ph_pipeline")


def _normalize(raw: str) -> str:
    text = raw.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[,/|].*", "", text).strip()
    return text


@lru_cache(maxsize=512)
def _nominatim_lookup(normalized: str) -> Optional[tuple[float, float]]:
    try:
        location = _geolocator.geocode(
            f"{normalized}, Philippines", timeout=5
        )
        if location:
            return (location.latitude, location.longitude)
    except Exception:
        # Catch all network/service errors — Nominatim is a best-effort fallback
        pass
    return None


def geocode(location_raw: str) -> dict:
    """
    Returns dict with keys: city, lat, lng, region.
    Falls back gracefully — never raises.
    """
    if not location_raw or not location_raw.strip():
        return {"city": None, "lat": None, "lng": None, "region": None}

    normalized = _normalize(location_raw)

    # Resolve aliases first
    canonical_key = ALIASES.get(normalized, normalized)

    if canonical_key in PH_CITY_LOOKUP:
        lat, lng, region = PH_CITY_LOOKUP[canonical_key]
        return {
            "city": canonical_key.title(),
            "lat": lat,
            "lng": lng,
            "region": region,
        }

    # Partial match — check if any known city name is a substring
    for key, (lat, lng, region) in PH_CITY_LOOKUP.items():
        if key in normalized or normalized in key:
            return {
                "city": key.title(),
                "lat": lat,
                "lng": lng,
                "region": region,
            }

    # Fallback to Nominatim
    coords = _nominatim_lookup(normalized)
    if coords:
        return {
            "city": location_raw.strip().title(),
            "lat": coords[0],
            "lng": coords[1],
            "region": "Unknown",
        }

    return {"city": location_raw.strip().title(), "lat": None, "lng": None, "region": "Unknown"}
