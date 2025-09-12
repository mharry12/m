from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
import logging

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

logger = logging.getLogger(__name__)

# ---------------------------
# CREATOR SIGNUP (Public)
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
                "email": user.email,
                "profile_picture": request.build_absolute_uri(creator_profile.profile_picture.url)
                    if creator_profile.profile_picture else None
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# ADMIN CREATOR MANAGEMENT
# ---------------------------
class AdminCreatorListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        creators = User.objects.filter(
            role='CREATOR',
            creator_profile__isnull=False
        ).select_related('creator_profile').order_by('-id')

        creators_data = []
        for creator in creators:
            creator_profile = creator.creator_profile
            created_date = getattr(creator, 'date_joined', None) or getattr(creator, 'created_at', None)

            creators_data.append({
                'id': creator.id,
                'email': creator.email,
                'full_name': creator.full_name,
                'access_code': creator_profile.access_code,
                'is_active': creator.is_active,
                'created_at': created_date.isoformat() if created_date else None,
                'profile_picture': request.build_absolute_uri(creator_profile.profile_picture.url)
                    if creator_profile.profile_picture else None,
                'status': 'active' if creator.is_active else 'inactive',
                'bio': creator_profile.bio or ''
            })

        return Response(creators_data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CreatorSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            creator_profile = user.creator_profile
            created_date = getattr(user, 'date_joined', None) or getattr(user, 'created_at', None)

            return Response({
                "message": "Creator account created successfully by admin!",
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "access_code": creator_profile.access_code,
                "is_active": user.is_active,
                "created_at": created_date.isoformat() if created_date else None,
                "profile_picture": request.build_absolute_uri(creator_profile.profile_picture.url)
                    if creator_profile.profile_picture else None,
                "status": 'active' if user.is_active else 'inactive'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminCreatorDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, creator_id):
        creator = get_object_or_404(
            User,
            id=creator_id,
            role='CREATOR',
            creator_profile__isnull=False
        )
        creator_profile = creator.creator_profile
        created_date = getattr(creator, 'date_joined', None) or getattr(creator, 'created_at', None)

        return Response({
            'id': creator.id,
            'email': creator.email,
            'full_name': creator.full_name,
            'access_code': creator_profile.access_code,
            'is_active': creator.is_active,
            'created_at': created_date.isoformat() if created_date else None,
            'profile_picture': request.build_absolute_uri(creator_profile.profile_picture.url)
                if creator_profile.profile_picture else None,
            'status': 'active' if creator.is_active else 'inactive',
            'bio': creator_profile.bio or ''
        }, status=status.HTTP_200_OK)

    def patch(self, request, creator_id):
        creator = get_object_or_404(User, id=creator_id, role='CREATOR')
        if 'is_active' in request.data:
            creator.is_active = request.data['is_active']
        if 'full_name' in request.data:
            creator.full_name = request.data['full_name']
        creator.save()

        if hasattr(creator, 'creator_profile') and 'bio' in request.data:
            creator.creator_profile.bio = request.data['bio']
            creator.creator_profile.save()

        return Response({
            "message": "Creator updated successfully",
            "is_active": creator.is_active,
            "full_name": creator.full_name
        }, status=status.HTTP_200_OK)

    def delete(self, request, creator_id):
        creator = get_object_or_404(User, id=creator_id, role='CREATOR')
        creator.is_active = False
        creator.save()
        return Response({"message": "Creator deactivated successfully"}, status=status.HTTP_200_OK)


# ---------------------------
# ADMIN STATS VIEW
# ---------------------------
class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        total_creators = User.objects.filter(role='CREATOR', creator_profile__isnull=False).count()
        active_creators = User.objects.filter(role='CREATOR', creator_profile__isnull=False, is_active=True).count()
        total_credit_cards = CreditCard.objects.count()
        total_posts = CreatorPost.objects.count()

        now = timezone.now()
        monthly_cards = CreditCard.objects.filter(created_at__month=now.month, created_at__year=now.year).count()
        monthly_creators = User.objects.filter(role='CREATOR', date_joined__month=now.month,
                                               date_joined__year=now.year).count()

        return Response({
            'totalCreators': total_creators,
            'activeCreators': active_creators,
            'totalCreditCards': total_credit_cards,
            'totalPosts': total_posts,
            'monthlyCards': monthly_cards,
            'monthlyCreators': monthly_creators
        }, status=status.HTTP_200_OK)


# ---------------------------
# ADMIN SIGNUP
# ---------------------------
class AdminSignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AdminSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Admin account created successfully!",
                "user_id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# LOGIN
# ---------------------------
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            if user.role not in ['ADMIN', 'CREATOR']:
                return Response({"detail": "Login restricted to creators and admins."},
                                status=status.HTTP_403_FORBIDDEN)

            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user_id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# GOOGLE AUTH
# ---------------------------
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            try:
                idinfo = id_token.verify_oauth2_token(
                    token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
                )
                if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                    raise ValueError('Wrong issuer.')

                email = idinfo.get('email')
                name = idinfo.get('name', '')

                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={'full_name': name, 'is_verified': True}
                )

                if user.role not in ['ADMIN', 'CREATOR']:
                    return Response({"detail": "Access restricted to creators or admins."},
                                    status=status.HTTP_403_FORBIDDEN)

                refresh = RefreshToken.for_user(user)
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user_id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                    'is_new_user': created
                }, status=status.HTTP_200_OK)

            except ValueError as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# FAN ACCESS (Public)
# ---------------------------
class FanAccessView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = FanAccessSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.validated_data['creator_profile']
            posts = CreatorPost.objects.filter(creator=profile.user).order_by('-created_at')
            post_data = CreatorPostSerializer(posts, many=True, context={'request': request}).data
            profile_pic_url = request.build_absolute_uri(profile.profile_picture.url) if profile.profile_picture else None

            return Response({
                "creator_name": profile.user.full_name,
                "creator_email": profile.user.email,
                "bio": profile.bio or '',
                "access_code": profile.access_code,
                "profile_pic": profile_pic_url,
                "posts": post_data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# LIST USERS (Admin only)
# ---------------------------
class ListUsersView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        users = User.objects.all().order_by('-id')
        user_data = []
        for user in users:
            created_date = getattr(user, 'date_joined', None) or getattr(user, 'created_at', None)
            user_data.append({
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "date_joined": created_date.isoformat() if created_date else None
            })
        return Response(user_data, status=status.HTTP_200_OK)


# ---------------------------
# CREATOR CONTENT (JWT protected)
# ---------------------------
class CreatorContentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, creator_id):
        creator_profile = get_object_or_404(CreatorProfile, id=creator_id)
        creator_user = creator_profile.user
        posts = CreatorPost.objects.filter(creator=creator_user).order_by('-created_at')
        serializer = CreatorPostSerializer(posts, many=True, context={'request': request})
        return Response({
            'creator': {
                'id': creator_user.id,
                'full_name': creator_user.full_name,
                'email': creator_user.email,
                'profile_picture': request.build_absolute_uri(creator_profile.profile_picture.url)
                    if creator_profile.profile_picture else None,
                'bio': creator_profile.bio or ''
            },
            'posts': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request, creator_id):
        creator_profile = get_object_or_404(CreatorProfile, id=creator_id)
        creator_user = creator_profile.user

        if request.user.id != creator_user.id and request.user.role != 'ADMIN':
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        post_data = request.data.copy()
        post_data['creator'] = creator_user.id
        serializer = CreatorPostSerializer(data=post_data, context={'request': request})
        if serializer.is_valid():
            post = serializer.save()
            return Response(CreatorPostSerializer(post, context={'request': request}).data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# ADMIN CREDIT CARDS
# ---------------------------
class AdminCreditCardListView(APIView):
    """
    Admin endpoint to view all credit cards
    """
    permission_classes = [IsAuthenticated]

    def check_admin_permission(self, user):
        """Check if user has admin permissions"""
        return hasattr(user, 'role') and user.role == 'ADMIN'

    def get(self, request):
        # Check admin permission first
        if not self.check_admin_permission(request.user):
            return Response(
                {"detail": "Only admin users can access this endpoint"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            credit_cards = CreditCard.objects.all().order_by('-created_at')
            serializer = CreditCardSerializer(credit_cards, many=True)
            
            # Return as a simple array, not wrapped in an object
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching credit cards: {str(e)}")
            return Response(
                {"detail": f"Error fetching credit cards: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )