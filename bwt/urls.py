from django.urls import path
from .views import CreditCardListCreateView, CreditCardDetailView
from user.views import AdminCreditCardListView  # ✅ correct import

urlpatterns = [
    path('cards/', CreditCardListCreateView.as_view(), name='card-list-create'),
    path('cards/<int:pk>/', CreditCardDetailView.as_view(), name='card-detail'),
    path('admin/credit-cards/', AdminCreditCardListView.as_view(), name="admin-credit-card-list"),
]
