from django.urls import path
from .views import (
    CreatorSignupView,
    AdminSignupView,
    LoginView,
    GoogleLoginView,
    FanAccessView,
    ListUsersView,
)
from .views import CreatorContentView



urlpatterns = [
    path('creator/signup/', CreatorSignupView.as_view(), name="creator-signup"),
    path('admin/signup/', AdminSignupView.as_view(), name="admin-signup"),
    path('login/', LoginView.as_view(), name="login"),
    path('google-login/', GoogleLoginView.as_view(), name="google-login"),
    path('fan/access/', FanAccessView.as_view(), name="fan-access"),
    path('admin/users/', ListUsersView.as_view(), name="list-users"),



    path('creator-posts/<int:creator_id>/', CreatorContentView.as_view(), name='creator-posts'),

]
