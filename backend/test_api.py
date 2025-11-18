"""
API Testing Script for ZABATDA Flask API

This script tests the Flask API endpoints to verify they're working correctly.

Usage:
    python backend/test_api.py

Note: Make sure the Flask server is running before executing this script.

Author: ZABATDA Development Team
Last Updated: November 18, 2025
"""

import requests
import os
import sys
from io import BytesIO
from PIL import Image
import numpy as np

# API configuration
# Note: Using port 5001 because macOS AirPlay uses port 5000
API_BASE_URL = "http://localhost:5001"


def create_test_image():
    """
    Create a simple test image in memory.

    Returns:
        BytesIO: Test image as bytes
    """
    # Create a simple 224x224 RGB image with random colors
    img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    img = Image.fromarray(img_array, 'RGB')

    # Save to BytesIO
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)

    return img_bytes


def test_health_endpoint():
    """Test the /health endpoint."""
    print("\n" + "=" * 60)
    print("TEST 1: Health Check Endpoint")
    print("=" * 60)

    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            print("✅ Health check passed!")
            return True
        else:
            print("❌ Health check failed!")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API server.")
        print("   Make sure the Flask server is running on http://localhost:5001")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_stats_endpoint():
    """Test the /api/stats endpoint."""
    print("\n" + "=" * 60)
    print("TEST 2: Statistics Endpoint")
    print("=" * 60)

    try:
        response = requests.get(f"{API_BASE_URL}/api/stats")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            data = response.json()
            if 'statistics' in data:
                print(f"\nStatistics:")
                print(f"  Total Products: {data['statistics']['total_products']}")
                print(f"  Model: {data['statistics']['model_name']}")
                print(f"  Model Loaded: {data['statistics']['model_loaded']}")
                print("✅ Stats endpoint passed!")
                return True
        else:
            print("❌ Stats endpoint failed!")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_search_endpoint_no_file():
    """Test the /api/search endpoint without a file (should fail)."""
    print("\n" + "=" * 60)
    print("TEST 3: Search Endpoint (No File - Should Fail)")
    print("=" * 60)

    try:
        response = requests.post(f"{API_BASE_URL}/api/search")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 400:
            print("✅ Correctly rejected request without image!")
            return True
        else:
            print("❌ Should have returned 400 error!")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_search_endpoint_with_image():
    """Test the /api/search endpoint with a test image."""
    print("\n" + "=" * 60)
    print("TEST 4: Search Endpoint (With Test Image)")
    print("=" * 60)

    try:
        # Create test image
        print("Creating test image...")
        test_image = create_test_image()

        # Send request
        files = {'image': ('test.jpg', test_image, 'image/jpeg')}
        response = requests.post(f"{API_BASE_URL}/api/search", files=files)

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                print(f"\n✅ Search successful!")
                print(f"   Found {data['count']} results")

                if data['count'] > 0:
                    print(f"\n   Top result:")
                    top = data['results'][0]
                    print(f"     Name: {top['name']}")
                    print(f"     Brand: {top['brand']}")
                    print(f"     Similarity: {top['similarity']:.4f}")
                else:
                    print("   ⚠️  No products in database yet")

                return True
        else:
            print("❌ Search failed!")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_with_real_image(image_path):
    """Test the /api/search endpoint with a real image file."""
    print("\n" + "=" * 60)
    print("TEST 5: Search Endpoint (With Real Image)")
    print("=" * 60)

    if not os.path.exists(image_path):
        print(f"⚠️  Image file not found: {image_path}")
        print("   Skipping real image test")
        return None

    try:
        print(f"Testing with image: {image_path}")

        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(f"{API_BASE_URL}/api/search", files=files)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")

            if data['status'] == 'success':
                print(f"\n✅ Search successful!")
                print(f"   Found {data['count']} results\n")

                if data['count'] > 0:
                    print(f"   {'Rank':<6} {'Similarity':<12} {'Brand':<15} {'Product Name'}")
                    print(f"   {'-'*6} {'-'*12} {'-'*15} {'-'*40}")

                    for i, product in enumerate(data['results'], 1):
                        similarity_pct = product['similarity'] * 100
                        print(f"   {i:<6} {similarity_pct:>6.2f}%      {product['brand']:<15} {product['name']}")

                return True
        else:
            print("❌ Search failed!")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_invalid_file_type():
    """Test uploading an invalid file type."""
    print("\n" + "=" * 60)
    print("TEST 6: Invalid File Type (Should Fail)")
    print("=" * 60)

    try:
        # Create a text file pretending to be an image
        fake_file = BytesIO(b"This is not an image")

        files = {'image': ('test.txt', fake_file, 'text/plain')}
        response = requests.post(f"{API_BASE_URL}/api/search", files=files)

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 400:
            print("✅ Correctly rejected invalid file type!")
            return True
        else:
            print("❌ Should have returned 400 error!")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║            ZABATDA API Testing Suite                     ║
║          Testing Flask API Endpoints                     ║
╚═══════════════════════════════════════════════════════════╝
    """)

    print(f"API Base URL: {API_BASE_URL}")
    print("\nStarting tests...\n")

    results = []

    # Run tests
    results.append(("Health Check", test_health_endpoint()))

    if results[0][1]:  # Only continue if server is reachable
        results.append(("Statistics", test_stats_endpoint()))
        results.append(("Search - No File", test_search_endpoint_no_file()))
        results.append(("Search - Test Image", test_search_endpoint_with_image()))
        results.append(("Search - Invalid Type", test_invalid_file_type()))

        # Try with real image if available
        sample_image = "data/product_images/sample.jpg"
        if os.path.exists(sample_image):
            result = test_search_with_real_image(sample_image)
            if result is not None:
                results.append(("Search - Real Image", result))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed! API is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
