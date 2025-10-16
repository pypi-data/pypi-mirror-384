"""Esi interactions"""

from dataclasses import dataclass

from bravado.exception import HTTPNotFound

from esi.clients import EsiClientProvider

from allianceauth.services.hooks import get_extension_logger

from . import __version__, models

logger = get_extension_logger(__name__)

esi = EsiClientProvider(app_info_text=f"aa-fleetcomp v{__version__}")


class CharacterNotInFleet(Exception):
    """Yield when the ESI returns a 404 error because the character isn't in fleet"""


class NoAccessToFleet(Exception):
    """Yield when the ESI returns a 404 error for a lack of access"""


@dataclass
class FleetData:
    """Fleet information pulled from ESI"""

    fleet_id: int
    fleet_commander: "models.FleetCommander"
    fleet_members: list["FleetMemberData"]


@dataclass
class FleetMemberData:
    """Information of a fleet member from the ESI"""

    character_id: int
    ship_type_id: int

    @classmethod
    def create_from_member_list(
        cls, fleet_members_info: list[dict]
    ) -> list["FleetMemberData"]:
        """Creates the list of member information from the ESI endpoint data"""
        return [
            FleetMemberData(
                character_id=fleet_member_info["character_id"],
                ship_type_id=fleet_member_info["ship_type_id"],
            )
            for fleet_member_info in fleet_members_info
        ]


def get_fleet_id(fleet_commander: "models.FleetCommander") -> int:
    """Return the current fleet id of this fleet commander"""

    fleet_info = __get_character_fleet_info(fleet_commander)
    fleet_id = fleet_info["fleet_id"]

    return fleet_id


def get_fleet_data(fleet_commander: "models.FleetCommander") -> FleetData:
    """
    Returns all data from the fleet FCed by this fleet commander
    """
    logger.info("Trying to query the fleet data of commander %s", fleet_commander)

    fleet_id = get_fleet_id(fleet_commander)
    fleet_members = __get_fleet_members(fleet_commander, fleet_id)

    logger.debug(fleet_commander)

    return FleetData(
        fleet_id=fleet_id,
        fleet_commander=fleet_commander,
        fleet_members=FleetMemberData.create_from_member_list(fleet_members),
    )


def __get_character_fleet_info(fleet_member: "models.FleetCommander"):
    """
    Pulls basic fleet information (fleet id, position in fleet)
    60 sec cache
    """

    try:
        fleet_info = esi.client.Fleets.get_characters_character_id_fleet(
            character_id=fleet_member.character_id,
            token=fleet_member.fetch_token().valid_access_token(),
        ).result()
    except HTTPNotFound as e:
        if "Character is not in a fleet" == e.swagger_result.get("error"):
            raise CharacterNotInFleet(
                "The character doesn't appear to be in a fleet"
            ) from e
        raise

    logger.debug(fleet_info)

    return fleet_info


def __get_fleet_members(fleet_member: "models.FleetCommander", fleet_id: int):
    """
    Pulls the fleet members information from the ESI
    5 sec cache
    """

    try:
        fleet_members = esi.client.Fleets.get_fleets_fleet_id_members(
            fleet_id=fleet_id,
            token=fleet_member.fetch_token().valid_access_token(),
        ).results()
    except HTTPNotFound as e:
        if "Character is not in a fleet" == e.swagger_result.get("error"):
            raise CharacterNotInFleet(
                "The character doesn't appear to be in a fleet"
            ) from e
        if (
            "The fleet does not exist or you don't have access to it!"
            == e.swagger_result.get("error")
        ):
            raise NoAccessToFleet(
                "The character doesn't appear to be a fleet commander"
            ) from e
        raise

    return fleet_members
