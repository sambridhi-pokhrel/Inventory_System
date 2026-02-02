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
    
    # AI-Powered Predictive Reordering URLs
    path("reorder-suggestions/", views.reorder_suggestions, name="reorder_suggestions"),
    path("ai/models/", views.ai_model_management, name="ai_model_management"),
    path("ai/forecast/<int:item_id>/", views.ai_demand_forecast, name="ai_demand_forecast"),
    
    # Transaction URLs
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/create/", views.transaction_create, name="transaction_create"),
    path("transactions/<int:transaction_id>/", views.transaction_detail, name="transaction_detail"),
    path("transactions/<int:transaction_id>/process-payment/", views.process_payment, name="process_payment"),
    path("transactions/export/csv/", views.transaction_export_csv, name="transaction_export_csv"),
    
    # AJAX URLs
    path("api/item-price/", views.get_item_price, name="get_item_price"),
]
