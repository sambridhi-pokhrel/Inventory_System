# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0012_customer_is_active_item_is_active_supplier_is_active_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='sku',
            field=models.CharField(blank=True, db_index=True, help_text='Stock Keeping Unit - Unique identifier', max_length=50, null=True, unique=True),
        ),
    ]
