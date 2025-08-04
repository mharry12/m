from django.db import models
from django.conf import settings

class CreditCard(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    card_holder_name = models.CharField(max_length=255)
    digit = models.CharField(max_length=18)
    brand = models.CharField(max_length=50)  # e.g., Visa, MasterCard
    exp_month = models.IntegerField()
    exp_year = models.IntegerField()
    cvv = models.CharField(max_length=4)
    is_default = models.BooleanField(default=False)
    
    # Billing Address fields
    billing_address_line1 = models.CharField(max_length=255)
    billing_address_line2 = models.CharField(max_length=255, blank=True, null=True)
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=100)
    billing_postal_code = models.CharField(max_length=20)
    billing_country = models.CharField(max_length=100)
    
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def last4(self):
        return self.digit[-4:] if self.digit else ""

    def __str__(self):
        return f"{self.brand} ending in {self.last4}"