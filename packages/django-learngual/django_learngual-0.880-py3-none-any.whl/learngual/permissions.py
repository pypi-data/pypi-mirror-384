from rest_framework import permissions

from . import custom_exceptions
from .translator import translate as _


class ExamplePermissions:
    class CanAccessView(permissions.BasePermission):
        def has_object_permission(self, request, view, obj):

            return False

        def has_permission(self, request, view):

            return True


class GeneralPermissions:
    class IsService(permissions.BasePermission):
        """if request is made from a service as a service

        Args:
            permissions (_type_): _description_
        """

        def has_object_permission(self, request, view, obj):

            return False

        def has_permission(self, request, view):
            return getattr(request.user, "is_service", False)

    class IsAccount(permissions.BasePermission):
        """if request is made from a service as a service

        Args:
            permissions (_type_): _description_
        """

        def has_permission(self, request, view):
            return getattr(request.user, "account", None) or getattr(
                request, "account", None
            )

    class IsApiKey(permissions.BasePermission):
        """if request is made with an apikey

        Args:
            permissions (_type_): _description_
        """

        def has_permission(self, request, view):
            api_key = str(
                request.META.get("HTTP_API_KEY", "") or request.GET.get("api-key", "")
            )
            return bool(api_key)

    class IsNotApiKey(permissions.BasePermission):
        """if request is not made with an api key

        Args:
            permissions (_type_): _description_
        """

        def has_permission(self, request, view):
            api_key = str(
                request.META.get("HTTP_API_KEY", "") or request.GET.get("api-key", "")
            )
            return not bool(api_key) and request.user.is_authenticated


class IsAuthenticated(permissions.BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        if bool(request.user and request.user.is_authenticated):
            return True
        raise custom_exceptions.UnAuthenticated(
            _("Authentication credentials were not provided")
        )
