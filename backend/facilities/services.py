"""
Service layer: distance maths, opening-hours parsing, and the OSRM client.

- `haversine_m` powers nearest-facility ranking (works on SQLite and
  PostgreSQL alike).
- `is_open_now` interprets common OSM opening-hours strings.
- `get_route` talks to the OSRM routing engine and returns turn-by-turn
  steps ready for the frontend.
"""
from __future__ import annotations

import math
from datetime import datetime

import requests
from django.conf import settings
from django.utils import timezone

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


# ── OSRM routing client ───────────────────────────────────────────────────────

class NoRouteError(ValueError):
    """OSRM reports no routable path between the points (HTTP 404 to client)."""


class RoutingServiceError(RuntimeError):
    """OSRM is unreachable or returned an unexpected payload (HTTP 502)."""


_TURN_VERBS = {
    "turn": "Turn",
    "end of road": "Turn",
    "fork": "Keep {mod}",
    "continue": "Continue",
    "merge": "Merge",
    "on ramp": "Take the ramp",
    "off ramp": "Take the exit",
    "new name": "Continue",
    "roundabout": "Enter the roundabout",
    "rotary": "Enter the roundabout",
    "roundabout turn": "Turn",
    "notification": "Continue",
}


def _step_instruction(step: dict, is_last: bool) -> str:
    maneuver = step.get("maneuver", {})
    mtype = maneuver.get("type", "continue")
    modifier = maneuver.get("modifier", "")
    road = step.get("name") or ""
    onto = f" onto {road}" if road else ""

    if is_last or mtype == "arrive":
        return f"You have arrived at your destination{onto}" if road else "You have arrived at your destination"
    if mtype == "depart":
        return f"Head {modifier or 'out'}{onto}" if road else f"Head {modifier or 'out'}"
    if mtype in ("roundabout", "rotary"):
        exit_no = maneuver.get("exit")
        exit_part = f" and take exit {exit_no}" if exit_no else ""
        return f"Enter the roundabout{exit_part}{onto}"

    verb_tpl = _TURN_VERBS.get(mtype, "Continue")
    verb = verb_tpl.format(mod=modifier.replace("_", " ").capitalize()) if "{mod}" in verb_tpl else verb_tpl
    if modifier:
        verb = f"{verb} {modifier.replace('_', ' ')}"
    return f"{verb}{onto}" if road else verb


def _maneuver_icon_type(step: dict, is_last: bool) -> str:
    """Coarse icon class for the UI (straight / left / right / roundabout / arrive)."""
    if is_last:
        return "arrive"
    maneuver = step.get("maneuver", {})
    mtype = maneuver.get("type", "continue")
    modifier = maneuver.get("modifier", "") or ""
    if mtype in ("roundabout", "rotary"):
        return "roundabout"
    if modifier in ("left", "sharp left", "slight left"):
        return "left"
    if modifier in ("right", "sharp right", "slight right"):
        return "right"
    if modifier == "uturn":
        return "uturn"
    return "straight"


def get_route(
    start_lon: float,
    start_lat: float,
    end_lon: float,
    end_lat: float,
    profile: str = "driving",
) -> dict:
    """
    Call OSRM and return a normalised route payload:

    {distance_m, duration_s, route: [[lon, lat], …], steps: [...],
     start: {lon, lat}, end: {lon, lat}}

    Raises NoRouteError / RoutingServiceError on failure.
    """
    if profile not in ("driving", "walking", "cycling"):
        profile = "driving"

    url = (
        f"{settings.OSRM_URL}/route/v1/{profile}/"
        f"{start_lon},{start_lat};{end_lon},{end_lat}"
    )
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "true",
        "alternatives": "false",
    }

    try:
        resp = requests.get(url, params=params, timeout=12)
    except requests.RequestException as exc:
        raise RoutingServiceError(f"OSRM request failed: {exc}") from exc

    if resp.status_code != 200:
        raise RoutingServiceError(f"OSRM returned HTTP {resp.status_code}")

    try:
        data = resp.json()
    except ValueError as exc:
        raise RoutingServiceError("OSRM returned invalid JSON") from exc

    code = data.get("code", "")
    if code == "NoRoute":
        raise NoRouteError("No drivable route between the requested points")
    if code != "Ok":
        raise RoutingServiceError(f"OSRM error: {code} {data.get('message', '')}")

    route = data["routes"][0]
    legs = route.get("legs") or [{}]
    raw_steps = legs[0].get("steps") or []
    total = len(raw_steps)

    steps = []
    for i, step in enumerate(raw_steps):
        is_last = i == total - 1
        maneuver = step.get("maneuver", {})
        location = maneuver.get("location", [None, None])
        steps.append(
            {
                "index": i,
                "instruction": _step_instruction(step, is_last),
                "type": maneuver.get("type", "continue"),
                "icon": _maneuver_icon_type(step, is_last),
                "name": step.get("name") or "",
                "distance_m": step.get("distance", 0.0),
                "duration_s": step.get("duration", 0.0),
                "location": {"lon": location[0], "lat": location[1]},
            }
        )

    return {
        "distance_m": route.get("distance", 0.0),
        "duration_s": route.get("duration", 0.0),
        "route": route["geometry"]["coordinates"],  # [[lon, lat], …]
        "steps": steps,
        "profile": profile,
        "start": {"lon": start_lon, "lat": start_lat},
        "end": {"lon": end_lon, "lat": end_lat},
    }


def ping_osrm(timeout: float = 5.0) -> dict:
    """Lightweight reachability check used by the health endpoint."""
    try:
        resp = requests.get(
            f"{settings.OSRM_URL}/nearest/v1/driving/36.8219,-1.2921",
            timeout=timeout,
        )
        if resp.status_code == 200:
            return {"status": "ok", "url": settings.OSRM_URL}
        return {"status": "degraded", "http_status": resp.status_code}
    except requests.RequestException as exc:
        return {"status": "error", "detail": str(exc)}
