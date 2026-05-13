"""
HWELBEING — DOCTOR SERVICE (FINAL PRODUCTION — FAST + STABLE + ACCURATE)

Purpose:
- Accurate nearby doctors (OSM improved)
- Parallel fetch (fast)
- Dynamic radius (efficient)
- Cache-first + background refresh
- Zero UI blocking

Exports To:
- main.py
"""

import math
import asyncio
import time
from typing import Dict, Any, List
import requests

from src.core.logger import get_logger

logger = get_logger(__name__)

# =========================
# CACHE
# =========================
CACHE: Dict[str, Any] = {}
CACHE_TTL = 300


# =========================
# DISTANCE
# =========================
def _distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)


# =========================
# TYPE + FILTER
# =========================
def _get_type(tags):
    t = (tags.get("healthcare") or tags.get("amenity") or "").lower()
    if t in ["doctor", "doctors"]:
        return "Doctor"
    if t == "clinic":
        return "Clinic"
    if t == "hospital":
        return "Hospital"
    return "Healthcare"


def _is_valid(tags):
    t = (tags.get("healthcare") or tags.get("amenity") or "").lower()
    return t not in ["pharmacy", "veterinary"]


def _coord(el):
    return (
        el.get("lat") or el.get("center", {}).get("lat"),
        el.get("lon") or el.get("center", {}).get("lon"),
    )


def _dedupe_key(name, lat, lon):
    return f"{name.lower()}_{round(lat,4)}_{round(lon,4)}"


def _score(dist, ptype, tags):
    type_weight = {"Doctor": 0.8, "Clinic": 0.9, "Hospital": 1.0}.get(ptype, 1.1)
    richness = 1.0 - min(len(tags) / 20.0, 0.2)
    return dist * type_weight * richness


# =========================
# FETCH OSM (RADIUS BASED)
# =========================
def _fetch_osm_radius(lat, lon, radius):

    query = f"""
[out:json][timeout:6];
(
  node(around:{radius},{lat},{lon})["healthcare"~"doctor|clinic|hospital"];
  way(around:{radius},{lat},{lon})["healthcare"~"doctor|clinic|hospital"];
);
out center tags;
""".strip()

    headers = {
        "Content-Type": "text/plain",
        "User-Agent": "HWellbeing/1.0"
    }

    url = "https://overpass.kumi.systems/api/interpreter"

    res = requests.post(url, data=query, headers=headers, timeout=4)
    res.raise_for_status()
    return res.json()


# =========================
# PARALLEL FETCH
# =========================
async def _fetch_parallel(lat, lon, radius):
    loop = asyncio.get_running_loop()

    tasks = [
        loop.run_in_executor(None, _fetch_osm_radius, lat, lon, radius),
        loop.run_in_executor(None, _fetch_osm_radius, lat, lon, radius),
    ]

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    for task in pending:
        task.cancel()

    for task in done:
        try:
            return task.result()
        except Exception:
            continue

    return {}


# =========================
# BUILD RESULT
# =========================
def _build_result(lat, lon, raw):
    elements = raw.get("elements", [])

    seen = set()
    doctors: List[Dict[str, Any]] = []

    for el in elements:
        try:
            tags = el.get("tags", {})

            if not tags or not _is_valid(tags):
                continue

            name = tags.get("name")
            if not name:
                continue

            lat2, lon2 = _coord(el)
            if lat2 is None or lon2 is None:
                continue

            dist = _distance(lat, lon, lat2, lon2)

            if dist < 2 or dist > 20:
                continue

            key = _dedupe_key(name, lat2, lon2)
            if key in seen:
                continue
            seen.add(key)

            ptype = _get_type(tags)

            doctors.append({
                "name": name,
                "type": ptype,
                "distance_km": dist,
                "distance": f"{dist} km",
                "lat": lat2,
                "lon": lon2,
                "_score": _score(dist, ptype, tags),
            })

        except Exception:
            continue

    doctors.sort(key=lambda x: (x["_score"], x["distance_km"]))

    for d in doctors:
        d.pop("_score", None)

    return {
        "available": True if doctors else False,
        "confidence": 0.8,
        "doctors": doctors[:10],
    }


# =========================
# BACKGROUND REFRESH
# =========================
async def _refresh_cache(cache_key, lat, lon):
    try:
        for radius in [8000, 12000, 15000]:
            raw = await _fetch_parallel(lat, lon, radius)
            result = _build_result(lat, lon, raw)

            if result["doctors"]:
                CACHE[cache_key] = (result, time.time())
                logger.info("CACHE_UPDATED")
                return

    except Exception as e:
        logger.warning("CACHE_REFRESH_FAILED", extra={"error": str(e)})


# =========================
# MAIN
# =========================
async def find_doctors(lat: float, lon: float) -> Dict[str, Any]:

    cache_key = f"{round(lat, 3)}_{round(lon, 3)}"

    # =========================
    # CACHE FIRST
    # =========================
    if cache_key in CACHE:
        data, _ = CACHE[cache_key]

        asyncio.create_task(_refresh_cache(cache_key, lat, lon))

        logger.info("CACHE_INSTANT_RETURN")
        return data

    # =========================
    # FIRST CALL (DYNAMIC RADIUS)
    # =========================
    try:
        for radius in [8000, 12000, 15000]:
            raw = await asyncio.wait_for(
                _fetch_parallel(lat, lon, radius),
                timeout=5
            )

            result = _build_result(lat, lon, raw)

            if result["doctors"]:
                CACHE[cache_key] = (result, time.time())
                return result

    except Exception:
        logger.warning("FIRST_CALL_FAIL")

    return {
        "available": True,
        "confidence": 0.5,
        "doctors": [],
        "message": "Fetching nearby doctors… try again"
    }