#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
django.setup()

from inventory.models import Item

# Add some test data
test_items = [
    {'name': 'Laptop Computer', 'quantity': 25, 'price': 899.99},
    {'name': 'Wireless Mouse', 'quantity': 5, 'price': 29.99},  # Low stock
    {'name': 'USB Cable', 'quantity': 0, 'price': 12.50},  # Out of stock
    {'name': 'Monitor 24"', 'quantity': 15, 'price': 249.99},
    {'name': 'Keyboard Mechanical', 'quantity': 8, 'price': 89.99},  # Low stock
    {'name': 'Webcam HD', 'quantity': 0, 'price': 59.99},  # Out of stock
    {'name': 'Headphones', 'quantity': 30, 'price': 79.99},
    {'name': 'Smartphone', 'quantity': 12, 'price': 699.99},
    {'name': 'Tablet', 'quantity': 3, 'price': 399.99},  # Low stock
    {'name': 'Charger Cable', 'quantity': 50, 'price': 19.99},
]

print("Adding test inventory items...")
for item_data in test_items:
    item, created = Item.objects.get_or_create(
        name=item_data['name'],
        defaults={
            'quantity': item_data['quantity'],
            'price': item_data['price']
        }
    )
    if created:
        print(f"✓ Added: {item.name} (Qty: {item.quantity}, Price: ${item.price})")
    else:
        print(f"- Already exists: {item.name}")

print(f"\nTotal items in inventory: {Item.objects.count()}")
print(f"Low stock items: {Item.objects.filter(quantity__lte=10, quantity__gt=0).count()}")
print(f"Out of stock items: {Item.objects.filter(quantity=0).count()}")