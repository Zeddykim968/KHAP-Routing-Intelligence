"""
KHAP facility data models.

Portable across SQLite (development) and PostgreSQL (production):
locations are stored as latitude/longitude floats with distance
calculations performed in the service layer, so no PostGIS extension
is required. Set DATABASE_URL to PostgreSQL when deploying at scale.
"""
from django.db import models


class Service(models.Model):
    """A healthcare service a facility can offer (maternity, lab, ICU…)."""

    CATEGORY_CHOICES = [
        ("care", "Primary care"),
        ("diagnostics", "Diagnostics"),
        ("specialist", "Specialist care"),
        ("support", "Support services"),
    ]

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    icon = models.CharField(max_length=40, blank=True, help_text="Icon key used by the web UI.")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="care")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Insurance(models.Model):
    """An insurance scheme or payment method accepted at a facility."""

    KIND_CHOICES = [
        ("public", "Public scheme"),
        ("private", "Private insurer"),
        ("self", "Self-pay"),
    ]

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default="private")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Facility(models.Model):
    """A healthcare facility (hospital, clinic, pharmacy…) with a location."""

    TYPE_CHOICES = [
        ("hospital", "Hospital"),
        ("clinic", "Clinic"),
        ("health_centre", "Health Centre"),
        ("dispensary", "Dispensary"),
        ("pharmacy", "Pharmacy"),
        ("dentist", "Dental Clinic"),
        ("laboratory", "Laboratory"),
        ("maternity", "Maternity Home"),
        ("eye_clinic", "Eye Clinic"),
    ]

    EMERGENCY_CHOICES = [
        ("yes", "24/7 emergency unit"),
        ("limited", "Emergency, limited hours"),
        ("no", "No emergency unit"),
        ("unknown", "Unknown"),
    ]

    WHEELCHAIR_CHOICES = [
        ("yes", "Wheelchair accessible"),
        ("limited", "Partially accessible"),
        ("no", "Not accessible"),
        ("unknown", "Unknown"),
    ]

    name = models.CharField(max_length=200)
    facility_type = models.CharField(max_length=20, choices=TYPE_CHOICES, db_index=True)
    operator = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    address = models.CharField(max_length=200, blank=True)
    town = models.CharField(max_length=100, blank=True, db_index=True)
    county = models.CharField(max_length=100, blank=True, db_index=True)

    emergency = models.CharField(
        max_length=10, choices=EMERGENCY_CHOICES, default="unknown"
    )
    opening_hours = models.CharField(
        max_length=160,
        blank=True,
        help_text='OSM-style hours, e.g. "24/7" or "Mo-Fr 08:00-17:00".',
    )
    wheelchair = models.CharField(
        max_length=10, choices=WHEELCHAIR_CHOICES, default="unknown"
    )

    latitude = models.FloatField()
    longitude = models.FloatField()

    services = models.ManyToManyField(Service, related_name="facilities", blank=True)
    insurances = models.ManyToManyField(
        Insurance, related_name="facilities", blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["facility_type", "name"]),
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_facility_type_display()})"
