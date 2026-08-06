from typing import Optional
from pydantic import BaseModel


class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat:   float
    end_lon:   float


class RouteResponse(BaseModel):
    """
    OSRM route result.

    `route` is a GeoJSON LineString geometry (list of [lon, lat] pairs)
    suitable for drawing directly on a Leaflet or MapLibre map.
    """
    distance_m:  float
    duration_s:  float
    route:       list[list[float]]   # [[lon, lat], ...]
    start:       Optional[dict] = None
    end:         Optional[dict] = None
