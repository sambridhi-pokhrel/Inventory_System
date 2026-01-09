from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from .models import Item
from users.decorators import (
    approved_user_required,
    manager_or_admin_required,
    admin_required,
    role_required
)
from users.utils import UserRoleManager


@approved_user_required
def item_list(request):
    """List all inventory items with search and filter functionality"""
    items = Item.objects.all()
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query)
        )
    
    # Handle filter
    filter_type = request.GET.get('filter', '')
    if filter_type == 'low_stock':
        items = items.filter(quantity__lte=10)
    elif filter_type == 'out_of_stock':
        items = items.filter(quantity=0)
    elif filter_type == 'in_stock':
        items = items.filter(quantity__gt=10)

    # Get role context using utility
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        "items": items,
        "search_query": search_query,
        "filter_type": filter_type,
    })

    return render(request, "inventory/list.html", context)


@manager_or_admin_required
def item_add(request):
    """Add new inventory item - Manager and Admin only"""
    if request.method == "POST":
        name = request.POST.get("name")
        quantity = request.POST.get("quantity")
        price = request.POST.get("price")

        # Validate input
        if not all([name, quantity, price]):
            messages.error(request, "All fields are required.")
            return render(request, "inventory/add.html")

        try:
            quantity = int(quantity)
            price = float(price)
            
            if quantity < 0 or price < 0:
                messages.error(request, "Quantity and price must be non-negative.")
                return render(request, "inventory/add.html")
            
            Item.objects.create(
                name=name,
                quantity=quantity,
                price=price
            )
            messages.success(request, f"Item '{name}' has been added successfully.")
            return redirect("inventory:item_list")
            
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid numbers for quantity and price.")
            return render(request, "inventory/add.html")

    context = UserRoleManager.get_context_for_user(request.user)
    return render(request, "inventory/add.html", context)


@manager_or_admin_required
def item_edit(request, item_id):
    """Edit inventory item - Manager and Admin only"""
    item = get_object_or_404(Item, id=item_id)

    if request.method == "POST":
        name = request.POST.get("name")
        quantity = request.POST.get("quantity")
        price = request.POST.get("price")

        # Validate input
        if not all([name, quantity, price]):
            messages.error(request, "All fields are required.")
            context = UserRoleManager.get_context_for_user(request.user)
            context["item"] = item
            return render(request, "inventory/edit.html", context)

        try:
            quantity = int(quantity)
            price = float(price)
            
            if quantity < 0 or price < 0:
                messages.error(request, "Quantity and price must be non-negative.")
                context = UserRoleManager.get_context_for_user(request.user)
                context["item"] = item
                return render(request, "inventory/edit.html", context)
            
            item.name = name
            item.quantity = quantity
            item.price = price
            item.save()
            
            messages.success(request, f"Item '{name}' has been updated successfully.")
            return redirect("inventory:item_list")
            
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid numbers for quantity and price.")
            context = UserRoleManager.get_context_for_user(request.user)
            context["item"] = item
            return render(request, "inventory/edit.html", context)

    context = UserRoleManager.get_context_for_user(request.user)
    context["item"] = item
    return render(request, "inventory/edit.html", context)


@admin_required
def item_delete(request, item_id):
    """Delete inventory item - Admin only"""
    item = get_object_or_404(Item, id=item_id)
    
    if request.method == "POST":
        item_name = item.name
        item.delete()
        messages.success(request, f"Item '{item_name}' has been deleted successfully.")
    
    return redirect("inventory:item_list")
