"""Views."""

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_page
from esi.decorators import token_required

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.services.hooks import get_extension_logger

from fleetcomp import ESI_SCOPES
from fleetcomp.app_settings import FLEETCOMP_FLEET_CACHE_MINUTES
from fleetcomp.esi import (
    CharacterNotInFleet,
    NoAccessToFleet,
    get_fleet_data,
    get_fleet_id,
)
from fleetcomp.models import FleetCommander, FleetSnapshot, ShipGrouping

logger = get_extension_logger(__name__)


@permission_required("fleetcomp.basic_access")
def index(request):
    """Render index view."""
    snapshots = FleetSnapshot.objects.all()
    if not request.user.has_perm("fleetcomp.view_all"):
        snapshots.filter(commander__character_ownership__user=request.user)
    return render(request, "fleetcomp/index.html", {"snapshots": snapshots})


@permission_required("fleetcomp.basic_access")
@token_required(scopes=ESI_SCOPES)
def capture_own_fleet_composition(request, token):
    """
    Adds a new fleet commander to the list of fleet commanders this user can pull data from.
    """
    logger.info("Capturing fleet composition from token %s", token)

    character_ownership: CharacterOwnership = get_object_or_404(
        request.user.character_ownerships.select_related("character"),
        character__character_id=token.character_id,
    )

    fleet_commander, created = FleetCommander.objects.get_or_create(
        character_ownership=character_ownership,
    )

    if created:
        logger.info(
            "Created a new fleet commander from char_ownership: %s", character_ownership
        )
        character_name = character_ownership.character.character_name
        messages.success(
            request, _(f"Successfully added new fleet commander: {character_name}")
        )

    return __capture_fleet_and_redirect(request, fleet_commander)


@permission_required("fleetcomp.view_all")
def capture_other_fleet_composition(request):
    """
    Enables to capture the fleet composition of another FC that registered
    """

    if request.method == "POST":
        commander_id = request.POST.get("commander_id")
        logger.info(
            "Capturing known commander fleet from commander id %s", commander_id
        )

        commander = get_object_or_404(FleetCommander, id=commander_id)

        return __capture_fleet_and_redirect(request, commander)

    logger.debug("Rendering all commander view")

    commanders = FleetCommander.objects.all()
    return render(
        request, "fleetcomp/all_fleet_commanders.html", {"commanders": commanders}
    )


def __capture_fleet_and_redirect(request, fleet_commander: FleetCommander):
    """
    Captures the fleet under this commander and returns a redirect to the snapshot if successful
    """

    logger.debug("Capturing fleet of commander %s", fleet_commander)

    try:
        fleet_id = get_fleet_id(fleet_commander)
        logger.debug("Fleet id found: %s", fleet_id)
    except CharacterNotInFleet:
        logger.error("The commander %s isn't in fleet", fleet_commander)
        messages.error(request, _("The character doesn't appear to be in a fleet"))
        return redirect("fleetcomp:index")

    if FleetSnapshot.objects.fleet_id_cache_hit(fleet_id):
        logger.info("Fleet cache hit. Returning the previous fleet")
        messages.warning(
            request,
            _(
                f"This fleet has already been captured too recently."
                f"You need to wait {FLEETCOMP_FLEET_CACHE_MINUTES} minutes between captures"
            ),
        )

        snapshot = FleetSnapshot.objects.get_last_fleet_id_record(fleet_id)

    else:
        logger.debug("No cache hit for fleet id %s", fleet_id)
        try:
            fleet_data = get_fleet_data(fleet_commander)
        except CharacterNotInFleet:
            logger.error("The commander isn't in a fleet")
            messages.error(request, _("The character doesn't appear to be in a fleet"))
            return redirect("fleetcomp:index")
        except NoAccessToFleet:
            logger.error("The character isn't the commander of its fleet")
            messages.error(
                request, _("The character doesn't appear to be a fleet commander")
            )
            return redirect("fleetcomp:index")

        snapshot = FleetSnapshot.objects.create_from_fleet_data(fleet_data)

    logger.debug(snapshot)
    return redirect("fleetcomp:view_snapshot", snapshot.id)


@permission_required("fleetcomp.basic_access")
def view_fleet(request, snapshot_id):
    """Displays the selected snapshot"""

    snapshot = get_object_or_404(FleetSnapshot, id=snapshot_id)
    logger.debug(snapshot)

    if snapshot.commander.user != request.user and not request.user.has_perm(
        "fleetcomp.view_all"
    ):
        logger.warning(
            "user %d tried to access the snapshot id %d", request.user, snapshot.id
        )
        messages.warning(
            request, _("You don't have the necessary roles to see this fleet")
        )
        return redirect("fleetcomp:index")

    main_ship_type = snapshot.get_main_ship_type()
    main_ship_type_count = snapshot.count_ship_type(main_ship_type)
    ship_groupings = ShipGrouping.objects.all()

    column_ids = (
        ShipGrouping.objects.order_by("column_index")
        .values_list("column_index", flat=True)
        .distinct()
    )
    columns = []
    for column_id in column_ids:
        columns.append(ShipGrouping.objects.filter(column_index=column_id))

    return render(
        request,
        "fleetcomp/snapshot.html",
        {
            "snapshot": snapshot,
            "main_ship_type": main_ship_type,
            "main_ship_type_count": main_ship_type_count,
            "ship_groupings": ship_groupings,
            "columns": columns,
        },
    )


@permission_required("fleetcomp.basic_access")
def user_details(request, snapshot_id: int, user_id: int | None = None):
    """Displays the details of a user"""

    snapshot = get_object_or_404(FleetSnapshot, id=snapshot_id)
    user = get_object_or_404(User, id=user_id) if user_id else None

    members = snapshot.get_user_members(user)

    context = {
        "user": user,
        "members": members,
    }

    return render(request, "fleetcomp/modals/user_details.html", context)


@cache_page(3600)
def modal_loader_body(request):
    """Draw the loader body. Useful for showing a spinner while loading a modal."""
    return render(request, "fleetcomp/modals/loader_body.html")
