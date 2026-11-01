from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from rest_framework import permissions


class IsManagerUser(permissions.BasePermission):
    """
    DRF permission class: Grants access strictly to Manager/Supervisor accounts.
    Employees attempting access receive 403 Forbidden.
    """
    message = "Access restricted to SCALE.Core System Supervisors (Managers)."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_manager
        )


class IsOperationalUser(permissions.BasePermission):
    """
    DRF permission class: Grants access to authenticated users (Managers and Employees).
    """
    message = "Authentication required for operational tasks."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated
        )


class ManagerRequiredMixin(UserPassesTestMixin):
    """
    View mixin requiring Manager role to view the page.
    Raises PermissionDenied (HTTP 403) for non-managers.
    """
    raise_exception = True

    def test_func(self):
        return bool(
            self.request.user and
            self.request.user.is_authenticated and
            self.request.user.is_manager
        )


class OperationalRequiredMixin(UserPassesTestMixin):
    """
    View mixin requiring authenticated user (Employee or Manager).
    """
    raise_exception = True

    def test_func(self):
        return bool(
            self.request.user and
            self.request.user.is_authenticated
        )
