"""DRF serializers for the facilities API."""
from rest_framework import serializers

from facilities import services
from facilities.models import Facility, Insurance, Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["slug", "name", "icon", "category"]


class InsuranceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insurance
        fields = ["slug", "name", "kind"]


class FacilitySerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)
    insurances = InsuranceSerializer(many=True, read_only=True)

    type_label = serializers.CharField(source="get_facility_type_display", read_only=True)
    emergency_label = serializers.CharField(
        source="get_emergency_display", read_only=True
    )
    distance_m = serializers.SerializerMethodField()
    travel_distance_m = serializers.SerializerMethodField()
    travel_duration_s = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()

    class Meta:
        model = Facility
        fields = [
            "id",
            "name",
            "facility_type",
            "type_label",
            "operator",
            "phone",
            "website",
            "address",
            "town",
            "county",
            "emergency",
            "emergency_label",
            "opening_hours",
            "wheelchair",
            "latitude",
            "longitude",
            "distance_m",
            "travel_distance_m",
            "travel_duration_s",
            "is_open",
            "services",
            "insurances",
        ]

    def get_distance_m(self, obj) -> float | None:
        value = getattr(obj, "distance_m", None)
        return round(value, 1) if value is not None else None

    def get_travel_distance_m(self, obj) -> float | None:
        """Road distance from the query origin (OpenRouteService matrix)."""
        value = getattr(obj, "travel_distance_m", None)
        return round(value, 1) if value is not None else None

    def get_travel_duration_s(self, obj) -> float | None:
        """Estimated road travel time from the query origin, in seconds."""
        value = getattr(obj, "travel_duration_s", None)
        return round(value, 1) if value is not None else None

    def get_is_open(self, obj) -> bool | None:
        return services.is_open_now(obj.opening_hours)


class FacilityBriefSerializer(serializers.ModelSerializer):
    """Compact payload for search suggestions."""

    type_label = serializers.CharField(source="get_facility_type_display", read_only=True)
    distance_m = serializers.SerializerMethodField()

    class Meta:
        model = Facility
        fields = [
            "id",
            "name",
            "facility_type",
            "type_label",
            "town",
            "county",
            "latitude",
            "longitude",
            "distance_m",
        ]

    def get_distance_m(self, obj) -> float | None:
        value = getattr(obj, "distance_m", None)
        return round(value, 1) if value is not None else None
