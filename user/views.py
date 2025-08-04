from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings

from .models import User, CreatorProfile, CreatorPost
from .permissions import IsAdmin
from .serializers import (
    CreatorSignupSerializer,
    AdminSignupSerializer,
    LoginSerializer,
    GoogleAuthSerializer,
    FanAccessSerializer,
    CreatorPostSerializer
)
from bwt.models import CreditCard
from bwt.serializers import CreditCardSerializer

# ---------------------------
# CREATOR SIGNUP VIEW
# ---------------------------
class CreatorSignupView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = CreatorSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            creator_profile = user.creator_profile

            return Response({
                "message": "Creator account created successfully!",
                "access_code": creator_profile.access_code,
                "full_name": user.full_name,
                "profile_picture": request.build_absolute_uri(creator_profile.profile_picture.url) if creator_profile.profile_picture else None
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ---------------------------
# ADMIN SIGNUP VIEW
# ---------------------------
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import AdminSignupSerializer


class AdminSignupView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = AdminSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            return Response({
                "message": "Admin account created successfully!",
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
                "refresh": str(refresh),
                "access": str(access)
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)







# ---------------------------
# LOGIN VIEW (JWT)
# ---------------------------
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            if user.role not in [User.ROLE.ADMIN, User.ROLE.CREATOR]:
                return Response({"error": "Login restricted to creators and admins."}, status=403)

            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
            })
        return Response(serializer.errors, status=400)

# ---------------------------
# GOOGLE AUTH VIEW (JWT)
# ---------------------------
@authentication_classes([])
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

                if user.role not in [User.ROLE.ADMIN, User.ROLE.CREATOR]:
                    return Response({"error": "Access restricted to creators or admins."}, status=403)

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

# ---------------------------
# FAN ACCESS VIEW (No Auth)
# ---------------------------
class FanAccessView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = FanAccessSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.validated_data['creator_profile']
            posts = CreatorPost.objects.filter(creator=profile.user)
            post_data = CreatorPostSerializer(posts, many=True).data

            profile_pic_url = request.build_absolute_uri(profile.profile_picture.url) if profile.profile_picture else None

            return Response({
                "creator_name": profile.user.full_name,
                "creator_email": profile.user.email,
                "bio": profile.bio,
                "access_code": profile.access_code,
                "profile_pic": profile_pic_url,
                "posts": post_data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ---------------------------
# LIST USERS (ADMIN-ONLY)
# ---------------------------
class ListUsersView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        users = User.objects.all()
        user_data = [
            {"email": user.email, "full_name": user.full_name, "role": user.role}
            for user in users
        ]
        return Response(user_data, status=status.HTTP_200_OK)

# ---------------------------
# POST CREATION VIEW (JWT Protected)
# ---------------------------
# Update your views.py
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CreatorPost
from .serializers import CreatorPostSerializer
from django.shortcuts import get_object_or_404
from .models import CreatorProfile  # or wherever your Creator model is
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

class CreatorContentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, creator_id):
        try:
            logger.info(f"Fetching content for creator_id: {creator_id}")
            logger.info(f"Requested by user: {request.user}")
            
            # Get creator profile
            creator_profile = get_object_or_404(CreatorProfile, id=creator_id)
            creator_user = creator_profile.user
            
            logger.info(f"Found creator: {creator_user}")
            
            # Get posts for this creator
            posts = CreatorPost.objects.filter(creator=creator_user).order_by('-created_at')
            logger.info(f"Found {posts.count()} posts")
            
            # Serialize the posts
            serializer = CreatorPostSerializer(posts, many=True, context={'request': request})
            
            logger.info(f"Serialized data: {serializer.data}")
            
            return Response(serializer.data)
            
        except CreatorProfile.DoesNotExist:
            logger.error(f"Creator profile with id {creator_id} not found")
            return JsonResponse({'error': 'Creator not found'}, status=404)
        except Exception as e:
            logger.error(f"Error fetching creator content: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
# ADMIN CREDIT CARD VIEW (Visible to Admins only)
# ---------------------------
class AdminCreditCardListView(generics.ListAPIView):
    serializer_class = CreditCardSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return CreditCard.objects.all()
