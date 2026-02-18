"""
Script to fetch images for existing items that don't have images
Run this once to populate images for all existing inventory items
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
django.setup()

from inventory.models import Item

print("=" * 70)
print("FETCHING IMAGES FOR EXISTING ITEMS")
print("=" * 70)

# Get all items without images
items_without_images = [item for item in Item.objects.all() if not item.image]

print(f"\nFound {len(items_without_images)} items without images")

if len(items_without_images) == 0:
    print("\n✓ All items already have images!")
else:
    print("\nFetching images...")
    
    success_count = 0
    failed_count = 0
    
    for i, item in enumerate(items_without_images, 1):
        print(f"\n[{i}/{len(items_without_images)}] Processing: {item.name}")
        
        try:
            # Save the item - this triggers automatic image fetching
            item.save()
            
            # Check if image was fetched
            if item.image:
                print(f"    ✓ Image fetched successfully")
                print(f"    ✓ Saved to: {item.image.name}")
                success_count += 1
            else:
                print(f"    ✗ Failed to fetch image")
                failed_count += 1
                
        except Exception as e:
            print(f"    ✗ Error: {e}")
            failed_count += 1
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total items processed: {len(items_without_images)}")
    print(f"✓ Successfully fetched: {success_count}")
    print(f"✗ Failed: {failed_count}")
    print("=" * 70)
