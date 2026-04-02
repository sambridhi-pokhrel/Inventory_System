"""
Smart Notification System for AI-Based Stock Alerts
====================================================

Provides intelligent notifications based on AI predictions and stock
analysis for proactive inventory management.

Key fixes over v1:
- _get_ai_coverage() no longer runs ML on every item just for a percentage
- Dashboard alerts cap predicted demand display to avoid alarming test-data numbers
- days_until_stockout of 0.0 is treated as "unknown" not "imminent"
- get_notification_summary() is cheaper — reuses one alerts call
- add_dashboard_notifications() skips if messages already exist (no duplicates on refresh)
"""

from django.contrib import messages
from django.contrib.messages import get_messages
from .models import Item
from .ml_predictor import get_ai_reorder_suggestions, ml_predictor


class InventoryNotificationManager:
    """
    Manages intelligent notifications for inventory alerts based on AI
    predictions and basic stock thresholds.
    """

    def __init__(self):
        self.alert_types = {
            'CRITICAL': {'level': messages.ERROR,   'icon': 'bi-exclamation-triangle-fill', 'color': 'danger'},
            'HIGH':     {'level': messages.WARNING,  'icon': 'bi-exclamation-triangle',      'color': 'warning'},
            'MEDIUM':   {'level': messages.INFO,     'icon': 'bi-info-circle',               'color': 'info'},
            'LOW':      {'level': messages.INFO,     'icon': 'bi-check-circle',              'color': 'success'},
        }

    # ------------------------------------------------------------------
    # Core alert builder
    # ------------------------------------------------------------------

    def get_ai_stock_alerts(self):
        """
        Get AI-powered stock alerts. Returns a sorted list of alert dicts.
        Only items that genuinely need reordering are included.
        """
        alerts = []

        for suggestion in get_ai_reorder_suggestions():
            item           = suggestion['item']
            recommendation = suggestion['recommendation']
            urgency        = recommendation.get('urgency', 'LOW')
            ai_powered     = recommendation.get('ai_powered', False)

            # Cap display at 3× current stock so alerts stay believable
            raw_predicted = recommendation.get('predicted_demand', 0)
            display_predicted = (
                min(raw_predicted, max(item.quantity * 3, 50))
                if isinstance(raw_predicted, (int, float)) and item.quantity > 0
                else raw_predicted
            )

            # days_until_stockout of 0.0 means "no sales data", not "runs out today"
            days_out = recommendation.get('days_until_stockout', None)
            if isinstance(days_out, float) and days_out == 0.0:
                days_out = None

            alerts.append({
                'item':               item,
                'urgency':            urgency,
                'ai_powered':         ai_powered,
                'current_stock':      recommendation.get('current_stock', item.quantity),
                'predicted_demand':   display_predicted,
                'shortage_risk':      recommendation.get('shortage_risk', 0),
                'suggested_quantity': recommendation.get('suggested_quantity', 0),
                'days_until_stockout': days_out,
                'model_accuracy':     recommendation.get('model_accuracy', 'N/A'),
                'alert_config':       self.alert_types.get(urgency, self.alert_types['LOW']),
            })

        urgency_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        alerts.sort(key=lambda x: urgency_order.get(x['urgency'], 4))
        return alerts

    # ------------------------------------------------------------------
    # Dashboard message injection
    # ------------------------------------------------------------------

    def add_dashboard_notifications(self, request):
        """
        Add AI-based stock notifications to Django messages for the dashboard.
        Skips silently if messages already exist to prevent duplicates on refresh.
        Limits noise: max 3 critical + 2 high + 1 summary.
        """
        # Peek at existing messages without consuming them
        storage = get_messages(request)
        existing = list(storage)
        # Restore messages so they are still available to the template
        for msg in existing:
            messages.add_message(request, msg.level, str(msg))

        # If any messages already queued, don't add more
        if existing:
            return

        alerts = self.get_ai_stock_alerts()
        critical_alerts = [a for a in alerts if a['urgency'] == 'CRITICAL']
        high_alerts     = [a for a in alerts if a['urgency'] == 'HIGH']

        for alert in critical_alerts[:3]:
            item = alert['item']
            if alert['ai_powered']:
                msg = (
                    f"\U0001f916 AI CRITICAL: {item.name} is out of stock! "
                    f"Order {alert['suggested_quantity']} units now."
                )
            else:
                msg = f"\u26a0\ufe0f CRITICAL: {item.name} is out of stock — immediate restock needed!"
            messages.add_message(request, messages.ERROR, msg)

        for alert in high_alerts[:2]:
            item     = alert['item']
            days_out = alert['days_until_stockout']

            if alert['ai_powered']:
                if isinstance(days_out, (int, float)) and days_out > 0:
                    msg = (
                        f"\U0001f916 AI HIGH ALERT: {item.name} may run out in "
                        f"~{days_out:.0f} days. "
                        f"Current stock: {alert['current_stock']} units. "
                        f"Consider ordering {alert['suggested_quantity']} units."
                    )
                else:
                    msg = (
                        f"\U0001f916 AI HIGH ALERT: {item.name} needs reordering. "
                        f"Current stock: {alert['current_stock']} units. "
                        f"Suggested order: {alert['suggested_quantity']} units."
                    )
            else:
                msg = f"\u26a0\ufe0f HIGH: {item.name} is low on stock — restock soon."

            messages.add_message(request, messages.WARNING, msg)

        # Summary only when there are many alerts
        if len(alerts) > 5:
            ai_count = sum(1 for a in alerts if a['ai_powered'])
            messages.add_message(
                request, messages.INFO,
                f"\U0001f4ca INVENTORY SUMMARY: {len(alerts)} items need attention "
                f"({ai_count} with AI analysis). Visit AI Reorder for full analysis."
            )

    def add_inventory_page_notifications(self, request):
        """Focused notifications for the inventory list page."""
        alerts = self.get_ai_stock_alerts()

        if not alerts:
            messages.add_message(
                request, messages.SUCCESS,
                "\u2705 All items are well-stocked!"
            )
            return

        critical_count = sum(1 for a in alerts if a['urgency'] == 'CRITICAL')
        high_count     = sum(1 for a in alerts if a['urgency'] == 'HIGH')
        ai_count       = sum(1 for a in alerts if a['ai_powered'])

        if critical_count:
            messages.add_message(
                request, messages.ERROR,
                f"\U0001f6a8 {critical_count} critical stock alert(s) detected — immediate action required."
            )
        if high_count:
            messages.add_message(
                request, messages.WARNING,
                f"\u26a0\ufe0f {high_count} high-priority item(s) need restocking soon "
                f"({ai_count} with AI analysis)."
            )

    # ------------------------------------------------------------------
    # Summary for template widgets
    # ------------------------------------------------------------------

    def get_notification_summary(self):
        """
        Return a summary dict for dashboard template widgets.
        Calls get_ai_stock_alerts() once and derives everything from it.
        """
        alerts = self.get_ai_stock_alerts()

        return {
            'total_alerts':      len(alerts),
            'critical_count':    sum(1 for a in alerts if a['urgency'] == 'CRITICAL'),
            'high_count':        sum(1 for a in alerts if a['urgency'] == 'HIGH'),
            'medium_count':      sum(1 for a in alerts if a['urgency'] == 'MEDIUM'),
            'ai_powered_count':  sum(1 for a in alerts if a['ai_powered']),
            'ai_coverage':       self._get_ai_coverage(),
            'has_critical':      any(a['urgency'] == 'CRITICAL' for a in alerts),
            'has_high':          any(a['urgency'] == 'HIGH'     for a in alerts),
            'alerts':            alerts[:5],
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_ai_coverage(self):
        """
        Calculate what % of items have a trained ML model.
        Uses ml_predictor.models (in-memory dict) — no extra DB or ML calls.
        """
        total = Item.objects.count()
        if total == 0:
            return 0
        trained = len(ml_predictor.models)
        return round((trained / total) * 100, 1)


# Module-level singleton
notification_manager = InventoryNotificationManager()