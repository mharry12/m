from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import CreditCard
from .serializers import CreditCardSerializer
from django.db import transaction

class CreditCardListCreateView(generics.ListCreateAPIView):
    serializer_class = CreditCardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CreditCard.objects.filter(user=self.request.user).order_by('-is_default', '-created_at')

    def perform_create(self, serializer):
        # Handle the default card setting
        is_default = serializer.validated_data.get('is_default', False)
        
        with transaction.atomic():
            # If this card is being set as default, remove default status from other cards
            if is_default:
                self.get_queryset().filter(is_default=True).update(is_default=False)
            
            # If this is the user's first card, make it the default
            elif self.get_queryset().count() == 0:
                serializer.validated_data['is_default'] = True
                
            serializer.save(user=self.request.user)


class CreditCardDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CreditCardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CreditCard.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Handle the default card setting
        is_default = serializer.validated_data.get('is_default', instance.is_default)
        
        with transaction.atomic():
            # If this card is being set as default, remove default status from other cards
            if is_default and not instance.is_default:
                self.get_queryset().filter(is_default=True).update(is_default=False)
                
            self.perform_update(serializer)
            
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        is_default = instance.is_default
        
        with transaction.atomic():
            self.perform_destroy(instance)
            
            # If the deleted card was the default, set the most recent card as default
            if is_default:
                latest_card = self.get_queryset().order_by('-created_at').first()
                if latest_card:
                    latest_card.is_default = True
                    latest_card.save()
                    
        return Response(status=status.HTTP_204_NO_CONTENT)


class SetDefaultCardView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            card = CreditCard.objects.get(pk=pk, user=request.user)
            
            with transaction.atomic():
                # Remove default status from all cards
                CreditCard.objects.filter(user=request.user, is_default=True).update(is_default=False)
                
                # Set the selected card as default
                card.is_default = True
                card.save()
                
            return Response({"message": "Default card updated successfully"}, status=status.HTTP_200_OK)
        except CreditCard.DoesNotExist:
            return Response({"error": "Card not found"}, status=status.HTTP_404_NOT_FOUND)


# user/views.py
# user/views.py
from rest_framework import generics
from .models import CreditCard
from .serializers import CreditCardSerializer
from user.permissions import IsAdmin  # Import the custom permission

class AdminCreditCardListView(generics.ListAPIView):
    serializer_class = CreditCardSerializer
    permission_classes = [IsAdmin]  # Use the custom permission

    def get_queryset(self):
        # Fetch all credit cards for all users
        return CreditCard.objects.all()

