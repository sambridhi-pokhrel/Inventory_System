from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.inventory_list, name="list"),
    path("add/", views.inventory_add, name="add"),
    path("edit/<int:id>/", views.inventory_edit, name="edit"),
    path("delete/<int:id>/", views.inventory_delete, name="delete"),
]
