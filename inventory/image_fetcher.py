"""
Automatic Product Image Fetcher
================================

This module provides functionality to automatically fetch product images
from Unsplash API when no image is manually uploaded by the user.

Academic Note (for FYP/Viva):
- Uses Unsplash API (free, public image service)
- Implements proper error handling for API failures
- Downloads and saves images to Django media directory
- Maintains system stability even if API is unavailable
"""

import requests
import os
from django.conf import settings
from django.core.files.base import ContentFile
from urllib.parse import quote
import logging

# Setup logging for debugging and error tracking
logger = logging.getLogger(__name__)


class ProductImageFetcher:
    """
    Handles automatic fetching of product images from Unsplash API
    
    How it works:
    1. Takes product name as search query
    2. Calls Unsplash API to search for relevant images
    3. Downloads the first matching image
    4. Saves it to media/products/ directory
    5. Returns the saved file for Django ImageField
    """
    
    def __init__(self):
        """Initialize with API credentials from settings"""
        self.access_key = settings.UNSPLASH_ACCESS_KEY
        self.api_url = settings.UNSPLASH_API_URL
        self.timeout = 10  # API request timeout in seconds
    
    def fetch_product_image(self, product_name):
        """
        Fetch a product image based on product name
        
        Args:
            product_name (str): Name of the product to search for
            
        Returns:
            ContentFile: Django file object ready to save to ImageField
            None: If fetching fails or API is unavailable
            
        Academic Explanation:
        - Uses HTTP GET request to Unsplash API
        - Searches for images matching product name
        - Downloads image in small size (400x300) to save bandwidth
        - Converts to Django ContentFile for database storage
        """
        
        # Check if API key is configured
        if not self.access_key or self.access_key == 'YOUR_UNSPLASH_ACCESS_KEY_HERE':
            logger.warning("Unsplash API key not configured. Skipping automatic image fetch.")
            return None
        
        try:
            # Step 1: Search for images using Unsplash API
            logger.info(f"Fetching image for product: {product_name}")
            
            # Prepare API request parameters
            params = {
                'query': product_name,
                'per_page': 1,  # We only need one image
                'orientation': 'squarish',  # Square images work best for products
                'client_id': self.access_key
            }
            
            # Make API request with timeout
            response = requests.get(
                self.api_url,
                params=params,
                timeout=self.timeout
            )
            
            # Check if API request was successful
            if response.status_code != 200:
                logger.error(f"Unsplash API error: {response.status_code}")
                return None
            
            # Parse JSON response
            data = response.json()
            
            # Check if any images were found
            if not data.get('results') or len(data['results']) == 0:
                logger.warning(f"No images found for: {product_name}")
                return None
            
            # Step 2: Get the first image URL
            first_image = data['results'][0]
            # Use 'small' size (400x300) - good balance between quality and file size
            image_url = first_image['urls']['small']
            
            logger.info(f"Found image URL: {image_url}")
            
            # Step 3: Download the image
            image_response = requests.get(image_url, timeout=self.timeout)
            
            if image_response.status_code != 200:
                logger.error(f"Failed to download image: {image_response.status_code}")
                return None
            
            # Step 4: Create Django ContentFile from downloaded image
            # This allows us to save it directly to ImageField
            image_content = ContentFile(image_response.content)
            
            # Generate a clean filename from product name
            # Example: "Wireless Mouse" -> "wireless_mouse.jpg"
            filename = self._generate_filename(product_name)
            
            logger.info(f"Successfully fetched image: {filename}")
            return image_content, filename
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while fetching image for: {product_name}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while fetching image: {str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error while fetching image: {str(e)}")
            return None
    
    def _generate_filename(self, product_name):
        """
        Generate a clean filename from product name
        
        Args:
            product_name (str): Original product name
            
        Returns:
            str: Clean filename suitable for file system
            
        Example:
            "Wireless Mouse" -> "wireless_mouse.jpg"
            "HP Laptop 15.6\"" -> "hp_laptop_156.jpg"
        """
        # Convert to lowercase and replace spaces with underscores
        clean_name = product_name.lower().replace(' ', '_')
        
        # Remove special characters
        clean_name = ''.join(c for c in clean_name if c.isalnum() or c == '_')
        
        # Limit length to 50 characters
        clean_name = clean_name[:50]
        
        # Add .jpg extension
        return f"{clean_name}.jpg"


# Create a singleton instance for easy import
image_fetcher = ProductImageFetcher()


def fetch_and_save_product_image(item, product_name):
    """
    Convenience function to fetch and save image to an Item instance
    
    Args:
        item: Django Item model instance
        product_name (str): Name of the product
        
    Returns:
        bool: True if image was fetched and saved, False otherwise
        
    Usage in views:
        if not item.image:
            fetch_and_save_product_image(item, item.name)
    """
    try:
        result = image_fetcher.fetch_product_image(product_name)
        
        if result:
            image_content, filename = result
            # Save to ImageField
            item.image.save(filename, image_content, save=True)
            logger.info(f"Image saved for product: {product_name}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error saving fetched image: {str(e)}")
        return False
