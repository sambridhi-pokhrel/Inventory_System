from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.item_list, name="item_list"),
    path("add/", views.item_add, name="item_add"),
    path("edit/<int:item_id>/", views.item_edit, name="item_edit"),
    path("delete/<int:item_id>/", views.item_delete, name="item_delete"),
    path("export/csv/", views.export_csv, name="export_csv"),
    path("export/pdf/", views.export_pdf, name="export_pdf"),
]
