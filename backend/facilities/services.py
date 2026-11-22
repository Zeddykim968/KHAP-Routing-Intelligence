"""
Service layer: distance maths, opening-hours parsing, and the OpenRouteService client.

- `haversine_m` is straight-line distance, used only to annotate the plain
  facility list and to pre-select candidate facilities for the ORS matrix.
  It is never used to rank or to produce a route.
- `is_open_now` interprets common OSM opening-hours strings.
- `ors_matrix` asks OpenRouteService for real road distance/duration from the
  user to a batch of facilities, which is what the nearest-facility endpoint
  ranks by.
- `get_route` returns turn-by-turn directions from OpenRouteService.

There is no fallback engine: every routing/distance failure raises
`RoutingServiceError` (or `NoRouteError` when ORS reports no path).
"""
from __future__ import annotations

import logging
import math
import time
from datetime import datetime

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# ── Distance ──────────────────────────────────────────────────────────────────

EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two WGS84 points, in metres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def in_kenya(lat: float, lon: float) -> bool:
    b = settings.KENYA_BOUNDS
    return b["lat_min"] <= lat <= b["lat_max"] and b["lon_min"] <= lon <= b["lon_max"]


# ── Opening hours ─────────────────────────────────────────────────────────────

_DAY_INDEX = {"mo": 0, "tu": 1, "we": 2, "th": 3, "fr": 4, "sa": 5, "su": 6}
_MINUTES_PER_DAY = 24 * 60


def _expand_days(part: str) -> set[int] | None:
    """Expand an OSM day spec such as `Mo-Fr`, `Sa`, `Mo,We,Fr`."""
    days: set[int] = set()
    for token in part.split(","):
        token = token.strip().lower()
        if not token:
            continue
        if token == "ph":  # public holidays — unknown, skip rule
            continue
        if "-" in token:
            start_s, end_s = token.split("-", 1)
            start, end = _DAY_INDEX.get(start_s), _DAY_INDEX.get(end_s)
            if start is None or end is None:
                return None
            if start <= end:
                days.update(range(start, end + 1))
            else:  # wraps the week, e.g. Fr-Mo
                days.update(range(start, 7))
                days.update(range(0, end + 1))
        else:
            idx = _DAY_INDEX.get(token)
            if idx is None:
                return None
            days.add(idx)
    return days or None


def _to_minutes(value: str) -> int | None:
    """`"08:30"` → 510. `"24:00"` → 1440."""
    value = value.strip()
    try:
        hh, mm = value.split(":", 1)
        h, m = int(hh), int(mm)
    except ValueError:
        return None
    if 0 <= h <= 24 and 0 <= m < 60:
        return min(h * 60 + m, _MINUTES_PER_DAY)
    return None


def is_open_now(opening_hours: str | None, now: datetime | None = None) -> bool | None:
    """
    Parse a common OSM opening-hours string.

    Returns True (open), False (closed), or None (cannot be determined).
    """
    text = (opening_hours or "").strip()
    if not text:
        return None

    lowered = text.lower()
    if lowered in ("24/7", "open", "mo-su 00:00-24:00"):
        return True
    if lowered in ("closed", "off"):
        return False

    now = now or timezone.localtime()
    today = now.weekday()
    minute_of_day = now.hour * 60 + now.minute

    for raw_rule in text.split(";"):
        rule = raw_rule.strip()
        if not rule:
            continue
        # Drop trailing "off" / "closed" annotations.
        for suffix in (" off", " closed"):
            if rule.lower().endswith(suffix):
                rule = rule[: -len(suffix)].strip()
        if not rule:
            continue
        if rule.lower() == "24/7":
            return True

        if " " in rule:
            day_part, time_part = rule.split(" ", 1)
        elif ":" in rule:
            day_part, time_part = "Mo-Su", rule
        else:
            continue

        days = _expand_days(day_part)
        if not days or today not in days:
            continue

        for span in time_part.split(","):
            if "-" not in span:
                continue
            start_s, end_s = span.split("-", 1)
            start = _to_minutes(start_s)
            end = _to_minutes(end_s)
            if start is None or end is None:
                continue
            if end <= start:  # overnight range e.g. 18:00-06:00 → until midnight
                end = _MINUTES_PER_DAY
            if start <= minute_of_day < end:
                return True
    return False


# ── Errors ────────────────────────────────────────────────────────────────────

class NoRouteError(ValueError):
    """The routing engine reports no path between the points (HTTP 404 to client)."""


class RoutingServiceError(RuntimeError):
    """OpenRouteService is unreachable, unconfigured, or returned an unexpected payload (HTTP 502)."""


# ── OpenRouteService client ───────────────────────────────────────────────────

# Public profile names used by the API ↔ ORS profile ids.
ORS_PROFILE_MAP = {
    "driving": "driving-car",
    "driving-car": "driving-car",
    "walking": "foot-walking",
    "foot-walking": "foot-walking",
    "cycling": "cycling-regular",
    "cycling-regular": "cycling-regular",
    "wheelchair": "wheelchair",
}


def ors_available() -> bool:
    """True when an OpenRouteService API key is configured."""
    return bool(getattr(settings, "ORS_API_KEY", ""))


def ors_profile_id(profile: str | None = None) -> str:
    """Map a public profile name (`driving`, `walking`, …) to an ORS profile id."""
    return ORS_PROFILE_MAP.get((profile or "").strip().lower(), settings.ORS_PROFILE)


def _ors_post(path: str, payload: dict, timeout: float | None = None) -> dict:
    """POST to OpenRouteService and return the decoded JSON, or raise."""
    key = settings.ORS_API_KEY
    if not key:
        raise RoutingServiceError(
            "OpenRouteService API key is not configured — set ORS_API_KEY"
        )

    try:
        resp = requests.post(
            f"{settings.ORS_URL}{path}",
            json=payload,
            headers={
                "Authorization": key,
                "Content-Type": "application/json",
                "Accept": "application/json, application/geo+json",
            },
            timeout=timeout or settings.ORS_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise RoutingServiceError(f"OpenRouteService request failed: {exc}") from exc

    if resp.status_code == 200:
        try:
            return resp.json()
        except ValueError as exc:
            raise RoutingServiceError("OpenRouteService returned invalid JSON") from exc

    detail = ""
    try:
        error = resp.json().get("error") or {}
        detail = error.get("message") or ""
    except ValueError:
        pass

    if resp.status_code == 404:
        raise NoRouteError(
            detail or "OpenRouteService could not find a routable path between the points"
        )
    suffix = f": {detail}" if detail else ""
    raise RoutingServiceError(
        f"OpenRouteService returned HTTP {resp.status_code}{suffix}"
    )


def ors_matrix(
    origin_lat: float,
    origin_lon: float,
    destinations: list[tuple[float, float]],
    profile: str | None = None,
) -> list[dict]:
    """
    Road distance and duration from `(origin_lat, origin_lon)` to each
    `(lat, lon)` destination, using the ORS Matrix API.

    Returns `[{"index": i, "distance_m": m|None, "duration_s": s|None}, …]`
    in the same order as `destinations`; unroutable points come back as None.
    Raises NoRouteError / RoutingServiceError on failure.
    """
    if not destinations:
        return []

    profile_id = ors_profile_id(profile)
    batch_size = settings.ORS_MATRIX_BATCH
    results: list[dict] = []

    for start in range(0, len(destinations), batch_size):
        batch = destinations[start : start + batch_size]
        locations = [[origin_lon, origin_lat]] + [
            [lon, lat] for lat, lon in batch
        ]
        payload = {
            "locations": locations,
            "sources": [0],
            "destinations": list(range(1, len(locations))),
            "metrics": ["distance", "duration"],
            "units": "m",
        }
        data = _ors_post(f"/v2/matrix/{profile_id}", payload)

        distances = (data.get("distances") or [[]])[0]
        durations = (data.get("durations") or [[]])[0]
        for offset in range(len(batch)):
            results.append(
                {
                    "index": start + offset,
                    "distance_m": distances[offset] if offset < len(distances) else None,
                    "duration_s": durations[offset] if offset < len(durations) else None,
                }
            )

    return results


_ORS_STEP_ICONS = {
    0: "left",
    1: "right",
    2: "left",       # sharp left
    3: "right",      # sharp right
    4: "left",       # slight left
    5: "right",      # slight right
    6: "straight",
    7: "roundabout",
    8: "roundabout",
    9: "uturn",
    10: "arrive",
    11: "straight",  # depart
    12: "straight",  # keep left
    13: "straight",  # keep right
}


def _ors_route(
    start_lon: float,
    start_lat: float,
    end_lon: float,
    end_lat: float,
    profile: str = "driving",
) -> dict:
    """Directions via the ORS Directions API, normalised to the API payload."""
    profile_id = ors_profile_id(profile)
    data = _ors_post(
        f"/v2/directions/{profile_id}/geojson",
        {
            "coordinates": [[start_lon, start_lat], [end_lon, end_lat]],
            "instructions": True,
            "language": "en",
            "units": "m",
        },
    )

    features = data.get("features") or []
    if not features:
        raise NoRouteError("No route found between the requested points")

    feature = features[0]
    geometry = feature.get("geometry") or {}
    coordinates = geometry.get("coordinates") or []
    if len(coordinates) < 2:
        raise NoRouteError("No route found between the requested points")

    properties = feature.get("properties") or {}
    summary = properties.get("summary") or {}
    segments = properties.get("segments") or []

    raw_steps = [step for segment in segments for step in (segment.get("steps") or [])]
    steps = []
    for i, step in enumerate(raw_steps):
        is_last = i == len(raw_steps) - 1
        icon = _ORS_STEP_ICONS.get(step.get("type"), "straight")
        if is_last:
            icon = "arrive"

        way_points = step.get("way_points") or []
        point = None
        if way_points and 0 <= way_points[0] < len(coordinates):
            point = coordinates[way_points[0]]

        instruction = (step.get("instruction") or "").strip()
        if is_last and not instruction:
            instruction = "You have arrived at your destination"

        steps.append(
            {
                "index": i,
                "instruction": instruction,
                "type": step.get("type"),
                "icon": icon,
                "name": step.get("name") or "",
                "distance_m": step.get("distance", 0.0),
                "duration_s": step.get("duration", 0.0),
                "location": {"lon": point[0], "lat": point[1]} if point else None,
            }
        )

    distance = summary.get("distance")
    duration = summary.get("duration")
    if distance is None:
        distance = sum(step.get("distance_m") or 0 for step in steps)
    if duration is None:
        duration = sum(step.get("duration_s") or 0 for step in steps)

    return {
        "distance_m": distance,
        "duration_s": duration,
        "route": coordinates,  # [[lon, lat], …]
        "steps": steps,
        "profile": profile,
        "engine": "openrouteservice",
        "start": {"lon": start_lon, "lat": start_lat},
        "end": {"lon": end_lon, "lat": end_lat},
    }


# ── Nearest-facility ranking (ORS travel matrix) ─────────────────────────────

def rank_facilities_by_travel(
    lat: float,
    lon: float,
    facilities: list,
    profile: str | None = None,
) -> tuple[list, dict]:
    """
    Rank candidate facilities by real travel distance from `(lat, lon)`.

    Each facility gets `travel_distance_m` and `travel_duration_s` from the ORS
    matrix. Every ORS failure is raised to the caller — there is no
    straight-line ranking fallback. Facilities ORS cannot route to are omitted
    (they have no road route) and counted in the returned metadata.
    """
    meta = {
        "engine": "openrouteservice",
        "profile": ors_profile_id(profile),
        "travel_distances": True,
    }
    facilities = list(facilities)
    if not facilities:
        meta["routed_count"] = 0
        return [], meta

    destinations = [(f.latitude, f.longitude) for f in facilities]
    matrix = ors_matrix(lat, lon, destinations, profile=profile)

    routed: list = []
    for index, facility in enumerate(facilities):
        row = matrix[index] if index < len(matrix) else {}
        distance = row.get("distance_m")
        if distance is None:
            continue
        facility.travel_distance_m = distance
        facility.travel_duration_s = row.get("duration_s")
        routed.append(facility)

    unrouted_count = len(facilities) - len(routed)
    if not routed:
        raise NoRouteError(
            "OpenRouteService could not route to any candidate facility from this location"
        )

    routed.sort(key=lambda f: f.travel_distance_m)

    meta["routed_count"] = len(routed)
    if unrouted_count:
        meta["unrouted_count"] = unrouted_count
        meta["note"] = (
            f"{unrouted_count} facility(ies) have no road route from this "
            "location and were omitted."
        )
        logger.info("ORS matrix left %s candidates unrouted", unrouted_count)

    return routed, meta


def get_route(
    start_lon: float,
    start_lat: float,
    end_lon: float,
    end_lat: float,
    profile: str = "driving",
) -> dict:
    """
    Road route between two points via OpenRouteService.

    Raises NoRouteError / RoutingServiceError on failure; there is no fallback
    routing engine.
    """
    if profile not in ("driving", "walking", "cycling", "wheelchair"):
        profile = "driving"
    return _ors_route(start_lon, start_lat, end_lon, end_lat, profile=profile)


_ORS_PING_TTL_S = 300
_ors_ping_cache: dict = {"at": 0.0, "result": None}


def ping_ors(timeout: float = 8.0) -> dict:
    """
    OpenRouteService reachability/credential check for the health endpoint.

    A tiny two-point matrix request is used (ORS has no public health route)
    and the result is cached briefly so health polling does not burn quota.
    """
    if not ors_available():
        return {"status": "not_configured", "note": "Set ORS_API_KEY to enable OpenRouteService"}

    now = time.monotonic()
    cached = _ors_ping_cache.get("result")
    if cached and now - _ors_ping_cache.get("at", 0.0) < _ORS_PING_TTL_S:
        return cached

    try:
        _ors_post(
            f"/v2/matrix/{settings.ORS_PROFILE}",
            {
                "locations": [[36.8219, -1.2921], [36.8150, -1.2900]],
                "sources": [0],
                "destinations": [1],
                "metrics": ["distance"],
                "units": "m",
            },
            timeout=timeout,
        )
        result = {"status": "ok", "url": settings.ORS_URL, "profile": settings.ORS_PROFILE}
    except NoRouteError as exc:
        result = {"status": "ok", "url": settings.ORS_URL, "note": str(exc)}
    except RoutingServiceError as exc:
        result = {"status": "error", "detail": str(exc)}

    _ors_ping_cache.update({"at": now, "result": result})
    return result
