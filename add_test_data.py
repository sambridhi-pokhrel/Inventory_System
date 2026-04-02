"""
Realistic Test Data Generator
==============================
Paste this entire script into: python manage.py shell

Creates 90 days of realistic sales + purchase transactions
so the ML model has enough data to train properly.
Uses direct DB insert to bypass stock validation on historical data.
"""

import random
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import connection
from inventory.models import Item

admin = User.objects.filter(is_superuser=True).first()
print(f"Using admin: {admin.username}\n")

# Daily demand range (min, max units sold per day when sale occurs)
DEMAND = {
    'Laptop':        (1, 2),
    'Headphones':    (1, 4),
    'Smartphone':    (1, 2),
    'Charger Cable': (2, 6),
    'board':         (1, 3),
    'Monitor':       (1, 2),
    'Test Monitor':  (1, 2),
    'Test Keyboard': (1, 3),
    'Tables':        (1, 2),
    'Guitar':        (1, 2),
    'Bag':           (1, 4),
    'Heater':        (1, 3),
}

# Sale probability per day (so not every item sells every day)
SALE_PROB = {
    'Laptop': 0.4, 'Headphones': 0.7, 'Smartphone': 0.35,
    'Charger Cable': 0.85, 'board': 0.6, 'Monitor': 0.4,
    'Test Monitor': 0.3, 'Test Keyboard': 0.55, 'Tables': 0.45,
    'Guitar': 0.35, 'Bag': 0.65, 'Heater': 0.5,
}

today = timezone.now()
DAYS = 90
created = 0

with connection.cursor() as cursor:
    for item in Item.objects.all():
        min_d, max_d = DEMAND.get(item.name, (1, 2))
        prob = SALE_PROB.get(item.name, 0.5)
        price = float(item.price)
        cost  = float(item.cost_price) if item.cost_price > 0 else price * 0.6

        print(f"  {item.name}...")

        for day_offset in range(DAYS, 0, -1):
            day = today - timedelta(days=day_offset)
            weekday = day.weekday()

            # ── Sale ──────────────────────────────────────────────────
            # Higher sale probability on weekends
            effective_prob = prob * (1.3 if weekday >= 5 else 1.0)
            if random.random() < effective_prob:
                qty = random.randint(min_d, max_d)
                unit_price = round(price * random.uniform(0.97, 1.03), 2)
                total = round(qty * unit_price, 2)
                ts = day.replace(
                    hour=random.randint(9, 18),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59),
                )
                cursor.execute("""
                    INSERT INTO inventory_transaction
                        (item_id, transaction_type, quantity, unit_price,
                         total_amount, payment_status, payment_method,
                         performed_by_id, timestamp, updated_at,
                         notes, is_active,
                         supplier_id, customer_id, payment_reference)
                    VALUES (%s,'SALE',%s,%s,%s,'PAID','CASH',%s,%s,%s,%s,1,NULL,NULL,NULL)
                """, [item.id, qty, unit_price, total, admin.id, ts, ts,
                      f'Historical sale day -{day_offset}'])
                created += 1

            # ── Purchase (restock every ~14 days) ─────────────────────
            if day_offset % 14 == 0:
                restock = random.randint(15, 30)
                unit_cost = round(cost * random.uniform(0.95, 1.05), 2)
                total_cost = round(restock * unit_cost, 2)
                ts = day.replace(
                    hour=random.randint(8, 10),
                    minute=random.randint(0, 30),
                    second=0,
                )
                cursor.execute("""
                    INSERT INTO inventory_transaction
                        (item_id, transaction_type, quantity, unit_price,
                         total_amount, payment_status, payment_method,
                         performed_by_id, timestamp, updated_at,
                         notes, is_active,
                         supplier_id, customer_id, payment_reference)
                    VALUES (%s,'PURCHASE',%s,%s,%s,'PAID','BANK_TRANSFER',%s,%s,%s,%s,1,NULL,NULL,NULL)
                """, [item.id, restock, unit_cost, total_cost, admin.id, ts, ts,
                      f'Historical restock day -{day_offset}'])
                created += 1

print(f"\n✅ Created {created} historical transactions!")
print("\nNow train the AI models by running:")
print("  from inventory.ml_predictor import train_all_models; train_all_models()")