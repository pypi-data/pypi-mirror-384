from django.utils.translation import gettext_lazy as _

from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook

from . import urls


class FleetcompMenuItem(MenuItemHook):
    """This class ensures only authorized users will see the menu entry"""

    def __init__(self):
        # setup menu entry for sidebar
        MenuItemHook.__init__(
            self,
            _("Fleet Composition"),
            "fas fa-people-group fa-fw",
            "fleetcomp:index",
            navactive=["fleetcomp:"],
        )

    def render(self, request):
        if request.user.has_perm("fleetcomp.basic_access"):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_menu():
    return FleetcompMenuItem()


@hooks.register("url_hook")
def register_urls():
    return UrlHook(urls, "fleetcomp", r"^fleetcomp/")
