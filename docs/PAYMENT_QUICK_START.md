# Payment Gateway - Quick Start Guide

## 🚀 Ready to Use!

The payment gateway integration is complete and ready for testing.

---

## Quick Test (5 Minutes)

### Step 1: Start Server
```bash
python manage.py runserver
```

### Step 2: Login
- Go to: http://127.0.0.1:8000/
- Login with your credentials

### Step 3: Create Sale Transaction
1. Navigate to: **Transactions → Create Transaction**
2. Fill in:
   - Item: Select any item
   - Transaction Type: **Sale**
   - Quantity: 1
   - Payment Method: **Khalti** or **eSewa**
3. Click **Create Transaction**

### Step 4: Pay with Khalti (Test)
1. Click **Pay with Khalti** button
2. Khalti widget opens
3. Use test credentials:
   - Mobile: **9800000000**
   - MPIN: **1111**
   - OTP: **987654**
4. Complete payment
5. ✅ Redirected to success page
6. ✅ Transaction status: **PAID**
7. ✅ Stock updated automatically

### Step 5: Pay with eSewa (Test)
1. Click **Pay with eSewa** button
2. Redirected to eSewa page
3. Use test credentials:
   - eSewa ID: **9806800001**
   - Password: **Nepal@123**
   - MPIN: **1122**
4. Complete payment
5. ✅ Redirected to success page
6. ✅ Transaction status: **PAID**
7. ✅ Stock updated automatically

---

## Test Credentials

### Khalti Test Mode
```
Mobile: 9800000000
MPIN: 1111
OTP: 987654
```

### eSewa Test Mode
```
eSewa ID: 9806800001 (or 9806800002, 9806800003)
Password: Nepal@123
MPIN: 1122
```

---

## Payment Status

### PENDING (Yellow Badge)
- Transaction created but payment not completed
- Click "Pay Now" to complete payment

### PAID (Green Badge)
- Payment successful
- Stock automatically updated
- Payment reference stored

### FAILED (Red Badge)
- Payment failed or cancelled
- Click "Retry Payment" to try again

---

## URLs

### Transaction Pages
- List: http://127.0.0.1:8000/inventory/transactions/
- Create: http://127.0.0.1:8000/inventory/transactions/create/
- Detail: http://127.0.0.1:8000/inventory/transactions/{id}/

### Payment Pages
- Khalti: http://127.0.0.1:8000/inventory/payment/khalti/initiate/{id}/
- eSewa: http://127.0.0.1:8000/inventory/payment/esewa/initiate/{id}/
- Success: http://127.0.0.1:8000/inventory/payment/success/{id}/
- Failure: http://127.0.0.1:8000/inventory/payment/failure/{id}/

---

## Configuration Files

### API Keys (Test Mode)
File: `inventory_system/settings.py`

```python
# Khalti (Test)
KHALTI_PUBLIC_KEY = 'test_public_key_dc74e0fd57cb46cd93832aee0a390234'
KHALTI_SECRET_KEY = 'test_secret_key_f59e8b7d18b4499ca40f68195a846e9b'

# eSewa (Test)
ESEWA_MERCHANT_ID = 'EPAYTEST'
```

---

## Features

✅ **Khalti Integration**
- Digital wallet payment
- Multiple payment methods
- Instant verification
- Test mode enabled

✅ **eSewa Integration**
- Online payment gateway
- Bank integration
- Secure verification
- Test mode enabled

✅ **Payment Status Tracking**
- PENDING → PAID → Stock Updated
- PENDING → FAILED → Can Retry
- Real-time status updates

✅ **Security**
- API verification
- Secure callbacks
- Atomic transactions
- Error handling

✅ **User Experience**
- Clear status indicators
- Easy payment flow
- Success confirmation
- Retry on failure

---

## Troubleshooting

### Payment Not Working?

1. **Check Internet Connection**
   - Payment gateways require internet

2. **Verify Test Credentials**
   - Use exact credentials provided above

3. **Check Server Logs**
   - Look for error messages in terminal

4. **Verify API Keys**
   - Check settings.py has correct keys

5. **Clear Browser Cache**
   - Sometimes helps with JavaScript issues

### Common Issues

**Issue**: Khalti widget not opening
**Solution**: Check browser console for JavaScript errors

**Issue**: eSewa redirect not working
**Solution**: Verify callback URLs in settings.py

**Issue**: Payment verified but stock not updated
**Solution**: Check transaction status is PAID

---

## For Production

### Replace Test Keys

1. **Get Live Khalti Keys**
   - Visit: https://khalti.com/
   - Sign up for merchant account
   - Get live public and secret keys

2. **Get Live eSewa Merchant ID**
   - Visit: https://esewa.com.np/
   - Apply for merchant account
   - Get live merchant ID

3. **Update Settings**
   ```python
   KHALTI_PUBLIC_KEY = 'live_public_key_...'
   KHALTI_SECRET_KEY = 'live_secret_key_...'
   ESEWA_MERCHANT_ID = 'your_merchant_id'
   ```

4. **Update URLs**
   ```python
   ESEWA_PAYMENT_URL = 'https://esewa.com.np/epay/main'
   ESEWA_VERIFY_URL = 'https://esewa.com.np/epay/transrec'
   ```

---

## Documentation

📖 **Detailed Setup**: See `PAYMENT_GATEWAY_SETUP.md`
📋 **Implementation Summary**: See `PAYMENT_INTEGRATION_SUMMARY.md`

---

## Support

Need help? Check:
1. Documentation files in project root
2. Code comments in `inventory/payment_gateways.py`
3. Django logs in terminal
4. Gateway documentation:
   - Khalti: https://docs.khalti.com/
   - eSewa: https://developer.esewa.com.np/

---

## Success! 🎉

Your inventory system now supports:
- ✅ Khalti payments
- ✅ eSewa payments
- ✅ Automatic verification
- ✅ Stock management
- ✅ Professional UI

**Ready for demonstration and deployment!**
