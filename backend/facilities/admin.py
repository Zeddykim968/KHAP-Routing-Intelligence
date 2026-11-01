from django.contrib import admin

from facilities.models import Facility, Insurance, Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "category", "order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Insurance)
class InsuranceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "kind", "order")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("kind",)
    search_fields = ("name",)


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "facility_type",
        "town",
        "county",
        "emergency",
        "opening_hours",
    )
    list_filter = ("facility_type", "county", "emergency")
    search_fields = ("name", "operator", "town", "county")
    filter_horizontal = ("services", "insurances")
    ordering = ("name",)
