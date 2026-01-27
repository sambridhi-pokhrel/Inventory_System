from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal

class Item(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
    
    @property
    def is_low_stock(self):
        """Returns True if quantity is 10 or less"""
        return self.quantity <= 10
    
    @property
    def stock_status(self):
        """Returns stock status for display"""
        if self.quantity == 0:
            return "out-of-stock"
        elif self.quantity <= 10:
            return "low-stock"
        else:
            return "in-stock"

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('SALE', 'Sale'),
        ('PURCHASE', 'Purchase'),
    ]
    
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['transaction_type', 'timestamp']),
            models.Index(fields=['item', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.item.name} ({self.quantity})"
    
    def clean(self):
        """Validate transaction data"""
        if self.quantity <= 0:
            raise ValidationError("Quantity must be positive")
        
        if self.unit_price <= 0:
            raise ValidationError("Unit price must be positive")
        
        # Check stock availability for sales
        if self.transaction_type == 'SALE':
            if self.item.quantity < self.quantity:
                raise ValidationError(f"Insufficient stock. Available: {self.item.quantity}")
    
    def save(self, *args, **kwargs):
        # Calculate total amount
        self.total_amount = Decimal(str(self.quantity)) * self.unit_price
        
        # Validate before saving
        self.clean()
        
        # Use atomic transaction to ensure data consistency
        with transaction.atomic():
            # Update item stock based on transaction type
            if self.transaction_type == 'SALE':
                self.item.quantity -= self.quantity
            elif self.transaction_type == 'PURCHASE':
                self.item.quantity += self.quantity
            
            # Ensure stock doesn't go negative
            if self.item.quantity < 0:
                raise ValidationError("Stock cannot be negative")
            
            self.item.save()
            super().save(*args, **kwargs)
