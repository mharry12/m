from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def generate_unique_username(self, base_username):
        base = base_username.replace(" ", "_").lower()
        unique = base
        count = 1
        while User.objects.filter(username=unique).exists():
            unique = f"{base}_{count}"
            count += 1
        return unique

    def post(self, request):
        id_token_from_frontend = request.data.get("access_token")
        if not id_token_from_frontend:
            return Response({"error": "ID token is required"}, status=400)

        try:
            idinfo = id_token.verify_oauth2_token(
                id_token_from_frontend,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID  # Set this in your settings.py
            )

            email = idinfo.get("email")
            username = idinfo.get("name") or email.split("@")[0]
            picture = idinfo.get("picture")

            if not email:
                return Response({"error": "Email not provided by Google"}, status=400)

            unique_username = self.generate_unique_username(username)

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": unique_username,
                    "role": User.ROLE.BASE_USER,
                    "profile_picture": picture,
                },
            )

            if created:
                user.set_unusable_password()
                user.save()

            refresh = RefreshToken.for_user(user)

            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "profile_picture": user.profile_picture,
                },
            })

        except ValueError:
            return Response({"error": "Invalid or expired Google token"}, status=401)
