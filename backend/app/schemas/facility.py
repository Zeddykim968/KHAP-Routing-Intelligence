from typing import Optional
from pydantic import BaseModel


class FacilityBase(BaseModel):
    id:            int
    name:          Optional[str] = None
    facility_type: Optional[str] = None
    operator:      Optional[str] = None
    phone:         Optional[str] = None
    website:       Optional[str] = None
    emergency:     Optional[str] = None
    opening_hours: Optional[str] = None
    wheelchair:    Optional[str] = None
    lat:           float
    lon:           float


class FacilityResponse(FacilityBase):
    """Returned for individual facility lookups and list endpoints."""

    class Config:
        from_attributes = True


class NearestFacilityResponse(FacilityBase):
    """Returned by /facilities/nearest — includes distance from search origin."""
    distance_m: float

    class Config:
        from_attributes = True


class FacilityListResponse(BaseModel):
    total:      int
    facilities: list[FacilityResponse]


class NearestListResponse(BaseModel):
    resolved_location: Optional[dict] = None
    facilities:        list[NearestFacilityResponse]
