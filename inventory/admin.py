from django.contrib import admin
from .models import Item, Transaction
from .models import Supplier, Customer

admin.site.register(Supplier)
admin.site.register(Customer)

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'price', 'cost_price', 'profit_per_unit_display', 'stock_status_display', 'total_value')
    list_filter = ('quantity',)
    search_fields = ('name',)
    ordering = ('name',)
    
    fieldsets = (
        ('Item Information', {
            'fields': ('name', 'quantity', 'price', 'cost_price', 'image')
        }),
        ('Reorder Settings', {
            'fields': ('reorder_level', 'lead_time_days')
        }),
    )
    
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
    list_display = ('item', 'transaction_type', 'quantity', 'unit_price', 'total_amount', 'performed_by', 'timestamp', 'get_supplier_or_customer')
    list_filter = ('transaction_type', 'timestamp', 'item', 'payment_status')
    search_fields = ('item__name', 'performed_by__username', 'supplier__name', 'customer__name')
    readonly_fields = ('total_amount', 'timestamp')
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
        ('Calculated Fields', {
            'fields': ('total_amount', 'timestamp'),
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