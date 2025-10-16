from django.test import TestCase
from eveuniverse.models import EveType

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.tests.auth_utils import AuthUtils

from ..models import FleetCommander, FleetMember, FleetSnapshot
from .testdata.load_eveuniverse import load_eveuniverse


class TestFleetMemberQuerySet(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.test_user = AuthUtils.create_user("test_user")
        AuthUtils.add_main_character_2(
            user=cls.test_user, name="test_char", character_id=1234
        )
        char_ownership = CharacterOwnership.objects.create(
            user=cls.test_user,
            character=cls.test_user.profile.main_character,
            owner_hash="badhash",
        )

        cls.fleet_commander = FleetCommander.objects.create(
            character_ownership=char_ownership
        )

    def setUp(self):
        super().setUp()
        self.snapshot = FleetSnapshot.objects.create(
            fleet_id=123, commander=self.fleet_commander
        )

    def test_exclude_capitals(self):
        FleetMember.objects.bulk_create(
            [
                FleetMember(
                    fleet=self.snapshot,
                    character=self.test_user.profile.main_character,
                    ship_type=EveType.objects.get(id=621),
                ),
                FleetMember(
                    fleet=self.snapshot,
                    character=self.test_user.profile.main_character,
                    ship_type=EveType.objects.get(id=11567),
                ),
                FleetMember(
                    fleet=self.snapshot,
                    character=self.test_user.profile.main_character,
                    ship_type=EveType.objects.get(id=28352),
                ),
            ]
        )
        qs = FleetMember.objects.all()

        self.assertEqual(qs.count(), 3)

        qs = qs.exclude_capitals()

        self.assertEqual(qs.count(), 1)

    def test_total_mass(self):
        FleetMember.objects.bulk_create(
            [
                FleetMember(
                    fleet=self.snapshot,
                    character=self.test_user.profile.main_character,
                    ship_type=EveType.objects.get(id=621),
                ),
                FleetMember(
                    fleet=self.snapshot,
                    character=self.test_user.profile.main_character,
                    ship_type=EveType.objects.get(id=11567),
                ),
            ]
        )

        qs = FleetMember.objects.all()

        self.assertEqual(qs.calculate_mass(), 11910000.0 + 2400000000.0)
