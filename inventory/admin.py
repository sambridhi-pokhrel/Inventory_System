from django.contrib import admin
from .models import Item

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'price', 'stock_status_display', 'total_value')
    list_filter = ('quantity',)
    search_fields = ('name',)
    ordering = ('name',)
    
    fieldsets = (
        ('Item Information', {
            'fields': ('name', 'quantity', 'price')
        }),
    )
    
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
        return f"${obj.quantity * obj.price:.2f}"
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