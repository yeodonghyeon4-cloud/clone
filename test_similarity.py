"""
Quick similarity search test script
Tests the API with one of the existing product images
"""
import requests
import sys

API_URL = "http://localhost:5001/api/search"
TEST_IMAGE = "data/product_images/diesel_m_caddix_top_black_001.jpg"

def test_similarity_search():
    """Test image similarity search with an existing product image."""

    print("=" * 70)
    print("ZABATDA Similarity Search Test")
    print("=" * 70)
    print(f"\nTest Image: {TEST_IMAGE}")
    print(f"API Endpoint: {API_URL}\n")

    try:
        # Open and send the image
        with open(TEST_IMAGE, 'rb') as image_file:
            files = {'image': image_file}

            print("Sending image to API...")
            print("(First request may take ~30 seconds to load CLIP model)\n")

            response = requests.post(API_URL, files=files)

        # Check response
        if response.status_code == 200:
            data = response.json()

            print("✅ Search successful!")
            print(f"\nFound {len(data['results'])} similar products:")
            print("-" * 70)

            for i, product in enumerate(data['results'], 1):
                similarity_percent = product['similarity'] * 100
                print(f"\n{i}. {product['name']}")
                print(f"   Brand: {product['brand']}")
                print(f"   Similarity: {similarity_percent:.1f}%")
                print(f"   Price: ₩{product['price']:,}")
                print(f"   Product ID: {product['id']}")
                print(f"   Image: {product['image_url']}")
                if 'product_url' in product and product['product_url']:
                    print(f"   URL: {product['product_url']}")

            print("\n" + "=" * 70)
            print(f"Search completed in {data['search_time_ms']:.0f}ms")
            print("=" * 70)

        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
            sys.exit(1)

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API")
        print("\nMake sure the Flask server is running:")
        print("   uv run python backend/app.py")
        sys.exit(1)

    except FileNotFoundError:
        print(f"❌ Error: Test image not found: {TEST_IMAGE}")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_similarity_search()
