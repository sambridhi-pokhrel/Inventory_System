from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def rupees(value):
    """Format value as Nepali rupees with Rs. symbol"""
    try:
        return f"Rs. {float(value):,.2f}"
    except (ValueError, TypeError):
        return "Rs. 0.00"

@register.filter
def rupees_int(value):
    """Format value as Nepali rupees without decimals"""
    try:
        return f"Rs. {int(float(value)):,}"
    except (ValueError, TypeError):
        return "Rs. 0"

@register.filter
def get_user_role(user):
    """Get user role as string"""
    if user.is_superuser:
        return "admin"
    elif user.groups.filter(name='Manager').exists():
        return "manager"
    elif user.groups.filter(name='Staff').exists():
        return "staff"
    else:
        return "user"

@register.filter
def can_add_items(user):
    """Check if user can add items"""
    return user.is_superuser or user.groups.filter(name='Manager').exists()

@register.filter
def can_edit_items(user):
    """Check if user can edit items"""
    return user.is_superuser or user.groups.filter(name='Manager').exists()

@register.filter
def can_delete_items(user):
    """Check if user can delete items"""
    return user.is_superuser