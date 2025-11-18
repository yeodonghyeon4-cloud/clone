"""
Database Population Script for ZABATDA MVP.

This script populates the PostgreSQL database with products and their CLIP embeddings:
1. Loads product metadata from data/product_metadata.json
2. Generates 512-dimensional CLIP embeddings for each product image
3. Inserts products with embeddings into the Supabase database

Usage:
    python backend/populate_db.py              # Populate all products
    python backend/populate_db.py --clear      # Clear database first
    python backend/populate_db.py --dry-run    # Test without inserting

Author: ZABATDA Development Team
Last Updated: November 18, 2025
"""

import json
import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import insert_product, get_product_count, delete_all_products
from embedding_service import generate_embedding, generate_embeddings_batch


# Configuration
PRODUCT_METADATA_PATH = "data/product_metadata.json"
PRODUCT_IMAGES_DIR = "data/product_images"


def load_product_metadata(metadata_path: str) -> List[Dict[str, Any]]:
    """
    Load product metadata from JSON file.

    Expected JSON format:
    [
        {
            "id": "nike-001",
            "name": "Nike Air Force 1 White",
            "brand": "Nike",
            "price": 120000,
            "category": "shoes",
            "product_url": "https://example.com/product",
            "image_filename": "nike_airforce_white.jpg"
        },
        ...
    ]

    Args:
        metadata_path (str): Path to product_metadata.json

    Returns:
        list: List of product dictionaries

    Raises:
        FileNotFoundError: If metadata file doesn't exist
        json.JSONDecodeError: If JSON is invalid
        ValueError: If required fields are missing
    """
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(
            f"Product metadata file not found: {metadata_path}\n"
            f"Please create this file with product information."
        )

    with open(metadata_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    # Validate structure
    if not isinstance(products, list):
        raise ValueError("Product metadata must be a JSON array")

    # Validate required fields
    required_fields = ['id', 'name', 'brand', 'price', 'category', 'product_url', 'image_filename']
    for i, product in enumerate(products):
        missing_fields = [field for field in required_fields if field not in product]
        if missing_fields:
            raise ValueError(
                f"Product at index {i} is missing required fields: {', '.join(missing_fields)}"
            )

    print(f"✅ Loaded {len(products)} products from {metadata_path}")
    return products


def validate_product_images(products: List[Dict[str, Any]], images_dir: str) -> List[str]:
    """
    Validate that all product images exist.

    Args:
        products (list): List of product dictionaries
        images_dir (str): Directory containing product images

    Returns:
        list: List of missing image filenames

    Raises:
        FileNotFoundError: If images directory doesn't exist
    """
    if not os.path.exists(images_dir):
        raise FileNotFoundError(
            f"Product images directory not found: {images_dir}\n"
            f"Please create this directory and add product images."
        )

    missing_images = []
    for product in products:
        image_path = os.path.join(images_dir, product['image_filename'])
        if not os.path.exists(image_path):
            missing_images.append(product['image_filename'])

    if missing_images:
        print(f"⚠️  Warning: {len(missing_images)} product images are missing:")
        for img in missing_images[:5]:  # Show first 5
            print(f"   - {img}")
        if len(missing_images) > 5:
            print(f"   ... and {len(missing_images) - 5} more")

    return missing_images


def populate_database(
    products: List[Dict[str, Any]],
    images_dir: str,
    use_batch: bool = True,
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Populate database with products and their embeddings.

    Args:
        products (list): List of product dictionaries
        images_dir (str): Directory containing product images
        use_batch (bool): Use batch embedding generation (faster)
        dry_run (bool): If True, don't actually insert into database

    Returns:
        dict: Statistics about the operation (inserted, failed, skipped)
    """
    stats = {
        'inserted': 0,
        'failed': 0,
        'skipped': 0
    }

    print(f"\n{'='*60}")
    print(f"Starting database population...")
    print(f"Total products to process: {len(products)}")
    print(f"Batch mode: {use_batch}")
    print(f"Dry run: {dry_run}")
    print(f"{'='*60}\n")

    if use_batch:
        # Batch processing: faster for many products
        print("Using batch processing for faster embedding generation...")

        # Prepare image paths
        valid_products = []
        image_paths = []

        for product in products:
            image_path = os.path.join(images_dir, product['image_filename'])
            if os.path.exists(image_path):
                valid_products.append(product)
                image_paths.append(image_path)
            else:
                print(f"⚠️  Skipping {product['id']}: Image not found ({product['image_filename']})")
                stats['skipped'] += 1

        if not valid_products:
            print("❌ No valid products to process!")
            return stats

        # Generate embeddings in batch
        print(f"\n🔄 Generating embeddings for {len(valid_products)} products...")
        try:
            embeddings = generate_embeddings_batch(image_paths)
            print(f"✅ Generated {len(embeddings)} embeddings")
        except Exception as e:
            print(f"❌ Failed to generate batch embeddings: {e}")
            stats['failed'] = len(valid_products)
            return stats

        # Insert products with embeddings
        print(f"\n🔄 Inserting products into database...")
        for i, (product, embedding) in enumerate(zip(valid_products, embeddings), 1):
            try:
                if not dry_run:
                    # Build image URL (for now, use relative path - update later for actual hosting)
                    image_url = f"/static/product_images/{product['image_filename']}"

                    insert_product(
                        product_id=product['id'],
                        name=product['name'],
                        brand=product['brand'],
                        price=product['price'],
                        category=product['category'],
                        product_url=product['product_url'],
                        image_url=image_url,
                        embedding=embedding
                    )

                print(f"  [{i}/{len(valid_products)}] ✅ {product['id']}: {product['name']}")
                stats['inserted'] += 1

            except Exception as e:
                print(f"  [{i}/{len(valid_products)}] ❌ {product['id']}: {e}")
                stats['failed'] += 1

    else:
        # Sequential processing: one product at a time
        print("Using sequential processing...")

        for i, product in enumerate(products, 1):
            print(f"\n[{i}/{len(products)}] Processing: {product['id']}")

            # Check if image exists
            image_path = os.path.join(images_dir, product['image_filename'])
            if not os.path.exists(image_path):
                print(f"  ⚠️  Skipping: Image not found ({product['image_filename']})")
                stats['skipped'] += 1
                continue

            try:
                # Generate embedding
                print(f"  🔄 Generating embedding...")
                embedding = generate_embedding(image_path)
                print(f"  ✅ Embedding generated (512 dimensions)")

                # Insert into database
                if not dry_run:
                    print(f"  🔄 Inserting into database...")
                    image_url = f"/static/product_images/{product['image_filename']}"

                    insert_product(
                        product_id=product['id'],
                        name=product['name'],
                        brand=product['brand'],
                        price=product['price'],
                        category=product['category'],
                        product_url=product['product_url'],
                        image_url=image_url,
                        embedding=embedding
                    )
                    print(f"  ✅ Inserted successfully")

                stats['inserted'] += 1

            except Exception as e:
                print(f"  ❌ Failed: {e}")
                stats['failed'] += 1

    return stats


def print_summary(stats: Dict[str, int], dry_run: bool = False):
    """
    Print summary of database population results.

    Args:
        stats (dict): Statistics dictionary
        dry_run (bool): Whether this was a dry run
    """
    print(f"\n{'='*60}")
    print(f"Database Population {'Dry Run ' if dry_run else ''}Summary")
    print(f"{'='*60}")
    print(f"✅ Successfully inserted: {stats['inserted']}")
    print(f"❌ Failed: {stats['failed']}")
    print(f"⚠️  Skipped (missing images): {stats['skipped']}")
    print(f"{'='*60}")

    if not dry_run and stats['inserted'] > 0:
        try:
            total_count = get_product_count()
            print(f"\n📊 Total products in database: {total_count}")
        except Exception as e:
            print(f"\n⚠️  Could not get product count: {e}")


def main():
    """Main function to populate database with product data."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Populate ZABATDA database with products and embeddings'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear all existing products before populating'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test run without actually inserting into database'
    )
    parser.add_argument(
        '--sequential',
        action='store_true',
        help='Use sequential processing instead of batch (slower but more verbose)'
    )
    parser.add_argument(
        '--metadata',
        type=str,
        default=PRODUCT_METADATA_PATH,
        help=f'Path to product metadata JSON (default: {PRODUCT_METADATA_PATH})'
    )
    parser.add_argument(
        '--images',
        type=str,
        default=PRODUCT_IMAGES_DIR,
        help=f'Path to product images directory (default: {PRODUCT_IMAGES_DIR})'
    )

    args = parser.parse_args()

    print("""
╔═══════════════════════════════════════════════════════════╗
║          ZABATDA Database Population Script              ║
║   Populating database with products and CLIP embeddings  ║
╚═══════════════════════════════════════════════════════════╝
    """)

    try:
        # Clear database if requested
        if args.clear:
            if args.dry_run:
                print("🔄 [DRY RUN] Would clear all existing products from database\n")
            else:
                print("🔄 Clearing all existing products from database...")
                deleted_count = delete_all_products()
                print(f"✅ Deleted {deleted_count} existing products\n")

        # Load product metadata
        print("🔄 Loading product metadata...")
        products = load_product_metadata(args.metadata)

        # Validate product images
        print("\n🔄 Validating product images...")
        missing_images = validate_product_images(products, args.images)

        if missing_images:
            if len(missing_images) == len(products):
                print("\n❌ Error: No product images found!")
                print(f"Please add product images to: {args.images}/")
                sys.exit(1)
            else:
                response = input("\nSome images are missing. Continue anyway? (y/n): ")
                if response.lower() != 'y':
                    print("❌ Aborted by user")
                    sys.exit(0)

        # Populate database
        use_batch = not args.sequential
        stats = populate_database(
            products=products,
            images_dir=args.images,
            use_batch=use_batch,
            dry_run=args.dry_run
        )

        # Print summary
        print_summary(stats, dry_run=args.dry_run)

        # Exit with appropriate code
        if stats['failed'] > 0:
            sys.exit(1)
        else:
            print("\n🎉 Database population completed successfully!")
            sys.exit(0)

    except FileNotFoundError as e:
        print(f"\n❌ File Error: {e}")
        print("\nPlease ensure you have:")
        print(f"1. Created {args.metadata} with product information")
        print(f"2. Created {args.images}/ directory with product images")
        sys.exit(1)

    except ValueError as e:
        print(f"\n❌ Validation Error: {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
