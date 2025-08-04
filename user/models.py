from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid

# --- ACCESS CODE GENERATOR ---
def generate_unique_access_code(full_name):
    base = ''.join(full_name.split()).upper()[:4]  # e.g., "JOHN"
    while True:
        random_suffix = uuid.uuid4().hex[:4].upper()  # e.g., "9ABF"
        code = f"{base}{random_suffix}"              # => "JOHN9ABF"
        from .models import CreatorProfile
        if not CreatorProfile.objects.filter(access_code=code).exists():
            return code


# --- USER MANAGER ---
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user  # 🔥 No CreatorProfile creation here

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


# --- USER MODEL ---
class User(AbstractBaseUser, PermissionsMixin):
    class ROLE:
        ADMIN = 'ADMIN'
        MANAGER = 'MANAGER'
        SUPPORT = 'SUPPORT'
        CUSTOMER = 'CUSTOMER'
        CREATOR = 'CREATOR'

        CHOICES = [
            (ADMIN, 'Admin'),
            (MANAGER, 'Manager'),
            (SUPPORT, 'Support'),
            (CUSTOMER, 'Customer'),
            (CREATOR, 'Creator'),
        ]

    email = models.EmailField(unique=True)
    access_code = models.CharField(max_length=100, unique=True, null=True, blank=True)

    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE.CHOICES, default=ROLE.CUSTOMER)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if self.access_code:
            self.access_code = self.access_code.strip()  # Clean whitespace
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


# --- CREATOR PROFILE ---
class CreatorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='creator_profile')
    access_code = models.CharField(max_length=20, unique=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to="profile_pics/", null=True, blank=True)

    def __str__(self):
        return f"{self.user.full_name}'s Profile"


class CreatorPost(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'CREATOR'})
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video = models.FileField(upload_to='creator_videos/', blank=True, null=True)
    image = models.ImageField(upload_to='creator_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
      return f"{self.title} by {self.creator.full_name}"
