from django.contrib import admin
from .models import Item, Transaction, Supplier, Customer

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'created_at', 'updated_at', 'created_by')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Supplier Information', {
            'fields': ('name', 'email', 'phone', 'address')
        }),
        ('Audit Trail', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Automatically set created_by when creating new supplier"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'created_at', 'updated_at', 'created_by')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('name', 'email', 'phone', 'address')
        }),
        ('Audit Trail', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Automatically set created_by when creating new customer"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'price', 'cost_price', 'profit_per_unit_display', 'stock_status_display', 'created_at', 'created_by')
    list_filter = ('quantity', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Item Information', {
            'fields': ('name', 'quantity', 'price', 'cost_price', 'image')
        }),
        ('Reorder Settings', {
            'fields': ('reorder_level', 'lead_time_days')
        }),
        ('Audit Trail', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Automatically set created_by when creating new item"""
        if not change:  # Only set on creation, not on update
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def profit_per_unit_display(self, obj):
        """Display profit per unit"""
        profit = obj.profit_per_unit
        if profit > 0:
            return f"Rs. {profit:,.2f}"
        elif profit < 0:
            return f"-Rs. {abs(profit):,.2f}"
        else:
            return "Rs. 0.00"
    profit_per_unit_display.short_description = 'Profit/Unit'
    
    def stock_status_display(self, obj):
        """Display stock status with color coding"""
        status = obj.stock_status
        if status == 'out-of-stock':
            return '🔴 Out of Stock'
        elif status == 'low-stock':
            return '🟡 Low Stock'
        else:
            return '🟢 In Stock'
    stock_status_display.short_description = 'Stock Status'
    
    def total_value(self, obj):
        """Calculate total value of this item"""
        return f"Rs. {obj.quantity * obj.price:,.2f}"
    total_value.short_description = 'Total Value'
    
    # Add custom actions
    actions = ['mark_as_low_stock', 'restock_items']
    
    def mark_as_low_stock(self, request, queryset):
        """Mark selected items as low stock (set quantity to 5)"""
        updated = queryset.update(quantity=5)
        self.message_user(request, f'{updated} items marked as low stock.')
    mark_as_low_stock.short_description = "Mark selected items as low stock"
    
    def restock_items(self, request, queryset):
        """Restock selected items (add 50 to quantity)"""
        for item in queryset:
            item.quantity += 50
            item.save()
        self.message_user(request, f'{queryset.count()} items restocked (+50 each).')
    restock_items.short_description = "Restock selected items (+50)"

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('item', 'transaction_type', 'quantity', 'unit_price', 'total_amount', 'performed_by', 'timestamp', 'updated_at', 'get_supplier_or_customer')
    list_filter = ('transaction_type', 'timestamp', 'updated_at', 'item', 'payment_status')
    search_fields = ('item__name', 'performed_by__username', 'supplier__name', 'customer__name')
    readonly_fields = ('total_amount', 'timestamp', 'updated_at')
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('item', 'transaction_type', 'quantity', 'unit_price')
        }),
        ('Supplier/Customer Information', {
            'fields': ('supplier', 'customer'),
            'description': 'For PURCHASE: select Supplier. For SALE: select Customer.'
        }),
        ('Payment Information', {
            'fields': ('payment_status', 'payment_method', 'payment_reference')
        }),
        ('Additional Information', {
            'fields': ('performed_by', 'notes')
        }),
        ('Audit Trail', {
            'fields': ('total_amount', 'timestamp', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_supplier_or_customer(self, obj):
        """Display supplier for purchases, customer for sales"""
        if obj.transaction_type == 'PURCHASE' and obj.supplier:
            return f"Supplier: {obj.supplier.name}"
        elif obj.transaction_type == 'SALE' and obj.customer:
            return f"Customer: {obj.customer.name}"
        return "-"
    get_supplier_or_customer.short_description = 'Supplier/Customer'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing transaction
            return self.readonly_fields + ('item', 'transaction_type', 'quantity', 'unit_price', 'performed_by')
        return self.readonly_fields