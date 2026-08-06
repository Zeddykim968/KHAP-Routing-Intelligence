"""
GET /facilities/nearest -- pulls from BOTH pools: routing DB to
resolve free-text (`q=`) into coordinates, facilities DB (Supabase)
for the actual nearest-facility + insurance-filter query.

GET /insurance-providers -- reads insurance_providers directly from
the facilities DB, so it always matches what's actually seeded there.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_facilities_pool, get_routing_pool
from app.models.schemas import FacilitySearchResponse
from app.services.search_service import get_insurance_providers, search_nearest_facilities

router = APIRouter(prefix="/facilities", tags=["search"])


@router.get("/nearest", response_model=FacilitySearchResponse)
async def nearest_facilities(
    lon: float | None = Query(None, description="Longitude, for coordinate search"),
    lat: float | None = Query(None, description="Latitude, for coordinate search"),
    q: str | None = Query(None, description="Free-text location, e.g. 'Kilimani, Nairobi'"),
    insurance: str | None = Query(None, description="Comma-separated providers, e.g. 'SHA,AAR'"),
    limit: int = Query(3, ge=3, le=20, description="Minimum 3 recommendations"),
    routing_pool=Depends(get_routing_pool),
    facilities_pool=Depends(get_facilities_pool),
):
    if (lon is None or lat is None) and not q:
        raise HTTPException(400, "Provide either lon & lat, or a text query 'q'")

    insurance_list = [p.strip() for p in insurance.split(",")] if insurance else None
    return await search_nearest_facilities(
        routing_pool, facilities_pool, lon, lat, q, limit, insurance_list
    )


@router.get("/insurance-providers")
async def insurance_providers(facilities_pool=Depends(get_facilities_pool)):
    return {"providers": await get_insurance_providers(facilities_pool)}
