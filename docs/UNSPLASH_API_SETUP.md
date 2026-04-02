# Automatic Product Image Fetching - Setup Guide

## ✅ SYSTEM STATUS: FULLY WORKING

The automatic image fetching feature is now fully functional and tested!

- ✅ All existing items have images
- ✅ New items automatically get images
- ✅ Lorem Picsum fallback working perfectly
- ✅ No API key required for basic functionality

## What is Automatic Image Fetching?

When you add a new product without uploading an image, the system automatically downloads a placeholder image. You can optionally upgrade to Unsplash API for more relevant product images.

## Current Implementation

### Working Features
1. **Lorem Picsum Integration** (No API key needed)
   - Automatically fetches placeholder images
   - 400x400 high-quality photos
   - Always available, no rate limits
   - Perfect for academic projects

2. **Unsplash API** (Optional upgrade)
   - More relevant product images
   - Requires free API key
   - 50 requests/hour limit
   - Falls back to Lorem Picsum if fails

### How It Works Right Now

```
User adds product without image
         ↓
System creates product in database
         ↓
System tries Unsplash (if configured)
         ↓ (if no API key or fails)
System fetches from Lorem Picsum
         ↓
Image downloaded and saved
         ↓
Product now has image!
```

## Optional: Upgrade to Unsplash API (Better Images)

If you want more relevant product images instead of random placeholders, follow these steps:

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

### Current Status: Already Working!

All your existing inventory items now have images. Try adding a new item:

### Test 1: Add Product Without Image (Using Lorem Picsum)
1. Go to Inventory → Add New Item
2. Enter product name: "Laptop"
3. Fill in other details
4. **Do NOT upload an image**
5. Click "Add Item"
6. ✅ System will automatically fetch a placeholder image from Lorem Picsum!

### Test 2: Add Product With Unsplash (If API Key Configured)

1. Configure Unsplash API key (see above)
2. Add product: "Wireless Mouse"
3. System will fetch relevant mouse image from Unsplash
4. If Unsplash fails, falls back to Lorem Picsum

### Test 3: Add Product With Manual Image
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

1. **No API Key**: Uses Lorem Picsum (working now!)
2. **API Down**: Falls back to Lorem Picsum
3. **No Internet**: Uses SVG placeholder
4. **No Matching Image**: Uses Lorem Picsum

**Your inventory system continues working normally!**

## Maintenance Scripts

### Fetch Images for Existing Items

If you add items manually to the database or want to refresh images:

```bash
python fetch_missing_images.py
```

This script:
- Finds all items without images
- Automatically fetches images for each
- Shows progress and summary
- Already run once (all items have images now!)

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
