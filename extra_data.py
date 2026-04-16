import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import connection
from inventory.models import Item

admin = User.objects.filter(is_superuser=True).first()
today = timezone.now()

DEMAND = {
    'Laptop':        (1, 3),
    'Headphones':    (3, 6),
    'Smartphone':    (2, 4),
    'Charger Cable': (5, 9),
    'board':         (2, 4),
    'Monitor':       (1, 3),
    'Test Monitor':  (1, 2),
    'Test Keyboard': (2, 4),
    'Tables':        (1, 3),
    'Guitar':        (1, 3),
    'Bag':           (3, 6),
    'Heater':        (2, 4),
}

METHODS = ['KHALTI', 'ESEWA', 'CASH', 'BANK_TRANSFER']
WEIGHTS = [40, 30, 20, 10]

START_OFFSET = 300
END_OFFSET   = 121

created = 0

# Use raw SQL with %% to escape percent signs for MySQL
with connection.cursor() as cursor:
    for item in Item.objects.all():
        base_weekday, base_weekend = DEMAND.get(item.name, (2, 4))
        price = float(item.price)
        cost  = float(item.cost_price) if item.cost_price > 0 else price * 0.6

        print(f"  {item.name}...")

        for day_offset in range(START_OFFSET, END_OFFSET, -1):
            day        = today - timedelta(days=day_offset)
            is_weekend = day.weekday() >= 5
            base       = base_weekend if is_weekend else base_weekday
            trend      = (START_OFFSET - day_offset) / START_OFFSET * 0.5
            noise      = random.choice([-1, 0, 0, 0, 1])
            qty        = max(1, int(base + trend + noise))

            method     = random.choices(METHODS, weights=WEIGHTS)[0]
            unit_price = round(price * random.uniform(0.98, 1.02), 2)
            total      = round(qty * unit_price, 2)
            ts         = day.replace(
                hour=random.randint(9, 18),
                minute=random.randint(0, 59),
                second=0
            )
            note = 'Historical sale extra'

            cursor.execute(
                "INSERT INTO inventory_transaction "
                "(item_id, transaction_type, quantity, unit_price, total_amount, "
                "payment_status, payment_method, performed_by_id, timestamp, updated_at, "
                "notes, is_active, supplier_id, customer_id, payment_reference) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [item.id, 'SALE', qty, unit_price, total,
                 'PAID', method, admin.id, ts, ts,
                 note, 1, None, None, None]
            )
            created += 1

            if day_offset % 21 == 0:
                restock    = random.randint(25, 45)
                unit_cost  = round(cost * random.uniform(0.97, 1.03), 2)
                total_cost = round(restock * unit_cost, 2)
                ts_p       = day.replace(hour=9, minute=0, second=0)
                cursor.execute(
                    "INSERT INTO inventory_transaction "
                    "(item_id, transaction_type, quantity, unit_price, total_amount, "
                    "payment_status, payment_method, performed_by_id, timestamp, updated_at, "
                    "notes, is_active, supplier_id, customer_id, payment_reference) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    [item.id, 'PURCHASE', restock, unit_cost, total_cost,
                     'PAID', 'BANK_TRANSFER', admin.id, ts_p, ts_p,
                     'Historical restock extra', 1, None, None, None]
                )
                created += 1

print(f"\n✅ Created {created} additional transactions (6 more months)!")
print("\nNow retrain:")
print("  from inventory.ml_predictor import train_all_models")
print("  results = train_all_models()")
print("  for name, r in results.items(): print(name, round(r['metrics']['accuracy'], 1))")