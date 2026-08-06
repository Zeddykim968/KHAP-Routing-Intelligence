from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.facility import FacilityResponse, FacilityListResponse, NearestListResponse
from app.services import facility_service

router = APIRouter(prefix="/facilities", tags=["Facilities"])


@router.get("", response_model=FacilityListResponse)
def list_facilities(
    skip:  int = Query(0,  ge=0,  description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    db: Session = Depends(get_db),
):
    """
    Return a paginated list of all healthcare facilities.
    """
    result = facility_service.get_facilities(db, skip=skip, limit=limit)
    return result


@router.get("/nearest", response_model=NearestListResponse)
def nearest_facilities(
    lon:           Optional[float] = Query(None, description="Origin longitude"),
    lat:           Optional[float] = Query(None, description="Origin latitude"),
    limit:         int             = Query(5, ge=1, le=20),
    facility_type: Optional[str]   = Query(None, description="Filter by facility type"),
    db: Session = Depends(get_db),
):
    """
    Find the N nearest facilities to a GPS coordinate.

    Requires `lon` and `lat`.  Uses PostGIS geography distance
    so results are in real-world metres.
    """
    if lon is None or lat is None:
        raise HTTPException(
            status_code=422,
            detail="Both `lon` and `lat` are required for nearest-facility search.",
        )

    facilities = facility_service.get_nearest_facilities(
        db, lon=lon, lat=lat, limit=limit, facility_type=facility_type
    )

    return {
        "resolved_location": {"lon": lon, "lat": lat},
        "facilities": facilities,
    }


@router.get("/{facility_id}", response_model=FacilityResponse)
def get_facility(facility_id: int, db: Session = Depends(get_db)):
    """
    Return full details for a single facility by ID.
    """
    facility = facility_service.get_facility_by_id(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail=f"Facility {facility_id} not found")
    return facility
