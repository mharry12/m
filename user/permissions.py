from .models import User
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated 
            and str(request.user.role).upper() == str(User.ROLE.ADMIN).upper()
        )


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == User.ROLE.MANAGER)


class IsSupport(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == User.ROLE.SUPPORT)


class IsCreator(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == User.ROLE.CREATOR)


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == User.ROLE.CUSTOMER)


class IsSupportOrAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated and request.user.role in {
                User.ROLE.ADMIN,
                User.ROLE.MANAGER,
                User.ROLE.SUPPORT
            })


from rest_framework import permissions
from .models import User

class IsCreatorOrAdmin(permissions.BasePermission):
    """
    Allows access only to authenticated users with CREATOR or ADMIN role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role in {User.ROLE.CREATOR, User.ROLE.ADMIN}
        )