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
    """List all inventory items with search, filter, and reorder suggestions"""
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
        # Filter items that need reordering based on predictive logic
        reorder_items = []
        for item in items:
            if item.needs_reorder:
                reorder_items.append(item.id)
        items = items.filter(id__in=reorder_items)

    # Calculate summary statistics
    total_items = Item.objects.count()
    low_stock_count = Item.objects.filter(quantity__lte=F('reorder_level'), quantity__gt=0).count()
    out_of_stock_count = Item.objects.filter(quantity=0).count()
    in_stock_count = Item.objects.filter(quantity__gt=F('reorder_level')).count()
    
    # Calculate reorder suggestions
    reorder_suggestions = []
    for item in Item.objects.all():
        if item.needs_reorder:
            reorder_suggestions.append(item)
    
    reorder_count = len(reorder_suggestions)

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
    })

    return render(request, "inventory/list.html", context)


@approved_user_required
def reorder_suggestions(request):
    """View all reorder suggestions with predictive analytics"""
    items = Item.objects.all()
    suggestions = []
    
    for item in items:
        if item.needs_reorder:
            daily_usage = item.get_average_daily_usage()
            predicted_needed = item.get_predicted_stock_needed()
            suggestions.append({
                'item': item,
                'daily_usage': daily_usage,
                'predicted_needed': predicted_needed,
                'days_until_stockout': item.quantity / daily_usage if daily_usage > 0 else float('inf'),
                'suggested_quantity': item.suggested_reorder_quantity,
            })
    
    # Sort by urgency (days until stockout)
    suggestions.sort(key=lambda x: x['days_until_stockout'])
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'suggestions': suggestions,
        'total_suggestions': len(suggestions),
    })
    
    return render(request, 'inventory/reorder_suggestions.html', context)


@manager_or_admin_required
def export_csv(request):
    """Export inventory data to CSV with reorder information"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Item Name', 'Quantity', 'Price (Rs.)', 'Total Value (Rs.)', 
        'Stock Status', 'Reorder Level', 'Lead Time (Days)', 
        'Daily Usage', 'Reorder Suggested', 'Suggested Quantity'
    ])
    
    # Write data
    for item in Item.objects.all():
        total_value = float(item.price) * item.quantity
        daily_usage = item.get_average_daily_usage()
        writer.writerow([
            item.name,
            item.quantity,
            f"{item.price:.2f}",
            f"{total_value:.2f}",
            item.stock_status.replace('-', ' ').title(),
            item.reorder_level,
            item.lead_time_days,
            f"{daily_usage:.2f}",
            'Yes' if item.needs_reorder else 'No',
            item.suggested_reorder_quantity if item.needs_reorder else 0,
        ])
    
    # Write summary
    writer.writerow([])  # Empty row
    writer.writerow(['SUMMARY'])
    writer.writerow(['Total Items', Item.objects.count()])
    writer.writerow(['In Stock Items', Item.objects.filter(quantity__gt=F('reorder_level')).count()])
    writer.writerow(['Low Stock Items', Item.objects.filter(quantity__lte=F('reorder_level'), quantity__gt=0).count()])
    writer.writerow(['Out of Stock Items', Item.objects.filter(quantity=0).count()])
    
    # Calculate reorder suggestions
    reorder_count = sum(1 for item in Item.objects.all() if item.needs_reorder)
    writer.writerow(['Items Needing Reorder', reorder_count])
    
    # Calculate total inventory value
    total_value = sum(float(item.price) * item.quantity for item in Item.objects.all())
    writer.writerow(['Total Inventory Value (Rs.)', f"{total_value:.2f}"])
    
    return response


@manager_or_admin_required
def item_add(request):
    """Add new inventory item with reorder settings"""
    if request.method == "POST":
        name = request.POST.get("name")
        quantity = request.POST.get("quantity")
        price = request.POST.get("price")
        reorder_level = request.POST.get("reorder_level", 10)
        lead_time_days = request.POST.get("lead_time_days", 7)

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
            
            Item.objects.create(
                name=name,
                quantity=quantity,
                price=price,
                reorder_level=reorder_level,
                lead_time_days=lead_time_days
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
    """Edit inventory item with reorder settings"""
    item = get_object_or_404(Item, id=item_id)

    if request.method == "POST":
        name = request.POST.get("name")
        quantity = request.POST.get("quantity")
        price = request.POST.get("price")
        reorder_level = request.POST.get("reorder_level")
        lead_time_days = request.POST.get("lead_time_days")

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
            quantity = int(quantity)
            unit_price = float(unit_price)
            
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
def transaction_export_csv(request):
    """Export transaction data to CSV with payment information"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions_report.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Date', 'Time', 'Item', 'Type', 'Quantity', 
        'Unit Price (Rs.)', 'Total Amount (Rs.)', 'Payment Status',
        'Payment Method', 'Payment Reference', 'Performed By', 'Notes'
    ])
    
    # Write transaction data
    for transaction in Transaction.objects.select_related('item', 'performed_by').all():
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
            transaction.notes or ''
        ])
    
    # Write summary
    writer.writerow([])
    writer.writerow(['SUMMARY'])
    
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
    
    writer.writerow(['Total Sales (Rs.)', f"{total_sales:.2f}"])
    writer.writerow(['Total Purchases (Rs.)', f"{total_purchases:.2f}"])
    writer.writerow(['Pending Payments (Rs.)', f"{pending_amount:.2f}"])
    writer.writerow(['Net Amount (Rs.)', f"{total_sales - total_purchases:.2f}"])
    writer.writerow(['Total Transactions', Transaction.objects.count()])
    
    return response