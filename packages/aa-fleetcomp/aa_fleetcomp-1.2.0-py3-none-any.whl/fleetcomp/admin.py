"""Admin site."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from eveuniverse.models import EveGroup, EveType

from fleetcomp.models import FleetMember, FleetSnapshot, ShipGrouping

# Register your models for the admin site here.

EVE_SHIP_CATEGORY_ID = 6


class FleetMembersInline(admin.TabularInline):
    model = FleetMember

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=...):
        return False

    def has_delete_permission(self, request, obj=...):
        return False


@admin.register(FleetSnapshot)
class FleetSnapshotAdmin(admin.ModelAdmin):
    list_display = ["commander", "timestamp", "fleet_id"]
    inlines = [FleetMembersInline]

    def has_change_permission(self, request, obj=...):
        return False


@admin.register(ShipGrouping)
class ShipGroupingAdmin(admin.ModelAdmin):
    list_display = ["display_name", "column_index", "ship_types", "ship_groups"]
    ordering = ["column_index"]
    filter_horizontal = ("associated_types", "associated_groups")

    fieldsets = (
        (
            None,
            {
                "fields": ("display_name", "column_index"),
            },
        ),
        (
            _("Associated entities"),
            {
                "fields": (
                    "associated_types",
                    "associated_groups",
                )
            },
        ),
    )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "associated_types":
            kwargs["queryset"] = EveType.objects.filter(
                eve_group__eve_category=EVE_SHIP_CATEGORY_ID
            ).order_by("name")
        elif db_field.name == "associated_groups":
            kwargs["queryset"] = EveGroup.objects.filter(
                eve_category=EVE_SHIP_CATEGORY_ID
            ).order_by("name")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    @admin.display(description=_("Ship types"))
    def ship_types(self, custom_grouping: ShipGrouping):
        return ", ".join(
            custom_grouping.associated_types.values_list("name", flat=True)
        )

    @admin.display(description=_("Ship groups"))
    def ship_groups(self, custom_grouping: ShipGrouping):
        return ", ".join(
            custom_grouping.associated_groups.values_list("name", flat=True)
        )
