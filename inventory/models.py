from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.files.base import ContentFile
import requests
import logging

# Setup logging for debugging
logger = logging.getLogger(__name__)

class Item(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    reorder_level = models.IntegerField(default=10, help_text="Minimum stock level before reorder suggestion")
    lead_time_days = models.IntegerField(default=7, help_text="Days required to restock this item")
    # Product image field - stores uploaded images in media/products/ directory
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        help_text="Upload product image (optional)"
    )

    def __str__(self):
        return self.name
    
    def get_image_url(self):
        """Return image URL or placeholder if no image exists"""
        if self.image:
            return self.image.url
        # Return placeholder image URL
        return '/static/images/no-image-placeholder.svg'
    
    def _fetch_product_image(self):
        """
        Automatically fetch product image from Unsplash API or Lorem Picsum
        
        Academic Explanation (for Viva):
        =====================================
        This method implements intelligent automatic image fetching with improved
        relevance and accuracy for product inventory systems.
        
        Image Fetching Strategy (Priority Order):
        1. Unsplash API (if configured) - High-quality, relevant product images
        2. Lorem Picsum (always available) - Consistent placeholder images
        3. SVG Placeholder (built-in) - Fallback if all else fails
        
        Unsplash Search Optimization:
        - Uses refined search queries with contextual keywords
        - Keywords: "product", "isolated", "white background", "catalog"
        - Filters results by orientation (square/landscape only)
        - Avoids unrelated categories (nature, people, abstract)
        - Multiple query variations for better success rate
        - Content filtering to ensure appropriate images
        
        Why This Improves Relevance:
        - Simple query "Laptop" → may return scenic laptop photos
        - Refined query "Laptop product isolated white background" → catalog-style product photo
        - Result: Clean, professional product images suitable for inventory
        
        Lorem Picsum Enhancement:
        - Uses 'seed' parameter for consistency
        - Same product name → same placeholder image
        - Prevents random image changes on page refresh
        - Professional photography suitable for placeholders
        
        Error Handling (Graceful Degradation):
        - If API key not configured → Skip Unsplash, use Lorem Picsum
        - If API request fails → Try Lorem Picsum
        - If no images found → Try Lorem Picsum
        - If download fails → Return None (uses SVG placeholder)
        - System never breaks due to image fetching
        
        Manual Upload Priority:
        - Manual uploads ALWAYS take precedence
        - Auto-fetch only happens when image field is empty
        - Users can replace auto-fetched images anytime
        
        This ensures:
        - Better visual consistency across inventory
        - More relevant product images
        - Professional catalog appearance
        - Stable system operation
        - Good user experience
        """
        from django.conf import settings
        
        # Check if Unsplash API is configured
        api_key = getattr(settings, 'UNSPLASH_ACCESS_KEY', None)
        use_unsplash = api_key and api_key != 'YOUR_UNSPLASH_ACCESS_KEY_HERE'
        
        try:
            if use_unsplash:
                # Try Unsplash API first (if configured)
                # Uses improved search queries for better product image relevance
                logger.info(f"Attempting Unsplash API with refined search for: {self.name}")
                result = self._fetch_from_unsplash(api_key)
                if result:
                    logger.info(f"Successfully fetched relevant product image from Unsplash")
                    return result
                logger.info("Unsplash search completed, falling back to Lorem Picsum")
            
            # Fallback to Lorem Picsum (no API key needed)
            # Uses seed parameter for consistent placeholders
            logger.info(f"Fetching consistent placeholder image for: {self.name}")
            return self._fetch_from_lorem_picsum()
            
        except Exception as e:
            logger.error(f"Error fetching image: {str(e)}")
            return None
    
    def _fetch_from_unsplash(self, api_key):
        """
        Fetch product image from Unsplash API with improved search relevance
        
        Academic Explanation (for Viva):
        =====================================
        This method uses advanced search query construction to fetch more relevant
        product images instead of random or artistic photos.
        
        Search Query Optimization:
        - Combines product name with contextual keywords
        - Keywords: "product", "isolated", "white background", "catalog"
        - These terms help Unsplash return product-style images
        - Filters out artistic, environmental, or unrelated photos
        
        Orientation Filtering:
        - Restricts to 'landscape' or 'squarish' orientations
        - Avoids portrait images which don't fit product displays
        - Ensures consistent visual presentation
        
        Content Type Filtering:
        - Prioritizes 'photo' content type
        - Avoids illustrations or graphics
        - Ensures professional product photography
        
        Why This Improves Relevance:
        - "product" keyword → focuses on commercial product photography
        - "isolated" keyword → prefers clean, isolated product shots
        - "white background" → matches e-commerce catalog style
        - "catalog" keyword → targets inventory-style images
        
        Example Queries:
        - Input: "Laptop"
        - Generated: "Laptop product isolated white background"
        - Result: Clean laptop photo on white background (catalog-style)
        
        Fallback Strategy:
        - If refined query returns no results, tries simple product name
        - If still no results, falls back to Lorem Picsum
        - System never breaks due to image fetching
        """
        try:
            from django.conf import settings
            api_url = getattr(settings, 'UNSPLASH_API_URL', 'https://api.unsplash.com/search/photos')
            
            # Construct refined search query for better product image relevance
            # Combine product name with contextual keywords that indicate product photography
            refined_query = f"{self.name} product isolated white background catalog"
            
            # Alternative query variations for better results
            # Try multiple query strategies to maximize relevance
            query_variations = [
                f"{self.name} product photo isolated",  # Primary: product-focused
                f"{self.name} product white background",  # Secondary: catalog-style
                f"{self.name} commercial product",       # Tertiary: commercial photography
                self.name                                 # Fallback: simple name
            ]
            
            for query_attempt, search_query in enumerate(query_variations, 1):
                logger.info(f"Unsplash search attempt {query_attempt}: '{search_query}'")
                
                params = {
                    'query': search_query,
                    'per_page': 3,  # Get top 3 results for better selection
                    'orientation': 'squarish',  # Square/landscape only (no portraits)
                    'content_filter': 'high',   # Filter out inappropriate content
                    'client_id': api_key
                }
                
                response = requests.get(api_url, params=params, timeout=10)
                
                if response.status_code != 200:
                    logger.warning(f"Unsplash API returned status {response.status_code}")
                    continue  # Try next query variation
                
                data = response.json()
                
                if not data.get('results') or len(data['results']) == 0:
                    logger.info(f"No images found for query: '{search_query}'")
                    continue  # Try next query variation
                
                # Filter results to find most relevant product image
                # Prioritize images with product-related keywords in description
                best_image = None
                for image in data['results']:
                    # Check image description and alt text for product-related terms
                    description = (image.get('description') or '').lower()
                    alt_description = (image.get('alt_description') or '').lower()
                    
                    # Product-related keywords that indicate good product photos
                    product_keywords = ['product', 'isolated', 'white', 'background', 
                                       'catalog', 'commercial', 'studio', 'object']
                    
                    # Unrelated keywords to avoid (nature, people, abstract)
                    avoid_keywords = ['landscape', 'nature', 'person', 'people', 
                                     'sunset', 'sky', 'mountain', 'forest', 'beach']
                    
                    # Check if image description contains product keywords
                    has_product_keywords = any(keyword in description or keyword in alt_description 
                                              for keyword in product_keywords)
                    
                    # Check if image description contains keywords to avoid
                    has_avoid_keywords = any(keyword in description or keyword in alt_description 
                                            for keyword in avoid_keywords)
                    
                    # Select image if it has product keywords and no avoid keywords
                    if has_product_keywords and not has_avoid_keywords:
                        best_image = image
                        logger.info(f"Found relevant product image with keywords")
                        break
                
                # If no filtered image found, use first result
                if not best_image and data['results']:
                    best_image = data['results'][0]
                    logger.info(f"Using first result from query: '{search_query}'")
                
                if best_image:
                    # Use 'small' size for faster loading and reasonable quality
                    image_url = best_image['urls']['small']
                    
                    logger.info(f"Selected Unsplash image: {image_url}")
                    logger.info(f"Image description: {best_image.get('alt_description', 'N/A')}")
                    
                    # Download the image
                    image_response = requests.get(image_url, timeout=10)
                    
                    if image_response.status_code != 200:
                        logger.warning(f"Failed to download image from: {image_url}")
                        continue  # Try next query variation
                    
                    # Generate clean filename
                    clean_name = self.name.lower().replace(' ', '_')
                    clean_name = ''.join(c for c in clean_name if c.isalnum() or c == '_')
                    clean_name = clean_name[:50]
                    filename = f"{clean_name}_unsplash.jpg"
                    
                    image_content = ContentFile(image_response.content)
                    
                    logger.info(f"Successfully fetched product image for: {self.name}")
                    return image_content, filename
            
            # All query variations failed
            logger.info(f"All Unsplash query variations failed for: {self.name}")
            return None
            
        except Exception as e:
            logger.warning(f"Unsplash fetch failed: {str(e)}")
            return None
    
    def _fetch_from_lorem_picsum(self):
        """
        Fetch placeholder image from Lorem Picsum (no API key needed)
        
        Academic Explanation (for Viva):
        =====================================
        Lorem Picsum provides free placeholder images without authentication.
        This serves as a reliable fallback when Unsplash is unavailable.
        
        Why Lorem Picsum:
        - No API key required (always accessible)
        - Free and unlimited usage
        - Reliable uptime
        - Consistent image quality
        - Good for development and testing
        
        Image Specifications:
        - Size: 400x400 pixels (square format)
        - Format: JPEG (good compression, small file size)
        - Quality: High-resolution photos
        - Content: Random but professional photography
        
        Fallback Strategy:
        - If Unsplash fails or is not configured → Use Lorem Picsum
        - If Lorem Picsum fails → Return None (uses SVG placeholder)
        - System remains stable in all scenarios
        
        URL Format: https://picsum.photos/400/400
        - Returns a random high-quality photo
        - Different image each time (adds variety)
        - Cached by browser for performance
        
        Alternative Placeholder Services (for reference):
        - Placeholder.com: https://via.placeholder.com/400
        - DummyImage: https://dummyimage.com/400x400
        - Lorem Picsum: https://picsum.photos/400/400 (chosen for quality)
        
        Why 400x400:
        - Square format fits product displays
        - Good balance between quality and file size
        - Consistent with thumbnail requirements
        - Scales well for different screen sizes
        """
        try:
            # Lorem Picsum URL for 400x400 square image
            # Using 'seed' parameter with product name for consistency
            # Same product name will get same placeholder image
            clean_name = self.name.lower().replace(' ', '')
            clean_name = ''.join(c for c in clean_name if c.isalnum())
            
            # Use seed for consistent placeholder per product
            # This ensures the same product always gets the same placeholder
            image_url = f'https://picsum.photos/seed/{clean_name}/400/400'
            
            logger.info(f"Fetching Lorem Picsum placeholder for: {self.name}")
            
            # Download the image
            response = requests.get(image_url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Lorem Picsum returned status {response.status_code}")
                return None
            
            # Generate filename
            clean_name = self.name.lower().replace(' ', '_')
            clean_name = ''.join(c for c in clean_name if c.isalnum() or c == '_')
            clean_name = clean_name[:50]
            filename = f"{clean_name}_placeholder.jpg"
            
            # Create ContentFile
            image_content = ContentFile(response.content)
            
            logger.info(f"Successfully fetched placeholder for: {self.name}")
            return image_content, filename
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout while fetching placeholder for: {self.name}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error while fetching placeholder: {str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error while fetching placeholder: {str(e)}")
            return None
    
    def save(self, *args, **kwargs):
        """
        Override save method to automatically fetch product image
        
        Academic Explanation (for Viva):
        =====================================
        This is a Django model override that adds custom logic before saving.
        
        Logic Flow:
        1. Check if this is a new item (pk is None) OR image field is empty
        2. If no image exists, attempt to fetch one automatically
        3. If fetch succeeds, assign the image to the ImageField
        4. If fetch fails, continue without image (uses placeholder in templates)
        5. Call parent save() to complete the database operation
        
        Key Points:
        - Manual uploads are ALWAYS prioritized (checked first)
        - Auto-fetch only happens when image field is empty
        - System never breaks if API fails (graceful degradation)
        - Works for both new items and updates
        
        Why in save() method?
        - Centralized logic (works everywhere Item is saved)
        - Automatic (no need to remember to call it)
        - Clean code (separation of concerns)
        - Django best practice (model handles its own data)
        """
        
        # Check if image field is empty (no manual upload)
        # Note: We check if the field has no file, not just if it's None
        if not self.image or not self.image.name:
            logger.info(f"No image provided for '{self.name}'. Attempting auto-fetch...")
            
            # Attempt to fetch image from Unsplash API
            result = self._fetch_product_image()
            
            if result:
                # Successfully fetched image
                image_content, filename = result
                
                # Save the fetched image to the ImageField
                # save=False prevents recursive save() calls
                self.image.save(filename, image_content, save=False)
                logger.info(f"Auto-fetched image saved for: {self.name}")
            else:
                # Fetch failed - will use placeholder in templates
                logger.info(f"Using placeholder image for: {self.name}")
        else:
            # Manual image was uploaded - use it
            logger.info(f"Using manually uploaded image for: {self.name}")
        
        # Call parent save() to complete the database operation
        super().save(*args, **kwargs)
    
    @property
    def is_low_stock(self):
        """Returns True if quantity is at or below reorder level"""
        return self.quantity <= self.reorder_level
    
    @property
    def stock_status(self):
        """Returns stock status for display"""
        if self.quantity == 0:
            return "out-of-stock"
        elif self.quantity <= self.reorder_level:
            return "low-stock"
        else:
            return "in-stock"
    
    def get_average_daily_usage(self, days=30):
        """Calculate average daily usage based on sales transactions"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        sales = self.transactions.filter(
            transaction_type='SALE',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        total_sold = sum(sale.quantity for sale in sales)
        return total_sold / days if days > 0 else 0
    
    def get_predicted_stock_needed(self):
        """Predict stock needed for lead time period"""
        daily_usage = self.get_average_daily_usage()
        return daily_usage * self.lead_time_days
    
    @property
    def needs_reorder(self):
        """Check if item needs reordering using AI-based prediction"""
        try:
            # Import here to avoid circular imports
            from .ml_predictor import ml_predictor
            
            # Get AI-powered recommendation
            recommendation = ml_predictor.calculate_reorder_recommendation(self)
            return recommendation['needs_reorder']
            
        except Exception as e:
            # Fallback to basic logic if AI fails
            print(f"AI prediction failed for {self.name}: {e}")
            return self.quantity <= self.reorder_level or self.quantity == 0
    
    @property
    def ai_reorder_info(self):
        """Get detailed AI-based reorder information"""
        try:
            from .ml_predictor import ml_predictor
            return ml_predictor.calculate_reorder_recommendation(self)
        except Exception as e:
            return {
                'needs_reorder': self.quantity <= self.reorder_level,
                'ai_powered': False,
                'error': str(e)
            }
    
    def get_ai_demand_forecast(self, days=7):
        """Get AI-powered demand forecast"""
        try:
            from .ml_predictor import ml_predictor
            return ml_predictor.predict_future_demand(self, days)
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def train_ai_model(self):
        """Train AI model for this specific item"""
        try:
            from .ml_predictor import ml_predictor
            return ml_predictor.train_demand_model(self)
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @property
    def suggested_reorder_quantity(self):
        """Suggest reorder quantity"""
        if self.needs_reorder:
            predicted_needed = self.get_predicted_stock_needed()
            shortage = predicted_needed - self.quantity
            # Add 20% buffer
            return int(shortage * 1.2)
        return 0

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('SALE', 'Sale'),
        ('PURCHASE', 'Purchase'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('PAID', 'Paid'),
        ('PENDING', 'Pending'),
        ('FAILED', 'Failed'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('KHALTI', 'Khalti'),
        ('ESEWA', 'eSewa'),
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CREDIT', 'Credit'),
    ]
    
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='KHALTI')
    payment_reference = models.CharField(max_length=100, blank=True, null=True, help_text="Payment gateway reference ID")
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['transaction_type', 'timestamp']),
            models.Index(fields=['item', 'timestamp']),
            models.Index(fields=['payment_status']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.item.name} ({self.quantity}) - {self.payment_status}"
    
    def clean(self):
        """Validate transaction data"""
        if self.quantity <= 0:
            raise ValidationError("Quantity must be positive")
        
        if self.unit_price <= 0:
            raise ValidationError("Unit price must be positive")
        
        # Check stock availability for sales
        # Only validate stock when:
        # 1. Creating a new PAID transaction (Cash/Bank Transfer)
        # 2. Updating existing transaction from PENDING to PAID
        if self.transaction_type == 'SALE' and self.payment_status == 'PAID':
            # For new transactions, always validate
            if not self.pk:
                if self.item.quantity < self.quantity:
                    raise ValidationError(f"Insufficient stock. Available: {self.item.quantity}")
            else:
                # For existing transactions, only validate if status is changing to PAID
                try:
                    old_transaction = Transaction.objects.get(pk=self.pk)
                    # Only validate if status is changing from non-PAID to PAID
                    if old_transaction.payment_status != 'PAID':
                        if self.item.quantity < self.quantity:
                            raise ValidationError(
                                f"Insufficient stock to complete payment. "
                                f"Available: {self.item.quantity}, Required: {self.quantity}. "
                                f"Please reduce quantity or restock item."
                            )
                except Transaction.DoesNotExist:
                    pass
    
    def simulate_khalti_payment(self):
        """Simulate Khalti payment processing"""
        import uuid
        if self.payment_method == 'KHALTI':
            # Simulate payment processing
            self.payment_status = 'PAID'
            self.payment_reference = f"KHALTI_{uuid.uuid4().hex[:8].upper()}"
            self.save()
            return True
        return False
    
    def save(self, *args, **kwargs):
        # Calculate total amount - ensure both values are Decimal
        from decimal import Decimal
        self.total_amount = Decimal(str(self.quantity)) * Decimal(str(self.unit_price))
        
        # Validate before saving
        self.clean()
        
        # Check if this is an update (existing transaction) or new creation
        is_new = self.pk is None
        
        # For existing transactions, check if payment status changed to PAID
        if not is_new:
            try:
                old_transaction = Transaction.objects.get(pk=self.pk)
                status_changed_to_paid = (
                    old_transaction.payment_status != 'PAID' and 
                    self.payment_status == 'PAID'
                )
            except Transaction.DoesNotExist:
                status_changed_to_paid = False
        else:
            # For new transactions, check if status is PAID
            status_changed_to_paid = self.payment_status == 'PAID'
        
        # Use atomic transaction to ensure data consistency
        with transaction.atomic():
            # Only update stock when payment status becomes PAID
            if status_changed_to_paid:
                # Update item stock based on transaction type
                if self.transaction_type == 'SALE':
                    self.item.quantity -= self.quantity
                elif self.transaction_type == 'PURCHASE':
                    self.item.quantity += self.quantity
                
                # Ensure stock doesn't go negative
                if self.item.quantity < 0:
                    raise ValidationError("Stock cannot be negative")
                
                self.item.save()
            
            super().save(*args, **kwargs)
