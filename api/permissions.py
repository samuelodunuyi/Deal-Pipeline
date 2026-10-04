from rest_framework.permissions import BasePermission
from rest_framework.settings import api_settings


class StaffOnlyDelete(BasePermission):
    """Any authenticated user may read and write, but only staff may delete records."""

    message = 'Only staff users can delete records.'

    def has_permission(self, request, view):
        if request.method != 'DELETE':
            return True
        return bool(request.user and request.user.is_staff)


class IsStaff(BasePermission):
    """Staff users only, for every method including reads."""

    message = 'This resource is restricted to staff users.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


# Honours API_REQUIRE_AUTH (via DEFAULT_PERMISSION_CLASSES) and adds the delete rule on top.
STANDARD_PERMISSIONS = [*api_settings.DEFAULT_PERMISSION_CLASSES, StaffOnlyDelete]
STAFF_ONLY_PERMISSIONS = [*api_settings.DEFAULT_PERMISSION_CLASSES, IsStaff]
