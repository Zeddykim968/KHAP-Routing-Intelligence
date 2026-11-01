"""API routes for the facilities app (mounted at /api/).

The Next.js dev-server rewrite forwards /api/* paths without the trailing
slash, so every endpoint is registered both with and without one.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from facilities import views


def dual(route: str, view, name: str | None = None) -> list:
    """Register an endpoint both with and without a trailing slash."""
    bare = route.rstrip("/")
    return [
        path(route, view, name=name),
        path(bare, view, name=f"{name}-bare" if name else None),
    ]


router = DefaultRouter()
router.register("facilities", views.FacilityViewSet, basename="facility")

router_bare = DefaultRouter(trailing_slash=False)
router_bare.register("facilities", views.FacilityViewSet, basename="facility-bare")

urlpatterns = [
    *dual("health/", views.HealthView.as_view(), name="health"),
    *dual("meta/", views.MetaView.as_view(), name="meta"),
    *dual("search/", views.SearchView.as_view(), name="search"),
    *dual("route/", views.RouteView.as_view(), name="route"),
    path("", include(router.urls)),
    path("", include(router_bare.urls)),
]
