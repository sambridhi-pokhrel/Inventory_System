# Payment Gateway Integration Guide

## ✅ SYSTEM STATUS: FULLY IMPLEMENTED

The Django Inventory Management System now supports Khalti and eSewa payment gateways for processing sale transactions.

---

## Overview

### Supported Payment Gateways

1. **Khalti** - Nepal's popular digital wallet
   - Mobile-first payment solution
   - Instant payment verification
   - Supports multiple payment methods (wallet, banking, cards)

2. **eSewa** - Nepal's first online payment gateway
   - Wide merchant acceptance
   - Bank integration
   - Trusted by millions

3. **Traditional Methods**
   - Cash
   - Bank Transfer
   - Credit

---

## How It Works

### Payment Flow

```
1. Create Transaction
   ↓
2. Select Payment Method (Khalti/eSewa/Cash)
   ↓
3. Transaction Created (Status: PENDING)
   ↓
4. Click "Pay Now" Button
   ↓
5. Redirect to Payment Gateway
   ↓
6. User Completes Payment
   ↓
7. Gateway Redirects Back
   ↓
8. System Verifies Payment
   ↓
9. Update Status (PAID/FAILED)
   ↓
10. Update Inventory Stock
```

### Security Features

- ✅ API keys stored securely in settings
- ✅ Payment verification before marking as complete
- ✅ Atomic database transactions
- ✅ Secure callback handling
- ✅ Comprehensive error logging
- ✅ Stock updates only after payment confirmation

---

## Configuration

### 1. Khalti Setup

#### Get API Keys

1. Visit: https://khalti.com/
2. Sign up for merchant account
3. Go to Settings → API Keys
4. Copy your Public Key and Secret Key

#### Configure in Django

Edit `inventory_system/settings.py`:

```python
# Khalti Configuration
KHALTI_PUBLIC_KEY = 'your_public_key_here'
KHALTI_SECRET_KEY = 'your_secret_key_here'
KHALTI_VERIFY_URL = 'https://khalti.com/api/v2/payment/verify/'
```

#### Test Mode

For development, use test keys:
```python
KHALTI_PUBLIC_KEY = 'test_public_key_dc74e0fd57cb46cd93832aee0a390234'
KHALTI_SECRET_KEY = 'test_secret_key_f59e8b7d18b4499ca40f68195a846e9b'
```

Test credentials:
- Mobile: 9800000000
- MPIN: 1111
- OTP: 987654

---

### 2. eSewa Setup

#### Get Merchant ID

1. Visit: https://esewa.com.np/
2. Apply for merchant account
3. Get your Merchant ID (SCD)

#### Configure in Django

Edit `inventory_system/settings.py`:

```python
# eSewa Configuration
ESEWA_MERCHANT_ID = 'your_merchant_id'
ESEWA_SUCCESS_URL = 'http://yourdomain.com/inventory/payment/esewa/verify/'
ESEWA_FAILURE_URL = 'http://yourdomain.com/inventory/payment/esewa/failure/'
ESEWA_PAYMENT_URL = 'https://esewa.com.np/epay/main'
ESEWA_VERIFY_URL = 'https://esewa.com.np/epay/transrec'
```

#### Test Mode

For development, use test configuration:
```python
ESEWA_MERCHANT_ID = 'EPAYTEST'
ESEWA_PAYMENT_URL = 'https://uat.esewa.com.np/epay/main'
ESEWA_VERIFY_URL = 'https://uat.esewa.com.np/epay/transrec'
```

Test credentials:
- eSewa ID: 9806800001, 9806800002, 9806800003, 9806800004, 9806800005
- Password: Nepal@123
- MPIN: 1122

---

## Usage Guide

### For Users

#### Creating a Sale Transaction

1. Navigate to **Transactions → Create Transaction**
2. Fill in transaction details:
   - Select item
   - Enter quantity
   - Choose transaction type: **Sale**
   - Select payment method: **Khalti** or **eSewa**
3. Click **Create Transaction**
4. Transaction created with status: **PENDING**

#### Completing Payment

1. Go to **Transaction Details** page
2. Click **Pay with Khalti** or **Pay with eSewa**
3. Complete payment on gateway page
4. Automatically redirected back
5. Payment verified and status updated to **PAID**
6. Inventory stock automatically updated

#### Payment Status

- **PENDING** - Payment not yet completed
- **PAID** - Payment successful, stock updated
- **FAILED** - Payment failed, can retry

---

## Technical Implementation

### Files Modified/Created

1. **Models** (`inventory/models.py`)
   - Added `ESEWA` to payment method choices
   - Payment status tracking
   - Payment reference storage

2. **Payment Gateway Module** (`inventory/payment_gateways.py`)
   - `KhaltiPaymentGateway` class
   - `EsewaPaymentGateway` class
   - Payment initiation and verification logic

3. **Views** (`inventory/views.py`)
   - `initiate_khalti_payment()` - Start Khalti payment
   - `verify_khalti_payment()` - Verify Khalti callback
   - `initiate_esewa_payment()` - Start eSewa payment
   - `verify_esewa_payment()` - Verify eSewa callback
   - `payment_success()` - Success page
   - `payment_failure()` - Failure page

4. **URLs** (`inventory/urls.py`)
   - Payment gateway routes
   - Callback URLs

5. **Templates**
   - `payment_khalti.html` - Khalti payment page
   - `payment_esewa.html` - eSewa payment page
   - `payment_success.html` - Success confirmation
   - `payment_failure.html` - Failure page with retry
   - Updated `transaction_detail.html` - Payment buttons
   - Updated `transaction_create.html` - eSewa option

6. **Settings** (`inventory_system/settings.py`)
   - Khalti API configuration
   - eSewa API configuration

---

## Testing

### Test Khalti Payment

1. Create a sale transaction with Khalti payment method
2. Click "Pay with Khalti"
3. Use test credentials:
   - Mobile: 9800000000
   - MPIN: 1111
   - OTP: 987654
4. Complete payment
5. Verify transaction status changes to PAID

### Test eSewa Payment

1. Create a sale transaction with eSewa payment method
2. Click "Pay with eSewa"
3. Use test credentials:
   - eSewa ID: 9806800001
   - Password: Nepal@123
   - MPIN: 1122
4. Complete payment
5. Verify transaction status changes to PAID

### Test Failure Scenarios

1. Cancel payment on gateway page
2. Use invalid credentials
3. Verify system handles gracefully
4. Check retry functionality

---

## For Academic Presentation (Viva)

### Key Points to Explain

1. **Payment Gateway Integration**
   - Third-party service integration
   - API-based communication
   - Secure payment processing

2. **Security Measures**
   - API key management
   - Payment verification (never trust client alone)
   - Atomic transactions
   - Error handling

3. **User Experience**
   - Seamless payment flow
   - Clear status indicators
   - Retry on failure
   - Success confirmation

4. **Technical Architecture**
   - Modular design (separate gateway classes)
   - Factory pattern for gateway selection
   - Callback handling
   - Database consistency

5. **Real-World Application**
   - E-commerce payment processing
   - Inventory management integration
   - Multi-gateway support
   - Nepal-specific payment solutions

### Technical Concepts Demonstrated

- **API Integration**: REST API calls to external services
- **Callback Handling**: Processing gateway responses
- **Payment Verification**: Server-side verification
- **Transaction Management**: Database atomicity
- **Error Handling**: Graceful degradation
- **Security**: API key management, verification
- **User Flow**: Multi-step process management

---

## Troubleshooting

### Payment Not Completing

**Problem**: Payment stuck in PENDING status

**Solutions**:
1. Check internet connection
2. Verify API keys are correct
3. Check gateway service status
4. Review server logs for errors
5. Ensure callback URLs are accessible

### Verification Failed

**Problem**: Payment completed but verification fails

**Solutions**:
1. Check API keys match gateway account
2. Verify callback URL is correct
3. Check server logs for API errors
4. Ensure amount matches exactly
5. Contact gateway support

### Stock Not Updating

**Problem**: Payment successful but stock unchanged

**Solutions**:
1. Check transaction status is PAID
2. Review database transaction logs
3. Verify save() method is called
4. Check for validation errors

---

## Production Deployment

### Environment Variables

For production, use environment variables:

```python
import os

# Khalti
KHALTI_PUBLIC_KEY = os.getenv('KHALTI_PUBLIC_KEY')
KHALTI_SECRET_KEY = os.getenv('KHALTI_SECRET_KEY')

# eSewa
ESEWA_MERCHANT_ID = os.getenv('ESEWA_MERCHANT_ID')
```

### Server Configuration

1. Set environment variables on server
2. Use HTTPS for all payment URLs
3. Configure proper callback URLs
4. Enable logging for debugging
5. Set up monitoring for payment failures

### Security Checklist

- ✅ API keys in environment variables
- ✅ HTTPS enabled
- ✅ Callback URLs whitelisted
- ✅ Payment verification enabled
- ✅ Error logging configured
- ✅ Database backups enabled

---

## API Documentation

### Khalti API

**Verification Endpoint**: `POST https://khalti.com/api/v2/payment/verify/`

**Headers**:
```
Authorization: Key {secret_key}
```

**Payload**:
```json
{
  "token": "payment_token",
  "amount": 10000  // in paisa
}
```

**Response**:
```json
{
  "idx": "transaction_id",
  "amount": 10000,
  "mobile": "98XXXXXXXX",
  "product_identity": "product_id",
  "product_name": "Product Name",
  "state": {
    "name": "Completed"
  }
}
```

### eSewa API

**Verification Endpoint**: `GET https://esewa.com.np/epay/transrec`

**Parameters**:
```
amt: total_amount
rid: reference_id
pid: product_id
scd: merchant_id
```

**Response**: XML format
```xml
<response>
    <response_code>Success</response_code>
</response>
```

---

## Support

### Khalti Support
- Website: https://khalti.com/
- Docs: https://docs.khalti.com/
- Email: support@khalti.com

### eSewa Support
- Website: https://esewa.com.np/
- Docs: https://developer.esewa.com.np/
- Email: support@esewa.com.np

---

## Conclusion

The payment gateway integration provides:
- ✅ Secure online payment processing
- ✅ Multiple payment options for users
- ✅ Automatic payment verification
- ✅ Seamless inventory integration
- ✅ Professional e-commerce experience
- ✅ Real-world application demonstration

Perfect for academic FYP demonstration and real-world deployment!
