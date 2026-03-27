"""
Email Notification Utility for Inventory Management System
Sends optional email alerts for low stock and transaction confirmations.
"""

from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_low_stock_alert(item, recipient_email):
    """
    Send low stock alert email for an item.
    
    Args:
        item: Item model instance
        recipient_email: Email address to send alert to
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f"⚠️ Low Stock Alert: {item.name}"
        message = (
            f"Hello,\n\n"
            f"This is an automated alert from the Inventory Management System.\n\n"
            f"Item: {item.name}\n"
            f"Current Stock: {item.quantity} units\n"
            f"Reorder Level: {item.reorder_level} units\n"
            f"Status: {'OUT OF STOCK' if item.quantity == 0 else 'LOW STOCK'}\n\n"
            f"Action Required: Please restock this item as soon as possible.\n\n"
            f"Best regards,\n"
            f"Inventory Management System"
        )
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info(f"Low stock alert sent for {item.name} to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send low stock alert for {item.name}: {e}")
        return False


def send_transaction_confirmation(transaction, recipient_email):
    """
    Send transaction confirmation email.
    
    Args:
        transaction: Transaction model instance
        recipient_email: Email address to send confirmation to
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f"Transaction Confirmation #{transaction.id}"
        
        message = (
            f"Hello,\n\n"
            f"Your transaction has been recorded successfully.\n\n"
            f"Transaction Details:\n"
            f"─────────────────────\n"
            f"Transaction ID: #{transaction.id}\n"
            f"Type: {transaction.get_transaction_type_display()}\n"
            f"Item: {transaction.item.name}\n"
            f"Quantity: {transaction.quantity} units\n"
            f"Unit Price: Rs. {transaction.unit_price:,.2f}\n"
            f"Total Amount: Rs. {transaction.total_amount:,.2f}\n"
            f"Payment Method: {transaction.get_payment_method_display()}\n"
            f"Payment Status: {transaction.get_payment_status_display()}\n"
            f"Date: {transaction.timestamp.strftime('%B %d, %Y at %I:%M %p')}\n"
        )
        
        if transaction.transaction_type == 'SALE' and transaction.payment_status == 'PAID':
            profit = transaction.total_profit
            message += f"Profit: Rs. {profit:,.2f}\n"
        
        if transaction.supplier:
            message += f"Supplier: {transaction.supplier.name}\n"
        
        if transaction.customer:
            message += f"Customer: {transaction.customer.name}\n"
        
        message += (
            f"\n"
            f"Thank you for using our Inventory Management System.\n\n"
            f"Best regards,\n"
            f"Inventory Management System"
        )
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info(f"Transaction confirmation sent for #{transaction.id} to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send transaction confirmation for #{transaction.id}: {e}")
        return False


def send_bulk_low_stock_alerts(recipient_emails):
    """
    Send bulk low stock alert for all low stock items.
    
    Args:
        recipient_emails: List of email addresses
        
    Returns:
        dict: Summary of sent emails
    """
    from .models import Item
    from django.db.models import F
    
    low_stock_items = Item.objects.filter(quantity__lte=F('reorder_level'))
    out_of_stock_items = Item.objects.filter(quantity=0)
    
    if not low_stock_items.exists() and not out_of_stock_items.exists():
        return {'success': True, 'message': 'No low stock items to report'}
    
    try:
        subject = "📊 Inventory Low Stock Report"
        
        message = (
            f"Hello,\n\n"
            f"This is your automated inventory low stock report.\n\n"
        )
        
        if out_of_stock_items.exists():
            message += f"⛔ OUT OF STOCK ({out_of_stock_items.count()} items):\n"
            for item in out_of_stock_items[:10]:
                message += f"  • {item.name} — 0 units (reorder at {item.reorder_level})\n"
            if out_of_stock_items.count() > 10:
                message += f"  ... and {out_of_stock_items.count() - 10} more\n"
            message += "\n"
        
        low_only = low_stock_items.exclude(quantity=0)
        if low_only.exists():
            message += f"⚠️ LOW STOCK ({low_only.count()} items):\n"
            for item in low_only[:10]:
                message += f"  • {item.name} — {item.quantity} units (reorder at {item.reorder_level})\n"
            if low_only.count() > 10:
                message += f"  ... and {low_only.count() - 10} more\n"
        
        message += (
            f"\n"
            f"Please review and restock these items as needed.\n\n"
            f"Best regards,\n"
            f"Inventory Management System"
        )
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_emails,
            fail_silently=False,
        )
        
        return {
            'success': True,
            'message': f'Bulk alert sent to {len(recipient_emails)} recipient(s)',
            'low_stock_count': low_stock_items.count(),
            'out_of_stock_count': out_of_stock_items.count()
        }
        
    except Exception as e:
        logger.error(f"Failed to send bulk low stock alert: {e}")
        return {'success': False, 'error': str(e)}
