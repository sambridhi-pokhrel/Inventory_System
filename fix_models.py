with open('inventory/models.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start = None
for i, l in enumerate(lines):
    if l.strip() == 'class StockAdjustment(models.Model):':
        start = i
        break

if start is None:
    print('StockAdjustment class not found!')
else:
    new_lines = lines[:start]
    new_lines.append('\n\nclass StockAdjustment(models.Model):\n')
    new_lines.append('    ADJUSTMENT_TYPES = [\n')
    new_lines.append("        ('add',    'Add Stock'),\n")
    new_lines.append("        ('remove', 'Remove Stock'),\n")
    new_lines.append('    ]\n')
    new_lines.append('\n')
    new_lines.append("    item            = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='adjustments')\n")
    new_lines.append('    adjustment_type = models.CharField(max_length=10, choices=ADJUSTMENT_TYPES)\n')
    new_lines.append('    quantity        = models.PositiveIntegerField()\n')
    new_lines.append('    reason          = models.CharField(max_length=200)\n')
    new_lines.append('    notes           = models.TextField(blank=True, null=True)\n')
    new_lines.append('    quantity_before = models.IntegerField()\n')
    new_lines.append('    quantity_after  = models.IntegerField()\n')
    new_lines.append('    adjusted_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)\n')
    new_lines.append('    adjusted_at     = models.DateTimeField(auto_now_add=True)\n')
    new_lines.append('\n')
    new_lines.append('    class Meta:\n')
    new_lines.append('        ordering = [\"-adjusted_at\"]\n')
    new_lines.append('\n')
    new_lines.append('    def __str__(self):\n')
    new_lines.append('        return f\"{self.adjustment_type} {self.quantity} - {self.item.name}\"\n')

    with open('inventory/models.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print('Fixed! Now run: python manage.py makemigrations')