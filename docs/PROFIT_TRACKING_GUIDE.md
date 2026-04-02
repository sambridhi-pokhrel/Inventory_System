# Profit Tracking - Quick Reference

## Where to See Profit Information

### 1. Inventory List Page (`/inventory/`)
- **Profit/Unit Column**: Shows profit per unit for each item
  - Green arrow (↑) = Positive profit
  - Red arrow (↓) = Loss
  - Displays: Selling price - Cost price
- **Cost Price**: Shown below profit amount in small text

### 2. Transaction List Page (`/inventory/transactions/`)
- **Total Profit Card**: Summary card showing total profit from all paid sales
  - Located in the top statistics row
  - Shows cumulative profit from all completed sales
- **Profit Column**: In the transactions table
  - Shows profit for each SALE transaction
  - Shows "-" for PURCHASE transactions (no profit)

### 3. Transaction Detail Page (`/inventory/transaction/<id>/`)
- **Profit Section**: For SALE transactions only
  - Shows total profit for that transaction
  - Shows profit per unit
  - Located in the right column under "Total Amount"

## How Profit is Calculated

```
Profit per Unit = Selling Price - Cost Price
Total Profit (for sale) = Profit per Unit × Quantity
```

## Setting Cost Price

You can set the cost price for items in two ways:

1. **Admin Panel** (`/admin/inventory/item/`)
   - Edit any item
   - Set "Cost price" field in "Item Information" section

2. **When Creating Items**
   - The cost_price field is available when adding new items
   - Default is Rs. 0.00

## Example

If you have:
- Item: Laptop
- Selling Price: Rs. 50,000
- Cost Price: Rs. 40,000
- Quantity Sold: 5 units

Then:
- Profit per Unit: Rs. 10,000
- Total Profit: Rs. 50,000

## Notes

- Profit is only calculated for SALE transactions
- PURCHASE transactions show "-" in profit column
- Total profit only includes PAID sales (not pending)
- All amounts are in Nepali Rupees (Rs.)
