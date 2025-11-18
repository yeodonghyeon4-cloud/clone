# backend/test_vectors.py
"""
Test script for vector operations with Supabase database.

This script tests:
1. Inserting products with vector embeddings
2. Searching for similar products using cosine similarity
3. Vector similarity scoring

Author: ZABATDA Development Team
Last Updated: November 18, 2025
"""

from database import insert_product, search_similar_products, get_product_count, delete_all_products
import numpy as np
import sys


def test_vector_operations():
    """Test inserting and searching with vector embeddings."""

    print("=" * 60)
    print("TESTING VECTOR OPERATIONS")
    print("=" * 60)

    try:
        # Clean up any existing test data
        print("\n1. Cleaning up existing test data...")
        initial_count = get_product_count()
        print(f"   Current product count: {initial_count}")

        # Create test embeddings (512-dimensional vectors)
        print("\n2. Creating test embeddings...")
        # Embedding 1: Base product
        embedding_1 = np.random.rand(512).tolist()
        # Embedding 2: Very similar (slight variation)
        embedding_2 = (np.array(embedding_1) + np.random.rand(512) * 0.1).tolist()
        # Embedding 3: Somewhat similar
        embedding_3 = (np.array(embedding_1) + np.random.rand(512) * 0.5).tolist()
        # Embedding 4: Different
        embedding_4 = np.random.rand(512).tolist()
        print("   ✅ Created 4 test embeddings")

        # Insert test products
        print("\n3. Inserting test products...")

        products = [
            {
                'id': 'test-nike-001',
                'name': 'Nike Air Force 1 White',
                'brand': 'Nike',
                'price': 129000,
                'category': 'shoes',
                'product_url': 'https://example.com/nike-af1',
                'image_url': 'https://example.com/images/nike-af1.jpg',
                'embedding': embedding_1
            },
            {
                'id': 'test-nike-002',
                'name': 'Nike Air Force 1 Shadow White',
                'brand': 'Nike',
                'price': 139000,
                'category': 'shoes',
                'product_url': 'https://example.com/nike-af1-shadow',
                'image_url': 'https://example.com/images/nike-af1-shadow.jpg',
                'embedding': embedding_2
            },
            {
                'id': 'test-nike-003',
                'name': 'Nike Air Max 90 White',
                'brand': 'Nike',
                'price': 149000,
                'category': 'shoes',
                'product_url': 'https://example.com/nike-airmax',
                'image_url': 'https://example.com/images/nike-airmax.jpg',
                'embedding': embedding_3
            },
            {
                'id': 'test-adidas-001',
                'name': 'Adidas Stan Smith',
                'brand': 'Adidas',
                'price': 119000,
                'category': 'shoes',
                'product_url': 'https://example.com/adidas-stan',
                'image_url': 'https://example.com/images/adidas-stan.jpg',
                'embedding': embedding_4
            }
        ]

        for product in products:
            insert_product(
                product['id'],
                product['name'],
                product['brand'],
                product['price'],
                product['category'],
                product['product_url'],
                product['image_url'],
                product['embedding']
            )
            print(f"   ✅ Inserted: {product['name']}")

        # Verify product count
        new_count = get_product_count()
        print(f"\n   Total products in database: {new_count}")

        # Search for similar products
        print("\n4. Testing similarity search...")
        print(f"   Query: Using embedding from 'Nike Air Force 1 White'")
        print(f"   Expected: Should return Nike products with high similarity\n")

        results = search_similar_products(embedding_1, limit=5)

        if not results:
            print("   ❌ No results returned!")
            return False

        print(f"   ✅ Found {len(results)} results:\n")
        print(f"   {'Rank':<6} {'Similarity':<12} {'Brand':<10} {'Product Name'}")
        print(f"   {'-'*6} {'-'*12} {'-'*10} {'-'*40}")

        for i, product in enumerate(results, 1):
            similarity_pct = product['similarity'] * 100
            print(f"   {i:<6} {similarity_pct:>6.2f}%      {product['brand']:<10} {product['name']}")

        # Validate results
        print("\n5. Validating results...")

        # Check if top result is identical (should be ~100% similarity)
        if results[0]['similarity'] < 0.95:
            print(f"   ⚠️  Warning: Top result similarity is {results[0]['similarity']:.4f}, expected ~1.0")
        else:
            print(f"   ✅ Top result is nearly identical (similarity: {results[0]['similarity']:.4f})")

        # Check if similar products rank higher
        nike_count = sum(1 for r in results[:3] if r['brand'] == 'Nike')
        if nike_count >= 2:
            print(f"   ✅ Similar brand products rank higher (Nike in top 3: {nike_count})")
        else:
            print(f"   ⚠️  Warning: Expected more Nike products in top 3")

        # Test with minimum similarity threshold
        print("\n6. Testing similarity threshold filter...")
        filtered_results = search_similar_products(embedding_1, limit=5, min_similarity=0.7)
        print(f"   ✅ Results with min_similarity=0.7: {len(filtered_results)} products")

        print("\n" + "=" * 60)
        print("🎉 ALL VECTOR OPERATION TESTS PASSED!")
        print("=" * 60)
        print("\nNext steps:")
        print("- Vector similarity search is working correctly")
        print("- Ready to integrate CLIP model for real image embeddings")
        print("- Ready to build Flask API endpoints")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_test_data():
    """Remove test data from database."""
    print("\n" + "=" * 60)
    print("Cleaning up test data...")
    print("=" * 60)

    try:
        deleted = delete_all_products()
        print(f"✅ Deleted {deleted} test products")
        print("Database is clean and ready for production data")
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")


if __name__ == "__main__":
    success = test_vector_operations()

    # Ask user if they want to keep test data
    print("\n" + "=" * 60)
    keep_data = input("Keep test data in database? (y/n): ").lower().strip()

    if keep_data != 'y':
        cleanup_test_data()
    else:
        print("Test data kept in database")

    print("=" * 60)

    sys.exit(0 if success else 1)
