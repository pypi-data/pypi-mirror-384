"""Models."""

from typing import ClassVar

from django.contrib.auth.models import User
from django.db import models
from django.db.models import QuerySet
from django.db.models.aggregates import Count
from django.utils.translation import gettext_lazy as _
from esi.models import Token
from eveuniverse.models import EveGroup, EveType

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

from . import ESI_SCOPES
from .app_settings import FLEETCOMP_DREADNOUGHT_WEIGHT_PENALTY
from .managers import (
    FleetMemberManager,
    FleetMemberQuerySet,
    FleetSnapshotManager,
    ShipGroupingManager,
)

logger = get_extension_logger(__name__)


EVE_ONLINE_DREADNOUGHT_GROUP = 485


class General(models.Model):
    """A metamodel for app permissions."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", "Can create snapshots and see own snapshots"),
            (
                "view_all",
                "Can view all recorded fleets and snapshot other people fleets",
            ),
        )


class ShipGrouping(models.Model):
    """Ship grouping"""

    objects: ClassVar[ShipGroupingManager] = ShipGroupingManager()

    column_index = models.PositiveIntegerField(
        default=0, help_text=_("Index of the column this grouping should be a part of")
    )
    display_name = models.CharField(
        max_length=50, help_text="Name of the grouping in the UI"
    )

    associated_types = models.ManyToManyField(
        EveType, help_text="Ship types associated to this grouping", blank=True
    )
    associated_groups = models.ManyToManyField(
        EveGroup, help_text="Eve ship groups associated to this grouping", blank=True
    )

    @property
    def internal_name(self) -> str:
        """Internal name to use when passing value around"""
        return self.display_name.lower().replace(" ", "_")

    def __str__(self):
        return f"Custom group for {self.display_name}"

    def get_snapshot_matches(
        self, snapshot: "FleetSnapshot"
    ) -> QuerySet["FleetMember"]:
        """Return all members matching the grouping"""
        return snapshot.members.all().filter_by_ship_grouping(self)


class FleetCommander(models.Model):
    """
    Member of a fleet with ESI stored
    """

    character_ownership = models.ForeignKey(
        CharacterOwnership,
        on_delete=models.CASCADE,
        related_name="+",
    )

    @property
    def character_id(self) -> int:
        """Return character id"""
        return self.character_ownership.character.character_id

    @property
    def character_name(self) -> str:
        """Return character name"""
        return self.character_ownership.character.character_name

    @property
    def user(self) -> User:
        """Return the associated user"""
        return self.character_ownership.user

    def fetch_token(self) -> Token:
        """Return a valid token if there is one"""
        token = (
            Token.objects.filter(
                character_id=self.character_id,
            )
            .require_scopes(ESI_SCOPES)
            .require_valid()
            .first()
        )

        if not token:
            raise Token.DoesNotExist(f"{self}: No valid token found")
        return token

    def __str__(self):
        return self.character_name


class FleetSnapshot(models.Model):
    """Takes a snapshot of a fleet at a given time"""

    objects: ClassVar[FleetSnapshotManager] = FleetSnapshotManager()

    fleet_id = models.BigIntegerField(help_text=_("EVE online fleet id"))
    timestamp = models.DateTimeField(
        auto_now_add=True, help_text=_("Time of the snapshot")
    )

    commander = models.ForeignKey(
        FleetCommander,
        on_delete=models.SET_NULL,
        null=True,
        help_text=_("Fleet commander at the time of the snapshot"),
    )

    @property
    def timestamp_str(self) -> str:
        """Timestamp displayed with leading zeroes"""
        return self.timestamp.strftime("%Y/%m/%d %H:%M")

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Fleet {self.fleet_id} at {self.timestamp}"

    def count_mains(self) -> int:
        """Counts how many main characters are in the fleet"""
        return (
            self.members.exclude(character__character_ownership=None)
            .values("character__character_ownership__user")
            .distinct()
            .count()
        )

    def get_user_ids(self):
        """Return the list of users in this fleet"""
        return self.members.values_list(
            "character__character_ownership__user", flat=True
        ).distinct()

    def count_orphans(self) -> int:
        """Count how many characters in the fleet don't have a main associated"""
        return self.members.filter(character__character_ownership=None).count()

    def count_members(self) -> int:
        """Counts how many characters are in the fleet"""
        return self.members.count()

    def get_user_members(self, user: User | None) -> FleetMemberQuerySet:
        """
        Returns characters in fleets linked to this user.
        If None is passed returns all orphans
        """
        if user:
            user_members = self.members.filter(
                character__character_ownership__user=user
            )
        else:
            user_members = self.members.filter(character__character_ownership=None)
        return user_members

    def get_main_ship_type(self) -> EveType:
        """Return the most popular ship type of this fleet"""

        def reduce_dreadnought_weight(ship_type_count):
            """
            Utility function reducing the weight of dreadnoughts to have them removed from main ship
            """
            if ship_type_count["ship_type__eve_group"] == EVE_ONLINE_DREADNOUGHT_GROUP:
                ship_type_count["id__count"] /= FLEETCOMP_DREADNOUGHT_WEIGHT_PENALTY
            return ship_type_count

        ship_type_counts = self.members.values(
            "ship_type", "ship_type__eve_group"
        ).annotate(Count("id"))
        penalized_ship_type_counts = list(
            map(reduce_dreadnought_weight, ship_type_counts)
        )
        print(penalized_ship_type_counts)
        penalized_ship_type_counts.sort(
            key=lambda ship_type_count: ship_type_count["id__count"], reverse=True
        )

        return EveType.objects.get(id=penalized_ship_type_counts[0]["ship_type"])

    def count_ship_type(self, ship_type: EveType) -> int:
        """Returns how many of a certain ship there is in the fleet"""
        return self.members.filter(ship_type=ship_type).count()

    def get_user_and_associated_members_list(
        self,
    ) -> list[tuple[User | None, list["FleetMember"]]]:
        """Returns all users and their associated member list"""
        res = []
        for user_id in self.get_user_ids():
            if user_id:
                user = User.objects.get(id=user_id)
                res.append((user, self.get_user_members(user)))
            else:
                res.append((None, self.get_user_members(None)))

        return res

    def get_total_mass(self) -> float:
        """Return the total ship mass in tons"""
        return self.members.all().calculate_mass() / 1000

    def get_subcap_mass(self) -> float:
        """Return the mass of subcap ships in tons"""
        return self.members.all().exclude_capitals().calculate_mass() / 1000


class FleetMember(models.Model):
    """Member of a fleet and its associated ships"""

    objects: ClassVar[FleetMemberManager] = FleetMemberManager()

    fleet = models.ForeignKey(
        FleetSnapshot, on_delete=models.CASCADE, related_name="members"
    )
    character = models.ForeignKey(EveCharacter, on_delete=models.CASCADE)
    ship_type = models.ForeignKey(EveType, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.character} - {self.ship_type}"
