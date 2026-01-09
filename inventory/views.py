from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Item


@login_required
def item_list(request):
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

    # ✅ ROLE CHECKS (DO THIS IN VIEW, NOT TEMPLATE)
    is_admin = request.user.is_superuser
    is_manager = request.user.groups.filter(name="Manager").exists()
    is_staff = request.user.groups.filter(name="Staff").exists()

    context = {
        "items": items,
        "is_admin": is_admin,
        "is_manager": is_manager,
        "is_staff": is_staff,
        "search_query": search_query,
        "filter_type": filter_type,
    }

    return render(request, "inventory/list.html", context)


@login_required
def item_add(request):
    # Only Admin & Manager can add
    if not (request.user.is_superuser or request.user.groups.filter(name="Manager").exists()):
        return redirect("inventory:item_list")

    if request.method == "POST":
        name = request.POST.get("name")
        quantity = request.POST.get("quantity")
        price = request.POST.get("price")

        Item.objects.create(
            name=name,
            quantity=quantity,
            price=price
        )
        return redirect("inventory:item_list")

    return render(request, "inventory/add.html")


@login_required
def item_edit(request, item_id):
    # Only Admin & Manager can edit
    if not (request.user.is_superuser or request.user.groups.filter(name="Manager").exists()):
        return redirect("inventory:item_list")

    item = get_object_or_404(Item, id=item_id)

    if request.method == "POST":
        item.name = request.POST.get("name")
        item.quantity = request.POST.get("quantity")
        item.price = request.POST.get("price")
        item.save()
        return redirect("inventory:item_list")

    context = {
        "item": item,
        "is_admin": request.user.is_superuser,
        "is_manager": request.user.groups.filter(name="Manager").exists(),
    }
    return render(request, "inventory/edit.html", context)


@login_required
def item_delete(request, item_id):
    # Only Admin can delete
    if not request.user.is_superuser:
        return redirect("inventory:item_list")

    item = get_object_or_404(Item, id=item_id)
    item.delete()
    return redirect("inventory:item_list")
