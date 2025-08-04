from rest_framework import permissions
from user.models import CreatorProfile
from rest_framework.exceptions import AuthenticationFailed

class HasValidAccessCode(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True  # Skip if already authenticated

        access_code = (
            request.data.get('access_code') or 
            request.headers.get('X-Access-Code') or
            request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        ).strip()
        
        if not access_code:
            raise AuthenticationFailed('Access code missing')
        
        try:
            profile = CreatorProfile.objects.get(access_code=access_code)
            request.user = profile.user
            return True
        except CreatorProfile.DoesNotExist:
            raise AuthenticationFailed('Invalid access code')
