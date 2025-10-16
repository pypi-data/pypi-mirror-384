"""Fleetcomp templatetags"""

from django import template
from django.contrib.auth.models import User
from eveuniverse.models import EveType

from fleetcomp.managers import FleetMemberQuerySet
from fleetcomp.models import FleetSnapshot, ShipGrouping

register = template.Library()


@register.simple_tag
def custom_grouping_counter_snapshot(
    snapshot: FleetSnapshot, custom_grouping: ShipGrouping
) -> int:
    """Returns how many ships of the given custom grouping are in the snapshot"""
    return custom_grouping.get_snapshot_matches(snapshot).count()


@register.simple_tag
def custom_grouping_counter_user(
    snapshot: FleetSnapshot, user: User, custom_grouping: ShipGrouping
) -> int:
    """Returns how many ships of the given user match the custom grouping"""
    return (
        custom_grouping.get_snapshot_matches(snapshot) & snapshot.get_user_members(user)
    ).count()


@register.simple_tag
def count_ship_type_in_fleet_members(
    ship_type: EveType, fleet_members: FleetMemberQuerySet
):
    """Count how many fleet members are in the given ship type"""
    return fleet_members.count_ship_type(ship_type)


@register.simple_tag
def count_ships_in_grouping(
    ship_grouping: ShipGrouping, fleet_members: FleetMemberQuerySet
):
    """Count the number of members with a ship matching this grouping"""
    return fleet_members.filter_by_ship_grouping(ship_grouping).count()


@register.simple_tag
def count_ships_not_in_groupings_or_mainline(
    fleet_members: FleetMemberQuerySet, mainline: EveType
):
    """Count members with a ship not matching any grouping"""
    return (
        fleet_members.exclude_ships_in_any_grouping()
        .exclude(ship_type=mainline)
        .count()
    )
