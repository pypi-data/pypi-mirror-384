"""Routes."""

from django.urls import path

from . import views

app_name = "fleetcomp"

urlpatterns = [
    path("", views.index, name="index"),
    path("fleet/add/own", views.capture_own_fleet_composition, name="add_own_snapshot"),
    path(
        "fleet/add/other",
        views.capture_other_fleet_composition,
        name="add_other_snapshot",
    ),
    path("fleet/<int:snapshot_id>", views.view_fleet, name="view_snapshot"),
    path(
        "fleet/<int:snapshot_id>/details",
        views.user_details,
        name="user_details_orphans",
    ),
    path(
        "fleet/<int:snapshot_id>/details/<int:user_id>",
        views.user_details,
        name="user_details",
    ),
    path("modal_loader_body", views.modal_loader_body, name="modal_loader_body"),
]
