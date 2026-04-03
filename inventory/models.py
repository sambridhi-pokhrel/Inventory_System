from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.core.files.base import ContentFile
import requests
import logging

logger = logging.getLogger(__name__)


class ActiveManager(models.Manager):
    """Manager that returns only active (non-deleted) records by default"""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Item(models.Model):
    name = models.CharField(max_length=100)
    supplier = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    sku = models.CharField(max_length=50, unique=True, db_index=True, null=True, blank=True, help_text="Stock Keeping Unit - Unique identifier")
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Cost price per unit")
    reorder_level = models.IntegerField(default=10)
    lead_time_days = models.IntegerField(default=7)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    # Soft delete field
    is_active = models.BooleanField(default=True, help_text="Set to False to soft delete")

    # Audit trail fields
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_items')
    
    # Managers
    objects = ActiveManager()  # Default manager returns only active items
    all_objects = models.Manager()  # Use this to get all items including deleted

    def __str__(self):
        return f"{self.name} (SKU: {self.sku})"
    
    @classmethod
    def get_by_sku(cls, sku):
        """
        Lookup item by SKU
        
        Args:
            sku (str): Stock Keeping Unit
            
        Returns:
            Item: Item object or None if not found
        """
        try:
            return cls.objects.get(sku=sku)
        except cls.DoesNotExist:
            return None
    
    def delete(self, *args, **kwargs):
        """Soft delete: mark as inactive instead of deleting"""
        self.is_active = False
        self.save()
    
    def hard_delete(self):
        """Permanently delete the record"""
        super().delete()
    
    def generate_sku(self):
        """Generate a unique SKU based on item name and ID"""
        import re
        # Clean name: remove special chars, convert to uppercase
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', self.name).upper()[:10]
        # Use timestamp for uniqueness
        from django.utils import timezone
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        return f"{clean_name}-{timestamp}"

    def save(self, *args, **kwargs):
        # Auto-generate SKU if not provided
        if not self.sku:
            self.sku = self.generate_sku()
        
        if not self.image or not self.image.name:
            try:
                from .image_fetcher import image_fetcher
                result = image_fetcher.fetch_product_image(self.name)
                
                if result:
                    image_content, filename = result
                    self.image.save(filename, image_content, save=False)
            except Exception as e:
                logger.warning(f"Failed to fetch image for {self.name}: {e}")
                pass

        super().save(*args, **kwargs)

    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level

    @property
    def profit_per_unit(self):
        """Calculate profit per unit (selling price - cost price)"""
        return self.price - self.cost_price

    @property
    def stock_status(self):
        """Returns stock status for display"""
        if self.quantity == 0:
            return "out-of-stock"
        elif self.quantity <= self.reorder_level:
            return "low-stock"
        else:
            return "in-stock"

    def get_image_url(self):
        """Return image URL or placeholder if no image exists"""
        if self.image:
            return self.image.url
        return '/static/images/no-image-placeholder.svg'

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
            from .ml_predictor import ml_predictor
            recommendation = ml_predictor.calculate_reorder_recommendation(self)
            return recommendation['needs_reorder']
        except Exception as e:
            logger.error(f"AI prediction failed for {self.name}: {e}")
            return self.quantity <= self.reorder_level or self.quantity == 0

    @property
    def ai_reorder_info(self):
        """Get detailed AI-based reorder information"""
        try:
            from .ml_predictor import ml_predictor
            return ml_predictor.calculate_reorder_recommendation(self)
        except Exception as e:
            logger.error(f"AI reorder info failed for {self.name}: {e}")
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
            logger.error(f"AI demand forecast failed for {self.name}: {e}")
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
            logger.error(f"AI model training failed for {self.name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @property
    def suggested_reorder_quantity(self):
        """Suggest reorder quantity"""
        if self.needs_reorder:
            predicted_needed = self.get_predicted_stock_needed()
            shortage = max(0, predicted_needed - self.quantity)
            return max(1, int(shortage * 1.2))
        return 0



class Supplier(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Soft delete field
    is_active = models.BooleanField(default=True, help_text="Set to False to soft delete")
    
    # Audit trail fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_suppliers')
    
    # Managers
    objects = ActiveManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.name
    
    def delete(self, *args, **kwargs):
        """Soft delete: mark as inactive instead of deleting"""
        self.is_active = False
        self.save()
    
    def hard_delete(self):
        """Permanently delete the record"""
        super().delete()


class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Soft delete field
    is_active = models.BooleanField(default=True, help_text="Set to False to soft delete")
    
    # Audit trail fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_customers')
    
    # Managers
    objects = ActiveManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.name
    
    def delete(self, *args, **kwargs):
        """Soft delete: mark as inactive instead of deleting"""
        self.is_active = False
        self.save()
    
    def hard_delete(self):
        """Permanently delete the record"""
        super().delete()


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
        ('ESEWA', 'eSewa'),
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
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Soft delete field
    is_active = models.BooleanField(default=True, help_text="Set to False to soft delete")

    # Supplier and Customer tracking
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Managers
    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.transaction_type} - {self.item.name} ({self.quantity}) - {self.payment_status}"
    
    def delete(self, *args, **kwargs):
        """Soft delete: mark as inactive instead of deleting"""
        self.is_active = False
        self.save()
    
    def hard_delete(self):
        """Permanently delete the record"""
        super().delete()
    
    @property
    def total_profit(self):
        """Calculate total profit for SALE transactions"""
        if self.transaction_type == 'SALE':
            profit_per_unit = self.unit_price - self.item.cost_price
            return profit_per_unit * self.quantity
        return Decimal('0.00')

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be positive")

        if self.unit_price <= 0:
            raise ValidationError("Unit price must be positive")

        if self.transaction_type == 'SALE' and self.payment_status == 'PAID':
            if self.item.quantity < self.quantity:
                raise ValidationError(f"Insufficient stock. Available: {self.item.quantity}")

    def save(self, *args, **kwargs):
        self.total_amount = Decimal(str(self.quantity)) * Decimal(str(self.unit_price))
        self.clean()

        is_new = self.pk is None

        if not is_new:
            try:
                old_transaction = Transaction.objects.get(pk=self.pk)
                status_changed_to_paid = (
                    old_transaction.payment_status != 'PAID' and
                    self.payment_status == 'PAID'
                )
            except Transaction.DoesNotExist:
                status_changed_to_paid = False
        else:
            status_changed_to_paid = self.payment_status == 'PAID'

        with transaction.atomic():
            if status_changed_to_paid:
                if self.transaction_type == 'SALE':
                    self.item.quantity -= self.quantity
                elif self.transaction_type == 'PURCHASE':
                    self.item.quantity += self.quantity
                    # Auto-update cost price when purchasing
                    self.item.cost_price = self.unit_price

                if self.item.quantity < 0:
                    raise ValidationError("Stock cannot be negative")

                self.item.save()

            super().save(*args, **kwargs)
    
    @classmethod
    def total_sales_for_month(cls, year, month):
        """
        Calculate total sales amount for a specific month
        
        Args:
            year (int): Year (e.g., 2026)
            month (int): Month (1-12)
            
        Returns:
            Decimal: Total sales amount for the month
        """
        from django.db.models import Sum
        
        result = cls.objects.filter(
            transaction_type='SALE',
            payment_status='PAID',
            timestamp__year=year,
            timestamp__month=month
        ).aggregate(total=Sum('total_amount'))
        
        return result['total'] or Decimal('0.00')
    
    @classmethod
    def total_purchases_for_month(cls, year, month):
        """
        Calculate total purchases amount for a specific month
        
        Args:
            year (int): Year (e.g., 2026)
            month (int): Month (1-12)
            
        Returns:
            Decimal: Total purchases amount for the month
        """
        from django.db.models import Sum
        
        result = cls.objects.filter(
            transaction_type='PURCHASE',
            payment_status='PAID',
            timestamp__year=year,
            timestamp__month=month
        ).aggregate(total=Sum('total_amount'))
        
        return result['total'] or Decimal('0.00')
    
    @classmethod
    def total_profit_for_month(cls, year, month):
        """
        Calculate total profit for a specific month (only from SALE transactions)
        
        Args:
            year (int): Year (e.g., 2026)
            month (int): Month (1-12)
            
        Returns:
            Decimal: Total profit for the month
        """
        sales = cls.objects.filter(
            transaction_type='SALE',
            payment_status='PAID',
            timestamp__year=year,
            timestamp__month=month
        ).select_related('item')
        
        total_profit = sum(sale.total_profit for sale in sales)
        return Decimal(str(total_profit))
    
    @classmethod
    def get_monthly_report(cls, year, month):
        """
        Get comprehensive monthly report with sales, purchases, and profit
        
        Args:
            year (int): Year (e.g., 2026)
            month (int): Month (1-12)
            
        Returns:
            dict: Dictionary containing sales, purchases, profit, and transaction counts
        """
        from django.db.models import Count
        
        sales_total = cls.total_sales_for_month(year, month)
        purchases_total = cls.total_purchases_for_month(year, month)
        profit_total = cls.total_profit_for_month(year, month)
        
        # Get transaction counts
        sales_count = cls.objects.filter(
            transaction_type='SALE',
            payment_status='PAID',
            timestamp__year=year,
            timestamp__month=month
        ).count()
        
        purchases_count = cls.objects.filter(
            transaction_type='PURCHASE',
            payment_status='PAID',
            timestamp__year=year,
            timestamp__month=month
        ).count()
        
        return {
            'year': year,
            'month': month,
            'total_sales': sales_total,
            'total_purchases': purchases_total,
            'total_profit': profit_total,
            'net_cash_flow': sales_total - purchases_total,
            'sales_count': sales_count,
            'purchases_count': purchases_count,
            'total_transactions': sales_count + purchases_count
        }




class StockAdjustment(models.Model):
    ADJUSTMENT_TYPES = [
        ('add',    'Add Stock'),
        ('remove', 'Remove Stock'),
    ]

    item            = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='adjustments')
    adjustment_type = models.CharField(max_length=10, choices=ADJUSTMENT_TYPES)
    quantity        = models.PositiveIntegerField()
    reason          = models.CharField(max_length=200)
    notes           = models.TextField(blank=True, null=True)
    quantity_before = models.IntegerField()
    quantity_after  = models.IntegerField()
    adjusted_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    adjusted_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-adjusted_at"]

    def __str__(self):
        return f"{self.adjustment_type} {self.quantity} - {self.item.name}"
