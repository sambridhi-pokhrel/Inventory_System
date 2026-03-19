"""
Chatbot module for Inventory Management System
Rule-based responses using Django ORM queries.
"""

from django.utils import timezone
from django.db.models import Sum, F
from datetime import date


def get_chatbot_response(message):
    """
    Process a user message and return a response dict.
    Returns: { 'reply': str, 'links': list (optional) }
    """
    msg = message.lower().strip()

    # Lazy imports to avoid circular issues
    from .models import Item, Transaction

    # ── Help / greeting ───────────────────────────────────────────
    if any(k in msg for k in ['help', 'what can you do', 'commands', 'options', 'hi', 'hello', 'hey', 'start', 'guide']):
        return {
            'reply': (
                "Hi! I'm your Inventory Assistant. Here's what you can ask me:\n\n"
                "📦 Inventory\n"
                "• How many items are in stock?\n"
                "• Show low stock items\n"
                "• Show out of stock items\n"
                "• What is the inventory value?\n\n"
                "💰 Sales & Transactions\n"
                "• Today's sales\n"
                "• Top selling products\n"
                "• Total sales revenue\n"
                "• How to record a sale?\n"
                "• How to record a purchase?\n\n"
                "📊 Reports & Analytics\n"
                "• This month's report\n"
                "• What does the analytics page show?\n\n"
                "⚙️ System Help\n"
                "• How to add an item?\n"
                "• How to edit an item?\n"
                "• How to delete an item?\n"
                "• How do payments work?\n"
                "• What is SKU?\n"
                "• What is reorder level?\n"
                "• How does AI reorder work?\n"
                "• How to manage users?\n"
                "• How to export data?"
            )
        }

    # ── Total items ───────────────────────────────────────────────
    if any(k in msg for k in ['how many items', 'total items', 'item count', 'items in stock', 'how many products', 'stock count']):
        total = Item.objects.count()
        out_of_stock = Item.objects.filter(quantity=0).count()
        low_stock = Item.objects.filter(quantity__lte=F('reorder_level'), quantity__gt=0).count()
        return {
            'reply': (
                f"There are {total} active items in inventory.\n"
                f"• {low_stock} running low on stock\n"
                f"• {out_of_stock} completely out of stock"
            ),
            'links': [{'label': 'View Inventory', 'url': '/inventory/'}]
        }

    # ── Out of stock — must come BEFORE low stock ─────────────────
    if any(k in msg for k in ['out of stock', 'no stock', 'zero stock', 'empty stock', 'out-of-stock']):
        out_items = Item.objects.filter(quantity=0)
        low_items = Item.objects.filter(quantity__lte=F('reorder_level'), quantity__gt=0)
        if not out_items.exists():
            reply = "No items are currently out of stock (quantity = 0)."
            if low_items.exists():
                names = [f"{i.name} (qty: {i.quantity})" for i in low_items[:5]]
                reply += f"\nHowever, {low_items.count()} item(s) are running low:\n" + "\n".join(f"• {n}" for n in names)
            return {
                'reply': reply,
                'links': [{'label': 'View Low Stock Items', 'url': '/inventory/?status=low-stock'}] if low_items.exists() else []
            }
        names = [i.name for i in out_items[:6]]
        return {
            'reply': f"{out_items.count()} item(s) are completely out of stock:\n" + "\n".join(f"• {n}" for n in names) + ("..." if out_items.count() > 6 else ""),
            'links': [{'label': 'View Out of Stock', 'url': '/inventory/?status=out-of-stock'}]
        }

    # ── Low stock ─────────────────────────────────────────────────
    if any(k in msg for k in ['low stock', 'low inventory', 'need restock', 'running low', 'reorder']):
        low_items = Item.objects.filter(quantity__lte=F('reorder_level'), quantity__gt=0)
        out_items = Item.objects.filter(quantity=0)
        parts = []
        if low_items.exists():
            names = [f"{i.name} (qty: {i.quantity}, reorder at: {i.reorder_level})" for i in low_items[:5]]
            parts.append(
                f"{low_items.count()} item(s) are low on stock:\n" +
                "\n".join(f"• {n}" for n in names) +
                ("\n..." if low_items.count() > 5 else "")
            )
        if out_items.exists():
            out_names = [i.name for i in out_items[:3]]
            parts.append(f"{out_items.count()} item(s) are completely out of stock: {', '.join(out_names)}.")
        if not parts:
            return {'reply': "Great news! All items are well stocked right now."}
        return {
            'reply': '\n\n'.join(parts),
            'links': [{'label': 'View Low Stock Items', 'url': '/inventory/?status=low-stock'}]
        }

    # ── Today's sales ─────────────────────────────────────────────
    if any(k in msg for k in ["today's sales", 'sales today', 'today sales', 'daily sales']):
        today = date.today()
        result = Transaction.objects.filter(
            transaction_type='SALE', payment_status='PAID', timestamp__date=today
        ).aggregate(total_qty=Sum('quantity'), total_amt=Sum('total_amount'))
        qty = result['total_qty'] or 0
        amt = result['total_amt'] or 0
        return {
            'reply': f"Today's sales ({today.strftime('%b %d, %Y')}):\n• {qty} unit(s) sold\n• Total: Rs. {amt:,.2f}",
            'links': [{'label': 'View Transactions', 'url': '/inventory/transactions/'}]
        }

    # ── Top selling products ──────────────────────────────────────
    if any(k in msg for k in ['top selling', 'best selling', 'most sold', 'popular products', 'top products']):
        top = (
            Transaction.objects.filter(transaction_type='SALE', payment_status='PAID')
            .values('item__name')
            .annotate(total=Sum('quantity'))
            .order_by('-total')[:5]
        )
        if not top:
            return {'reply': "No sales recorded yet. Start adding transactions to see top products."}
        lines = [f"{i+1}. {p['item__name']} — {p['total']} units" for i, p in enumerate(top)]
        return {
            'reply': "Top selling products:\n" + "\n".join(lines),
            'links': [{'label': 'View Analytics', 'url': '/inventory/analytics/'}]
        }

    # ── Total sales amount ────────────────────────────────────────
    if any(k in msg for k in ['total sales', 'total revenue', 'how much sales', 'sales amount', 'all sales']):
        result = Transaction.objects.filter(
            transaction_type='SALE', payment_status='PAID'
        ).aggregate(total=Sum('total_amount'))
        amt = result['total'] or 0
        count = Transaction.objects.filter(transaction_type='SALE', payment_status='PAID').count()
        return {
            'reply': f"Total sales revenue (all time):\n• Rs. {amt:,.2f} from {count} paid transaction(s).",
            'links': [{'label': 'View Transactions', 'url': '/inventory/transactions/'}]
        }

    # ── Inventory value ───────────────────────────────────────────
    if any(k in msg for k in ['inventory value', 'stock value', 'total value', 'worth', 'asset value']):
        total = sum(float(i.price) * i.quantity for i in Item.objects.all())
        return {
            'reply': f"The total current inventory value is Rs. {total:,.2f}.",
            'links': [{'label': 'View Inventory', 'url': '/inventory/'}]
        }

    # ── Monthly report ────────────────────────────────────────────
    if any(k in msg for k in ['monthly report', 'monthly sales', 'this month', 'month report', 'monthly summary']):
        now = timezone.now()
        sales = Transaction.total_sales_for_month(now.year, now.month)
        purchases = Transaction.total_purchases_for_month(now.year, now.month)
        profit = Transaction.total_profit_for_month(now.year, now.month)
        return {
            'reply': (
                f"This month ({now.strftime('%B %Y')}):\n"
                f"• Sales: Rs. {sales:,.2f}\n"
                f"• Purchases: Rs. {purchases:,.2f}\n"
                f"• Profit: Rs. {profit:,.2f}"
            ),
            'links': [{'label': 'Full Monthly Report', 'url': '/inventory/reports/monthly/'}]
        }

    # ── Analytics page ────────────────────────────────────────────
    if any(k in msg for k in ['analytics', 'charts', 'graphs', 'dashboard analytics', 'sales chart', 'analytics page']):
        return {
            'reply': (
                "The Analytics page shows 5 live charts:\n"
                "• Sales Trend — units sold over last 30 days\n"
                "• Top 5 Products — best sellers by quantity\n"
                "• Monthly Revenue — revenue grouped by month\n"
                "• Stock Distribution — current stock as a pie chart\n"
                "• Purchase vs Sales — side-by-side comparison"
            ),
            'links': [{'label': 'Open Analytics', 'url': '/inventory/analytics/'}]
        }

    # ── How to add item ───────────────────────────────────────────
    if any(k in msg for k in ['how to add', 'add item', 'add product', 'new item', 'create item', 'adding item']):
        return {
            'reply': (
                "To add a new item:\n"
                "1. Go to Inventory → click 'Add Item'\n"
                "2. Enter the item name, quantity, and price\n"
                "3. Set the reorder level (minimum stock before alert)\n"
                "4. Set lead time (days needed to restock)\n"
                "5. Optionally upload an image — or leave it blank to auto-fetch from Unsplash\n"
                "6. Click 'Add Item' to save"
            ),
            'links': [{'label': 'Add Item', 'url': '/inventory/add/'}]
        }

    # ── How to edit item ──────────────────────────────────────────
    if any(k in msg for k in ['edit item', 'update item', 'change item', 'modify item', 'how to edit']):
        return {
            'reply': (
                "To edit an item:\n"
                "1. Go to Inventory and find the item\n"
                "2. Click the edit (pencil) icon next to it\n"
                "3. Update the fields you want to change\n"
                "4. Click 'Update Item' to save\n\n"
                "Note: Only Managers and Admins can edit items."
            ),
            'links': [{'label': 'View Inventory', 'url': '/inventory/'}]
        }

    # ── How to delete item ────────────────────────────────────────
    if any(k in msg for k in ['delete item', 'remove item', 'how to delete', 'soft delete']):
        return {
            'reply': (
                "To delete an item:\n"
                "1. Go to Inventory and find the item\n"
                "2. Click the delete (trash) icon\n"
                "3. Confirm the deletion\n\n"
                "Items are soft-deleted — they are marked inactive but not permanently removed. "
                "Admins can restore them from the Admin panel."
            ),
            'links': [{'label': 'View Inventory', 'url': '/inventory/'}]
        }

    # ── How to record a sale ──────────────────────────────────────
    if any(k in msg for k in ['record sale', 'how to sell', 'create sale', 'make a sale', 'sell item', 'how to record a sale']):
        return {
            'reply': (
                "To record a sale:\n"
                "1. Go to Transactions → 'New Transaction'\n"
                "2. Select the item from the dropdown\n"
                "3. Set Transaction Type to 'Sale'\n"
                "4. Enter quantity and unit price\n"
                "5. Select a customer (optional)\n"
                "6. Choose payment method (Cash, Khalti, eSewa, etc.)\n"
                "7. Click 'Create Transaction'\n\n"
                "Stock is automatically reduced when payment is marked as Paid."
            ),
            'links': [{'label': 'New Transaction', 'url': '/inventory/transactions/create/'}]
        }

    # ── How to record a purchase ──────────────────────────────────
    if any(k in msg for k in ['record purchase', 'how to purchase', 'create purchase', 'buy stock', 'restock item', 'how to record a purchase']):
        return {
            'reply': (
                "To record a purchase:\n"
                "1. Go to Transactions → 'New Transaction'\n"
                "2. Select the item from the dropdown\n"
                "3. Set Transaction Type to 'Purchase'\n"
                "4. Enter quantity and unit price\n"
                "5. Select a supplier (optional)\n"
                "6. Click 'Create Transaction'\n\n"
                "Stock is automatically increased and the item's cost price is updated."
            ),
            'links': [{'label': 'New Transaction', 'url': '/inventory/transactions/create/'}]
        }

    # ── Transactions list ─────────────────────────────────────────
    if any(k in msg for k in ['view transactions', 'transaction list', 'sales history', 'purchase history', 'all transactions']):
        count = Transaction.objects.count()
        paid = Transaction.objects.filter(payment_status='PAID').count()
        pending = Transaction.objects.filter(payment_status='PENDING').count()
        return {
            'reply': (
                f"Transaction summary:\n"
                f"• Total: {count} transaction(s)\n"
                f"• Paid: {paid}\n"
                f"• Pending: {pending}"
            ),
            'links': [{'label': 'View Transactions', 'url': '/inventory/transactions/'}]
        }

    # ── Payments ──────────────────────────────────────────────────
    if any(k in msg for k in ['payment', 'khalti', 'esewa', 'how to pay', 'payment method', 'pay for transaction']):
        return {
            'reply': (
                "This system supports multiple payment methods:\n"
                "• Cash — marked as Paid immediately\n"
                "• Bank Transfer — marked as Paid immediately\n"
                "• Khalti — digital wallet (Nepal)\n"
                "• eSewa — digital wallet (Nepal)\n"
                "• Credit — for deferred payments\n\n"
                "For Khalti/eSewa, a payment simulation mode is available for testing. "
                "After creating a transaction, open it and click 'Process Payment'."
            ),
            'links': [{'label': 'View Transactions', 'url': '/inventory/transactions/'}]
        }

    # ── SKU ───────────────────────────────────────────────────────
    if any(k in msg for k in ['sku', 'stock keeping unit', 'what is sku', 'item code']):
        return {
            'reply': (
                "SKU stands for Stock Keeping Unit — a unique code for each item.\n\n"
                "• SKUs are auto-generated when you add a new item\n"
                "• You can also set a custom SKU manually\n"
                "• SKUs are visible in the Admin panel and item list\n"
                "• They help identify items quickly without using the full name"
            ),
            'links': [{'label': 'View Inventory', 'url': '/inventory/'}]
        }

    # ── Reorder level ─────────────────────────────────────────────
    if any(k in msg for k in ['reorder level', 'what is reorder', 'reorder threshold', 'minimum stock', 'reorder point']):
        return {
            'reply': (
                "The Reorder Level is the minimum stock quantity before the system alerts you to restock.\n\n"
                "Example: If an item has reorder level = 10 and current stock drops to 8, "
                "it will appear as 'Low Stock'.\n\n"
                "You can set the reorder level when adding or editing an item. "
                "The AI Reorder system also uses this to suggest restocking quantities."
            ),
            'links': [{'label': 'View Reorder Suggestions', 'url': '/inventory/reorder-suggestions/'}]
        }

    # ── AI reorder / AI system ────────────────────────────────────
    if any(k in msg for k in ['ai reorder', 'ai system', 'how does ai work', 'machine learning', 'demand forecast', 'ai prediction', 'ai model']):
        return {
            'reply': (
                "The AI Reorder system uses machine learning to predict future demand:\n\n"
                "• It analyses past sales transactions for each item\n"
                "• Predicts how much stock you'll need in the coming days\n"
                "• Flags items as Critical, High, Medium, or Low priority\n"
                "• Suggests a reorder quantity based on predicted demand\n\n"
                "To train AI models, go to AI Models page. Items need at least 7 sales records to train."
            ),
            'links': [
                {'label': 'AI Reorder Suggestions', 'url': '/inventory/reorder-suggestions/'},
                {'label': 'AI Model Management', 'url': '/inventory/ai/models/'}
            ]
        }

    # ── Export data ───────────────────────────────────────────────
    if any(k in msg for k in ['export', 'download', 'csv', 'export data', 'download report', 'export inventory']):
        return {
            'reply': (
                "You can export data as CSV files:\n\n"
                "• Inventory Export — includes all items with AI insights\n"
                "  Go to Inventory → 'Export CSV'\n\n"
                "• Transaction Export — includes all transactions with payment details\n"
                "  Go to Transactions → 'Export CSV'"
            ),
            'links': [
                {'label': 'Export Inventory', 'url': '/inventory/export/csv/'},
                {'label': 'Export Transactions', 'url': '/inventory/transactions/export/csv/'}
            ]
        }

    # ── User roles / permissions ──────────────────────────────────
    if any(k in msg for k in ['user role', 'roles', 'permissions', 'access level', 'who can', 'staff access', 'manager access', 'admin access']):
        return {
            'reply': (
                "The system has 3 user roles:\n\n"
                "👑 Admin\n"
                "• Full access to everything\n"
                "• Can approve/reject users and assign roles\n"
                "• Can delete items and transactions\n\n"
                "🔧 Manager\n"
                "• Can add, edit items and create transactions\n"
                "• Can view analytics and reports\n"
                "• Cannot delete or manage users\n\n"
                "👁 Staff\n"
                "• Read-only access\n"
                "• Can view inventory and transactions\n"
                "• Cannot make changes"
            )
        }

    # ── How to manage users ───────────────────────────────────────
    if any(k in msg for k in ['manage users', 'approve user', 'user management', 'add user', 'new user', 'register user', 'pending users']):
        return {
            'reply': (
                "User management (Admin only):\n\n"
                "• New users register at /users/register/\n"
                "• Their account starts as 'Pending'\n"
                "• An Admin must approve them and assign a role (Manager or Staff)\n"
                "• Go to Users → 'Manage Users' to see pending approvals\n\n"
                "Only Admins can approve, reject, or change user roles."
            ),
            'links': [{'label': 'Manage Users', 'url': '/users/manage/'}]
        }

    # ── Profit / cost price ───────────────────────────────────────
    if any(k in msg for k in ['profit', 'cost price', 'how is profit', 'profit calculation', 'margin']):
        return {
            'reply': (
                "Profit is calculated as:\n"
                "Profit = (Selling Price − Cost Price) × Quantity\n\n"
                "• Cost price is automatically updated when you record a Purchase transaction\n"
                "• Profit is shown per transaction in the Transactions list\n"
                "• Monthly profit is shown in the Monthly Report\n\n"
                "Make sure to record purchase transactions first so cost prices are accurate."
            ),
            'links': [{'label': 'View Transactions', 'url': '/inventory/transactions/'}]
        }

    # ── Supplier / Customer ───────────────────────────────────────
    if any(k in msg for k in ['supplier', 'customer', 'vendor', 'buyer', 'who is supplier', 'who is customer']):
        return {
            'reply': (
                "Suppliers and Customers can be linked to transactions:\n\n"
                "• Supplier — linked to Purchase transactions (who you buy from)\n"
                "• Customer — linked to Sale transactions (who you sell to)\n\n"
                "When creating a transaction, select the relevant supplier or customer from the dropdown. "
                "They can be managed from the Admin panel."
            ),
            'links': [{'label': 'New Transaction', 'url': '/inventory/transactions/create/'}]
        }

    # ── How to add item (navigation shortcut) ────────────────────
    if any(k in msg for k in ['where to add', 'where is add', 'find add item', 'navigate to add']):
        return {
            'reply': "Go to the top navigation bar → click 'Inventory' → then click the 'Add Item' button on the top right of the inventory page.",
            'links': [{'label': 'Add Item', 'url': '/inventory/add/'}]
        }

    # ── Dashboard ─────────────────────────────────────────────────
    if any(k in msg for k in ['dashboard', 'home page', 'main page', 'overview', 'go to dashboard']):
        return {
            'reply': (
                "The Dashboard gives you a quick overview:\n"
                "• Total items, low stock count, out of stock count\n"
                "• Total inventory value\n"
                "• 7-day sales trend mini chart\n"
                "• AI stock alerts (critical, high priority)\n"
                "• Recent items list\n"
                "• Quick action buttons"
            ),
            'links': [{'label': 'Go to Dashboard', 'url': '/users/dashboard/'}]
        }

    # ── Fallback ──────────────────────────────────────────────────
    return {
        'reply': (
            "I couldn't understand that. Here are some things you can ask:\n"
            "• 'Show low stock items'\n"
            "• 'How to add an item?'\n"
            "• 'How do payments work?'\n"
            "• 'What is reorder level?'\n"
            "• 'How does AI reorder work?'\n\n"
            "Type 'help' to see the full list."
        )
    }
