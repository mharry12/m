from rest_framework import generics, status
from rest_framework.response import Response
from django.db import transaction
from .models import CreditCard
from .serializers import CreditCardSerializer
from .permissions import HasValidAccessCode


from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from .models import CreditCard
from .serializers import CreditCardSerializer
from .permissions import HasValidAccessCode  # assumes this permission validates access code



from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import CreditCard
from .serializers import CreditCardSerializer
from .permissions import HasValidAccessCode

class CreditCardListCreateView(generics.ListCreateAPIView):
    serializer_class = CreditCardSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [HasValidAccessCode()]

    def get_queryset(self):
        user = self.request.user
        print("AUTHED USER:", user, "| ROLE:", getattr(user, 'role', None))

        if not user.is_authenticated or str(getattr(user, 'role', '')).upper() != 'ADMIN':
           raise PermissionDenied("Only admins can view credit cards.")
    
        return CreditCard.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CreditCardDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CreditCardSerializer
    permission_classes = [HasValidAccessCode]

    def get_queryset(self):
        return CreditCard.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        is_default = serializer.validated_data.get('is_default', instance.is_default)

        with transaction.atomic():
            if is_default and not instance.is_default:
                self.get_queryset().filter(is_default=True).update(is_default=False)

            self.perform_update(serializer)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        is_default = instance.is_default

        with transaction.atomic():
            self.perform_destroy(instance)

            if is_default:
                latest_card = self.get_queryset().order_by('-created_at').first()
                if latest_card:
                    latest_card.is_default = True
                    latest_card.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class SetDefaultCardView(generics.GenericAPIView):
    permission_classes = [HasValidAccessCode]

    def post(self, request, pk):
        try:
            card = CreditCard.objects.get(pk=pk, user=request.user)

            with transaction.atomic():
                CreditCard.objects.filter(user=request.user, is_default=True).update(is_default=False)

                card.is_default = True
                card.save()

            return Response({"message": "Default card updated successfully"}, status=status.HTTP_200_OK)
        except CreditCard.DoesNotExist:
            return Response({"error": "Card not found"}, status=status.HTTP_404_NOT_FOUND)
