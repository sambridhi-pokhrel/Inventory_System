"""
Smart Notification System for AI-Based Stock Alerts
==================================================

This module provides intelligent notifications based on AI predictions
and stock analysis for proactive inventory management.
"""

from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Item
from .ml_predictor import get_ai_reorder_suggestions


class InventoryNotificationManager:
    """
    Manages intelligent notifications for inventory alerts based on AI predictions
    """
    
    def __init__(self):
        self.alert_types = {
            'CRITICAL': {
                'level': messages.ERROR,
                'icon': 'bi-exclamation-triangle-fill',
                'color': 'danger'
            },
            'HIGH': {
                'level': messages.WARNING,
                'icon': 'bi-exclamation-triangle',
                'color': 'warning'
            },
            'MEDIUM': {
                'level': messages.INFO,
                'icon': 'bi-info-circle',
                'color': 'info'
            },
            'LOW': {
                'level': messages.INFO,
                'icon': 'bi-check-circle',
                'color': 'success'
            }
        }
    
    def get_ai_stock_alerts(self):
        """
        Get AI-powered stock alerts with detailed information
        
        Returns:
            list: List of alert dictionaries with AI insights
        """
        alerts = []
        ai_suggestions = get_ai_reorder_suggestions()
        
        for suggestion in ai_suggestions:
            item = suggestion['item']
            recommendation = suggestion['recommendation']
            
            urgency = recommendation.get('urgency', 'LOW')
            ai_powered = recommendation.get('ai_powered', False)
            
            alert = {
                'item': item,
                'urgency': urgency,
                'ai_powered': ai_powered,
                'current_stock': recommendation.get('current_stock', item.quantity),
                'predicted_demand': recommendation.get('predicted_demand', 'N/A'),
                'shortage_risk': recommendation.get('shortage_risk', 0),
                'suggested_quantity': recommendation.get('suggested_quantity', 0),
                'days_until_stockout': recommendation.get('days_until_stockout', 'N/A'),
                'model_accuracy': recommendation.get('model_accuracy', 'N/A'),
                'alert_config': self.alert_types.get(urgency, self.alert_types['LOW'])
            }
            
            alerts.append(alert)
        
        # Sort by urgency (Critical first)
        urgency_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        alerts.sort(key=lambda x: urgency_order.get(x['urgency'], 4))
        
        return alerts
    
    def add_dashboard_notifications(self, request):
        """
        Add AI-based stock notifications to Django messages for dashboard display
        
        Args:
            request: Django request object
        """
        alerts = self.get_ai_stock_alerts()
        
        # Group alerts by urgency
        critical_alerts = [a for a in alerts if a['urgency'] == 'CRITICAL']
        high_alerts = [a for a in alerts if a['urgency'] == 'HIGH']
        
        # Add critical alerts (out of stock)
        for alert in critical_alerts[:3]:  # Limit to top 3 critical
            item = alert['item']
            if alert['ai_powered']:
                message = f"🤖 AI CRITICAL ALERT: {item.name} is out of stock! " \
                         f"Predicted demand: {alert['predicted_demand']} units. " \
                         f"Immediate reorder of {alert['suggested_quantity']} units recommended."
            else:
                message = f"⚠️ CRITICAL: {item.name} is out of stock and needs immediate restocking!"
            
            messages.add_message(request, messages.ERROR, message)
        
        # Add high priority alerts (low stock with AI predictions)
        for alert in high_alerts[:2]:  # Limit to top 2 high priority
            item = alert['item']
            if alert['ai_powered']:
                days_until_stockout = alert['days_until_stockout']
                if isinstance(days_until_stockout, (int, float)) and days_until_stockout != float('inf'):
                    message = f"🤖 AI HIGH ALERT: {item.name} will run out in {days_until_stockout:.1f} days! " \
                             f"Current: {alert['current_stock']} units, " \
                             f"Predicted demand: {alert['predicted_demand']} units. " \
                             f"Order {alert['suggested_quantity']} units now."
                else:
                    message = f"🤖 AI HIGH ALERT: {item.name} needs reordering! " \
                             f"Current: {alert['current_stock']} units, " \
                             f"AI suggests ordering {alert['suggested_quantity']} units."
            else:
                message = f"⚠️ HIGH PRIORITY: {item.name} is low on stock and needs restocking soon."
            
            messages.add_message(request, messages.WARNING, message)
        
        # Add summary notification if there are many alerts
        total_alerts = len(alerts)
        if total_alerts > 5:
            ai_powered_count = sum(1 for a in alerts if a['ai_powered'])
            message = f"📊 INVENTORY SUMMARY: {total_alerts} items need attention " \
                     f"({ai_powered_count} with AI analysis). " \
                     f"Visit AI Reorder page for complete analysis."
            messages.add_message(request, messages.INFO, message)
    
    def add_inventory_page_notifications(self, request):
        """
        Add focused notifications for inventory list page
        
        Args:
            request: Django request object
        """
        alerts = self.get_ai_stock_alerts()
        
        if not alerts:
            # Positive message when no alerts
            ai_coverage = self._get_ai_coverage()
            message = f"✅ All items are well-stocked! AI system monitoring {ai_coverage:.0f}% of inventory."
            messages.add_message(request, messages.SUCCESS, message)
            return
        
        # Critical and high priority summary
        critical_count = sum(1 for a in alerts if a['urgency'] == 'CRITICAL')
        high_count = sum(1 for a in alerts if a['urgency'] == 'HIGH')
        ai_count = sum(1 for a in alerts if a['ai_powered'])
        
        if critical_count > 0:
            message = f"🚨 {critical_count} CRITICAL stock alert{'s' if critical_count > 1 else ''} detected! " \
                     f"Immediate action required."
            messages.add_message(request, messages.ERROR, message)
        
        if high_count > 0:
            message = f"⚠️ {high_count} HIGH priority item{'s' if high_count > 1 else ''} need{'s' if high_count == 1 else ''} restocking soon. " \
                     f"AI analysis available for {ai_count} item{'s' if ai_count != 1 else ''}."
            messages.add_message(request, messages.WARNING, message)
    
    def get_notification_summary(self):
        """
        Get summary of current notifications for display in templates
        
        Returns:
            dict: Summary of notification counts and AI insights
        """
        alerts = self.get_ai_stock_alerts()
        
        summary = {
            'total_alerts': len(alerts),
            'critical_count': sum(1 for a in alerts if a['urgency'] == 'CRITICAL'),
            'high_count': sum(1 for a in alerts if a['urgency'] == 'HIGH'),
            'medium_count': sum(1 for a in alerts if a['urgency'] == 'MEDIUM'),
            'ai_powered_count': sum(1 for a in alerts if a['ai_powered']),
            'ai_coverage': self._get_ai_coverage(),
            'has_critical': any(a['urgency'] == 'CRITICAL' for a in alerts),
            'has_high': any(a['urgency'] == 'HIGH' for a in alerts),
            'alerts': alerts[:5]  # Top 5 alerts for display
        }
        
        return summary
    
    def _get_ai_coverage(self):
        """Calculate AI coverage percentage"""
        total_items = Item.objects.count()
        if total_items == 0:
            return 0
        
        items_with_ai = sum(1 for item in Item.objects.all() 
                           if item.ai_reorder_info.get('ai_powered', False))
        return (items_with_ai / total_items) * 100


# Global notification manager instance
notification_manager = InventoryNotificationManager()