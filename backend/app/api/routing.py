from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.route import RouteRequest, RouteResponse
from app.services import routing_service

router = APIRouter(prefix="/route", tags=["Routing"])


@router.post("", response_model=RouteResponse)
def get_route(payload: RouteRequest, db: Session = Depends(get_db)):
    """
    Calculate a driving route between two GPS coordinates using OSRM.

    Input
    -----
    - start_lat, start_lon  — origin (WGS84)
    - end_lat,   end_lon    — destination (WGS84)

    Output
    ------
    - distance_m  — total route distance in metres
    - duration_s  — estimated travel time in seconds
    - route       — GeoJSON LineString coordinates [[lon, lat], ...]

    Returns 404 when OSRM finds no path between the two points
    (e.g. disconnected road graph segments).
    """
    try:
        result = routing_service.calculate_route(
            db,
            start_lon=payload.start_lon,
            start_lat=payload.start_lat,
            end_lon=payload.end_lon,
            end_lat=payload.end_lat,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
