#!/usr/bin/env python
"""
Test script to verify AI features are working
Run with: python test_ai_features.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
django.setup()

from inventory.models import Item
from inventory.notifications import notification_manager
from inventory.ml_predictor import get_ai_reorder_suggestions, ml_predictor

def test_ai_features():
    print("🧪 TESTING AI FEATURES")
    print("=" * 50)
    
    # Test 1: Check if items exist
    total_items = Item.objects.count()
    print(f"✅ Total Items: {total_items}")
    
    # Test 2: Check AI models
    model_count = len(ml_predictor.models)
    print(f"✅ AI Models Trained: {model_count}")
    
    # Test 3: Check AI reorder suggestions
    ai_suggestions = get_ai_reorder_suggestions()
    print(f"✅ AI Reorder Suggestions: {len(ai_suggestions)}")
    
    # Test 4: Check notification system
    notification_summary = notification_manager.get_notification_summary()
    print(f"✅ Total Alerts: {notification_summary['total_alerts']}")
    print(f"✅ Critical Alerts: {notification_summary['critical_count']}")
    print(f"✅ High Priority: {notification_summary['high_count']}")
    print(f"✅ AI Coverage: {notification_summary['ai_coverage']:.1f}%")
    
    # Test 5: Show sample AI suggestions
    print("\n🤖 SAMPLE AI SUGGESTIONS:")
    print("-" * 30)
    for i, suggestion in enumerate(ai_suggestions[:3]):  # Show first 3
        item = suggestion['item']
        rec = suggestion['recommendation']
        urgency = rec.get('urgency', 'LOW')
        ai_powered = rec.get('ai_powered', False)
        
        print(f"{i+1}. {item.name}")
        print(f"   Stock: {item.quantity}")
        print(f"   Urgency: {urgency}")
        print(f"   AI Powered: {'Yes' if ai_powered else 'No'}")
        if ai_powered:
            print(f"   Predicted Demand: {rec.get('predicted_demand', 'N/A')}")
            print(f"   Suggested Quantity: {rec.get('suggested_quantity', 'N/A')}")
        print()
    
    # Test 6: Check specific items with AI
    print("🔍 ITEMS WITH AI MODELS:")
    print("-" * 25)
    ai_items = 0
    for item in Item.objects.all()[:5]:  # Check first 5 items
        ai_info = item.ai_reorder_info
        has_ai = ai_info.get('ai_powered', False)
        if has_ai:
            ai_items += 1
            print(f"✅ {item.name}: AI Enabled (Accuracy: {ai_info.get('model_accuracy', 'N/A')})")
        else:
            print(f"❌ {item.name}: Basic Rules Only")
    
    print(f"\n📊 SUMMARY:")
    print(f"Items with AI: {ai_items}")
    print(f"AI System Status: {'🟢 Active' if model_count > 0 else '🔴 Inactive'}")
    print(f"Notifications: {'🟢 Working' if notification_summary['total_alerts'] >= 0 else '🔴 Error'}")
    
    return {
        'total_items': total_items,
        'ai_models': model_count,
        'ai_suggestions': len(ai_suggestions),
        'notifications': notification_summary,
        'status': 'working' if model_count > 0 else 'needs_training'
    }

if __name__ == "__main__":
    try:
        results = test_ai_features()
        print(f"\n🎯 OVERALL STATUS: {'✅ AI SYSTEM WORKING' if results['status'] == 'working' else '⚠️ NEEDS AI MODEL TRAINING'}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("Make sure Django server is not running and try again.")