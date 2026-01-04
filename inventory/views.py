from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Item
from .decorators import role_required

@login_required
@role_required(["Admin", "Manager", "Staff"])
def item_list(request):
    items = Item.objects.all()
    return render(request, "inventory/list.html", {"items": items})


@login_required
@role_required(["Admin", "Manager"])
def item_create(request):
    if request.method == "POST":
        name = request.POST["name"]
        quantity = request.POST["quantity"]
        price = request.POST["price"]
        Item.objects.create(name=name, quantity=quantity, price=price)
        return redirect("inventory:list")

    return render(request, "inventory/create.html")


@login_required
@role_required(["Admin", "Manager"])
def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk)

    if request.method == "POST":
        item.name = request.POST["name"]
        item.quantity = request.POST["quantity"]
        item.price = request.POST["price"]
        item.save()
        return redirect("inventory:list")

    return render(request, "inventory/update.html", {"item": item})


@login_required
@role_required(["Admin"])
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    item.delete()
    return redirect("inventory:list")
