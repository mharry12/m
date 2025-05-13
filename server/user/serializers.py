# user/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User

# ----------------------
# USER SIGNUP SERIALIZER
# ----------------------
class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'full_name']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
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
# LOGIN SERIALIZER
# ----------------------
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        data['user'] = user
        return data


# ----------------------
# GOOGLE AUTH SERIALIZER
# ----------------------
class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()
