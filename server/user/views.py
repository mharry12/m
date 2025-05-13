from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from rest_framework.decorators import authentication_classes, permission_classes
from google.auth.transport import requests as google_requests
from django.conf import settings



from .models import User
from .serializers import (
    UserSignupSerializer,
    AdminSignupSerializer,
    LoginSerializer,
    GoogleAuthSerializer
)

# ---------------------------
# USER SIGNUP VIEW
# ---------------------------
class UserSignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# ADMIN SIGNUP VIEW
# ---------------------------
class AdminSignupView(APIView):
    permission_classes = [AllowAny]  # Change to IsAdminUser if only admins should access

    def post(self, request):
        serializer = AdminSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Admin account created successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# LOGIN VIEW
# ---------------------------
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


# ---------------------------
# GOOGLE AUTH VIEW
# ---------------------------
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import authentication_classes, permission_classes

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from user.models import User
from user.serializers import GoogleAuthSerializer


@authentication_classes([])  # disable authentication
@permission_classes([AllowAny])
class GoogleLoginView(APIView):
    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            try:
                idinfo = id_token.verify_oauth2_token(
                    token,
                    google_requests.Request(),
                    settings.GOOGLE_CLIENT_ID
                )

                if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                    raise ValueError('Wrong issuer.')

                email = idinfo.get('email')
                name = idinfo.get('name', '')

                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={'full_name': name, 'is_verified': True}
                )

                refresh = RefreshToken.for_user(user)

                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'email': user.email,
                    'name': user.full_name,
                    'is_new_user': created
                })

            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# user/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializers import UserSignupSerializer  # You might want to create a new serializer for listing users
from .permissions import IsAdmin  # Import the custom permission

class ListUsersView(APIView):
    permission_classes = [IsAdmin]  # Only admin can access this view

    def get(self, request):
        users = User.objects.all()  # Fetch all users
        # You can use a serializer to return user data as needed
        # This could be a basic serializer or one that excludes sensitive info
        user_data = [{"email": user.email, "full_name": user.full_name, "role": user.role} for user in users]
        return Response(user_data, status=status.HTTP_200_OK)
