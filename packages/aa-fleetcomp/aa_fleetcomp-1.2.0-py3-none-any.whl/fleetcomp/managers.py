"""Managers."""

from datetime import timedelta
from enum import IntEnum

from django.db import models
from django.db.models import Q, Sum
from django.utils.timezone import now
from eveuniverse.models import EveType

from allianceauth.eveonline.models import EveCharacter

from . import esi
from . import models as fleetcomp_models
from .app_settings import FLEETCOMP_FLEET_CACHE_MINUTES


class EveGroupIds(IntEnum):
    """Groups id of several Eve groups"""

    FORCE_AUXILIARY = 1538
    DREADNOUGHT = 485
    CARRIER = 547
    SUPERCARRIER = 659
    TITAN = 30
    FREIGHTER = 513
    CAPITAL_INDUSTRIAL_SHIP = 883


class ShipGroupingManager(models.Manager):
    """Manager for ShipGrouping"""

    def get_all_type_ids(self) -> list[int]:
        """Return all type ids present in groupings"""
        return list(self.values_list("associated_types__id", flat=True).distinct())

    def get_all_group_ids(self) -> list[int]:
        """Return all group ids present in groupings"""
        return list(self.values_list("associated_groups__id", flat=True).distinct())


class FleetSnapshotManager(models.Manager):
    """Manager for FLeetSnapshot"""

    def create_from_fleet_data(
        self, fleet_data: "esi.FleetData"
    ) -> "fleetcomp_models.FleetSnapshot":
        """Create a snapshot from the data received by the ESI"""

        snapshot: "fleetcomp_models.FleetSnapshot" = self.create(
            fleet_id=fleet_data.fleet_id,
            commander=fleet_data.fleet_commander,
        )

        for member in fleet_data.fleet_members:
            try:
                character = EveCharacter.objects.get(character_id=member.character_id)
            except EveCharacter.DoesNotExist:
                character = EveCharacter.objects.create_character(
                    character_id=member.character_id
                )
            ship_type, _ = EveType.objects.get_or_create_esi(id=member.ship_type_id)
            fleetcomp_models.FleetMember.objects.create(
                character=character, ship_type=ship_type, fleet=snapshot
            )

        return snapshot

    def fleet_id_cache_hit(self, fleet_id: int) -> bool:
        """
        Returns true if there is a fleet in the database created less than FLEETCOMP_FLEET_CACHE_MINUTES minutes ago
        """
        return self.filter(
            fleet_id=fleet_id,
            timestamp__gt=now() + timedelta(minutes=-FLEETCOMP_FLEET_CACHE_MINUTES),
        ).exists()

    def get_last_fleet_id_record(self, fleet_id) -> "fleetcomp_models.FleetSnapshot":
        """Returns the last record of a fleet with this id"""
        # TODO check that the ordering is correct
        return self.filter(fleet_id=fleet_id).first()


class FleetMemberQuerySet(models.QuerySet):
    """Custom QuerySet class for FleetMember"""

    def filter_by_ship_grouping(
        self, ship_grouping: "fleetcomp_models.ShipGrouping"
    ) -> models.QuerySet:
        """Filters fleet members if their ship type matches the given ship grouping"""
        return self.filter(
            Q(ship_type__eve_group__in=ship_grouping.associated_groups.all())
            | Q(ship_type__in=ship_grouping.associated_types.all())
        )

    def exclude_ships_in_any_grouping(self):
        """Exccludes all fleet members with a ship that would match an existing queryset"""
        excluded_groups_ids = fleetcomp_models.ShipGrouping.objects.get_all_group_ids()
        excluded_types_ids = fleetcomp_models.ShipGrouping.objects.get_all_type_ids()

        return self.exclude(ship_type__eve_group__id__in=excluded_groups_ids).exclude(
            ship_type__id__in=excluded_types_ids
        )

    def filter_by_ship_type(self, ship_type: EveType):
        """Filters by the members ship type"""
        return self.filter(ship_type=ship_type)

    def count_ship_type(self, ship_type: EveType) -> int:
        """Count how many fleet members have the given ship type"""
        return self.filter_by_ship_type(ship_type).count()

    def exclude_capitals(self):
        """Will exclude all members sitting in a capital ship"""
        return self.exclude(
            ship_type__eve_group__id__in=[
                EveGroupIds.FORCE_AUXILIARY,
                EveGroupIds.DREADNOUGHT,
                EveGroupIds.CARRIER,
                EveGroupIds.FREIGHTER,
                EveGroupIds.SUPERCARRIER,
                EveGroupIds.TITAN,
                EveGroupIds.CAPITAL_INDUSTRIAL_SHIP,
            ]
        )

    def calculate_mass(self) -> float:
        """Returns the sum of the mass of all ships in this queryset"""
        return self.aggregate(mass_total=Sum("ship_type__mass"))["mass_total"]


class FleetMemberManager(models.Manager):
    """Custom Manager for FleetMember"""

    def get_queryset(self) -> FleetMemberQuerySet:
        """Custom get_queryset method"""
        return FleetMemberQuerySet(self.model, using=self._db)
