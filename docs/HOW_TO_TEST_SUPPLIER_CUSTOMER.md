# How to Test Supplier & Customer Fields

## ✅ Admin Configuration Updated!

The supplier and customer fields are now visible in the admin panel.

---

## 🔄 **Step 1: Refresh Your Browser**

1. Go to your admin panel: `http://127.0.0.1:8000/admin/`
2. **Press Ctrl + F5** (hard refresh) to clear cache
3. Or close browser and reopen

---

## 📝 **Step 2: Create a PURCHASE Transaction**

### Go to Add Transaction:
1. Click **"Transactions"** under INVENTORY
2. Click **"ADD TRANSACTION +"** button

### You Should Now See This Form:

```
TRANSACTION DETAILS
─────────────────────────────────────
Item: [Dropdown - Select an item]
Transaction type: [Dropdown - Select "Purchase"]
Quantity: [Number field]
Unit price: [Number field]

SUPPLIER/CUSTOMER INFORMATION ⭐ NEW!
─────────────────────────────────────
For PURCHASE: select Supplier. For SALE: select Customer.

Supplier: [Dropdown - Select supplier] ⭐
Customer: [Dropdown - Select customer] ⭐

PAYMENT INFORMATION
─────────────────────────────────────
Payment status: [Dropdown]
Payment method: [Dropdown]
Payment reference: [Text field]

ADDITIONAL INFORMATION
─────────────────────────────────────
Performed by: [Dropdown]
Notes: [Text area]
```

### Fill in the Form:
1. **Item:** Select "Laptop" (or any item)
2. **Transaction type:** Select **"Purchase"**
3. **Quantity:** 10
4. **Unit price:** 50000
5. **Supplier:** Select **"CG Electronics Nepal"** ⭐
6. **Customer:** Leave blank (not needed for purchase)
7. **Payment status:** PAID
8. **Payment method:** CASH
9. **Performed by:** Select your username
10. Click **"SAVE"**

---

## 📝 **Step 3: Create a SALE Transaction**

### Add Another Transaction:
1. Click **"ADD TRANSACTION +"** again

### Fill in the Form:
1. **Item:** Select "Laptop"
2. **Transaction type:** Select **"Sale"**
3. **Quantity:** 2
4. **Unit price:** 60000
5. **Supplier:** Leave blank (not needed for sale)
6. **Customer:** Select **"Herald College Kathmandu"** ⭐
7. **Payment status:** PAID
8. **Payment method:** CASH
9. **Performed by:** Select your username
10. Click **"SAVE"**

---

## ✅ **Step 4: Verify It's Working**

### Check Transaction List:
1. Go to **"Transactions"** list in admin
2. You should see a new column: **"Supplier/Customer"**
3. Your PURCHASE should show: "Supplier: CG Electronics Nepal"
4. Your SALE should show: "Customer: Herald College Kathmandu"

### Check Transaction Details:
1. Click on any transaction
2. Scroll to **"Supplier/Customer Information"** section
3. You should see the supplier or customer you selected

---

## 🎯 **What You Should See:**

### Transaction List View:
```
TRANSACTIONS
─────────────────────────────────────────────────────────────────
Item      | Type     | Qty | Amount    | User  | Date       | Supplier/Customer
Laptop    | Purchase | 10  | 500,000   | admin | 2026-02-28 | Supplier: CG Electronics Nepal
Laptop    | Sale     | 2   | 120,000   | admin | 2026-02-28 | Customer: Herald College Kathmandu
```

### Transaction Detail View:
```
TRANSACTION #123
─────────────────────────────────────
TRANSACTION DETAILS
Item: Laptop
Transaction type: Purchase
Quantity: 10
Unit price: Rs. 50,000

SUPPLIER/CUSTOMER INFORMATION
Supplier: CG Electronics Nepal ✅
Customer: (blank)

PAYMENT INFORMATION
Payment status: PAID
Payment method: CASH
```

---

## 🐛 **If You Still Don't See the Fields:**

### Option 1: Restart Django Server
```bash
# Stop server (Ctrl+C in terminal)
# Start again
python manage.py runserver
```

### Option 2: Clear Browser Cache
1. Press **Ctrl + Shift + Delete**
2. Clear cache
3. Refresh page

### Option 3: Check in Django Shell
```bash
python manage.py shell
```

```python
from inventory.models import Transaction

# Check if fields exist
t = Transaction.objects.first()
print(hasattr(t, 'supplier'))  # Should be True
print(hasattr(t, 'customer'))  # Should be True
```

---

## 📊 **Business Logic:**

### PURCHASE Transactions:
- ✅ Select **Supplier**
- ❌ Leave **Customer** blank
- Example: "Buying 10 laptops from CG Electronics"

### SALE Transactions:
- ❌ Leave **Supplier** blank
- ✅ Select **Customer**
- Example: "Selling 2 laptops to Herald College"

---

## 🎬 **For Your Demo:**

### Show Your Supervisor:
1. **Create a PURCHASE** with supplier
2. **Create a SALE** with customer
3. **Show transaction list** with supplier/customer column
4. **Explain:** "When we buy, we track the supplier. When we sell, we track the customer."

### Sample Transactions to Create:

**Purchase Examples:**
1. Buy 50 books from "Ratna Pustak Bhandar"
2. Buy 20 chairs from "Nepal Furniture House"
3. Buy 100 bottles from "Kathmandu Beverages"

**Sale Examples:**
1. Sell 10 books to "Herald College Kathmandu"
2. Sell 5 chairs to "Budhanilkantha School Library"
3. Sell 20 bottles to "Himalayan Java Cafe"

---

## ✅ **Success Checklist:**

- [ ] Refreshed admin panel
- [ ] Can see "Supplier/Customer Information" section
- [ ] Supplier dropdown shows all 6 suppliers
- [ ] Customer dropdown shows all 6 customers
- [ ] Created PURCHASE with supplier
- [ ] Created SALE with customer
- [ ] Transaction list shows supplier/customer
- [ ] Transaction detail shows supplier/customer

---

**Try it now and let me know if you see the fields!** 🎉
