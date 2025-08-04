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

    def post(self, request):
        id_token_from_frontend = request.data.get("access_token")
        if not id_token_from_frontend:
            return Response({"error": "ID token is required"}, status=400)

        try:
            idinfo = id_token.verify_oauth2_token(
                id_token_from_frontend,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            email = idinfo.get("email")
            full_name = idinfo.get("name", "")
            if not email:
                return Response({"error": "Email not provided by Google"}, status=400)

            # If user already exists, fetch; otherwise, create with default role
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": full_name,
                    "is_verified": True,
                    "role": User.ROLE.CUSTOMER,
                }
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
                    "full_name": user.full_name,
                    "email": user.email,
                    "role": user.role,
                },
                "is_new_user": created
            })

        except ValueError:
            return Response({"error": "Invalid or expired Google token"}, status=401)
