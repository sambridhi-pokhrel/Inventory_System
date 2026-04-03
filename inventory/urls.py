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
    path("adjust/<int:item_id>/", views.stock_adjustment, name="stock_adjustment"),
    path("purchase-order/<int:item_id>/", views.create_purchase_order, name="create_purchase_order"),

    # Supplier URLs
    path("suppliers/", views.supplier_list, name="supplier_list"),
    path("suppliers/add/", views.supplier_add, name="supplier_add"),
    path("suppliers/edit/<int:supplier_id>/", views.supplier_edit, name="supplier_edit"),
    path("suppliers/delete/<int:supplier_id>/", views.supplier_delete, name="supplier_delete"),

    # Customer URLs
    path("customers/", views.customer_list, name="customer_list"),
    path("customers/add/", views.customer_add, name="customer_add"),
    path("customers/edit/<int:customer_id>/", views.customer_edit, name="customer_edit"),
    path("customers/delete/<int:customer_id>/", views.customer_delete, name="customer_delete"),

    # AI-Powered Predictive Reordering URLs
    path("reorder-suggestions/", views.reorder_suggestions, name="reorder_suggestions"),
    path("ai/models/", views.ai_model_management, name="ai_model_management"),
    path("ai/forecast/<int:item_id>/", views.ai_demand_forecast, name="ai_demand_forecast"),

    # Analytics URLs
    path("analytics/", views.analytics_dashboard, name="analytics_dashboard"),
    path("analytics/item/<int:item_id>/", views.item_analytics, name="item_analytics"),
    path("reports/monthly/", views.monthly_report, name="monthly_report"),

    # Transaction URLs
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/create/", views.transaction_create, name="transaction_create"),
    path("transactions/<int:transaction_id>/", views.transaction_detail, name="transaction_detail"),
    path("transactions/<int:transaction_id>/process-payment/", views.process_payment, name="process_payment"),
    path("transactions/export/csv/", views.transaction_export_csv, name="transaction_export_csv"),

    # Payment Gateway URLs
    path("payment/khalti/initiate/<int:transaction_id>/", views.initiate_khalti_payment, name="initiate_khalti_payment"),
    path("payment/khalti/verify/", views.verify_khalti_payment, name="verify_khalti_payment"),
    path("payment/esewa/initiate/<int:transaction_id>/", views.initiate_esewa_payment, name="initiate_esewa_payment"),
    path("payment/esewa/verify/", views.verify_esewa_payment, name="verify_esewa_payment"),
    path("payment/esewa/failure/", views.esewa_payment_failure, name="esewa_payment_failure"),
    path("payment/success/<int:transaction_id>/", views.payment_success, name="payment_success"),
    path("payment/failure/<int:transaction_id>/", views.payment_failure, name="payment_failure"),

    # Payment Simulation URLs
    path("payment/simulate/<int:transaction_id>/<str:gateway_type>/", views.simulate_payment_page, name="simulate_payment_page"),
    path("payment/simulate/complete/<int:transaction_id>/", views.simulate_payment_complete, name="simulate_payment_complete"),

    # AJAX URLs
    path("api/item-price/", views.get_item_price, name="get_item_price"),
    path("api/chatbot/", views.chatbot_api, name="chatbot_api"),
]