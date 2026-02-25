# Get Unsplash API Key - Quick Guide (5 Minutes)

## Why You Need This

Without Unsplash API key:
- ❌ System uses Lorem Picsum (random photos)
- ❌ "Heater" → random nature picture
- ❌ No product relevance

With Unsplash API key:
- ✅ System uses smart search
- ✅ "Heater" → actual heater product photo
- ✅ Catalog-style images

---

## Step-by-Step (5 Minutes)

### Step 1: Sign Up (2 minutes)

1. Go to: **https://unsplash.com/**
2. Click **"Join"** (top right)
3. Sign up with:
   - Email
   - Or Google account
   - Or GitHub account
4. Verify your email

### Step 2: Register as Developer (1 minute)

1. Go to: **https://unsplash.com/developers**
2. Click **"Register as a Developer"**
3. Accept the API Terms
4. Click **"Accept"**

### Step 3: Create Application (1 minute)

1. Click **"New Application"**
2. Fill in the form:
   - **Application name**: `Django Inventory System`
   - **Description**: `Academic FYP project for inventory management with automatic product image fetching`
   - Check all the guideline boxes
3. Click **"Create Application"**

### Step 4: Get Your Keys (30 seconds)

1. You'll see your application dashboard
2. Find **"Access Key"** (looks like a long string)
3. Copy it (click the copy icon)

Example: `abc123xyz456def789ghi012jkl345mno678pqr901stu234`

### Step 5: Update Django Settings (30 seconds)

1. Open: `inventory_system/settings.py`
2. Find this line:
   ```python
   UNSPLASH_ACCESS_KEY = 'YOUR_UNSPLASH_ACCESS_KEY_HERE'
   ```
3. Replace with your key:
   ```python
   UNSPLASH_ACCESS_KEY = 'abc123xyz456def789ghi012jkl345mno678pqr901stu234'
   ```
4. Save the file

### Step 6: Restart Server (10 seconds)

```bash
# Stop server (Ctrl+C)
# Start again
python manage.py runserver
```

---

## Test It

1. **Delete the "heater" item** (or any item with random image)
2. **Create new item**: "Heater"
3. **Don't upload image**
4. **Click "Add Item"**
5. ✅ **Result**: Actual heater product photo!

---

## What You'll Get

### Before (Lorem Picsum):
- "Heater" → Random nature photo
- "Laptop" → Random building photo
- "Chair" → Random person photo

### After (Unsplash with smart search):
- "Heater" → Actual heater product photo
- "Laptop" → Clean laptop on white background
- "Chair" → Catalog-style chair photo

---

## API Limits (Free Tier)

- **50 requests per hour** (plenty for testing)
- **50,000 requests per month** (more than enough)
- Perfect for academic projects

---

## Troubleshooting

### Can't find "Access Key"?
- Look for "Keys" section in your application dashboard
- Should be labeled "Access Key" or "Application ID"

### Key not working?
- Make sure you copied the entire key (no spaces)
- Check you're using "Access Key" not "Secret Key"
- Restart Django server after updating settings

### Still getting random images?
- Check settings.py was saved
- Verify key is in quotes: `'your_key_here'`
- Restart server
- Check server logs for errors

---

## For Your FYP

With Unsplash API:
- ✅ Professional product images
- ✅ Catalog-style presentation
- ✅ Demonstrates API integration
- ✅ Shows smart search implementation
- ✅ Better for supervisor demo

**Takes 5 minutes, makes huge difference in presentation!**
