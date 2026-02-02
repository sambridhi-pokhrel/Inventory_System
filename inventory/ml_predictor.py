"""
AI-Based Inventory Demand Forecasting Module
============================================

This module implements machine learning-based demand forecasting for inventory management.
Uses scikit-learn to train models on historical sales data and predict future demand.

Academic FYP Implementation - Real AI, not hard-coded rules.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from django.utils import timezone
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

from .models import Item, Transaction


class InventoryDemandPredictor:
    """
    AI-powered inventory demand forecasting using machine learning.
    
    This class implements real machine learning algorithms to predict
    future inventory demand based on historical sales patterns.
    """
    
    def __init__(self):
        self.models = {}  # Store trained models per item
        self.scalers = {}  # Store feature scalers per item
        self.predictions_cache = {}  # Cache predictions temporarily
        self.model_metrics = {}  # Store model performance metrics
    
    def prepare_training_data(self, item, days_history=90):
        """
        Prepare training data for ML model from historical sales transactions.
        
        Args:
            item: Item instance to prepare data for
            days_history: Number of days of historical data to use
            
        Returns:
            tuple: (X_features, y_target) for ML training
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_history)
        
        # Get historical sales transactions
        sales = Transaction.objects.filter(
            item=item,
            transaction_type='SALE',
            payment_status='PAID',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
        
        if sales.count() < 7:  # Need minimum data for ML
            return None, None
        
        # Create daily aggregated data
        daily_data = []
        current_date = start_date.date()
        
        while current_date <= end_date.date():
            # Get sales for this specific day
            day_sales = sales.filter(
                timestamp__date=current_date
            )
            
            daily_quantity = sum(sale.quantity for sale in day_sales)
            
            # Create features for ML model
            features = {
                'day_of_week': current_date.weekday(),  # 0=Monday, 6=Sunday
                'day_of_month': current_date.day,
                'month': current_date.month,
                'days_since_start': (current_date - start_date.date()).days,
                'is_weekend': 1 if current_date.weekday() >= 5 else 0,
                'is_month_start': 1 if current_date.day <= 7 else 0,
                'is_month_end': 1 if current_date.day >= 24 else 0,
                'quantity_sold': daily_quantity
            }
            
            daily_data.append(features)
            current_date += timedelta(days=1)
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(daily_data)
        
        if len(df) < 14:  # Need minimum samples for training
            return None, None
        
        # Prepare features (X) and target (y)
        feature_columns = [
            'day_of_week', 'day_of_month', 'month', 'days_since_start',
            'is_weekend', 'is_month_start', 'is_month_end'
        ]
        
        X = df[feature_columns].values
        y = df['quantity_sold'].values
        
        return X, y
    
    def train_demand_model(self, item):
        """
        Train machine learning model for demand prediction.
        
        Args:
            item: Item instance to train model for
            
        Returns:
            dict: Training results and model metrics
        """
        print(f"Training AI model for item: {item.name}")
        
        # Prepare training data
        X, y = self.prepare_training_data(item)
        
        if X is None or len(X) < 10:
            return {
                'success': False,
                'error': 'Insufficient historical data for ML training',
                'min_required': 10,
                'available': len(X) if X is not None else 0
            }
        
        try:
            # Split data for training and validation
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Feature scaling for better ML performance
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train Linear Regression model
            model = LinearRegression()
            model.fit(X_train_scaled, y_train)
            
            # Make predictions on test set
            y_pred = model.predict(X_test_scaled)
            
            # Calculate model performance metrics
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            
            # Calculate accuracy (for business understanding)
            accuracy = max(0, 100 - (mae / (np.mean(y_test) + 0.001)) * 100)
            
            # Store trained model and scaler
            self.models[item.id] = model
            self.scalers[item.id] = scaler
            
            # Store model metrics
            self.model_metrics[item.id] = {
                'mae': mae,
                'mse': mse,
                'rmse': rmse,
                'accuracy': accuracy,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'feature_importance': model.coef_.tolist(),
                'trained_at': timezone.now()
            }
            
            return {
                'success': True,
                'metrics': self.model_metrics[item.id],
                'model_type': 'Linear Regression',
                'features_used': [
                    'day_of_week', 'day_of_month', 'month', 'days_since_start',
                    'is_weekend', 'is_month_start', 'is_month_end'
                ]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'ML training failed: {str(e)}'
            }
    
    def predict_future_demand(self, item, forecast_days=7):
        """
        Predict future demand using trained ML model.
        
        Args:
            item: Item instance to predict for
            forecast_days: Number of days to forecast
            
        Returns:
            dict: Prediction results with confidence metrics
        """
        if item.id not in self.models:
            # Train model if not exists
            training_result = self.train_demand_model(item)
            if not training_result['success']:
                return {
                    'success': False,
                    'error': training_result['error'],
                    'fallback_used': True
                }
        
        try:
            model = self.models[item.id]
            scaler = self.scalers[item.id]
            
            # Prepare future dates for prediction
            start_date = timezone.now().date() + timedelta(days=1)
            predictions = []
            
            for i in range(forecast_days):
                future_date = start_date + timedelta(days=i)
                
                # Create features for future date
                features = np.array([[
                    future_date.weekday(),  # day_of_week
                    future_date.day,        # day_of_month
                    future_date.month,      # month
                    i + 1,                  # days_since_start (relative)
                    1 if future_date.weekday() >= 5 else 0,  # is_weekend
                    1 if future_date.day <= 7 else 0,        # is_month_start
                    1 if future_date.day >= 24 else 0        # is_month_end
                ]])
                
                # Scale features and predict
                features_scaled = scaler.transform(features)
                predicted_demand = model.predict(features_scaled)[0]
                
                # Ensure non-negative prediction
                predicted_demand = max(0, predicted_demand)
                
                predictions.append({
                    'date': future_date,
                    'predicted_demand': round(predicted_demand, 2),
                    'day_of_week': future_date.strftime('%A'),
                    'is_weekend': future_date.weekday() >= 5
                })
            
            # Calculate summary statistics
            total_predicted_demand = sum(p['predicted_demand'] for p in predictions)
            avg_daily_demand = total_predicted_demand / forecast_days
            
            # Cache predictions
            self.predictions_cache[item.id] = {
                'predictions': predictions,
                'total_demand': total_predicted_demand,
                'avg_daily_demand': avg_daily_demand,
                'forecast_days': forecast_days,
                'predicted_at': timezone.now(),
                'model_accuracy': self.model_metrics[item.id]['accuracy']
            }
            
            return {
                'success': True,
                'predictions': predictions,
                'summary': {
                    'total_predicted_demand': total_predicted_demand,
                    'avg_daily_demand': avg_daily_demand,
                    'forecast_period': f'{forecast_days} days',
                    'model_accuracy': f"{self.model_metrics[item.id]['accuracy']:.1f}%"
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Prediction failed: {str(e)}'
            }
    
    def calculate_reorder_recommendation(self, item):
        """
        Calculate AI-based reorder recommendation.
        
        Args:
            item: Item instance to analyze
            
        Returns:
            dict: Reorder recommendation with AI insights
        """
        # Get AI prediction for lead time period
        forecast_result = self.predict_future_demand(item, item.lead_time_days)
        
        if not forecast_result['success']:
            # Fallback to basic calculation if AI fails
            return {
                'needs_reorder': item.quantity <= item.reorder_level or item.quantity == 0,
                'ai_powered': False,
                'urgency': 'CRITICAL' if item.quantity == 0 else 'HIGH' if item.quantity <= item.reorder_level else 'LOW',
                'current_stock': item.quantity,
                'predicted_demand': 0,
                'stock_needed': 0,
                'shortage_risk': 0,
                'days_until_stockout': float('inf'),
                'suggested_quantity': max(0, item.reorder_level - item.quantity + 10) if item.quantity <= item.reorder_level else 0,
                'model_accuracy': 'N/A',
                'reason': 'AI prediction failed, using fallback logic',
                'error': forecast_result.get('error', 'Unknown error'),
                'ai_insights': {
                    'avg_daily_demand': 0,
                    'forecast_period': f"{item.lead_time_days} days",
                    'safety_buffer': 0,
                    'confidence': 'Low'
                }
            }
        
        # AI-based analysis
        predicted_demand = forecast_result['summary']['total_predicted_demand']
        current_stock = item.quantity
        safety_buffer = predicted_demand * 0.2  # 20% safety buffer
        
        # Calculate reorder metrics
        stock_needed = predicted_demand + safety_buffer
        shortage_risk = max(0, stock_needed - current_stock)
        days_until_stockout = current_stock / forecast_result['summary']['avg_daily_demand'] if forecast_result['summary']['avg_daily_demand'] > 0 else float('inf')
        
        # AI decision logic
        needs_reorder = (
            current_stock < stock_needed or  # Predicted shortage
            days_until_stockout < item.lead_time_days or  # Will run out before restock
            current_stock == 0  # Already out of stock
        )
        
        # Determine urgency level
        if current_stock == 0:
            urgency = 'CRITICAL'
        elif days_until_stockout < item.lead_time_days:
            urgency = 'HIGH'
        elif shortage_risk > 0:
            urgency = 'MEDIUM'
        else:
            urgency = 'LOW'
        
        # Calculate suggested order quantity
        if needs_reorder:
            # Order enough for lead time + buffer + some extra for next cycle
            suggested_quantity = int(shortage_risk + (predicted_demand * 0.5))
        else:
            suggested_quantity = 0
        
        return {
            'needs_reorder': needs_reorder,
            'ai_powered': True,
            'urgency': urgency,
            'current_stock': current_stock,
            'predicted_demand': round(predicted_demand, 2),
            'stock_needed': round(stock_needed, 2),
            'shortage_risk': round(shortage_risk, 2),
            'days_until_stockout': round(days_until_stockout, 1),
            'suggested_quantity': suggested_quantity,
            'model_accuracy': forecast_result['summary']['model_accuracy'],
            'ai_insights': {
                'avg_daily_demand': round(forecast_result['summary']['avg_daily_demand'], 2),
                'forecast_period': f"{item.lead_time_days} days",
                'safety_buffer': round(safety_buffer, 2),
                'confidence': 'High' if self.model_metrics.get(item.id, {}).get('accuracy', 0) > 70 else 'Medium'
            }
        }
    
    def get_model_info(self, item):
        """Get information about the trained model for an item."""
        if item.id not in self.models:
            return None
        
        return {
            'model_type': 'Linear Regression (scikit-learn)',
            'metrics': self.model_metrics.get(item.id, {}),
            'last_trained': self.model_metrics.get(item.id, {}).get('trained_at'),
            'features_used': [
                'Day of Week', 'Day of Month', 'Month', 'Time Trend',
                'Weekend Flag', 'Month Start Flag', 'Month End Flag'
            ]
        }


# Global predictor instance
ml_predictor = InventoryDemandPredictor()


def train_all_models():
    """
    Train ML models for all items with sufficient data.
    Useful for batch training or system initialization.
    """
    results = {}
    items = Item.objects.all()
    
    print(f"Training AI models for {items.count()} items...")
    
    for item in items:
        result = ml_predictor.train_demand_model(item)
        results[item.name] = result
        
        if result['success']:
            print(f"✓ {item.name}: Accuracy {result['metrics']['accuracy']:.1f}%")
        else:
            print(f"✗ {item.name}: {result['error']}")
    
    return results


def get_ai_reorder_suggestions():
    """
    Get AI-powered reorder suggestions for all items.
    
    Returns:
        list: List of items with AI-based reorder recommendations
    """
    suggestions = []
    items = Item.objects.all()
    
    for item in items:
        recommendation = ml_predictor.calculate_reorder_recommendation(item)
        
        if recommendation['needs_reorder']:
            suggestions.append({
                'item': item,
                'recommendation': recommendation
            })
    
    # Sort by urgency and shortage risk
    urgency_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    suggestions.sort(key=lambda x: (
        urgency_order.get(x['recommendation'].get('urgency', 'LOW'), 4),
        -x['recommendation'].get('shortage_risk', 0)
    ))
    
    return suggestions