from rest_framework import serializers
from .models import CreditCard

class CreditCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCard
        fields = [
            'id',
            'card_holder_name',
            'digit',
            'brand',
            'cvv',
            'exp_month',
            'exp_year',
            'is_default',
            'billing_address_line1',
            'billing_address_line2',
            'billing_city',
            'billing_state',
            'billing_postal_code',
            'billing_country',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
        
    def validate_digit(self, value):
        """
        Check that the credit card number contains only digits and has an appropriate length.
        """
        if not value.isdigit():
            raise serializers.ValidationError("Card number must contain only digits.")
        
        # Most credit cards are between 13-19 digits
        if not (13 <= len(value) <= 19):
            raise serializers.ValidationError("Card number must be between 13 and 19 digits.")
            
        return value
    
    def validate_exp_year(self, value):
        """
        Check that the expiration year is not in the past.
        """
        import datetime
        current_year = datetime.datetime.now().year
        
        if value < current_year:
            raise serializers.ValidationError("Card expiration year cannot be in the past.")
            
        return value
    
    def validate(self, data):
        """
        Check that the expiration date (month and year combination) is not in the past.
        Also validate that required billing address fields are not empty.
        """
        import datetime
        
        current_date = datetime.datetime.now()
        exp_month = data.get('exp_month')
        exp_year = data.get('exp_year')
        
        if exp_year == current_date.year and exp_month < current_date.month:
            raise serializers.ValidationError({"exp_month": "Card has expired."})
        
        # Validate billing address fields
        required_billing_fields = [
            'billing_address_line1',
            'billing_city',
            'billing_state',
            'billing_postal_code',
            'billing_country'
        ]
        
        errors = {}
        for field in required_billing_fields:
            if field in data and not data[field].strip():
                errors[field] = f"{field.replace('billing_', '').replace('_', ' ').title()} is required."
        
        if errors:
            raise serializers.ValidationError(errors)
            
        return data