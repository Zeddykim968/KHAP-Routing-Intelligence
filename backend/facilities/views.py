"""
Facilities API views.

Endpoints
---------
GET  /api/health/               app + database + OSRM health check
GET  /api/meta/                 filter metadata (types, services, insurers)
GET  /api/facilities/           list/filter facilities (q, type, service, insurance…)
GET  /api/facilities/nearest/   N nearest facilities to a GPS point
GET  /api/facilities/{id}/      full detail for one facility
GET  /api/search/               quick text search with optional distance
POST /api/route/                OSRM route: geometry + turn-by-turn steps
"""
from __future__ import annotations

from django.db import connection
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, mixins

from facilities import services
from facilities.models import Facility, Insurance, Service
from facilities.serializers import (
    FacilityBriefSerializer,
    FacilitySerializer,
    InsuranceSerializer,
    ServiceSerializer,
)

MAX_NEAREST = 50


def _apply_filters(qs, params):
    """Translate query params into a facility queryset."""
    q = (params.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(facility_type__icontains=q)
            | Q(operator__icontains=q)
            | Q(town__icontains=q)
            | Q(county__icontains=q)
        )

    ftype = (params.get("facility_type") or params.get("type") or "").strip()
    if ftype:
        qs = qs.filter(facility_type__iexact=ftype)

    service = (params.get("service") or "").strip()
    if service:
        qs = qs.filter(services__slug=service)

    insurance = (params.get("insurance") or "").strip()
    if insurance:
        qs = qs.filter(insurances__slug=insurance)

    county = (params.get("county") or "").strip()
    if county:
        qs = qs.filter(county__iexact=county)

    if (params.get("emergency") or "").lower() in ("1", "true", "yes"):
        qs = qs.filter(emergency="yes")

    if (params.get("wheelchair") or "").lower() in ("1", "true", "yes"):
        qs = qs.filter(wheelchair__in=("yes", "limited"))

    if (params.get("open_now") or "").lower() in ("1", "true", "yes"):
        # Opening hours vary; filter in Python over the (bounded) result set.
        qs = [f for f in qs if services.is_open_now(f.opening_hours) is True]

    return qs


def _parse_point(params):
    try:
        lat = float(params.get("lat"))
        lon = float(params.get("lon"))
    except (TypeError, ValueError):
        raise ValidationError(
            "Both `lat` and `lon` numeric query params are required."
        )
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValidationError("Coordinates out of range.")
    return lat, lon


class FacilityViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    """List, filter, retrieve — and find the nearest facilities."""

    serializer_class = FacilitySerializer

    def get_queryset(self):
        qs = Facility.objects.prefetch_related("services", "insurances")
        if getattr(self, "action", None) != "nearest":
            qs = _apply_filters(qs, self.request.query_params)
        return qs

    def _with_distance(self, qs, lat, lon):
        """Annotate every facility with its great-circle distance, sorted."""
        iterable = qs if isinstance(qs, list) else list(qs)
        for facility in iterable:
            facility.distance_m = services.haversine_m(
                lat, lon, facility.latitude, facility.longitude
            )
        iterable.sort(key=lambda f: f.distance_m)
        return iterable

    def list(self, request, *args, **kwargs):
        # Optional lat/lon on the plain list adds distance and sorts by it.
        if request.query_params.get("lat") and request.query_params.get("lon"):
            lat, lon = _parse_point(request.query_params)
            iterable = self._with_distance(self.get_queryset(), lat, lon)
            page = self.paginate_queryset(iterable)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="nearest")
    def nearest(self, request):
        """GET /api/facilities/nearest/?lat=&lon=&limit=&type=… — N closest."""
        lat, lon = _parse_point(request.query_params)
        try:
            limit = int(request.query_params.get("limit", 8))
        except ValueError:
            limit = 8
        limit = max(1, min(limit, MAX_NEAREST))

        queryset = _apply_filters(
            Facility.objects.prefetch_related("services", "insurances"),
            request.query_params,
        )
        nearest = self._with_distance(queryset, lat, lon)[:limit]

        serializer = self.get_serializer(nearest, many=True)
        return Response(
            {
                "resolved_location": {"lat": lat, "lon": lon},
                "count": len(serializer.data),
                "facilities": serializer.data,
            }
        )


class SearchView(APIView):
    """GET /api/search/?q=hospital&lat=&lon= — quick typeahead search."""

    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        if not q:
            raise ValidationError("`q` query param is required.")

        try:
            limit = int(request.query_params.get("limit", 15))
        except ValueError:
            limit = 15

        qs = Facility.objects.filter(
            Q(name__icontains=q)
            | Q(operator__icontains=q)
            | Q(town__icontains=q)
            | Q(county__icontains=q)
            | Q(facility_type__icontains=q)
        )

        lat = lon = None
        if request.query_params.get("lat") and request.query_params.get("lon"):
            lat, lon = _parse_point(request.query_params)

        results = list(qs[: max(1, min(limit, 50))])
        if lat is not None:
            for facility in results:
                facility.distance_m = services.haversine_m(
                    lat, lon, facility.latitude, facility.longitude
                )
            results.sort(key=lambda f: f.distance_m)

        return Response(
            FacilityBriefSerializer(results, many=True).data,
            status=status.HTTP_200_OK,
        )


class MetaView(APIView):
    """GET /api/meta/ — everything the filter UI needs."""

    def get(self, request):
        types = (
            Facility.objects.values("facility_type")
            .annotate(count=Count("id"))
            .order_by("facility_type")
        )
        type_labels = dict(Facility.TYPE_CHOICES)

        data = {
            "facility_types": [
                {"value": t["facility_type"], "label": type_labels.get(t["facility_type"], t["facility_type"]), "count": t["count"]}
                for t in types
            ],
            "services": ServiceSerializer(
                Service.objects.all(), many=True
            ).data,
            "insurers": InsuranceSerializer(
                Insurance.objects.all(), many=True
            ).data,
            "counties": sorted(
                Facility.objects.exclude(county="")
                .order_by()  # clear Meta ordering so DISTINCT applies cleanly
                .values_list("county", flat=True)
                .distinct()
            ),
            "total_facilities": Facility.objects.count(),
        }
        return Response(data)


class RouteView(APIView):
    """POST /api/route/ — OSRM route between two GPS points."""

    def post(self, request):
        try:
            start_lat = float(request.data.get("start_lat"))
            start_lon = float(request.data.get("start_lon"))
            end_lat = float(request.data.get("end_lat"))
            end_lon = float(request.data.get("end_lon"))
        except (TypeError, ValueError):
            raise ValidationError(
                "start_lat, start_lon, end_lat and end_lon are required numbers."
            )

        for label, lat, lon in (
            ("start", start_lat, start_lon),
            ("end", end_lat, end_lon),
        ):
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValidationError(f"{label} coordinates out of range.")
            if not services.in_kenya(lat, lon):
                raise ValidationError(
                    f"{label} coordinate lies outside the Kenya service area."
                )

        profile = request.data.get("profile", "driving")

        try:
            result = services.get_route(
                start_lon, start_lat, end_lon, end_lat, profile=profile
            )
        except services.NoRouteError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except services.RoutingServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(result)


class HealthView(APIView):
    """GET /api/health/ — database + OSRM reachability."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        checks = {}
        overall = "healthy"

        try:
            count = Facility.objects.count()
            checks["database"] = {"status": "ok", "facility_count": count}
            if count == 0:
                overall = "degraded"
                checks["database"]["note"] = (
                    "Connected but no facilities loaded — run `manage.py seed_facilities`"
                )
        except Exception as exc:  # pragma: no cover
            checks["database"] = {"status": "error", "detail": str(exc)}
            overall = "unhealthy"

        osrm = services.ping_osrm()
        checks["osrm"] = osrm
        if osrm["status"] == "error":
            overall = "unhealthy" if overall == "healthy" else overall
        elif osrm["status"] != "ok" and overall == "healthy":
            overall = "degraded"

        from django.conf import settings as dj_settings

        return Response(
            {
                "status": overall,
                "service": dj_settings.APP_NAME,
                "version": dj_settings.APP_VERSION,
                "database_engine": connection.vendor,
                "checks": checks,
            }
        )
