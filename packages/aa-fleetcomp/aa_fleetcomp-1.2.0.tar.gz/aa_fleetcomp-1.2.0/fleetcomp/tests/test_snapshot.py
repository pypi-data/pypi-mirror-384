from django.test import TestCase
from eveuniverse.models import EveType

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.tests.auth_utils import AuthUtils

from fleetcomp.models import FleetCommander, FleetMember, FleetSnapshot
from fleetcomp.tests.testdata.load_eveuniverse import load_eveuniverse


class TestSnapshot(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        # create a global fleet commander
        cls.user = AuthUtils.create_user("test_user")
        cls.character = AuthUtils.add_main_character_2(
            cls.user, "test character", 1, "123", "Test corporation", "TEST"
        )
        character_ownership = CharacterOwnership.objects.create(
            character=cls.character,
            user=cls.user,
            owner_hash="fake hash",
        )
        cls.fleet_commander = FleetCommander.objects.create(
            character_ownership=character_ownership,
        )

    def test_main_ship_reduce_dread(self):
        fleet_snapshot: FleetSnapshot = FleetSnapshot.objects.create(
            fleet_id=10,
            commander=self.fleet_commander,
        )

        revelation_type = EveType.objects.get(id=19720)
        caracal_type = EveType.objects.get(id=621)
        FleetMember.objects.create(
            fleet=fleet_snapshot, character=self.character, ship_type=revelation_type
        )
        FleetMember.objects.create(
            fleet=fleet_snapshot, character=self.character, ship_type=revelation_type
        )
        FleetMember.objects.create(
            fleet=fleet_snapshot, character=self.character, ship_type=caracal_type
        )

        self.assertEqual(fleet_snapshot.get_main_ship_type(), caracal_type)
