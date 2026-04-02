with open('inventory/templates/inventory/list.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if '{% if item.needs_reorder %}' in line:
        skip = True
        # Add the simple replacement
        indent = '                '
        new_lines.append(indent + '<span class="badge bg-success mb-1"><i class="bi bi-check-circle me-1"></i>Well Stocked</span>\n')
        new_lines.append(indent + '<div><small class="text-muted">{{ item.lead_time_days }}d lead</small></div>\n')
        continue
    if skip:
        if '{% endif %}' in line:
            skip = False
        continue
    new_lines.append(line)

with open('inventory/templates/inventory/list.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Fixed!')