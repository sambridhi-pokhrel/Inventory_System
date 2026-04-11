from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, F, Count
from django.db.models.functions import TruncDate, TruncMonth
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
import csv
import io
import uuid
import logging
from .models import Item, Transaction, Supplier, Customer
from .forms import TransactionForm, TransactionFilterForm
from users.decorators import (
    approved_user_required,
    manager_or_admin_required,
    admin_required,
    role_required
)
from users.utils import UserRoleManager

logger = logging.getLogger(__name__)


@approved_user_required
def item_list(request):
    """List all inventory items with search, filter, and AI-powered notifications"""
    from .notifications import notification_manager
    
    # Add smart notifications based on AI predictions
    notification_manager.add_inventory_page_notifications(request)
    
    items = Item.objects.all()
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query)
        )
    
    # Handle filter
    filter_type = request.GET.get('status', '')
    if filter_type == 'low-stock':
        items = items.filter(quantity__lte=F('reorder_level'))
    elif filter_type == 'out-of-stock':
        items = items.filter(quantity=0)
    elif filter_type == 'in-stock':
        items = items.filter(quantity__gt=F('reorder_level'))
    elif filter_type == 'reorder-suggested':
        # Filter items that need reordering based on AI logic
        reorder_items = []
        for item in items:
            if item.needs_reorder:
                reorder_items.append(item.id)
        items = items.filter(id__in=reorder_items)
    elif filter_type == 'ai-critical':
        # New filter: AI Critical alerts
        ai_alerts = notification_manager.get_ai_stock_alerts()
        critical_item_ids = [a['item'].id for a in ai_alerts if a['urgency'] == 'CRITICAL']
        items = items.filter(id__in=critical_item_ids)

    # Calculate summary statistics
    total_items = Item.objects.count()
    low_stock_count = Item.objects.filter(quantity__lte=F('reorder_level'), quantity__gt=0).count()
    out_of_stock_count = Item.objects.filter(quantity=0).count()
    in_stock_count = Item.objects.filter(quantity__gt=F('reorder_level')).count()
    
    # Get AI-powered reorder suggestions
    reorder_suggestions = []
    for item in Item.objects.all():
        if item.needs_reorder:
            reorder_suggestions.append(item)
    
    reorder_count = len(reorder_suggestions)
    
    # Get notification summary for template
    notification_summary = notification_manager.get_notification_summary()

    # Get role context using utility
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        "items": items,
        "search_query": search_query,
        "filter_type": filter_type,
        "total_items": total_items,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "in_stock_count": in_stock_count,
        "reorder_count": reorder_count,
        "reorder_suggestions": reorder_suggestions[:5],  # Show top 5 in sidebar
        "notification_summary": notification_summary,  # AI notification data
    })

    return render(request, "inventory/list.html", context)


@approved_user_required
def reorder_suggestions(request):
    """View AI-powered reorder suggestions with machine learning insights"""
    from .ml_predictor import get_ai_reorder_suggestions, ml_predictor
    
    # Get AI-powered suggestions
    ai_suggestions = get_ai_reorder_suggestions()
    
    # Prepare detailed suggestions with AI insights
    detailed_suggestions = []
    for suggestion in ai_suggestions:
        item = suggestion['item']
        recommendation = suggestion['recommendation']
        
        # Get model information
        model_info = ml_predictor.get_model_info(item)
        
        # Handle cases where AI prediction failed
        urgency = recommendation.get('urgency', 'LOW')
        urgency_class = urgency.lower()
        
        detailed_suggestions.append({
            'item': item,
            'recommendation': recommendation,
            'model_info': model_info,
            'urgency_class': urgency_class,
            'urgency_icon': {
                'CRITICAL': 'bi-exclamation-triangle-fill text-danger',
                'HIGH': 'bi-exclamation-triangle text-warning',
                'MEDIUM': 'bi-info-circle text-info',
                'LOW': 'bi-check-circle text-success'
            }.get(urgency, 'bi-info-circle')
        })
    
    # Calculate summary statistics
    total_suggestions = len(detailed_suggestions)
    critical_count = sum(1 for s in detailed_suggestions if s['recommendation'].get('urgency') == 'CRITICAL')
    high_count = sum(1 for s in detailed_suggestions if s['recommendation'].get('urgency') == 'HIGH')
    
    # Get overall AI system status
    total_items = Item.objects.count()
    items_with_models = len(ml_predictor.models)
    ai_coverage = (items_with_models / total_items * 100) if total_items > 0 else 0
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'suggestions': detailed_suggestions,
        'total_suggestions': total_suggestions,
        'critical_count': critical_count,
        'high_count': high_count,
        'ai_system_status': {
            'total_items': total_items,
            'items_with_ai_models': items_with_models,
            'ai_coverage_percent': round(ai_coverage, 1),
            'system_status': 'Active' if items_with_models > 0 else 'Training Required'
        }
    })
    
    return render(request, 'inventory/reorder_suggestions.html', context)


@manager_or_admin_required
def export_csv(request):
    """Export inventory data to CSV with AI prediction insights"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_ai_report.csv"'
    
    writer = csv.writer(response)
    
    # Write header with AI prediction columns
    writer.writerow([
        'Item Name', 'Current Stock', 'Unit Price (Rs.)', 'Stock Value (Rs.)', 
        'Stock Status', 'Reorder Level', 'Lead Time (Days)',
        # AI Prediction Columns
        'AI Prediction Available', 'Predicted Demand (7 days)', 'AI Accuracy (%)',
        'AI Reorder Recommended', 'AI Urgency Level', 'AI Suggested Quantity',
        'Days Until Stockout', 'Shortage Risk (Units)'
    ])
    
    # Write data with AI insights
    for item in Item.objects.all():
        stock_value = float(item.price) * item.quantity
        
        # Get AI prediction data
        ai_reorder_info = item.ai_reorder_info
        forecast_result = item.get_ai_demand_forecast(days=7)
        
        # Extract AI data safely
        ai_available = ai_reorder_info.get('ai_powered', False)
        predicted_demand = forecast_result.get('summary', {}).get('total_predicted_demand', 'N/A') if forecast_result.get('success') else 'N/A'
        ai_accuracy = ai_reorder_info.get('model_accuracy', 'N/A') if ai_available else 'N/A'
        ai_reorder = 'Yes' if ai_reorder_info.get('needs_reorder', False) else 'No'
        ai_urgency = ai_reorder_info.get('urgency', 'N/A') if ai_available else 'N/A'
        ai_suggested_qty = ai_reorder_info.get('suggested_quantity', 0) if ai_available else 0
        days_until_stockout = ai_reorder_info.get('days_until_stockout', 'N/A') if ai_available else 'N/A'
        shortage_risk = ai_reorder_info.get('shortage_risk', 0) if ai_available else 0
        
        writer.writerow([
            item.name,
            item.quantity,
            f"{item.price:.2f}",
            f"{stock_value:.2f}",
            item.stock_status.replace('-', ' ').title(),
            item.reorder_level,
            item.lead_time_days,
            # AI Prediction Data
            'Yes' if ai_available else 'No',
            f"{predicted_demand:.1f}" if isinstance(predicted_demand, (int, float)) else predicted_demand,
            ai_accuracy,
            ai_reorder,
            ai_urgency,
            ai_suggested_qty,
            f"{days_until_stockout:.1f}" if isinstance(days_until_stockout, (int, float)) and days_until_stockout != float('inf') else days_until_stockout,
            f"{shortage_risk:.1f}" if isinstance(shortage_risk, (int, float)) else shortage_risk
        ])
    
    # Write AI system summary
    writer.writerow([])  # Empty row
    writer.writerow(['AI SYSTEM SUMMARY'])
    
    # Calculate AI coverage and performance
    total_items = Item.objects.count()
    items_with_ai = sum(1 for item in Item.objects.all() if item.ai_reorder_info.get('ai_powered', False))
    ai_coverage = (items_with_ai / total_items * 100) if total_items > 0 else 0
    
    # Get AI reorder suggestions
    from .ml_predictor import get_ai_reorder_suggestions
    ai_suggestions = get_ai_reorder_suggestions()
    critical_alerts = sum(1 for s in ai_suggestions if s['recommendation'].get('urgency') == 'CRITICAL')
    high_alerts = sum(1 for s in ai_suggestions if s['recommendation'].get('urgency') == 'HIGH')
    
    writer.writerow(['Total Items', total_items])
    writer.writerow(['Items with AI Models', items_with_ai])
    writer.writerow(['AI Coverage (%)', f"{ai_coverage:.1f}%"])
    writer.writerow(['AI Reorder Suggestions', len(ai_suggestions)])
    writer.writerow(['Critical AI Alerts', critical_alerts])
    writer.writerow(['High Priority AI Alerts', high_alerts])
    
    # Calculate total inventory value
    total_value = sum(float(item.price) * item.quantity for item in Item.objects.all())
    writer.writerow(['Total Inventory Value (Rs.)', f"{total_value:.2f}"])
    
    return response


@manager_or_admin_required
def item_add(request):
    """Add new inventory item with reorder settings and automatic image fetching"""
    if request.method == "POST":
        name = request.POST.get("name")
        sku = request.POST.get("sku", "").strip() or None
        quantity = request.POST.get("quantity")
        price = request.POST.get("price")
        reorder_level = request.POST.get("reorder_level", 10)
        lead_time_days = request.POST.get("lead_time_days", 7)
        image = request.FILES.get("image")  # Get uploaded image

        # Validate input
        if not all([name, quantity, price]):
            messages.error(request, "Name, quantity, and price are required.")
            return render(request, "inventory/add.html")

        try:
            quantity = int(quantity)
            price = float(price)
            reorder_level = int(reorder_level)
            lead_time_days = int(lead_time_days)
            
            if quantity < 0 or price < 0 or reorder_level < 0 or lead_time_days < 1:
                messages.error(request, "All values must be non-negative (lead time must be at least 1 day).")
                return render(request, "inventory/add.html")
            
            # Create item - automatic image fetching happens in model's save() method
            # If user uploaded image: uses uploaded image
            # If no image uploaded: automatically fetches from Unsplash API
            # If API fails: uses placeholder (system remains stable)
            item = Item.objects.create(
                name=name,
                sku=sku,
                quantity=quantity,
                price=price,
                reorder_level=reorder_level,
                lead_time_days=lead_time_days,
                image=image,
                created_by=request.user
            )
            
            # Show appropriate success message
            if image:
                messages.success(request, f"Item '{name}' has been added successfully with your uploaded image.")
            elif item.image:
                # Check if Unsplash is configured
                from django.conf import settings
                unsplash_key = getattr(settings, 'UNSPLASH_ACCESS_KEY', None)
                if unsplash_key and unsplash_key != 'YOUR_UNSPLASH_ACCESS_KEY_HERE':
                    messages.success(request, f"Item '{name}' has been added with product image from Unsplash.")
                else:
                    messages.warning(
                        request,
                        f"Item '{name}' added with placeholder image. "
                        f"For product-specific images, configure Unsplash API key in settings. "
                        f"See GET_UNSPLASH_KEY_QUICK.md for instructions."
                    )
            else:
                messages.success(request, f"Item '{name}' has been added successfully.")
            
            return redirect("inventory:item_list")
            
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid numbers for all fields.")
            return render(request, "inventory/add.html")

    context = UserRoleManager.get_context_for_user(request.user)
    return render(request, "inventory/add.html", context)


@manager_or_admin_required
def item_edit(request, item_id):
    """Edit inventory item with reorder settings and image upload"""
    item = get_object_or_404(Item, id=item_id)

    if request.method == "POST":
        name = request.POST.get("name")
        quantity = request.POST.get("quantity")
        price = request.POST.get("price")
        reorder_level = request.POST.get("reorder_level")
        lead_time_days = request.POST.get("lead_time_days")
        image = request.FILES.get("image")  # Get uploaded image

        # Validate input
        if not all([name, quantity, price, reorder_level, lead_time_days]):
            messages.error(request, "All fields are required.")
            context = UserRoleManager.get_context_for_user(request.user)
            context["item"] = item
            return render(request, "inventory/edit.html", context)

        try:
            quantity = int(quantity)
            price = float(price)
            reorder_level = int(reorder_level)
            lead_time_days = int(lead_time_days)
            
            if quantity < 0 or price < 0 or reorder_level < 0 or lead_time_days < 1:
                messages.error(request, "All values must be non-negative (lead time must be at least 1 day).")
                context = UserRoleManager.get_context_for_user(request.user)
                context["item"] = item
                return render(request, "inventory/edit.html", context)
            
            item.name = name
            item.quantity = quantity
            item.price = price
            item.reorder_level = reorder_level
            item.lead_time_days = lead_time_days
            
            # Update image if new one is uploaded
            if image:
                item.image = image
            
            item.save()
            
            messages.success(request, f"Item '{name}' has been updated successfully.")
            return redirect("inventory:item_list")
            
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid numbers for all fields.")
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

# ==================== TRANSACTION VIEWS ====================

@approved_user_required
@approved_user_required
def transaction_list(request):
    """List all transactions with filtering, pagination, and payment status"""
    transactions = Transaction.objects.select_related('item', 'performed_by').all()
    
    # Handle filtering
    transaction_type = request.GET.get('type', '')
    payment_status = request.GET.get('payment_status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if payment_status:
        transactions = transactions.filter(payment_status=payment_status)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            transactions = transactions.filter(timestamp__date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            transactions = transactions.filter(timestamp__date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Separate sales and purchases for display
    recent_sales = Transaction.objects.filter(
        transaction_type='SALE'
    ).select_related('item', 'performed_by').order_by('-timestamp')[:10]
    
    recent_purchases = Transaction.objects.filter(
        transaction_type='PURCHASE'
    ).select_related('item', 'performed_by').order_by('-timestamp')[:10]
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate summary statistics
    total_sales = Transaction.objects.filter(
        transaction_type='SALE', 
        payment_status='PAID'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_purchases = Transaction.objects.filter(
        transaction_type='PURCHASE'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    pending_payments = Transaction.objects.filter(
        payment_status='PENDING'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Calculate total profit from paid sales
    paid_sales = Transaction.objects.filter(
        transaction_type='SALE',
        payment_status='PAID'
    ).select_related('item')
    
    total_profit = sum(sale.total_profit for sale in paid_sales)
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'transactions': page_obj,
        'recent_sales': recent_sales,
        'recent_purchases': recent_purchases,
        'total_sales': total_sales,
        'total_purchases': total_purchases,
        'pending_payments': pending_payments,
        'total_profit': total_profit,
        'transaction_count': transactions.count(),
        'filters': {
            'type': transaction_type,
            'payment_status': payment_status,
            'date_from': date_from,
            'date_to': date_to,
        }
    })
    
    return render(request, 'inventory/transaction_list.html', context)


@manager_or_admin_required
def transaction_create(request):
    """Create new transaction with payment processing"""
    if request.method == 'POST':
        item_id = request.POST.get('item')
        transaction_type = request.POST.get('transaction_type')
        quantity = request.POST.get('quantity')
        unit_price = request.POST.get('unit_price')
        payment_method = request.POST.get('payment_method', 'KHALTI')
        notes = request.POST.get('notes', '')
        supplier_id = request.POST.get('supplier')  # Get supplier
        customer_id = request.POST.get('customer')  # Get customer
        
        try:
            item = Item.objects.get(id=item_id)
            # Convert quantity to integer (handle decimal inputs)
            quantity = int(float(quantity))  # Convert to float first, then to int
            unit_price = float(unit_price)
            
            # Validate inputs
            if quantity <= 0:
                messages.error(request, "Quantity must be greater than 0.")
                context = UserRoleManager.get_context_for_user(request.user)
                context.update({
                    'items': Item.objects.all().order_by('name'),
                    'suppliers': Supplier.objects.all().order_by('name'),
                    'customers': Customer.objects.all().order_by('name'),
                })
                return render(request, 'inventory/transaction_create.html', context)
            
            if unit_price <= 0:
                messages.error(request, "Unit price must be greater than 0.")
                context = UserRoleManager.get_context_for_user(request.user)
                context.update({
                    'items': Item.objects.all().order_by('name'),
                    'suppliers': Supplier.objects.all().order_by('name'),
                    'customers': Customer.objects.all().order_by('name'),
                })
                return render(request, 'inventory/transaction_create.html', context)
            
            # Create transaction with PENDING status
            # For SALE transactions with Khalti/eSewa, user will complete payment separately
            # For PURCHASE transactions, mark as PAID immediately (no payment gateway needed)
            
            if transaction_type == 'PURCHASE':
                # Purchases are always marked as PAID (company is buying inventory)
                payment_status = 'PAID'
            elif payment_method in ['KHALTI', 'ESEWA']:
                # Sales with Khalti/eSewa start as PENDING (user needs to pay)
                payment_status = 'PENDING'
            else:
                # Sales with Cash/Bank Transfer/Credit are marked as PAID
                payment_status = 'PAID'
            
            # Get supplier or customer objects
            supplier = None
            customer = None
            if supplier_id:
                try:
                    supplier = Supplier.objects.get(id=supplier_id)
                except Supplier.DoesNotExist:
                    pass
            if customer_id:
                try:
                    customer = Customer.objects.get(id=customer_id)
                except Customer.DoesNotExist:
                    pass
            
            transaction = Transaction.objects.create(
                item=item,
                transaction_type=transaction_type,
                quantity=quantity,
                unit_price=unit_price,
                payment_method=payment_method,
                performed_by=request.user,
                notes=notes,
                payment_status=payment_status,
                supplier=supplier,  # Add supplier
                customer=customer,  # Add customer
            )
            if transaction_type == 'PURCHASE':
                item.cost_price = unit_price
                item.save(update_fields=['cost_price'])
            
            # Show appropriate message based on payment status
            if payment_status == 'PENDING':
                messages.success(
                    request,
                    f"Transaction #{transaction.id} created successfully! "
                    f"Please complete payment to finalize the transaction."
                )
                # Redirect to transaction detail page where user can pay
                return redirect('inventory:transaction_detail', transaction_id=transaction.id)
            else:
                messages.success(
                    request,
                    f"Transaction #{transaction.id} completed successfully via {payment_method}!"
                )
                return redirect('inventory:transaction_list')
            
        except ValueError as e:
            messages.error(request, "Please enter valid numbers for quantity and price.")
        except Item.DoesNotExist:
            messages.error(request, "Selected item does not exist.")
        except Exception as e:
            messages.error(request, f"Error creating transaction: {str(e)}")
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'items': Item.objects.all().order_by('name'),
        'suppliers': Supplier.objects.all().order_by('name'),
        'customers': Customer.objects.all().order_by('name'),
    })
    
    return render(request, 'inventory/transaction_create.html', context)


@approved_user_required
def transaction_detail(request, transaction_id):
    """View transaction details with payment information"""
    transaction = get_object_or_404(
        Transaction.objects.select_related('item', 'performed_by'),
        id=transaction_id
    )
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'transaction': transaction,
        'KHALTI_ENABLED': getattr(settings, 'KHALTI_ENABLED', False),
    })
    
    return render(request, 'inventory/transaction_detail.html', context)


@manager_or_admin_required
def process_payment(request, transaction_id):
    """Process payment for pending transactions"""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    if transaction.payment_status == 'PENDING':
        if transaction.payment_method == 'KHALTI':
            success = transaction.simulate_khalti_payment()
            if success:
                messages.success(
                    request,
                    f"Payment processed successfully! Reference: {transaction.payment_reference}"
                )
            else:
                messages.error(request, "Payment processing failed.")
        else:
            transaction.payment_status = 'PAID'
            transaction.save()
            messages.success(request, "Payment marked as completed.")
    else:
        messages.info(request, "Transaction payment is already processed.")
    
    return redirect('inventory:transaction_detail', transaction_id=transaction_id)


@manager_or_admin_required
def get_item_price(request):
    """AJAX endpoint to get item price and stock info for transaction form"""
    item_id = request.GET.get('item_id')
    if item_id:
        try:
            item = Item.objects.get(id=item_id)
            return JsonResponse({
                'price': str(item.price),
                'quantity': item.quantity,
                'name': item.name,
                'stock_status': item.stock_status,
                'needs_reorder': item.needs_reorder,
            })
        except Item.DoesNotExist:
            pass
    
    return JsonResponse({'error': 'Item not found'}, status=404)


@manager_or_admin_required
def ai_model_management(request):
    """Manage AI models for demand forecasting"""
    from .ml_predictor import ml_predictor, train_all_models
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'train_all':
            # Train models for all items
            results = train_all_models()
            success_count = sum(1 for r in results.values() if r['success'])
            total_count = len(results)
            
            if success_count > 0:
                messages.success(
                    request, 
                    f"Successfully trained AI models for {success_count}/{total_count} items!"
                )
            else:
                messages.warning(request, "No AI models could be trained. Items may need more transaction history.")
        
        elif action == 'train_single':
            item_id = request.POST.get('item_id')
            try:
                item = Item.objects.get(id=item_id)
                result = ml_predictor.train_demand_model(item)
                
                if result['success']:
                    messages.success(
                        request,
                        f"AI model trained for {item.name} with {result['metrics']['accuracy']:.1f}% accuracy!"
                    )
                else:
                    messages.error(request, f"Failed to train model for {item.name}: {result['error']}")
            except Item.DoesNotExist:
                messages.error(request, "Item not found.")
    
    # Get model status for all items
    items_status = []
    for item in Item.objects.all():
        model_info = ml_predictor.get_model_info(item)
        
        # Get recent transaction count
        recent_sales = Transaction.objects.filter(
            item=item,
            transaction_type='SALE',
            timestamp__gte=timezone.now() - timedelta(days=90)
        ).count()
        
        items_status.append({
            'item': item,
            'has_model': model_info is not None,
            'model_info': model_info,
            'recent_sales_count': recent_sales,
            'can_train': recent_sales >= 7,  # Minimum data requirement
        })
    
    # Calculate summary statistics
    total_items = len(items_status)
    items_with_models = sum(1 for item in items_status if item['has_model'])
    items_trainable = sum(1 for item in items_status if item['can_train'])
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'items_status': items_status,
        'summary': {
            'total_items': total_items,
            'items_with_models': items_with_models,
            'items_trainable': items_trainable,
            'coverage_percent': round((items_with_models / total_items * 100) if total_items > 0 else 0, 1)
        }
    })
    
    return render(request, 'inventory/ai_model_management.html', context)


@manager_or_admin_required
def ai_demand_forecast(request, item_id):
    """View AI demand forecast for a specific item"""
    item = get_object_or_404(Item, id=item_id)
    
    # Get AI forecast
    forecast_result = item.get_ai_demand_forecast(days=14)  # 2 weeks forecast
    reorder_info = item.ai_reorder_info
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'item': item,
        'forecast_result': forecast_result,
        'reorder_info': reorder_info,
    })
    
    return render(request, 'inventory/ai_demand_forecast.html', context)


@manager_or_admin_required
def analytics_dashboard(request):
    """Analytics dashboard with Chart.js visualizations"""
    import json
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncDate, TruncMonth
    
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=29)
    
    # --- 1. Sales Trend (last 30 days) ---
    sales_by_day = (
        Transaction.objects.filter(
            transaction_type='SALE',
            payment_status='PAID',
            timestamp__date__gte=thirty_days_ago,
        )
        .annotate(day=TruncDate('timestamp'))
        .values('day')
        .annotate(qty=Sum('quantity'))
        .order_by('day')
    )
    day_map = {r['day']: r['qty'] for r in sales_by_day}
    trend_labels = []
    trend_data = []
    for i in range(30):
        d = thirty_days_ago + timedelta(days=i)
        trend_labels.append(d.strftime('%b %d'))
        trend_data.append(day_map.get(d, 0))

    # --- 2. Top 5 Selling Products ---
    top_products = (
        Transaction.objects.filter(
            transaction_type='SALE',
            payment_status='PAID',
        )
        .values('item__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:5]
    )
    top_labels = [p['item__name'] for p in top_products]
    top_data = [p['total_qty'] for p in top_products]

    # --- 3. Monthly Revenue (last 6 months) ---
    six_months_ago = today.replace(day=1) - timedelta(days=150)
    monthly_revenue = (
        Transaction.objects.filter(
            transaction_type='SALE',
            payment_status='PAID',
            timestamp__date__gte=six_months_ago,
        )
        .annotate(month=TruncMonth('timestamp'))
        .values('month')
        .annotate(revenue=Sum('total_amount'))
        .order_by('month')
    )
    rev_labels = [r['month'].strftime('%b %Y') for r in monthly_revenue]
    rev_data = [float(r['revenue']) for r in monthly_revenue]

    # --- 4. Stock Distribution (pie) ---
    items_qs = Item.objects.all()
    stock_labels = [item.name for item in items_qs]
    stock_data = [item.quantity for item in items_qs]

    # --- 5. Purchase vs Sales comparison (last 6 months) ---
    monthly_purchases = (
        Transaction.objects.filter(
            transaction_type='PURCHASE',
            payment_status='PAID',
            timestamp__date__gte=six_months_ago,
        )
        .annotate(month=TruncMonth('timestamp'))
        .values('month')
        .annotate(total=Sum('total_amount'))
        .order_by('month')
    )
    from dateutil.relativedelta import relativedelta

    rev_map = {r['month'].strftime('%b %Y'): float(r['revenue']) for r in monthly_revenue}
    pur_map = {r['month'].strftime('%b %Y'): float(r['total']) for r in monthly_purchases}

    compare_labels    = []
    compare_sales     = []
    compare_purchases = []

    for i in range(5, -1, -1):
        target = today.replace(day=1) - relativedelta(months=i)
        label  = target.strftime('%b %Y')
        compare_labels.append(label)
        compare_sales.append(rev_map.get(label, 0))
        compare_purchases.append(pur_map.get(label, 0))

    # --- Summary stats ---
    total_sales_amount = Transaction.objects.filter(
        transaction_type='SALE', payment_status='PAID'
    ).aggregate(t=Sum('total_amount'))['t'] or 0
    total_purchase_amount = Transaction.objects.filter(
        transaction_type='PURCHASE', payment_status='PAID'
    ).aggregate(t=Sum('total_amount'))['t'] or 0
    total_transactions = Transaction.objects.count()
    total_items = Item.objects.count()

    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'trend_labels': json.dumps(trend_labels),
        'trend_data': json.dumps(trend_data),
        'top_labels': json.dumps(top_labels),
        'top_data': json.dumps(top_data),
        'rev_labels': json.dumps(rev_labels),
        'rev_data': json.dumps(rev_data),
        'stock_labels': json.dumps(stock_labels),
        'stock_data': json.dumps(stock_data),
        'compare_labels': json.dumps(compare_labels),
        'compare_sales': json.dumps(compare_sales),
        'compare_purchases': json.dumps(compare_purchases),
        'total_sales_amount': total_sales_amount,
        'total_purchase_amount': total_purchase_amount,
        'total_transactions': total_transactions,
        'total_items': total_items,
    })
    
    return render(request, 'inventory/analytics_dashboard.html', context)


@manager_or_admin_required
def item_analytics(request, item_id):
    """Detailed analytics for a specific item"""
    from .analytics import analytics
    
    item = get_object_or_404(Item, id=item_id)
    
    # Generate item-specific charts
    actual_vs_predicted = analytics.generate_actual_vs_predicted_chart(
        item_id=item_id, days=14
    )
    
    # Get item transaction history
    transactions = Transaction.objects.filter(item=item).order_by('-timestamp')[:20]
    
    # Calculate item statistics
    total_sales = Transaction.objects.filter(
        item=item, 
        transaction_type='SALE',
        payment_status='PAID'
    ).aggregate(
        total_quantity=Sum('quantity'),
        total_amount=Sum('total_amount')
    )
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'item': item,
        'actual_vs_predicted': actual_vs_predicted,
        'transactions': transactions,
        'total_sales': total_sales,
    })
    
    return render(request, 'inventory/item_analytics.html', context)


@manager_or_admin_required
def transaction_export_csv(request):
    """Export transaction data to CSV with AI prediction insights"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions_ai_report.csv"'
    
    writer = csv.writer(response)
    
    # Write header with AI prediction columns
    writer.writerow([
        'Date', 'Time', 'Item', 'Type', 'Quantity', 
        'Unit Price (Rs.)', 'Total Amount (Rs.)', 'Payment Status',
        'Payment Method', 'Payment Reference', 'Performed By', 'Notes',
        # AI Prediction Columns
        'Item AI Status', 'Current Stock After', 'AI Reorder Needed', 'AI Urgency'
    ])
    
    # Write transaction data with AI insights
    for transaction in Transaction.objects.select_related('item', 'performed_by').all():
        # Get AI insights for the item
        ai_reorder_info = transaction.item.ai_reorder_info
        ai_powered = ai_reorder_info.get('ai_powered', False)
        ai_reorder_needed = 'Yes' if ai_reorder_info.get('needs_reorder', False) else 'No'
        ai_urgency = ai_reorder_info.get('urgency', 'N/A') if ai_powered else 'N/A'
        
        writer.writerow([
            transaction.timestamp.strftime('%Y-%m-%d'),
            transaction.timestamp.strftime('%H:%M:%S'),
            transaction.item.name,
            transaction.transaction_type,
            transaction.quantity,
            f"{transaction.unit_price:.2f}",
            f"{transaction.total_amount:.2f}",
            transaction.payment_status,
            transaction.payment_method,
            transaction.payment_reference or '',
            transaction.performed_by.get_full_name() or transaction.performed_by.username,
            transaction.notes or '',
            # AI Data
            'AI-Enabled' if ai_powered else 'Basic Rules',
            transaction.item.quantity,
            ai_reorder_needed,
            ai_urgency
        ])
    
    # Write AI-enhanced summary
    writer.writerow([])
    writer.writerow(['AI-ENHANCED TRANSACTION SUMMARY'])
    
    total_sales = Transaction.objects.filter(
        transaction_type='SALE', 
        payment_status='PAID'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_purchases = Transaction.objects.filter(
        transaction_type='PURCHASE'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    pending_amount = Transaction.objects.filter(
        payment_status='PENDING'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # AI insights
    from .ml_predictor import get_ai_reorder_suggestions
    ai_suggestions = get_ai_reorder_suggestions()
    items_needing_reorder = len(ai_suggestions)
    critical_items = sum(1 for s in ai_suggestions if s['recommendation'].get('urgency') == 'CRITICAL')
    
    writer.writerow(['Total Sales (Rs.)', f"{total_sales:.2f}"])
    writer.writerow(['Total Purchases (Rs.)', f"{total_purchases:.2f}"])
    writer.writerow(['Pending Payments (Rs.)', f"{pending_amount:.2f}"])
    writer.writerow(['Net Amount (Rs.)', f"{total_sales - total_purchases:.2f}"])
    writer.writerow(['Total Transactions', Transaction.objects.count()])
    writer.writerow([''])
    writer.writerow(['AI REORDER INSIGHTS'])
    writer.writerow(['Items Needing Reorder (AI)', items_needing_reorder])
    writer.writerow(['Critical Stock Alerts', critical_items])
    
    return response


# ==================== PAYMENT GATEWAY VIEWS ====================

@manager_or_admin_required
def initiate_khalti_payment(request, transaction_id):
    """
    Initiate Khalti payment for a transaction
    
    Academic Explanation (for Viva):
    ---------------------------------
    This view prepares payment data and renders a page that initiates
    Khalti payment using their JavaScript SDK.
    
    Flow:
    1. Get transaction from database
    2. Validate transaction is eligible for payment
    3. Prepare payment configuration
    4. Render page with Khalti payment widget
    5. User completes payment on Khalti
    6. Khalti calls our verification endpoint
    """
    from .payment_gateways import KhaltiPaymentGateway
    from .payment_simulation import PaymentSimulator
    
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Validate transaction
    if transaction.payment_status == 'PAID':
        messages.info(request, "This transaction is already paid.")
        return redirect('inventory:transaction_detail', transaction_id=transaction_id)
    
    if transaction.payment_method != 'KHALTI':
        messages.error(request, "This transaction is not set for Khalti payment.")
        return redirect('inventory:transaction_detail', transaction_id=transaction_id)
    
    # Check if simulation mode is enabled
    if PaymentSimulator.is_simulation_mode():
        messages.info(request, "🧪 Using simulation mode (Khalti gateway not accessible)")
        return redirect('inventory:simulate_payment_page', transaction_id=transaction_id, gateway_type='khalti')
    
    # Check if Khalti is enabled
    if not getattr(settings, 'KHALTI_ENABLED', False):
        messages.error(
            request, 
            "Khalti payment is not configured. Please contact administrator or use simulation mode."
        )
        return redirect('inventory:transaction_detail', transaction_id=transaction_id)
    
    # Initialize Khalti gateway
    khalti = KhaltiPaymentGateway()
    payment_data = khalti.initiate_payment(transaction, request)
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'transaction': transaction,
        'payment_data': payment_data,
        'khalti_public_key': settings.KHALTI_PUBLIC_KEY,
    })
    
    return render(request, 'inventory/payment_khalti.html', context)


@manager_or_admin_required
def verify_khalti_payment(request):
    """
    Verify Khalti payment after user completes payment
    
    Academic Explanation (for Viva):
    ---------------------------------
    This is the callback endpoint that Khalti redirects to after payment.
    We receive a payment token and must verify it with Khalti's API
    before marking the transaction as paid.
    
    Security:
    - Never trust client-side data alone
    - Always verify with gateway's API
    - Use atomic transactions for database updates
    """
    from .payment_gateways import KhaltiPaymentGateway
    from django.db import transaction as db_transaction
    
    # Get payment data from Khalti callback
    token = request.GET.get('token')
    amount = request.GET.get('amount')
    transaction_id = request.GET.get('product_identity')
    
    if not all([token, amount, transaction_id]):
        messages.error(request, "Invalid payment callback data.")
        return redirect('inventory:transaction_list')
    
    try:
        transaction_obj = Transaction.objects.get(id=transaction_id)
        
        # Verify payment with Khalti API
        khalti = KhaltiPaymentGateway()
        verification_result = khalti.verify_payment(token, amount)
        
        if verification_result['success']:
            # Payment verified successfully
            with db_transaction.atomic():
                transaction_obj.payment_status = 'PAID'
                transaction_obj.payment_reference = verification_result['transaction_id']
                transaction_obj.save()
            
            messages.success(
                request,
                f"Payment successful! Transaction #{transaction_obj.id} has been completed. "
                f"Reference: {verification_result['transaction_id']}"
            )
            return redirect('inventory:payment_success', transaction_id=transaction_obj.id)
        else:
            # Payment verification failed
            transaction_obj.payment_status = 'FAILED'
            transaction_obj.save()
            
            messages.error(
                request,
                f"Payment verification failed: {verification_result.get('error', 'Unknown error')}"
            )
            return redirect('inventory:payment_failure', transaction_id=transaction_obj.id)
            
    except Transaction.DoesNotExist:
        messages.error(request, "Transaction not found.")
        return redirect('inventory:transaction_list')
    except Exception as e:
        logger.error(f"Khalti verification error: {str(e)}")
        messages.error(request, f"Error processing payment: {str(e)}")
        return redirect('inventory:transaction_list')


@manager_or_admin_required
def initiate_esewa_payment(request, transaction_id):
    """
    Initiate eSewa payment for a transaction
    
    Academic Explanation (for Viva):
    ---------------------------------
    eSewa uses form-based payment initiation. We generate an HTML form
    with payment parameters and auto-submit it to eSewa's payment page.
    
    Flow:
    1. Get transaction from database
    2. Validate transaction
    3. Generate payment form data
    4. Render page with auto-submitting form
    5. User redirected to eSewa payment page
    6. After payment, eSewa redirects to our success/failure URL
    """
    from .payment_gateways import EsewaPaymentGateway
    from .payment_simulation import PaymentSimulator
    
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Validate transaction
    if transaction.payment_status == 'PAID':
        messages.info(request, "This transaction is already paid.")
        return redirect('inventory:transaction_detail', transaction_id=transaction_id)
    
    if transaction.payment_method != 'ESEWA':
        messages.error(request, "This transaction is not set for eSewa payment.")
        return redirect('inventory:transaction_detail', transaction_id=transaction_id)
    
    # Check if simulation mode is enabled
    if PaymentSimulator.is_simulation_mode():
        messages.info(request, "🧪 Using simulation mode (eSewa gateway not accessible)")
        return redirect('inventory:simulate_payment_page', transaction_id=transaction_id, gateway_type='esewa')
    
    # Check if eSewa is enabled
    if not getattr(settings, 'ESEWA_ENABLED', False):
        messages.warning(
            request,
            "eSewa test environment is not accessible. Using simulation mode for demonstration."
        )
        return redirect('inventory:simulate_payment_page', transaction_id=transaction_id, gateway_type='esewa')
    
    # Initialize eSewa gateway
    esewa = EsewaPaymentGateway()
    payment_form = esewa.generate_payment_form(transaction)
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'transaction': transaction,
        'payment_form': payment_form,
    })
    
    return render(request, 'inventory/payment_esewa.html', context)


@manager_or_admin_required
def verify_esewa_payment(request):
    """
    Verify eSewa payment after successful payment
    
    Academic Explanation (for Viva):
    ---------------------------------
    This is the success callback URL for eSewa. After successful payment,
    eSewa redirects here with payment parameters. We must verify these
    with eSewa's verification API before marking transaction as paid.
    
    Security:
    - Verify all parameters with eSewa API
    - Use atomic transactions
    - Log all verification attempts
    """
    from .payment_gateways import EsewaPaymentGateway
    from django.db import transaction as db_transaction
    
    # Get payment data from eSewa callback
    ref_id = request.GET.get('refId')
    oid = request.GET.get('oid')  # Our transaction ID (format: TXN123)
    amt = request.GET.get('amt')
    
    if not all([ref_id, oid, amt]):
        messages.error(request, "Invalid payment callback data.")
        return redirect('inventory:transaction_list')
    
    try:
        # Extract transaction ID from oid (format: TXN123 -> 123)
        transaction_id = oid.replace('TXN', '')
        transaction_obj = Transaction.objects.get(id=transaction_id)
        
        # Verify payment with eSewa API
        esewa = EsewaPaymentGateway()
        verification_result = esewa.verify_payment(oid, ref_id, amt)
        
        if verification_result['success']:
            # Payment verified successfully
            with db_transaction.atomic():
                transaction_obj.payment_status = 'PAID'
                transaction_obj.payment_reference = ref_id
                transaction_obj.save()
            
            messages.success(
                request,
                f"Payment successful! Transaction #{transaction_obj.id} has been completed. "
                f"Reference: {ref_id}"
            )
            return redirect('inventory:payment_success', transaction_id=transaction_obj.id)
        else:
            # Payment verification failed
            transaction_obj.payment_status = 'FAILED'
            transaction_obj.save()
            
            messages.error(
                request,
                f"Payment verification failed: {verification_result.get('error', 'Unknown error')}"
            )
            return redirect('inventory:payment_failure', transaction_id=transaction_obj.id)
            
    except Transaction.DoesNotExist:
        messages.error(request, "Transaction not found.")
        return redirect('inventory:transaction_list')
    except Exception as e:
        logger.error(f"eSewa verification error: {str(e)}")
        messages.error(request, f"Error processing payment: {str(e)}")
        return redirect('inventory:transaction_list')


@manager_or_admin_required
def esewa_payment_failure(request):
    """
    Handle eSewa payment failure
    
    This is called when user cancels payment or payment fails on eSewa
    """
    messages.error(request, "Payment was cancelled or failed. Please try again.")
    return redirect('inventory:transaction_list')


@approved_user_required
def payment_success(request, transaction_id):
    """
    Payment success page
    
    Shows payment confirmation and transaction details
    """
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'transaction': transaction,
        'page_title': 'Payment Successful',
    })
    
    return render(request, 'inventory/payment_success.html', context)


@approved_user_required
def payment_failure(request, transaction_id):
    """
    Payment failure page
    
    Shows payment failure message and allows retry
    """
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'transaction': transaction,
        'page_title': 'Payment Failed',
    })
    
    return render(request, 'inventory/payment_failure.html', context)


# ==================== PAYMENT SIMULATION VIEWS ====================

@manager_or_admin_required
def simulate_payment_page(request, transaction_id, gateway_type):
    """
    Show simulated payment page when actual gateways are not accessible
    
    This is used for:
    - Testing when payment gateways are down
    - Academic demonstration without real gateway accounts
    - Development without internet connection
    """
    from .payment_simulation import PaymentSimulator
    
    if not PaymentSimulator.is_simulation_mode():
        messages.error(request, "Simulation mode is not enabled.")
        return redirect('inventory:transaction_detail', transaction_id=transaction_id)
    
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    gateway_names = {
        'khalti': 'Khalti',
        'esewa': 'eSewa'
    }
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'transaction': transaction,
        'gateway_type': gateway_type,
        'gateway_name': gateway_names.get(gateway_type, 'Payment Gateway'),
    })
    
    return render(request, 'inventory/payment_simulation.html', context)


@manager_or_admin_required
def simulate_payment_complete(request, transaction_id):
    """
    Complete simulated payment
    
    Simulates the callback from payment gateway
    """
    from .payment_simulation import PaymentSimulator
    from django.db import transaction as db_transaction
    from django.core.exceptions import ValidationError
    
    if not PaymentSimulator.is_simulation_mode():
        messages.error(request, "Simulation mode is not enabled.")
        return redirect('inventory:transaction_detail', transaction_id=transaction_id)
    
    if request.method != 'POST':
        return redirect('inventory:transaction_detail', transaction_id=transaction_id)
    
    transaction_obj = get_object_or_404(Transaction, id=transaction_id)
    action = request.POST.get('action')
    gateway = request.POST.get('gateway')
    
    if action == 'success':
        # Simulate successful payment
        try:
            with db_transaction.atomic():
                if gateway == 'khalti':
                    result = PaymentSimulator.simulate_khalti_payment(transaction_obj)
                else:
                    result = PaymentSimulator.simulate_esewa_payment(transaction_obj)
                
                transaction_obj.payment_status = 'PAID'
                transaction_obj.payment_reference = result['transaction_id'] if gateway == 'khalti' else result['ref_id']
                transaction_obj.save()
            
            messages.success(
                request,
                f"✅ Payment simulated successfully! Transaction #{transaction_obj.id} completed. "
                f"Reference: {transaction_obj.payment_reference} (Simulation Mode)"
            )
            return redirect('inventory:payment_success', transaction_id=transaction_obj.id)
            
        except ValidationError as e:
            # Handle insufficient stock error
            transaction_obj.payment_status = 'FAILED'
            transaction_obj.save()
            
            error_message = str(e.messages[0]) if hasattr(e, 'messages') else str(e)
            messages.error(
                request,
                f"❌ Payment cannot be completed: {error_message} "
                f"Transaction #{transaction_obj.id} marked as FAILED."
            )
            return redirect('inventory:payment_failure', transaction_id=transaction_obj.id)
            
        except Exception as e:
            logger.error(f"Simulation payment error: {str(e)}")
            messages.error(
                request,
                f"❌ Error processing payment: {str(e)}"
            )
            return redirect('inventory:transaction_detail', transaction_id=transaction_obj.id)
    
    else:
        # Simulate failed payment
        transaction_obj.payment_status = 'FAILED'
        transaction_obj.save()
        
        messages.error(
            request,
            f"❌ Payment simulation failed. Transaction #{transaction_obj.id} marked as failed. (Simulation Mode)"
        )
        return redirect('inventory:payment_failure', transaction_id=transaction_obj.id)



@approved_user_required
def monthly_report(request):
    """Display monthly sales, purchases, and profit reports"""
    from django.utils import timezone
    from dateutil.relativedelta import relativedelta
    
    # Get year and month from request or use current
    now = timezone.now()
    year = int(request.GET.get('year', now.year))
    month = int(request.GET.get('month', now.month))
    
    # Get the monthly report
    report = Transaction.get_monthly_report(year, month)
    
    # Get month name
    from calendar import month_name
    month_name_str = month_name[month]
    
    # Get last 6 months for comparison (accurate month calculation)
    reports_history = []
    current_date = now.replace(day=1)  # Start from first day of current month
    
    for i in range(6):
        # Subtract i months accurately
        target_date = current_date - relativedelta(months=i)
        temp_year = target_date.year
        temp_month = target_date.month
        
        temp_report = Transaction.get_monthly_report(temp_year, temp_month)
        temp_report['month_name'] = month_name[temp_month]
        reports_history.append(temp_report)
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'report': report,
        'year': year,
        'month': month,
        'month_name': month_name_str,
        'reports_history': reports_history,
    })
    
    return render(request, 'inventory/monthly_report.html', context)



# ==================== CHATBOT VIEW ====================

@approved_user_required
def chatbot_api(request):
    """Process chatbot messages and return JSON responses"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json as _json
    try:
        body = _json.loads(request.body)
        message = body.get('message', '').strip()
    except Exception:
        message = request.POST.get('message', '').strip()

    if not message:
        return JsonResponse({'reply': 'Please type a message.'})

    from .chatbot import get_chatbot_response
    response = get_chatbot_response(message)
    return JsonResponse(response)
# ==================== SUPPLIER VIEWS ====================

@manager_or_admin_required
def supplier_list(request):
    """List all suppliers"""
    suppliers = Supplier.objects.all()
    search = request.GET.get('search', '')
    if search:
        suppliers = suppliers.filter(Q(name__icontains=search) | Q(email__icontains=search))
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({'suppliers': suppliers, 'search_query': search})
    return render(request, 'inventory/supplier_list.html', context)


@manager_or_admin_required
def supplier_add(request):
    """Add a new supplier"""
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        phone   = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        if not name:
            messages.error(request, 'Supplier name is required.')
            return render(request, 'inventory/supplier_form.html', UserRoleManager.get_context_for_user(request.user))
        Supplier.objects.create(
            name=name, email=email or None, phone=phone or None,
            address=address or None, created_by=request.user
        )
        messages.success(request, f"Supplier '{name}' added successfully.")
        return redirect('inventory:supplier_list')
    context = UserRoleManager.get_context_for_user(request.user)
    return render(request, 'inventory/supplier_form.html', context)


@manager_or_admin_required
def supplier_edit(request, supplier_id):
    """Edit a supplier"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    if request.method == 'POST':
        supplier.name    = request.POST.get('name', '').strip()
        supplier.email   = request.POST.get('email', '').strip() or None
        supplier.phone   = request.POST.get('phone', '').strip() or None
        supplier.address = request.POST.get('address', '').strip() or None
        if not supplier.name:
            messages.error(request, 'Supplier name is required.')
            context = UserRoleManager.get_context_for_user(request.user)
            context['supplier'] = supplier
            return render(request, 'inventory/supplier_form.html', context)
        supplier.save()
        messages.success(request, f"Supplier '{supplier.name}' updated successfully.")
        return redirect('inventory:supplier_list')
    context = UserRoleManager.get_context_for_user(request.user)
    context['supplier'] = supplier
    return render(request, 'inventory/supplier_form.html', context)


@admin_required
def supplier_delete(request, supplier_id):
    """Delete (soft) a supplier"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    if request.method == 'POST':
        name = supplier.name
        supplier.delete()
        messages.success(request, f"Supplier '{name}' deleted.")
    return redirect('inventory:supplier_list')


# ==================== CUSTOMER VIEWS ====================

@manager_or_admin_required
def customer_list(request):
    """List all customers"""
    customers = Customer.objects.all()
    search = request.GET.get('search', '')
    if search:
        customers = customers.filter(Q(name__icontains=search) | Q(email__icontains=search))
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({'customers': customers, 'search_query': search})
    return render(request, 'inventory/customer_list.html', context)


@manager_or_admin_required
def customer_add(request):
    """Add a new customer"""
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        phone   = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        if not name:
            messages.error(request, 'Customer name is required.')
            return render(request, 'inventory/customer_form.html', UserRoleManager.get_context_for_user(request.user))
        Customer.objects.create(
            name=name, email=email or None, phone=phone or None,
            address=address or None, created_by=request.user
        )
        messages.success(request, f"Customer '{name}' added successfully.")
        return redirect('inventory:customer_list')
    context = UserRoleManager.get_context_for_user(request.user)
    return render(request, 'inventory/customer_form.html', context)


@manager_or_admin_required
def customer_edit(request, customer_id):
    """Edit a customer"""
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        customer.name    = request.POST.get('name', '').strip()
        customer.email   = request.POST.get('email', '').strip() or None
        customer.phone   = request.POST.get('phone', '').strip() or None
        customer.address = request.POST.get('address', '').strip() or None
        if not customer.name:
            messages.error(request, 'Customer name is required.')
            context = UserRoleManager.get_context_for_user(request.user)
            context['customer'] = customer
            return render(request, 'inventory/customer_form.html', context)
        customer.save()
        messages.success(request, f"Customer '{customer.name}' updated successfully.")
        return redirect('inventory:customer_list')
    context = UserRoleManager.get_context_for_user(request.user)
    context['customer'] = customer
    return render(request, 'inventory/customer_form.html', context)


@admin_required
def customer_delete(request, customer_id):
    """Delete (soft) a customer"""
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        name = customer.name
        customer.delete()
        messages.success(request, f"Customer '{name}' deleted.")
    return redirect('inventory:customer_list')
@manager_or_admin_required
def stock_adjustment(request, item_id):
    from .models import StockAdjustment
    item = get_object_or_404(Item, id=item_id)
    adjustments = StockAdjustment.objects.filter(item=item)[:10]

    if request.method == 'POST':
        adjustment_type = request.POST.get('adjustment_type')
        quantity        = request.POST.get('quantity')
        reason          = request.POST.get('reason', '').strip()
        notes           = request.POST.get('notes', '').strip()

        if not all([adjustment_type, quantity, reason]):
            messages.error(request, 'Please fill in all required fields.')
            context = UserRoleManager.get_context_for_user(request.user)
            context.update({'item': item, 'adjustments': adjustments})
            return render(request, 'inventory/stock_adjustment.html', context)

        try:
            qty = int(quantity)
            if qty <= 0:
                raise ValueError

            qty_before = item.quantity

            if adjustment_type == 'add':
                item.quantity += qty
            elif adjustment_type == 'remove':
                if item.quantity - qty < 0:
                    messages.error(request, f'Cannot remove {qty} units — only {item.quantity} in stock.')
                    context = UserRoleManager.get_context_for_user(request.user)
                    context.update({'item': item, 'adjustments': adjustments})
                    return render(request, 'inventory/stock_adjustment.html', context)
                item.quantity -= qty
            else:
                messages.error(request, 'Invalid adjustment type.')
                return redirect('inventory:stock_adjustment', item_id=item_id)

            item.save()

            StockAdjustment.objects.create(
                item=item,
                adjustment_type=adjustment_type,
                quantity=qty,
                reason=reason,
                notes=notes or None,
                quantity_before=qty_before,
                quantity_after=item.quantity,
                adjusted_by=request.user,
            )

            action = 'added to' if adjustment_type == 'add' else 'removed from'
            messages.success(
                request,
                f'✅ {qty} units {action} {item.name}. '
                f'Stock: {qty_before} → {item.quantity} units. Reason: {reason}'
            )
            return redirect('inventory:item_list')

        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid quantity.')

    context = UserRoleManager.get_context_for_user(request.user)
    context.update({'item': item, 'adjustments': adjustments})
    return render(request, 'inventory/stock_adjustment.html', context)
@manager_or_admin_required
def create_purchase_order(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    from inventory.ml_predictor import ml_predictor
    suggestion = ml_predictor.calculate_reorder_recommendation(item)
    suggested_qty = suggestion.get('suggested_quantity', item.reorder_level * 2)
    if suggested_qty < 1:
        suggested_qty = item.reorder_level * 2
    suppliers = Supplier.objects.all()

    if request.method == 'POST':
        supplier_id = request.POST.get('supplier_id')
        quantity    = request.POST.get('quantity')
        unit_price  = request.POST.get('unit_price')
        notes       = request.POST.get('notes', '').strip()
        try:
            qty   = int(quantity)
            price = float(unit_price)
            if qty <= 0 or price < 0:
                raise ValueError
            supplier = get_object_or_404(Supplier, id=supplier_id) if supplier_id else None
            Transaction.objects.create(
                item=item, transaction_type='PURCHASE', quantity=qty,
                unit_price=price, total_amount=qty * price,
                payment_status='PAID', payment_method='BANK_TRANSFER',
                supplier=supplier, performed_by=request.user,
                notes=notes or f'AI reorder suggestion. Suggested qty: {suggested_qty}',
            )
            if supplier and not item.supplier:
                item.supplier = supplier
                item.save()
            messages.success(request, f'✅ Purchase order created for {qty} units of {item.name}. New stock: {item.quantity + qty} units.')
            return redirect('inventory:reorder_suggestions')
        except (ValueError, TypeError):
            messages.error(request, 'Please enter valid quantity and price.')

    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'item': item, 'suggestion': suggestion, 'suggested_qty': suggested_qty,
        'suppliers': suppliers,
        'default_supplier': item.supplier,
        'default_price': item.cost_price if item.cost_price > 0 else item.price * 0.6,
    })
    return render(request, 'inventory/create_purchase_order.html', context)