from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.facility import FacilityResponse
from app.services import facility_service

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=list[FacilityResponse])
def search(
    q:             Optional[str] = Query(None, description="Search term (name, type, or operator)"),
    facility_type: Optional[str] = Query(None, description="Filter by facility type, e.g. hospital"),
    operator:      Optional[str] = Query(None, description="Filter by operator / owner"),
    limit:         int           = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Search facilities by name, type, or operator.

    All parameters are optional and are ANDed together when provided.

    Examples
    --------
    - `/search?q=Nairobi`
    - `/search?facility_type=hospital`
    - `/search?operator=government&facility_type=clinic`
    """
    return facility_service.search_facilities(
        db,
        q=q,
        facility_type=facility_type,
        operator=operator,
        limit=limit,
    )
