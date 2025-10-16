from django.core.management import BaseCommand
from eveuniverse.models import EveGroup

from fleetcomp.models import ShipGrouping


class Command(BaseCommand):

    help = "Creates default groupings in the database"

    def handle(self, *args, **kwargs):
        """Add default objects"""

        logistics, _ = ShipGrouping.objects.get_or_create(
            column_index=10,
            display_name="Logistics",
        )
        logi_cruisers, _ = EveGroup.objects.get_or_create_esi(id=832)
        logi_frigates, _ = EveGroup.objects.get_or_create_esi(id=1527)
        logistics.associated_groups.add(logi_cruisers, logi_frigates)

        hic, _ = ShipGrouping.objects.get_or_create(
            column_index=10,
            display_name="HIC",
        )
        hic_group, _ = EveGroup.objects.get_or_create_esi(id=894)
        hic.associated_groups.add(hic_group)

        links, _ = ShipGrouping.objects.get_or_create(
            column_index=10,
            display_name="Link Ships",
        )
        command_ships_group, _ = EveGroup.objects.get_or_create_esi(id=540)
        links.associated_groups.add(command_ships_group)

        cynoes, _ = ShipGrouping.objects.get_or_create(
            column_index=10,
            display_name="Cynoes",
        )
        force_recon_group, _ = EveGroup.objects.get_or_create_esi(id=833)
        cynoes.associated_groups.add(force_recon_group)

        dreads, _ = ShipGrouping.objects.get_or_create(
            column_index=20,
            display_name="Dreadnoughts",
        )
        dreadnought_group, _ = EveGroup.objects.get_or_create_esi(id=485)
        dreads.associated_groups.add(dreadnought_group)

        faxes, _ = ShipGrouping.objects.get_or_create(
            column_index=20,
            display_name="FAXes",
        )
        force_auxiliary_group, _ = EveGroup.objects.get_or_create_esi(id=1538)
        faxes.associated_groups.add(force_auxiliary_group)
