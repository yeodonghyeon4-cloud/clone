"""
Test all product images with Option 2 (Baseline CLIP)
Generates a comprehensive report of top-3 matches for each image
"""
from pathlib import Path
from sentence_transformers import SentenceTransformer
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json

# Configuration
MODEL_NAME = 'clip-ViT-B-16'
IMAGE_DIR = 'data/product_images'

# Categories
CATEGORIES = {
    'diesel': ['diesel_m_caddix_top_black_001.jpg', 'diesel_m_caddix_top_black_002.jpg',
               'diesel_m_caddix_top_black_003.jpg', 'diesel_m_caddix_top_black_004.jpg',
               'diesel_m_caddix_top_black_005.jpg'],
    'ugg': ['UGG_001.jpg', 'UGG_002.jpg', 'UGG_003.jpg', 'UGG_004.jpg', 'UGG_005.jpg', 'UGG_006.jpg']
}

def get_category(filename):
    """Determine product category from filename."""
    for category, files in CATEGORIES.items():
        if filename in files:
            return category
    return 'unknown'

def generate_embedding(image_path, model):
    """Generate embedding with standard CLIP."""
    image = Image.open(image_path)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    return model.encode(image)

def test_all_images():
    """Test all images and generate comprehensive report."""
    print("=" * 100)
    print("COMPREHENSIVE TEST: All 11 Product Images with ViT-B-16")
    print("=" * 100)
    print(f"\nModel: {MODEL_NAME}")
    print("Testing each product as query to see top-3 matches\n")

    # Load model
    print("Loading model...")
    model = SentenceTransformer(MODEL_NAME)
    print("✓ Model loaded\n")

    # Get all images and generate embeddings
    image_files = sorted(Path(IMAGE_DIR).glob('*.jpg'))
    print(f"Generating embeddings for {len(image_files)} images...\n")

    embeddings = []
    for img_path in image_files:
        emb = generate_embedding(str(img_path), model)
        embeddings.append(emb)

    embeddings_array = np.array(embeddings)
    similarity_matrix = cosine_similarity(embeddings_array)

    # Test each image as query
    results = []
    correct_top1 = 0
    correct_top3 = 0

    print("=" * 100)
    print("RESULTS: Top-3 Matches for Each Product")
    print("=" * 100)

    for query_idx, query_file in enumerate(image_files):
        query_name = query_file.name
        query_cat = get_category(query_name)

        # Get top matches
        matches = [(image_files[i].name, get_category(image_files[i].name),
                   similarity_matrix[query_idx][i]) for i in range(len(image_files))]
        matches.sort(key=lambda x: x[2], reverse=True)

        # Count correct matches in top-3 (excluding self)
        top3_without_self = [m for m in matches[1:4]]  # Skip self (rank 1)
        correct_in_top3 = sum(1 for m in top3_without_self if m[1] == query_cat)

        # Check if first non-self match is correct category
        first_match_correct = top3_without_self[0][1] == query_cat
        if first_match_correct:
            correct_top1 += 1
        if correct_in_top3 > 0:
            correct_top3 += 1

        # Display results
        print(f"\n📦 Query: {query_name} ({query_cat})")
        print("-" * 100)
        for i, (name, cat, score) in enumerate(matches[1:4], 2):  # Ranks 2-4 (skip self)
            marker = "✓" if cat == query_cat else "✗"
            print(f"  Rank {i}: {name:<45} ({cat:<7}) Similarity: {score:.4f} {marker}")

        results.append({
            'query': query_name,
            'category': query_cat,
            'top3_matches': [{'name': m[0], 'category': m[1], 'similarity': float(m[2])}
                           for m in top3_without_self],
            'correct_in_top3': correct_in_top3,
            'first_match_correct': first_match_correct
        })

    # Summary statistics
    print("\n\n" + "=" * 100)
    print("SUMMARY STATISTICS")
    print("=" * 100)

    accuracy_top1 = (correct_top1 / len(image_files)) * 100
    accuracy_top3 = (correct_top3 / len(image_files)) * 100

    print(f"\n📊 Overall Accuracy:")
    print(f"  Top-1 Accuracy (first match is correct category): {correct_top1}/{len(image_files)} ({accuracy_top1:.1f}%)")
    print(f"  Top-3 Accuracy (at least 1 correct in top-3):     {correct_top3}/{len(image_files)} ({accuracy_top3:.1f}%)")

    # Per-category breakdown
    diesel_results = [r for r in results if r['category'] == 'diesel']
    ugg_results = [r for r in results if r['category'] == 'ugg']

    diesel_top1 = sum(1 for r in diesel_results if r['first_match_correct'])
    ugg_top1 = sum(1 for r in ugg_results if r['first_match_correct'])

    print(f"\n📈 Per-Category Performance:")
    print(f"  Diesel Tops (5 images):")
    print(f"    Top-1 Accuracy: {diesel_top1}/5 ({diesel_top1/5*100:.1f}%)")
    print(f"  UGG Shoes (6 images):")
    print(f"    Top-1 Accuracy: {ugg_top1}/6 ({ugg_top1/6*100:.1f}%)")

    # Save results
    output_data = {
        'model': MODEL_NAME,
        'total_images': len(image_files),
        'top1_accuracy': accuracy_top1,
        'top3_accuracy': accuracy_top3,
        'diesel_top1_accuracy': diesel_top1/5*100,
        'ugg_top1_accuracy': ugg_top1/6*100,
        'detailed_results': results
    }

    output_file = 'backend/test_all_images_results.json'
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n💾 Detailed results saved to: {output_file}")
    print("=" * 100)

    return output_data

if __name__ == "__main__":
    test_all_images()
