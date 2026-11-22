"""Root URL configuration for KHAP."""
from django.contrib import admin
from django.urls import include, path
from rest_framework.decorators import api_view

from khap import settings

API_INFO = {
    "service": settings.APP_NAME,
    "version": settings.APP_VERSION,
    "endpoints": {
        "health": "GET  /api/health/",
        "meta": "GET  /api/meta/",
        "facilities": "GET  /api/facilities/",
        "facility_detail": "GET  /api/facilities/{id}/",
        "nearest": "GET  /api/facilities/nearest/?lat=&lon=&limit=&profile=",
        "search": "GET  /api/search/?q=",
        "route": "POST /api/route/",
    },
}

    
@api_view(["GET"])
def api_index(_request):
    from rest_framework.response import Response

    return Response(API_INFO)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("facilities.urls")),
    path("api", api_index, name="api-index"),
    path("", api_index, name="api-root"),
]
