"""
Payment Gateway Simulation Module

This module provides simulated payment gateway functionality for testing
when actual payment gateways (Khalti/eSewa) are not accessible.

Academic Explanation (for Viva):
---------------------------------
In real-world development, payment gateway test environments may not always
be available. This simulation allows:
1. Testing payment flow without external dependencies
2. Demonstrating payment integration logic
3. Development when offline or gateway is down
4. Academic demonstration without real gateway accounts

This is ONLY for development/testing. Never use in production!
"""

import uuid
from django.conf import settings


class PaymentSimulator:
    """
    Simulates payment gateway behavior for testing
    
    This class mimics the behavior of real payment gateways:
    - Generates mock payment references
    - Simulates payment success/failure
    - Provides test payment pages
    """
    
    @staticmethod
    def is_simulation_mode():
        """Check if simulation mode is enabled"""
        return getattr(settings, 'PAYMENT_SIMULATION_MODE', False)
    
    @staticmethod
    def simulate_khalti_payment(transaction):
        """
        Simulate Khalti payment completion
        
        Returns mock payment data similar to real Khalti response
        """
        return {
            'success': True,
            'transaction_id': f"KHALTI_SIM_{uuid.uuid4().hex[:8].upper()}",
            'amount': int(float(transaction.total_amount) * 100),  # In paisa
            'message': 'Payment simulated successfully (Test Mode)'
        }
    
    @staticmethod
    def simulate_esewa_payment(transaction):
        """
        Simulate eSewa payment completion
        
        Returns mock payment data similar to real eSewa response
        """
        return {
            'success': True,
            'ref_id': f"ESEWA_SIM_{uuid.uuid4().hex[:8].upper()}",
            'amount': float(transaction.total_amount),
            'message': 'Payment simulated successfully (Test Mode)'
        }
    
    @staticmethod
    def get_simulation_message():
        """Get message to display in simulation mode"""
        return (
            "🧪 SIMULATION MODE: Payment gateways are simulated for testing. "
            "This demonstrates the payment flow without connecting to real gateways. "
            "In production, this would connect to actual Khalti/eSewa servers."
        )
