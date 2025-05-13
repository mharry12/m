from .models import User
from rest_framework.permissions import BasePermission



class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == User.ROLE.ADMIN)

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == User.ROLE.MANAGER)

class IsSupport(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == User.ROLE.SUPPORT)

class IsSupportorIsAdminorIsManager(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated and request.user.role in {
                User.ROLE.MANAGER,
                User.ROLE.SUPPORT,
                User.ROLE.ADMIN
            })
