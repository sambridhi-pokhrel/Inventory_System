# How to Get Khalti Test Keys

## Current Status

Khalti is currently **DISABLED** in your system. eSewa works fine.

To enable Khalti, you need to get real API keys from Khalti.

---

## Option 1: Get Khalti Test Keys (Recommended)

### Step 1: Sign Up for Khalti Merchant Account

1. **Visit Khalti Test Admin**:
   - Go to: https://test-admin.khalti.com/
   - This is the TEST environment (safe for development)

2. **Create Account**:
   - Click "Sign Up" or "Register"
   - Fill in your details:
     - Name
     - Email
     - Phone number
     - Password
   - Verify your email

3. **Complete Merchant Profile**:
   - Login to test admin
   - Complete your merchant profile
   - Add business details (can be test data)

### Step 2: Get Your API Keys

1. **Navigate to Settings**:
   - Click on your profile/settings
   - Go to "API Keys" or "Developer Settings"

2. **Copy Your Keys**:
   - **Public Key**: Starts with `test_public_key_...`
   - **Secret Key**: Starts with `test_secret_key_...`
   - Keep these safe!

### Step 3: Update Django Settings

1. **Open**: `inventory_system/settings.py`

2. **Replace**:
   ```python
   KHALTI_PUBLIC_KEY = None  # Current
   KHALTI_SECRET_KEY = None  # Current
   KHALTI_ENABLED = False    # Current
   ```

3. **With**:
   ```python
   KHALTI_PUBLIC_KEY = 'test_public_key_YOUR_ACTUAL_KEY_HERE'
   KHALTI_SECRET_KEY = 'test_secret_key_YOUR_ACTUAL_KEY_HERE'
   KHALTI_ENABLED = True  # Enable Khalti
   ```

4. **Save** and restart server

### Step 4: Test

1. Create a SALE transaction with Khalti
2. Click "Pay with Khalti"
3. Use test credentials:
   - Mobile: 9800000000
   - MPIN: 1111
   - OTP: 987654

---

## Option 2: Use Only eSewa (Current Setup)

If you don't want to set up Khalti right now, you can use only eSewa:

### Current Configuration:
- ✅ eSewa: **ENABLED** and working
- ❌ Khalti: **DISABLED** (no valid keys)

### To Use eSewa:

1. Create SALE transaction
2. Select **eSewa** as payment method
3. Click "Pay with eSewa"
4. Use test credentials:
   - eSewa ID: 9806800001
   - Password: Nepal@123
   - MPIN: 1122

---

## Option 3: Use Cash/Bank Transfer (No Gateway)

For immediate testing without any payment gateway:

1. Create SALE transaction
2. Select **Cash** or **Bank Transfer**
3. Transaction is marked as PAID immediately
4. No payment gateway needed

---

## Why Khalti is Disabled

The error you saw:
```
public_key: Invalid key. Make sure it is a public key.
```

This means the test keys I provided are not valid Khalti keys. Khalti requires real keys from their system, even for testing.

---

## What Works Right Now

✅ **eSewa Payment**: Fully functional
✅ **Cash Payment**: Works immediately
✅ **Bank Transfer**: Works immediately
✅ **Credit**: Works immediately
❌ **Khalti Payment**: Disabled (needs real keys)

---

## For Your FYP Demonstration

You have two options:

### Option A: Show eSewa Only
- eSewa works perfectly
- No need for Khalti keys
- Still demonstrates payment gateway integration
- Sufficient for academic demonstration

### Option B: Get Khalti Keys
- Takes 10-15 minutes to sign up
- Shows both payment gateways
- More impressive for demonstration
- Follow steps above

---

## Quick Test (eSewa)

Right now, you can test the complete payment flow with eSewa:

```bash
python manage.py runserver
```

1. Go to: http://127.0.0.1:8000/inventory/transactions/create/
2. Create SALE transaction
3. Select **eSewa (Digital Wallet)**
4. Click "Create Transaction"
5. Click "Pay with eSewa"
6. Use credentials:
   - eSewa ID: 9806800001
   - Password: Nepal@123
   - MPIN: 1122
7. Complete payment
8. ✅ Transaction marked as PAID
9. ✅ Stock updated

---

## For Production

When deploying to production:

1. **Get Live Keys**:
   - Khalti: https://admin.khalti.com/ (not test-admin)
   - eSewa: https://esewa.com.np/

2. **Update Settings**:
   ```python
   KHALTI_PUBLIC_KEY = 'live_public_key_...'
   KHALTI_SECRET_KEY = 'live_secret_key_...'
   KHALTI_ENABLED = True
   
   ESEWA_MERCHANT_ID = 'your_live_merchant_id'
   ESEWA_PAYMENT_URL = 'https://esewa.com.np/epay/main'
   ESEWA_VERIFY_URL = 'https://esewa.com.np/epay/transrec'
   ```

3. **Test with Real Money** (small amounts first!)

---

## Summary

**Current Status**:
- eSewa: ✅ Working
- Khalti: ❌ Disabled (needs keys)
- Cash/Bank: ✅ Working

**To Enable Khalti**:
1. Sign up at https://test-admin.khalti.com/
2. Get API keys
3. Update settings.py
4. Set KHALTI_ENABLED = True
5. Restart server

**Or Just Use eSewa**:
- Already working
- No setup needed
- Perfect for demonstration

Choose what works best for your timeline!
