from django.db import connection
from inventory.ml_predictor import train_all_models

with connection.cursor() as cursor:
    cursor.execute("DELETE FROM inventory_transaction WHERE notes LIKE 'Historical%'")
    print(f"Cleared historical transactions")

exec(open('better_data.py').read())

results = train_all_models()
for name, r in results.items():
    print(name, round(r['metrics']['accuracy'], 1))