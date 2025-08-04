# backends.py
from django.contrib.auth.backends import BaseBackend
from django.db.models import Q
from .models import User, CreatorProfile

class CustomBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, access_code=None, **kwargs):
        # Access code authentication (for fan access)
        if access_code:
            try:
                # Trim whitespace and check access code
                access_code = access_code.strip()
                profile = CreatorProfile.objects.get(access_code=access_code)
                if profile and profile.user.is_active:
                    return profile.user  # Return creator user
            except CreatorProfile.DoesNotExist:
                return None
        
        # Standard email/password authentication
        if email and password:
            try:
                user = User.objects.get(email=email)
                if user.check_password(password) and user.is_active:
                    return user
            except User.DoesNotExist:
                return None
        
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None