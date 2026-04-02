"""
AI-Based Inventory Demand Forecasting Module
============================================

Implements Linear Regression-based demand forecasting for inventory management.
Uses scikit-learn to train models on historical sales data and predict future demand.

Key improvements over v1:
- Graceful fallback when data is sparse (new items / test data)
- Rolling average features for better trend detection
- Fixed days_since_start bug in future predictions
- Smarter minimum data handling
- Cleaner reorder recommendation logic
- Suggested quantity capped to prevent inflated test-data numbers
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from django.utils import timezone
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

import logging
logger = logging.getLogger(__name__)

from .models import Item, Transaction


class InventoryDemandPredictor:
    """
    AI-powered inventory demand forecasting using Linear Regression.

    Trains one model per item using historical daily sales data.
    Falls back to a simple moving average when data is insufficient.
    """

    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.model_metrics = {}

    def _get_daily_sales_df(self, item, days_history=90):
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_history)

        sales = Transaction.objects.filter(
            item=item,
            transaction_type='SALE',
            payment_status='PAID',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')

        date_range = pd.date_range(
            start=start_date.date(),
            end=end_date.date(),
            freq='D'
        )

        sales_by_day = {}
        for sale in sales:
            day = sale.timestamp.date()
            sales_by_day[day] = sales_by_day.get(day, 0) + sale.quantity

        rows = []
        for i, dt in enumerate(date_range):
            d = dt.date()
            rows.append({
                'date': d,
                'quantity_sold': sales_by_day.get(d, 0),
                'day_of_week': d.weekday(),
                'day_of_month': d.day,
                'month': d.month,
                'is_weekend': int(d.weekday() >= 5),
                'is_month_start': int(d.day <= 7),
                'is_month_end': int(d.day >= 24),
                'days_since_start': i,
            })

        if not rows:
            return None

        df = pd.DataFrame(rows)
        df['rolling_avg_7'] = df['quantity_sold'].rolling(window=7, min_periods=1).mean()
        df['rolling_avg_14'] = df['quantity_sold'].rolling(window=14, min_periods=1).mean()

        return df

    def _feature_columns(self):
        return [
            'day_of_week', 'day_of_month', 'month', 'days_since_start',
            'is_weekend', 'is_month_start', 'is_month_end',
            'rolling_avg_7', 'rolling_avg_14',
        ]

    def _simple_moving_average(self, item, days=14):
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        sales = Transaction.objects.filter(
            item=item,
            transaction_type='SALE',
            payment_status='PAID',
            timestamp__gte=start_date,
        )
        total = sum(s.quantity for s in sales)
        return total / days if days > 0 else 0

    def train_demand_model(self, item, days_history=90):
        df = self._get_daily_sales_df(item, days_history)

        if df is None or len(df) < 14:
            return {
                'success': False,
                'error': 'Insufficient historical data (need at least 14 days)',
                'available': len(df) if df is not None else 0,
            }

        non_zero_days = (df['quantity_sold'] > 0).sum()
        if non_zero_days < 3:
            return {
                'success': False,
                'error': 'Not enough actual sales transactions to train model',
                'non_zero_days': int(non_zero_days),
            }

        try:
            feature_cols = self._feature_columns()
            X = df[feature_cols].values
            y = df['quantity_sold'].values

            split_idx = max(1, int(len(X) * 0.8))
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]

            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            model = LinearRegression()
            model.fit(X_train_scaled, y_train)

            if len(X_test) > 0:
                y_pred = model.predict(X_test_scaled)
                mae = float(mean_absolute_error(y_test, y_pred))
                rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
                mean_actual = float(np.mean(y_test)) + 1e-9
                accuracy = float(max(0, 100 - (mae / mean_actual) * 100))
            else:
                mae = rmse = 0.0
                accuracy = 50.0

            self.models[item.id] = model
            self.scalers[item.id] = scaler
            self.model_metrics[item.id] = {
                'mae': mae,
                'rmse': rmse,
                'accuracy': accuracy,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'trained_at': timezone.now(),
                'feature_coefficients': dict(zip(feature_cols, model.coef_.tolist())),
            }

            return {
                'success': True,
                'model_type': 'Linear Regression',
                'features_used': feature_cols,
                'metrics': self.model_metrics[item.id],
            }

        except Exception as e:
            logger.error(f"ML training failed for {item.name}: {e}")
            return {'success': False, 'error': str(e)}

    def predict_future_demand(self, item, forecast_days=7):
        if item.id not in self.models:
            train_result = self.train_demand_model(item)
        else:
            train_result = {'success': True}

        today = timezone.now().date()

        if train_result.get('success'):
            try:
                model = self.models[item.id]
                scaler = self.scalers[item.id]

                df_history = self._get_daily_sales_df(item, days_history=90)
                last_rolling_7 = float(df_history['rolling_avg_7'].iloc[-1]) if df_history is not None else 0.0
                last_rolling_14 = float(df_history['rolling_avg_14'].iloc[-1]) if df_history is not None else 0.0
                history_len = len(df_history) if df_history is not None else 90

                predictions = []
                for i in range(forecast_days):
                    future_date = today + timedelta(days=i + 1)
                    features = np.array([[
                        future_date.weekday(),
                        future_date.day,
                        future_date.month,
                        history_len + i,
                        int(future_date.weekday() >= 5),
                        int(future_date.day <= 7),
                        int(future_date.day >= 24),
                        last_rolling_7,
                        last_rolling_14,
                    ]])
                    features_scaled = scaler.transform(features)
                    predicted = max(0.0, float(model.predict(features_scaled)[0]))
                    predictions.append({
                        'date': future_date,
                        'predicted_demand': round(predicted, 2),
                        'day_of_week': future_date.strftime('%A'),
                        'is_weekend': future_date.weekday() >= 5,
                    })

                total = sum(p['predicted_demand'] for p in predictions)
                avg_daily = total / forecast_days
                accuracy = self.model_metrics.get(item.id, {}).get('accuracy', 50.0)

                return {
                    'success': True,
                    'method': 'ml',
                    'predictions': predictions,
                    'summary': {
                        'total_predicted_demand': round(total, 2),
                        'avg_daily_demand': round(avg_daily, 2),
                        'forecast_period': f'{forecast_days} days',
                        'model_accuracy': f'{accuracy:.1f}%',
                    },
                }

            except Exception as e:
                logger.warning(f"ML prediction failed for {item.name}, falling back: {e}")

        # Fallback: simple moving average
        avg_daily = self._simple_moving_average(item, days=14)
        predictions = []
        for i in range(forecast_days):
            future_date = today + timedelta(days=i + 1)
            predictions.append({
                'date': future_date,
                'predicted_demand': round(avg_daily, 2),
                'day_of_week': future_date.strftime('%A'),
                'is_weekend': future_date.weekday() >= 5,
            })

        total = avg_daily * forecast_days
        return {
            'success': True,
            'method': 'moving_average',
            'predictions': predictions,
            'summary': {
                'total_predicted_demand': round(total, 2),
                'avg_daily_demand': round(avg_daily, 2),
                'forecast_period': f'{forecast_days} days',
                'model_accuracy': 'N/A (moving average)',
            },
        }

    def calculate_reorder_recommendation(self, item):
        forecast = self.predict_future_demand(item, item.lead_time_days)

        current_stock = item.quantity
        ai_powered = forecast.get('method') == 'ml'

        predicted_demand = forecast['summary']['total_predicted_demand']
        avg_daily = forecast['summary']['avg_daily_demand']

        # 20% safety buffer
        safety_buffer = predicted_demand * 0.2
        stock_needed = predicted_demand + safety_buffer
        shortage_risk = max(0.0, stock_needed - current_stock)

        # Days until stockout
        if avg_daily > 0:
            days_until_stockout = round(current_stock / avg_daily, 1)
        else:
            days_until_stockout = float('inf')

        # Reorder decision
        needs_reorder = (
            current_stock == 0
            or days_until_stockout < item.lead_time_days
            or current_stock < stock_needed
        )

        # Urgency
        if current_stock == 0:
            urgency = 'CRITICAL'
        elif days_until_stockout < item.lead_time_days:
            urgency = 'HIGH'
        elif shortage_risk > 0:
            urgency = 'MEDIUM'
        else:
            urgency = 'LOW'

        # Suggested order quantity — capped to prevent inflated test-data numbers
        if needs_reorder:
            raw_qty = max(0, int(shortage_risk + predicted_demand * 0.5))
            cap = max(item.reorder_level * 3, 50)  # max 3× reorder level, min 50
            suggested_quantity = min(raw_qty, cap)
        else:
            suggested_quantity = 0

        accuracy = self.model_metrics.get(item.id, {}).get('accuracy', 0)
        confidence = 'High' if accuracy > 70 else 'Medium' if accuracy > 40 else 'Low'

        return {
            'needs_reorder': needs_reorder,
            'ai_powered': ai_powered,
            'method': forecast.get('method', 'moving_average'),
            'urgency': urgency,
            'current_stock': current_stock,
            'predicted_demand': round(predicted_demand, 2),
            'stock_needed': round(stock_needed, 2),
            'shortage_risk': round(shortage_risk, 2),
            'days_until_stockout': days_until_stockout,
            'suggested_quantity': suggested_quantity,
            'model_accuracy': forecast['summary']['model_accuracy'],
            'ai_insights': {
                'avg_daily_demand': round(avg_daily, 2),
                'forecast_period': f'{item.lead_time_days} days',
                'safety_buffer': round(safety_buffer, 2),
                'confidence': confidence,
            },
        }

    def get_model_info(self, item):
        if item.id not in self.models:
            return None
        metrics = self.model_metrics.get(item.id, {})
        return {
            'model_type': 'Linear Regression (scikit-learn)',
            'features_used': self._feature_columns(),
            'metrics': metrics,
            'last_trained': metrics.get('trained_at'),
        }


# Module-level singleton
ml_predictor = InventoryDemandPredictor()


def train_all_models():
    """Batch-train models for every item. Useful for testing."""
    results = {}
    for item in Item.objects.all():
        result = ml_predictor.train_demand_model(item)
        results[item.name] = result
        status = '✓' if result['success'] else '✗'
        detail = (
            f"accuracy {result['metrics']['accuracy']:.1f}%"
            if result['success']
            else result['error']
        )
        print(f"{status} {item.name}: {detail}")
    return results


def get_ai_reorder_suggestions():
    """
    Return a sorted list of items that need reordering, with AI recommendations.
    CRITICAL → HIGH → MEDIUM → LOW, then by shortage risk descending.
    """
    urgency_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    suggestions = []

    for item in Item.objects.all():
        rec = ml_predictor.calculate_reorder_recommendation(item)
        if rec['needs_reorder']:
            suggestions.append({'item': item, 'recommendation': rec})

    suggestions.sort(key=lambda x: (
        urgency_order.get(x['recommendation']['urgency'], 4),
        -x['recommendation']['shortage_risk'],
    ))

    return suggestions