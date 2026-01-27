from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    # Inventory URLs
    path("", views.item_list, name="item_list"),
    path("add/", views.item_add, name="item_add"),
    path("edit/<int:item_id>/", views.item_edit, name="item_edit"),
    path("delete/<int:item_id>/", views.item_delete, name="item_delete"),
    path("export/csv/", views.export_csv, name="export_csv"),
    path("export/pdf/", views.export_pdf, name="export_pdf"),
    
    # Transaction URLs
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/create/", views.transaction_create, name="transaction_create"),
    path("transactions/<int:transaction_id>/", views.transaction_detail, name="transaction_detail"),
    path("transactions/export/csv/", views.transaction_export_csv, name="transaction_export_csv"),
    
    # AJAX URLs
    path("api/item-price/", views.get_item_price, name="get_item_price"),
]
