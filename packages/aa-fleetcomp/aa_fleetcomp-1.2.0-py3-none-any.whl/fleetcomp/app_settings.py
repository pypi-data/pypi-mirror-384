"""App settings."""

from django.conf import settings

FLEETCOMP_FLEET_CACHE_MINUTES = getattr(settings, "FLEETCOMP_FLEET_CACHE_MINUTES", 5)

FLEETCOMP_DREADNOUGHT_WEIGHT_PENALTY = getattr(
    settings, "FLEETCOMP_DREADNOUGHT_WEIGHT_PENALTY", 5
)
