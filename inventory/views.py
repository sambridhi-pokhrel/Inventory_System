from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, F
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import io
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
    """List all inventory items with search and filter functionality"""
    items = Item.objects.all()
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query)
        )
    
    # Handle filter
    filter_type = request.GET.get('filter', '')
    if filter_type == 'low_stock':
        items = items.filter(quantity__lte=10)
    elif filter_type == 'out_of_stock':
        items = items.filter(quantity=0)
    elif filter_type == 'in_stock':
        items = items.filter(quantity__gt=10)

    # Calculate summary statistics
    total_items = Item.objects.count()
    low_stock_count = Item.objects.filter(quantity__lte=10, quantity__gt=0).count()
    out_of_stock_count = Item.objects.filter(quantity=0).count()
    in_stock_count = Item.objects.filter(quantity__gt=10).count()

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
    })

    return render(request, "inventory/list.html", context)


@manager_or_admin_required
def export_csv(request):
    """Export inventory data to CSV - Manager and Admin only"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow(['Item Name', 'Quantity', 'Price ($)', 'Total Value ($)', 'Stock Status'])
    
    # Write data
    for item in Item.objects.all():
        total_value = float(item.price) * item.quantity
        writer.writerow([
            item.name,
            item.quantity,
            f"{item.price:.2f}",
            f"{total_value:.2f}",
            item.stock_status.replace('-', ' ').title()
        ])
    
    # Write summary
    writer.writerow([])  # Empty row
    writer.writerow(['SUMMARY'])
    writer.writerow(['Total Items', Item.objects.count()])
    writer.writerow(['In Stock Items', Item.objects.filter(quantity__gt=10).count()])
    writer.writerow(['Low Stock Items', Item.objects.filter(quantity__lte=10, quantity__gt=0).count()])
    writer.writerow(['Out of Stock Items', Item.objects.filter(quantity=0).count()])
    
    # Calculate total inventory value
    total_value = sum(float(item.price) * item.quantity for item in Item.objects.all())
    writer.writerow(['Total Inventory Value ($)', f"{total_value:.2f}"])
    
    return response


@manager_or_admin_required
def export_pdf(request):
    """Export inventory data to PDF - Manager and Admin only"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.pdf"'
    
    # Create PDF document
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # Center alignment
        textColor=colors.darkblue
    )
    
    # Build content
    content = []
    
    # Title
    title = Paragraph("Inventory Management Report", title_style)
    content.append(title)
    content.append(Spacer(1, 20))
    
    # Summary section
    summary_data = [
        ['Summary', ''],
        ['Total Items', str(Item.objects.count())],
        ['In Stock Items', str(Item.objects.filter(quantity__gt=10).count())],
        ['Low Stock Items', str(Item.objects.filter(quantity__lte=10, quantity__gt=0).count())],
        ['Out of Stock Items', str(Item.objects.filter(quantity=0).count())],
    ]
    
    # Calculate total value
    total_value = sum(float(item.price) * item.quantity for item in Item.objects.all())
    summary_data.append(['Total Inventory Value', f"${total_value:.2f}"])
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    content.append(summary_table)
    content.append(Spacer(1, 30))
    
    # Detailed inventory table
    detail_title = Paragraph("Detailed Inventory", styles['Heading2'])
    content.append(detail_title)
    content.append(Spacer(1, 12))
    
    # Prepare data for detailed table
    data = [['Item Name', 'Quantity', 'Price ($)', 'Total Value ($)', 'Status']]
    
    for item in Item.objects.all():
        total_value = float(item.price) * item.quantity
        status = item.stock_status.replace('-', ' ').title()
        data.append([
            item.name,
            str(item.quantity),
            f"{item.price:.2f}",
            f"{total_value:.2f}",
            status
        ])
    
    # Create table
    table = Table(data, colWidths=[2.5*inch, 1*inch, 1*inch, 1.2*inch, 1.3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    content.append(table)
    
    # Build PDF
    doc.build(content)
    
    # Get PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    response.write(pdf_data)
    return response


@manager_or_admin_required
def item_add(request):
    """Add new inventory item - Manager and Admin only"""
    if request.method == "POST":
        name = request.POST.get("name")
        quantity = request.POST.get("quantity")
        price = request.POST.get("price")

        # Validate input
        if not all([name, quantity, price]):
            messages.error(request, "All fields are required.")
            return render(request, "inventory/add.html")

        try:
            quantity = int(quantity)
            price = float(price)
            
            if quantity < 0 or price < 0:
                messages.error(request, "Quantity and price must be non-negative.")
                return render(request, "inventory/add.html")
            
            Item.objects.create(
                name=name,
                quantity=quantity,
                price=price
            )
            messages.success(request, f"Item '{name}' has been added successfully.")
            return redirect("inventory:item_list")
            
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid numbers for quantity and price.")
            return render(request, "inventory/add.html")

    context = UserRoleManager.get_context_for_user(request.user)
    return render(request, "inventory/add.html", context)


@manager_or_admin_required
def item_edit(request, item_id):
    """Edit inventory item - Manager and Admin only"""
    item = get_object_or_404(Item, id=item_id)

    if request.method == "POST":
        name = request.POST.get("name")
        quantity = request.POST.get("quantity")
        price = request.POST.get("price")

        # Validate input
        if not all([name, quantity, price]):
            messages.error(request, "All fields are required.")
            context = UserRoleManager.get_context_for_user(request.user)
            context["item"] = item
            return render(request, "inventory/edit.html", context)

        try:
            quantity = int(quantity)
            price = float(price)
            
            if quantity < 0 or price < 0:
                messages.error(request, "Quantity and price must be non-negative.")
                context = UserRoleManager.get_context_for_user(request.user)
                context["item"] = item
                return render(request, "inventory/edit.html", context)
            
            item.name = name
            item.quantity = quantity
            item.price = price
            item.save()
            
            messages.success(request, f"Item '{name}' has been updated successfully.")
            return redirect("inventory:item_list")
            
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid numbers for quantity and price.")
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
    """List all transactions with filtering and pagination"""
    transactions = Transaction.objects.select_related('item', 'performed_by').all()
    
    # Handle filtering
    filter_form = TransactionFilterForm(request.GET)
    if filter_form.is_valid():
        if filter_form.cleaned_data['transaction_type']:
            transactions = transactions.filter(
                transaction_type=filter_form.cleaned_data['transaction_type']
            )
        
        if filter_form.cleaned_data['item']:
            transactions = transactions.filter(
                item=filter_form.cleaned_data['item']
            )
        
        if filter_form.cleaned_data['date_from']:
            transactions = transactions.filter(
                timestamp__date__gte=filter_form.cleaned_data['date_from']
            )
        
        if filter_form.cleaned_data['date_to']:
            transactions = transactions.filter(
                timestamp__date__lte=filter_form.cleaned_data['date_to']
            )
    
    # Pagination
    paginator = Paginator(transactions, 20)  # Show 20 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate summary statistics
    total_sales = Transaction.objects.filter(transaction_type='SALE').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    total_purchases = Transaction.objects.filter(transaction_type='PURCHASE').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    recent_transactions = Transaction.objects.select_related('item', 'performed_by')[:5]
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_sales': total_sales,
        'total_purchases': total_purchases,
        'recent_transactions': recent_transactions,
        'transaction_count': transactions.count(),
    })
    
    return render(request, 'inventory/transaction_list.html', context)


@manager_or_admin_required
def transaction_create(request):
    """Create new transaction - Manager and Admin only"""
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            try:
                transaction = form.save(commit=False)
                transaction.performed_by = request.user
                transaction.save()
                
                messages.success(
                    request, 
                    f"{transaction.transaction_type.title()} transaction for {transaction.item.name} "
                    f"(Qty: {transaction.quantity}) completed successfully."
                )
                return redirect('inventory:transaction_list')
                
            except Exception as e:
                messages.error(request, f"Error creating transaction: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = TransactionForm()
    
    context = UserRoleManager.get_context_for_user(request.user)
    context.update({
        'form': form,
        'items': Item.objects.all().order_by('name'),
    })
    
    return render(request, 'inventory/transaction_create.html', context)


@approved_user_required
def transaction_detail(request, transaction_id):
    """View transaction details"""
    transaction = get_object_or_404(
        Transaction.objects.select_related('item', 'performed_by'),
        id=transaction_id
    )
    
    context = UserRoleManager.get_context_for_user(request.user)
    context['transaction'] = transaction
    
    return render(request, 'inventory/transaction_detail.html', context)


@manager_or_admin_required
def get_item_price(request):
    """AJAX endpoint to get item price for transaction form"""
    item_id = request.GET.get('item_id')
    if item_id:
        try:
            item = Item.objects.get(id=item_id)
            return JsonResponse({
                'price': str(item.price),
                'quantity': item.quantity,
                'name': item.name
            })
        except Item.DoesNotExist:
            pass
    
    return JsonResponse({'error': 'Item not found'}, status=404)


@manager_or_admin_required
def transaction_export_csv(request):
    """Export transaction data to CSV - Manager and Admin only"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions_report.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Date', 'Time', 'Item', 'Type', 'Quantity', 
        'Unit Price ($)', 'Total Amount ($)', 'Performed By', 'Notes'
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
            transaction.performed_by.get_full_name() or transaction.performed_by.username,
            transaction.notes or ''
        ])
    
    # Write summary
    writer.writerow([])  # Empty row
    writer.writerow(['SUMMARY'])
    
    total_sales = Transaction.objects.filter(transaction_type='SALE').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    total_purchases = Transaction.objects.filter(transaction_type='PURCHASE').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    writer.writerow(['Total Sales ($)', f"{total_sales:.2f}"])
    writer.writerow(['Total Purchases ($)', f"{total_purchases:.2f}"])
    writer.writerow(['Net Amount ($)', f"{total_sales - total_purchases:.2f}"])
    writer.writerow(['Total Transactions', Transaction.objects.count()])
    
    return response