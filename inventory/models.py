from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, timedelta

class Item(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    reorder_level = models.IntegerField(default=10, help_text="Minimum stock level before reorder suggestion")
    lead_time_days = models.IntegerField(default=7, help_text="Days required to restock this item")

    def __str__(self):
        return self.name
    
    @property
    def is_low_stock(self):
        """Returns True if quantity is at or below reorder level"""
        return self.quantity <= self.reorder_level
    
    @property
    def stock_status(self):
        """Returns stock status for display"""
        if self.quantity == 0:
            return "out-of-stock"
        elif self.quantity <= self.reorder_level:
            return "low-stock"
        else:
            return "in-stock"
    
    def get_average_daily_usage(self, days=30):
        """Calculate average daily usage based on sales transactions"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        sales = self.transactions.filter(
            transaction_type='SALE',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        total_sold = sum(sale.quantity for sale in sales)
        return total_sold / days if days > 0 else 0
    
    def get_predicted_stock_needed(self):
        """Predict stock needed for lead time period"""
        daily_usage = self.get_average_daily_usage()
        return daily_usage * self.lead_time_days
    
    @property
    def needs_reorder(self):
        """Check if item needs reordering using AI-based prediction"""
        try:
            # Import here to avoid circular imports
            from .ml_predictor import ml_predictor
            
            # Get AI-powered recommendation
            recommendation = ml_predictor.calculate_reorder_recommendation(self)
            return recommendation['needs_reorder']
            
        except Exception as e:
            # Fallback to basic logic if AI fails
            print(f"AI prediction failed for {self.name}: {e}")
            return self.quantity <= self.reorder_level or self.quantity == 0
    
    @property
    def ai_reorder_info(self):
        """Get detailed AI-based reorder information"""
        try:
            from .ml_predictor import ml_predictor
            return ml_predictor.calculate_reorder_recommendation(self)
        except Exception as e:
            return {
                'needs_reorder': self.quantity <= self.reorder_level,
                'ai_powered': False,
                'error': str(e)
            }
    
    def get_ai_demand_forecast(self, days=7):
        """Get AI-powered demand forecast"""
        try:
            from .ml_predictor import ml_predictor
            return ml_predictor.predict_future_demand(self, days)
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def train_ai_model(self):
        """Train AI model for this specific item"""
        try:
            from .ml_predictor import ml_predictor
            return ml_predictor.train_demand_model(self)
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @property
    def suggested_reorder_quantity(self):
        """Suggest reorder quantity"""
        if self.needs_reorder:
            predicted_needed = self.get_predicted_stock_needed()
            shortage = predicted_needed - self.quantity
            # Add 20% buffer
            return int(shortage * 1.2)
        return 0

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('SALE', 'Sale'),
        ('PURCHASE', 'Purchase'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('PAID', 'Paid'),
        ('PENDING', 'Pending'),
        ('FAILED', 'Failed'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('KHALTI', 'Khalti'),
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CREDIT', 'Credit'),
    ]
    
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='KHALTI')
    payment_reference = models.CharField(max_length=100, blank=True, null=True, help_text="Payment gateway reference ID")
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['transaction_type', 'timestamp']),
            models.Index(fields=['item', 'timestamp']),
            models.Index(fields=['payment_status']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.item.name} ({self.quantity}) - {self.payment_status}"
    
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
    
    def simulate_khalti_payment(self):
        """Simulate Khalti payment processing"""
        import uuid
        if self.payment_method == 'KHALTI':
            # Simulate payment processing
            self.payment_status = 'PAID'
            self.payment_reference = f"KHALTI_{uuid.uuid4().hex[:8].upper()}"
            self.save()
            return True
        return False
    
    def save(self, *args, **kwargs):
        # Calculate total amount - ensure both values are Decimal
        from decimal import Decimal
        self.total_amount = Decimal(str(self.quantity)) * Decimal(str(self.unit_price))
        
        # Validate before saving
        self.clean()
        
        # Use atomic transaction to ensure data consistency
        with transaction.atomic():
            # Only update stock if payment is successful or for purchases
            should_update_stock = (
                self.payment_status == 'PAID' or 
                self.transaction_type == 'PURCHASE'
            )
            
            if should_update_stock:
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
