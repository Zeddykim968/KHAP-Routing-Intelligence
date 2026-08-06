"""
POST /route -- entirely within the routing DB (roads, vertices,
pgRouting). No facilities DB involved.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_routing_pool
from app.models.schemas import RouteRequest, RouteResponse
from app.services.routing_service import get_shortest_route

router = APIRouter(prefix="/route", tags=["routing"])


@router.post("", response_model=RouteResponse)
async def compute_route(req: RouteRequest, pool=Depends(get_routing_pool)):
    result = await get_shortest_route(
        pool, req.start_lon, req.start_lat, req.end_lon, req.end_lat
    )
    if result is None:
        raise HTTPException(
            404,
            "No route found between these points -- they may be in "
            "disconnected parts of the road network.",
        )
    return result
