"""
Pydantic request/response shapes for /route and /facilities/nearest.
"""
from pydantic import BaseModel
from uuid import UUID

class RouteRequest(BaseModel):
    start_lon: float
    start_lat: float
    end_lon: float
    end_lat: float


class RouteResponse(BaseModel):
    route: dict          # GeoJSON LineString, ready for react-leaflet
    distance_m: float
    edge_count: int


class FacilityResult(BaseModel):
    facility_id: UUID
    name: str
    facility_type: str
    lon: float
    lat: float
    distance_m: float
    insurance_accepted: list[str] = []


class ResolvedLocation(BaseModel):
    matched_name: str
    lon: float
    lat: float


class FacilitySearchResponse(BaseModel):
    resolved_location: ResolvedLocation | None = None
    facilities: list[FacilityResult]
