# user/urls.py

from django.urls import path
from .views import (
    UserSignupView,
    AdminSignupView,
    LoginView,
    GoogleLoginView,
    ListUsersView,  # Add the ListUsersView here
)

urlpatterns = [
    path('user/signup/', UserSignupView.as_view(), name="user-signup"),
    path('admin/signup/', AdminSignupView.as_view(), name="admin-signup"),
    path('user/login/', LoginView.as_view(), name="user-login"),
    path('user/google-login/', GoogleLoginView.as_view(), name="google-login"),
    path('admin/users/', ListUsersView.as_view(), name="list-users"),  # New URL for listing users
]
