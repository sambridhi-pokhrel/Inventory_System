from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, F, Count
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import io
import uuid
from .models import Item, Transaction
from .forms import TransactionForm, TransactionFilterForm
from users.decorators import (
    approved_user_required,
    manager_or_admin_required,
    admin_required,
    role_required
)
from users.utils import UserRoleManager


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
    """Add new inventory item with reorder settings and image upload"""
    if request.method == "POST":
        name = request.POST.get("name")
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
            
            # Create item with image
            Item.objects.create(
                name=name,
                quantity=quantity,
                price=price,
                reorder_level=reorder_level,
                lead_time_days=lead_time_days,
                image=image  # Save uploaded image
            )
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
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'transactions': page_obj,
        'recent_sales': recent_sales,
        'recent_purchases': recent_purchases,
        'total_sales': total_sales,
        'total_purchases': total_purchases,
        'pending_payments': pending_payments,
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
        
        try:
            item = Item.objects.get(id=item_id)
            # Convert quantity to integer (handle decimal inputs)
            quantity = int(float(quantity))  # Convert to float first, then to int
            unit_price = float(unit_price)
            
            # Validate inputs
            if quantity <= 0:
                messages.error(request, "Quantity must be greater than 0.")
                context = UserRoleManager.get_context_for_user(request.user)
                context.update({'items': Item.objects.all().order_by('name')})
                return render(request, 'inventory/transaction_create.html', context)
            
            if unit_price <= 0:
                messages.error(request, "Unit price must be greater than 0.")
                context = UserRoleManager.get_context_for_user(request.user)
                context.update({'items': Item.objects.all().order_by('name')})
                return render(request, 'inventory/transaction_create.html', context)
            
            # Create transaction
            transaction = Transaction.objects.create(
                item=item,
                transaction_type=transaction_type,
                quantity=quantity,
                unit_price=unit_price,
                payment_method=payment_method,
                performed_by=request.user,
                notes=notes,
                payment_status='PENDING'
            )
            
            # Simulate payment processing
            if payment_method == 'KHALTI':
                success = transaction.simulate_khalti_payment()
                if success:
                    messages.success(
                        request,
                        f"Transaction completed successfully! Payment processed via Khalti. "
                        f"Reference: {transaction.payment_reference}"
                    )
                else:
                    messages.warning(request, "Transaction created but payment processing failed.")
            else:
                # For other payment methods, mark as paid immediately
                transaction.payment_status = 'PAID'
                transaction.save()
                messages.success(request, f"Transaction completed successfully via {payment_method}!")
            
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
    context['transaction'] = transaction
    
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
    """Analytics dashboard with comprehensive visualizations"""
    from .analytics import analytics
    
    # Generate all charts
    sales_trend = analytics.generate_sales_trend_chart(days=30)
    inventory_performance = analytics.generate_inventory_performance_chart()
    ai_performance = analytics.generate_ai_model_performance_chart()
    
    # Get top selling item for actual vs predicted chart
    top_item = Transaction.objects.filter(
        transaction_type='SALE',
        payment_status='PAID'
    ).values('item').annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold').first()
    
    actual_vs_predicted = None
    if top_item:
        actual_vs_predicted = analytics.generate_actual_vs_predicted_chart(
            item_id=top_item['item'], days=14
        )
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'sales_trend': sales_trend,
        'inventory_performance': inventory_performance,
        'ai_performance': ai_performance,
        'actual_vs_predicted': actual_vs_predicted,
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