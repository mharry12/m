# urls.py
from django.urls import path
from .views import (
    CreatorSignupView,
    AdminSignupView, 
    LoginView,
    GoogleLoginView,
    FanAccessView,
    ListUsersView,
    CreatorContentView,
    AdminCreatorListView,
    AdminCreatorDetailView,
    AdminStatsView,
    AdminCreditCardListView,
)

urlpatterns = [
    # Authentication endpoints
    path('login/', LoginView.as_view(), name='login'),
    path('google-login/', GoogleLoginView.as_view(), name='google_login'),
    
    # Public creator signup
    path('creator/signup/', CreatorSignupView.as_view(), name='creator_signup'),
    
    # Admin signup
    path('admin/signup/', AdminSignupView.as_view(), name='admin_signup'),
    
    # Fan access (public)
    path('fan/access/', FanAccessView.as_view(), name='fan_access'),
    
    # Creator content
    path('creator/<int:creator_id>/content/', CreatorContentView.as_view(), name='creator_content'),
    
    # Admin endpoints
    path('admin/users/', ListUsersView.as_view(), name='admin_users'),
    path('admin/creators/', AdminCreatorListView.as_view(), name='admin_creators'),
    path('admin/creators/<int:creator_id>/', AdminCreatorDetailView.as_view(), name='admin_creator_detail'),
    path('admin/stats/', AdminStatsView.as_view(), name='admin_stats'),
    path('admin/cards/', AdminCreditCardListView.as_view(), name='admin_cards'),
]