from django.db import models

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
