"""
Analytics Module for Inventory Management System
===============================================

This module generates professional Matplotlib-based visualizations for:
1. Sales trend analysis using historical transaction data
2. Actual vs Predicted demand comparison using AI predictions
3. Inventory performance metrics and insights

Academic FYP Implementation - Professional data visualization
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for web
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q
import io
import base64
from decimal import Decimal

from .models import Item, Transaction
from .ml_predictor import ml_predictor


class InventoryAnalytics:
    """
    Professional analytics class for generating business intelligence visualizations
    """
    
    def __init__(self):
        # Set professional styling
        plt.style.use('default')
        self.colors = {
            'primary': '#714b67',      # Main theme color
            'secondary': '#9c7a8a',    # Lighter variant
            'success': '#28a745',      # Green for positive metrics
            'warning': '#ffc107',      # Yellow for warnings
            'danger': '#dc3545',       # Red for critical items
            'info': '#17a2b8',         # Blue for information
            'light': '#f8f9fa',        # Light background
            'dark': '#343a40'          # Dark text
        }
    
    def _setup_plot_style(self, fig, ax, title, xlabel, ylabel):
        """Apply consistent professional styling to plots"""
        # Set figure background
        fig.patch.set_facecolor('white')
        ax.set_facecolor('#fafafa')
        
        # Set title and labels
        ax.set_title(title, fontsize=16, fontweight='bold', color=self.colors['dark'], pad=20)
        ax.set_xlabel(xlabel, fontsize=12, color=self.colors['dark'])
        ax.set_ylabel(ylabel, fontsize=12, color=self.colors['dark'])
        
        # Style the axes
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.spines['bottom'].set_color('#cccccc')
        ax.tick_params(colors=self.colors['dark'], labelsize=10)
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Tight layout
        plt.tight_layout()
    
    def _plot_to_base64(self, fig):
        """Convert matplotlib figure to base64 string for web display"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close(fig)
        
        graphic = base64.b64encode(image_png)
        return graphic.decode('utf-8')
    
    def generate_sales_trend_chart(self, days=30):
        """
        Generate sales trend analysis chart using historical transaction data
        
        Args:
            days: Number of days to analyze (default: 30)
            
        Returns:
            dict: Chart data and base64 image
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get daily sales data
        sales_data = []
        current_date = start_date.date()
        
        while current_date <= end_date.date():
            daily_sales = Transaction.objects.filter(
                transaction_type='SALE',
                payment_status='PAID',
                timestamp__date=current_date
            ).aggregate(
                total_quantity=Sum('quantity'),
                total_amount=Sum('total_amount'),
                transaction_count=Count('id')
            )
            
            sales_data.append({
                'date': current_date,
                'quantity': daily_sales['total_quantity'] or 0,
                'amount': float(daily_sales['total_amount'] or 0),
                'transactions': daily_sales['transaction_count'] or 0
            })
            
            current_date += timedelta(days=1)
        
        # Create DataFrame for easier manipulation
        df = pd.DataFrame(sales_data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Create the plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot 1: Sales Amount Trend
        ax1.plot(df['date'], df['amount'], color=self.colors['primary'], 
                linewidth=2.5, marker='o', markersize=4, alpha=0.8)
        ax1.fill_between(df['date'], df['amount'], alpha=0.2, color=self.colors['primary'])
        
        self._setup_plot_style(fig, ax1, 
                              f'Daily Sales Revenue Trend ({days} Days)',
                              'Date', 'Sales Amount (Rs.)')
        
        # Format x-axis dates
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//10)))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Add trend line
        if len(df) > 1:
            z = np.polyfit(range(len(df)), df['amount'], 1)
            p = np.poly1d(z)
            ax1.plot(df['date'], p(range(len(df))), "--", 
                    color=self.colors['danger'], alpha=0.8, linewidth=2,
                    label=f"Trend: {'↗' if z[0] > 0 else '↘'}")
            ax1.legend()
        
        # Plot 2: Transaction Volume
        bars = ax2.bar(df['date'], df['transactions'], 
                      color=self.colors['info'], alpha=0.7, width=0.8)
        
        self._setup_plot_style(fig, ax2,
                              'Daily Transaction Volume',
                              'Date', 'Number of Transactions')
        
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//10)))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{int(height)}', ha='center', va='bottom', fontsize=8)
        
        # Calculate summary statistics
        total_sales = df['amount'].sum()
        avg_daily_sales = df['amount'].mean()
        total_transactions = df['transactions'].sum()
        peak_day = df.loc[df['amount'].idxmax(), 'date'].strftime('%Y-%m-%d') if total_sales > 0 else 'N/A'
        
        chart_data = {
            'image': self._plot_to_base64(fig),
            'summary': {
                'total_sales': total_sales,
                'avg_daily_sales': avg_daily_sales,
                'total_transactions': total_transactions,
                'peak_day': peak_day,
                'days_analyzed': days
            }
        }
        
        return chart_data
    
    def generate_actual_vs_predicted_chart(self, item_id=None, days=14):
        """
        Generate actual vs predicted demand comparison using AI predictions
        
        Args:
            item_id: Specific item to analyze (if None, analyzes top selling item)
            days: Number of days to forecast
            
        Returns:
            dict: Chart data and base64 image
        """
        # Get item to analyze
        if item_id:
            try:
                item = Item.objects.get(id=item_id)
            except Item.DoesNotExist:
                return {'error': 'Item not found'}
        else:
            # Get top selling item
            top_item = Transaction.objects.filter(
                transaction_type='SALE',
                payment_status='PAID'
            ).values('item').annotate(
                total_sold=Sum('quantity')
            ).order_by('-total_sold').first()
            
            if not top_item:
                return {'error': 'No sales data available'}
            
            item = Item.objects.get(id=top_item['item'])
        
        # Get historical actual sales (last 30 days)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        historical_data = []
        current_date = start_date.date()
        
        while current_date <= end_date.date():
            daily_sales = Transaction.objects.filter(
                item=item,
                transaction_type='SALE',
                payment_status='PAID',
                timestamp__date=current_date
            ).aggregate(total_quantity=Sum('quantity'))
            
            historical_data.append({
                'date': current_date,
                'actual': daily_sales['total_quantity'] or 0
            })
            
            current_date += timedelta(days=1)
        
        # Get AI predictions for future
        forecast_result = item.get_ai_demand_forecast(days=days)
        
        if not forecast_result['success']:
            return {'error': f'AI prediction failed: {forecast_result["error"]}'}
        
        # Prepare data for plotting
        historical_df = pd.DataFrame(historical_data)
        historical_df['date'] = pd.to_datetime(historical_df['date'])
        
        # Create future dates and predictions
        future_dates = []
        predictions = []
        
        for pred in forecast_result['predictions']:
            future_dates.append(pred['date'])
            predictions.append(pred['predicted_demand'])
        
        future_df = pd.DataFrame({
            'date': pd.to_datetime(future_dates),
            'predicted': predictions
        })
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Plot historical actual data
        ax.plot(historical_df['date'], historical_df['actual'], 
               color=self.colors['primary'], linewidth=2.5, marker='o', 
               markersize=5, label='Actual Sales', alpha=0.8)
        
        # Plot AI predictions
        ax.plot(future_df['date'], future_df['predicted'], 
               color=self.colors['danger'], linewidth=2.5, marker='s', 
               markersize=5, label='AI Predictions', alpha=0.8, linestyle='--')
        
        # Fill areas
        ax.fill_between(historical_df['date'], historical_df['actual'], 
                       alpha=0.2, color=self.colors['primary'])
        ax.fill_between(future_df['date'], future_df['predicted'], 
                       alpha=0.2, color=self.colors['danger'])
        
        # Add vertical line to separate actual from predicted
        today = timezone.now().date()
        ax.axvline(x=pd.to_datetime(today), color='gray', linestyle='-', 
                  alpha=0.5, linewidth=2, label='Today')
        
        # Setup styling
        self._setup_plot_style(fig, ax,
                              f'Actual vs AI Predicted Demand - {item.name}',
                              'Date', 'Daily Demand (Units)')
        
        # Format dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add legend
        ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
        
        # Add annotations
        if len(predictions) > 0:
            max_pred = max(predictions)
            max_pred_date = future_dates[predictions.index(max_pred)]
            ax.annotate(f'Peak Predicted: {max_pred:.1f}', 
                       xy=(pd.to_datetime(max_pred_date), max_pred),
                       xytext=(10, 10), textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor=self.colors['warning'], alpha=0.7),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        # Calculate accuracy if we have overlapping data
        accuracy_info = "N/A"
        if hasattr(ml_predictor, 'model_metrics') and item.id in ml_predictor.model_metrics:
            accuracy = ml_predictor.model_metrics[item.id].get('accuracy', 0)
            accuracy_info = f"{accuracy:.1f}%"
        
        chart_data = {
            'image': self._plot_to_base64(fig),
            'item_name': item.name,
            'summary': {
                'historical_days': len(historical_data),
                'forecast_days': days,
                'total_actual': sum(h['actual'] for h in historical_data),
                'total_predicted': sum(predictions),
                'avg_actual': np.mean([h['actual'] for h in historical_data]),
                'avg_predicted': np.mean(predictions) if predictions else 0,
                'model_accuracy': accuracy_info
            }
        }
        
        return chart_data
    
    def generate_inventory_performance_chart(self):
        """
        Generate inventory performance overview chart
        
        Returns:
            dict: Chart data and base64 image
        """
        # Get inventory data
        items = Item.objects.all()
        
        categories = []
        stock_levels = []
        reorder_levels = []
        colors_list = []
        
        for item in items:
            categories.append(item.name[:15] + '...' if len(item.name) > 15 else item.name)
            stock_levels.append(item.quantity)
            reorder_levels.append(item.reorder_level)
            
            # Color based on stock status
            if item.quantity == 0:
                colors_list.append(self.colors['danger'])
            elif item.quantity <= item.reorder_level:
                colors_list.append(self.colors['warning'])
            else:
                colors_list.append(self.colors['success'])
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 8))
        
        x = np.arange(len(categories))
        width = 0.35
        
        # Create bars
        bars1 = ax.bar(x - width/2, stock_levels, width, label='Current Stock', 
                      color=colors_list, alpha=0.8)
        bars2 = ax.bar(x + width/2, reorder_levels, width, label='Reorder Level', 
                      color=self.colors['info'], alpha=0.6)
        
        # Setup styling
        self._setup_plot_style(fig, ax,
                              'Inventory Performance Overview',
                              'Items', 'Quantity (Units)')
        
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend()
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{int(height)}', ha='center', va='bottom', fontsize=9)
        
        # Calculate summary
        total_items = len(items)
        out_of_stock = sum(1 for item in items if item.quantity == 0)
        low_stock = sum(1 for item in items if 0 < item.quantity <= item.reorder_level)
        well_stocked = total_items - out_of_stock - low_stock
        
        chart_data = {
            'image': self._plot_to_base64(fig),
            'summary': {
                'total_items': total_items,
                'out_of_stock': out_of_stock,
                'low_stock': low_stock,
                'well_stocked': well_stocked,
                'stock_efficiency': (well_stocked / total_items * 100) if total_items > 0 else 0
            }
        }
        
        return chart_data
    
    def generate_ai_model_performance_chart(self):
        """
        Generate AI model performance visualization
        
        Returns:
            dict: Chart data and base64 image
        """
        items = Item.objects.all()
        
        model_data = []
        for item in items:
            model_info = ml_predictor.get_model_info(item)
            if model_info:
                accuracy = model_info['metrics'].get('accuracy', 0)
                training_samples = model_info['metrics'].get('training_samples', 0)
                model_data.append({
                    'name': item.name[:12] + '...' if len(item.name) > 12 else item.name,
                    'accuracy': accuracy,
                    'samples': training_samples,
                    'status': 'Trained'
                })
            else:
                model_data.append({
                    'name': item.name[:12] + '...' if len(item.name) > 12 else item.name,
                    'accuracy': 0,
                    'samples': 0,
                    'status': 'Not Trained'
                })
        
        if not model_data:
            return {'error': 'No model data available'}
        
        # Create the plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Model Accuracy
        names = [d['name'] for d in model_data]
        accuracies = [d['accuracy'] for d in model_data]
        colors = [self.colors['success'] if acc > 50 else 
                 self.colors['warning'] if acc > 0 else 
                 self.colors['danger'] for acc in accuracies]
        
        bars1 = ax1.bar(names, accuracies, color=colors, alpha=0.8)
        ax1.set_title('AI Model Accuracy by Item', fontsize=14, fontweight='bold', pad=15)
        ax1.set_ylabel('Accuracy (%)')
        ax1.set_xlabel('Items')
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        ax1.grid(True, alpha=0.3)
        
        # Add value labels
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=9)
        
        # Plot 2: Training Data Availability
        samples = [d['samples'] for d in model_data]
        bars2 = ax2.bar(names, samples, color=self.colors['info'], alpha=0.8)
        ax2.set_title('Training Data Samples', fontsize=14, fontweight='bold', pad=15)
        ax2.set_ylabel('Number of Samples')
        ax2.set_xlabel('Items')
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        ax2.grid(True, alpha=0.3)
        
        # Add value labels
        for bar in bars2:
            height = bar.get_height()
            if height > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{int(height)}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        # Calculate summary
        trained_models = sum(1 for d in model_data if d['status'] == 'Trained')
        avg_accuracy = np.mean([d['accuracy'] for d in model_data if d['accuracy'] > 0])
        total_samples = sum(d['samples'] for d in model_data)
        
        chart_data = {
            'image': self._plot_to_base64(fig),
            'summary': {
                'total_items': len(model_data),
                'trained_models': trained_models,
                'avg_accuracy': avg_accuracy if not np.isnan(avg_accuracy) else 0,
                'total_samples': total_samples,
                'ai_coverage': (trained_models / len(model_data) * 100) if model_data else 0
            }
        }
        
        return chart_data


# Global analytics instance
analytics = InventoryAnalytics()