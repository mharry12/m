from django.contrib.auth.models import BaseUserManager
from django.utils.crypto import get_random_string

class AppUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        """Create and return a regular user or content creator with email and password."""
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        # Automatically create creator profile if this is a content creator
        # if extra_fields.get("is_creator"):
        #     from .models import CreatorProfile
        #     CreatorProfile.objects.create(
        #         user=user,
        #         access_code=get_random_string(10).upper()
        #     )

        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        """Create and return a superuser with admin permissions."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, username, password, **extra_fields)
