from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Item
from .decorators import admin_required, manager_required, staff_required


@login_required
@staff_required
def inventory_list(request):
    items = Item.objects.all()
    return render(request, "inventory/list.html", {"items": items})


@login_required
@manager_required
def inventory_add(request):
    if request.method == "POST":
        Item.objects.create(
            name=request.POST["name"],
            quantity=request.POST["quantity"]
        )
        return redirect("inventory:list")
    return render(request, "inventory/add.html")


@login_required
@manager_required
def inventory_edit(request, id):
    item = get_object_or_404(Item, id=id)
    if request.method == "POST":
        item.name = request.POST["name"]
        item.quantity = request.POST["quantity"]
        item.save()
        return redirect("inventory:list")
    return render(request, "inventory/edit.html", {"item": item})


@login_required
@admin_required
def inventory_delete(request, id):
    item = get_object_or_404(Item, id=id)
    item.delete()
    return redirect("inventory:list")
