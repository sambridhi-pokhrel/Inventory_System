# Unsplash API Setup Guide

## What is Automatic Image Fetching?

When you add a new product without uploading an image, the system automatically searches for and downloads a relevant product image from Unsplash (a free stock photo service).

## How to Get Your Free Unsplash API Key

### Step 1: Create Unsplash Account
1. Go to: https://unsplash.com/
2. Click "Join" or "Sign up"
3. Create a free account (use your email)

### Step 2: Register as Developer
1. Go to: https://unsplash.com/developers
2. Click "Register as a Developer"
3. Accept the API Terms

### Step 3: Create New Application
1. Click "New Application"
2. Fill in the form:
   - **Application name**: Django Inventory System
   - **Description**: Academic FYP project for inventory management
   - Check all the guidelines boxes
3. Click "Create Application"

### Step 4: Get Your Access Key
1. You'll see your application dashboard
2. Find "Access Key" (looks like: `abc123xyz456...`)
3. Copy this key

### Step 5: Configure in Django

Open `inventory_system/settings.py` and replace:

```python
UNSPLASH_ACCESS_KEY = 'YOUR_UNSPLASH_ACCESS_KEY_HERE'
```

With your actual key:

```python
UNSPLASH_ACCESS_KEY = 'abc123xyz456...'  # Your actual key here
```

## Testing the Feature

### Test 1: Add Product Without Image
1. Go to Inventory → Add New Item
2. Enter product name: "Laptop"
3. Fill in other details
4. **Do NOT upload an image**
5. Click "Add Item"
6. System will automatically fetch a laptop image!

### Test 2: Add Product With Manual Image
1. Go to Inventory → Add New Item
2. Enter product name: "Mouse"
3. Upload your own image
4. Click "Add Item"
5. System will use YOUR image (not auto-fetch)

## How It Works (For Viva/Presentation)

```
User adds product without image
         ↓
System creates product in database
         ↓
System calls Unsplash API
         ↓
API searches for product name
         ↓
System downloads first matching image
         ↓
Image saved to media/products/
         ↓
Product now has image!
```

## API Limits (Free Tier)

- **50 requests per hour**
- **50,000 requests per month**
- More than enough for academic projects!

## What If API Fails?

The system is designed to handle failures gracefully:

1. **No API Key**: Uses placeholder image
2. **API Down**: Uses placeholder image
3. **No Internet**: Uses placeholder image
4. **No Matching Image**: Uses placeholder image

**Your inventory system continues working normally!**

## For Academic Presentation

### Key Points to Mention:

1. **Automatic Enhancement**: System automatically improves user experience
2. **Graceful Degradation**: Works even when API is unavailable
3. **User Priority**: Manual uploads always take precedence
4. **Error Handling**: Comprehensive try-catch blocks
5. **Logging**: All API calls are logged for debugging
6. **Performance**: Images cached locally (not fetched every time)

### Technical Implementation:

- **Library**: Python `requests` for HTTP calls
- **API**: Unsplash REST API (industry standard)
- **Storage**: Django media files system
- **Error Handling**: Try-except with logging
- **Timeout**: 10 seconds (prevents hanging)

## Troubleshooting

### Problem: "Auto-fetch unavailable"
**Solution**: Check if API key is configured in settings.py

### Problem: "Image auto-fetch failed"
**Solution**: 
1. Check internet connection
2. Verify API key is correct
3. Check API rate limits (50/hour)

### Problem: Wrong image fetched
**Solution**: Use more specific product names
- Bad: "Item"
- Good: "Wireless Mouse"
- Better: "Logitech Wireless Mouse"

## Alternative: Using Demo Mode

If you don't want to set up API key, the system works fine with placeholder images. Just leave the setting as:

```python
UNSPLASH_ACCESS_KEY = 'YOUR_UNSPLASH_ACCESS_KEY_HERE'
```

## Security Notes

- **Never commit API keys to Git**: Add to .gitignore
- **Use environment variables in production**: `os.getenv('UNSPLASH_KEY')`
- **API key is read-only**: Cannot modify your Unsplash account

## For Production Deployment

In production, use environment variables:

```python
import os
UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY', 'YOUR_UNSPLASH_ACCESS_KEY_HERE')
```

Then set environment variable on server:
```bash
export UNSPLASH_ACCESS_KEY="your_actual_key"
```

---

**That's it!** Your inventory system now has automatic product image fetching. 🎉
