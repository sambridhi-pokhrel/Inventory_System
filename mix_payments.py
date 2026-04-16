import random
from django.db import connection

methods = ['KHALTI', 'ESEWA', 'CASH', 'BANK_TRANSFER']
weights = [40, 30, 20, 10]

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT id FROM inventory_transaction
        WHERE notes LIKE '%Historical%'
        AND transaction_type = 'SALE'
    """)
    sale_ids = [row[0] for row in cursor.fetchall()]

    for txn_id in sale_ids:
        method = random.choices(methods, weights=weights)[0]
        cursor.execute("""
            UPDATE inventory_transaction
            SET payment_method = %s
            WHERE id = %s
        """, [method, txn_id])

    print(f"Updated {len(sale_ids)} sale transactions with mixed payment methods")
    print("  ~40% Khalti, ~30% eSewa, ~20% Cash, ~10% Bank Transfer")