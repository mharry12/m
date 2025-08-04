from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, CreatorProfile
import uuid
from rest_framework import serializers
from .models import User, CreatorProfile, generate_unique_access_code

class CreatorSignupSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(write_only=True, required=False)  # ← NEW

    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'profile_picture']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        profile_picture = validated_data.pop('profile_picture', None)  # ← handle image separately
        validated_data['role'] = User.ROLE.CREATOR
        validated_data['is_active'] = True

        user = User.objects.create_user(**validated_data)

        # generate access code
        access_code = generate_unique_access_code(user.full_name)

        # create profile with optional image
        CreatorProfile.objects.create(
            user=user,
            access_code=access_code,
            profile_picture=profile_picture
        )

        return user





# ----------------------
# ADMIN SIGNUP SERIALIZER
# ----------------------
class AdminSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'full_name']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['role'] = User.ROLE.ADMIN
        validated_data['is_staff'] = True
        validated_data['is_superuser'] = True
        validated_data['is_active'] = True
        user = User.objects.create_user(**validated_data)
        return user


# ----------------------
# FAN ACCESS SERIALIZER
# ----------------------
class FanAccessSerializer(serializers.Serializer):
    email = serializers.EmailField()
    access_code = serializers.CharField()

    def validate(self, data):
        access_code = data.get("access_code")
        try:
            profile = CreatorProfile.objects.select_related('user').get(access_code=access_code)
        except CreatorProfile.DoesNotExist:
            raise serializers.ValidationError("Invalid access code.")
        data['creator_profile'] = profile
        return data


# ----------------------
# CREATOR PROFILE SERIALIZER (OPTIONAL)
# ----------------------
class CreatorProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name')
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = CreatorProfile
        fields = ['full_name', 'email', 'bio', 'access_code']


# ----------------------
# LOGIN SERIALIZER
# ----------------------
from rest_framework import serializers

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        
        # Include the user object in the validated data
        data['user'] = user
        return data



# ----------------------
# GOOGLE AUTH SERIALIZER
# ----------------------
class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()


from rest_framework import serializers
from .models import CreatorPost
from rest_framework.exceptions import PermissionDenied

class CreatorPostSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = CreatorPost
        fields = [
            'id', 'title', 'description',
            'video', 'image', 'created_at',
            'image_url', 'video_url', 'likes_count', 
            'comments_count', 'duration'
        ]
        read_only_fields = ['id', 'created_at', 'creator']

    def validate(self, data):
        request = self.context.get('request')
        if request and request.user.role != 'CREATOR':
            raise PermissionDenied("Only creators can post content")
        return data

    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_video_url(self, obj):
        request = self.context.get('request')
        if obj.video and hasattr(obj.video, 'url'):
            return request.build_absolute_uri(obj.video.url)
        return None
    
    def get_likes_count(self, obj):
        # Add your logic here or return 0 for now
        return getattr(obj, 'likes_count', 0)
    
    def get_comments_count(self, obj):
        # Add your logic here or return 0 for now  
        return getattr(obj, 'comments_count', 0)
    
    def get_duration(self, obj):
        # Add your logic for video duration or return None
        return getattr(obj, 'duration', None)