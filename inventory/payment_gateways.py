"""
Payment Gateway Integration Module
===================================

This module handles integration with Khalti and eSewa payment gateways
for processing sale transactions in the inventory management system.

Academic Explanation (for Viva):
---------------------------------
Payment gateways are third-party services that securely process online payments.
This implementation follows industry-standard practices:

1. Payment Initiation: Create payment request with gateway
2. User Redirect: Send user to gateway's secure payment page
3. Payment Processing: User completes payment on gateway
4. Callback: Gateway redirects back to our system
5. Verification: We verify payment with gateway's API
6. Status Update: Update transaction status based on verification

Security Features:
- API keys stored in settings (not hardcoded)
- Payment verification before marking as complete
- Secure callback handling
- Transaction atomicity (all-or-nothing updates)

Why Two Gateways?
- Khalti: Popular in Nepal, mobile-first
- eSewa: Widely used, bank integration
- Provides user choice and redundancy
"""

import requests
import hashlib
import hmac
import base64
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


class KhaltiPaymentGateway:
    """
    Khalti Payment Gateway Integration
    
    Khalti is a popular digital wallet and payment gateway in Nepal.
    
    Flow:
    1. initiate_payment() - Create payment request
    2. User redirected to Khalti payment page
    3. User completes payment
    4. Khalti redirects to our verify URL
    5. verify_payment() - Verify with Khalti API
    6. Update transaction status
    
    Documentation: https://docs.khalti.com/
    """
    
    def __init__(self):
        self.public_key = settings.KHALTI_PUBLIC_KEY
        self.secret_key = settings.KHALTI_SECRET_KEY
        self.verify_url = settings.KHALTI_VERIFY_URL
    
    def initiate_payment(self, transaction, request):
        """
        Prepare payment data for Khalti
        
        Args:
            transaction: Transaction model instance
            request: Django request object
        
        Returns:
            dict: Payment configuration for frontend
        """
        # Convert amount to paisa (Khalti uses paisa, 1 rupee = 100 paisa)
        amount_in_paisa = int(float(transaction.total_amount) * 100)
        
        # Build return URL (where Khalti redirects after payment)
        return_url = request.build_absolute_uri(
            reverse('inventory:verify_khalti_payment')
        )
        
        payment_data = {
            'public_key': self.public_key,
            'amount': amount_in_paisa,
            'product_identity': str(transaction.id),
            'product_name': f"{transaction.item.name} - {transaction.transaction_type}",
            'product_url': request.build_absolute_uri(
                reverse('inventory:transaction_detail', args=[transaction.id])
            ),
            'return_url': return_url,
        }
        
        logger.info(f"Khalti payment initiated for transaction {transaction.id}")
        return payment_data
    
    def verify_payment(self, token, amount):
        """
        Verify payment with Khalti API
        
        Args:
            token: Payment token from Khalti
            amount: Amount in paisa
        
        Returns:
            dict: Verification response with success status
        """
        try:
            headers = {
                'Authorization': f'Key {self.secret_key}'
            }
            
            payload = {
                'token': token,
                'amount': amount
            }
            
            logger.info(f"Verifying Khalti payment with token: {token}")
            
            response = requests.post(
                self.verify_url,
                headers=headers,
                data=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Khalti verification successful: {data}")
                return {
                    'success': True,
                    'data': data,
                    'transaction_id': data.get('idx'),
                    'amount': data.get('amount'),
                }
            else:
                logger.error(f"Khalti verification failed: {response.text}")
                return {
                    'success': False,
                    'error': 'Payment verification failed',
                    'details': response.text
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Khalti verification error: {str(e)}")
            return {
                'success': False,
                'error': 'Network error during verification',
                'details': str(e)
            }
        except Exception as e:
            logger.error(f"Khalti verification exception: {str(e)}")
            return {
                'success': False,
                'error': 'Unexpected error',
                'details': str(e)
            }


class EsewaPaymentGateway:
    """
    eSewa Payment Gateway Integration
    
    eSewa is Nepal's first online payment gateway.
    
    Flow:
    1. generate_payment_form() - Create HTML form with payment data
    2. Form auto-submits to eSewa
    3. User completes payment on eSewa
    4. eSewa redirects to success/failure URL
    5. verify_payment() - Verify with eSewa API
    6. Update transaction status
    
    Documentation: https://developer.esewa.com.np/
    """
    
    def __init__(self):
        self.merchant_id = settings.ESEWA_MERCHANT_ID
        self.payment_url = settings.ESEWA_PAYMENT_URL
        self.verify_url = settings.ESEWA_VERIFY_URL
        self.success_url = settings.ESEWA_SUCCESS_URL
        self.failure_url = settings.ESEWA_FAILURE_URL
    
    def generate_payment_form(self, transaction):
        """
        Generate eSewa payment form data
        
        Args:
            transaction: Transaction model instance
        
        Returns:
            dict: Form data for eSewa payment
        """
        # eSewa requires amount as string with 2 decimal places
        total_amount = f"{float(transaction.total_amount):.2f}"
        
        # eSewa form parameters
        form_data = {
            'amt': total_amount,  # Total amount
            'psc': '0',  # Service charge (0 for now)
            'pdc': '0',  # Delivery charge (0 for now)
            'txAmt': '0',  # Tax amount (0 for now)
            'tAmt': total_amount,  # Total amount (amt + psc + pdc + txAmt)
            'pid': f"TXN{transaction.id}",  # Product/Transaction ID
            'scd': self.merchant_id,  # Merchant ID
            'su': self.success_url,  # Success URL
            'fu': self.failure_url,  # Failure URL
        }
        
        logger.info(f"eSewa payment form generated for transaction {transaction.id}")
        return {
            'action_url': self.payment_url,
            'form_data': form_data
        }
    
    def verify_payment(self, transaction_id, ref_id, amount):
        """
        Verify payment with eSewa API
        
        Args:
            transaction_id: Our transaction ID (pid)
            ref_id: eSewa reference ID (refId)
            amount: Total amount
        
        Returns:
            dict: Verification response with success status
        """
        try:
            # eSewa verification parameters
            params = {
                'amt': amount,
                'rid': ref_id,
                'pid': transaction_id,
                'scd': self.merchant_id
            }
            
            logger.info(f"Verifying eSewa payment: {params}")
            
            response = requests.get(
                self.verify_url,
                params=params,
                timeout=10
            )
            
            # eSewa returns XML response
            response_text = response.text.strip()
            
            # Check if response contains success indicators
            # eSewa returns response code in XML format
            if response.status_code == 200 and 'Success' in response_text:
                logger.info(f"eSewa verification successful: {response_text}")
                return {
                    'success': True,
                    'ref_id': ref_id,
                    'response': response_text
                }
            else:
                logger.error(f"eSewa verification failed: {response_text}")
                return {
                    'success': False,
                    'error': 'Payment verification failed',
                    'response': response_text
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"eSewa verification error: {str(e)}")
            return {
                'success': False,
                'error': 'Network error during verification',
                'details': str(e)
            }
        except Exception as e:
            logger.error(f"eSewa verification exception: {str(e)}")
            return {
                'success': False,
                'error': 'Unexpected error',
                'details': str(e)
            }


# Gateway factory for easy access
def get_payment_gateway(payment_method):
    """
    Factory function to get appropriate payment gateway
    
    Args:
        payment_method: Payment method string ('KHALTI' or 'ESEWA')
    
    Returns:
        Payment gateway instance or None
    """
    if payment_method == 'KHALTI':
        return KhaltiPaymentGateway()
    elif payment_method == 'ESEWA':
        return EsewaPaymentGateway()
    else:
        return None
