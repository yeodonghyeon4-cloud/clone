"""
Embedding Service module for ZABATDA MVP.

This module handles all image embedding operations using the CLIP model:
- Loading and caching the CLIP model
- Generating 512-dimensional embeddings from images
- Processing images from file paths or bytes
- Batch processing for multiple images

Uses sentence-transformers library with 'clip-ViT-B-16' model.
Model download: ~600MB (only on first run, then cached)

Author: ZABATDA Development Team
Last Updated: January 21, 2025
"""

from sentence_transformers import SentenceTransformer
from PIL import Image
from io import BytesIO
from typing import List, Union
import numpy as np


# Global model instance (loaded once and reused)
_model = None


def get_model() -> SentenceTransformer:
    """
    Load and return the CLIP model (singleton pattern).

    The model is loaded once on first call and cached for subsequent calls.
    This avoids reloading the ~600MB model on every request.

    Model: 'clip-ViT-B-16' from sentence-transformers
    - Output: 512-dimensional embedding vector
    - Captures visual features with 16x16 patches (better detail than B-32)
    - Chosen for 100% top-1 accuracy in product matching tests

    Returns:
        SentenceTransformer: Loaded CLIP model instance

    Note:
        First call will download ~600MB model from Hugging Face.
        Subsequent calls use cached model from ~/.cache/torch/sentence_transformers/
    """
    global _model

    if _model is None:
        print("Loading CLIP model 'clip-ViT-B-16'...")
        print("Note: First run will download ~600MB. Please be patient...")
        _model = SentenceTransformer('clip-ViT-B-16')
        print("Model loaded successfully!")

    return _model


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Preprocess image for optimal CLIP encoding.

    Performs the following operations:
    - Convert to RGB mode (handles RGBA, grayscale, etc.)
    - Basic validation

    Args:
        image (PIL.Image.Image): Input image

    Returns:
        PIL.Image.Image: Preprocessed image

    Raises:
        ValueError: If image is invalid or corrupted
    """
    try:
        # Convert to RGB if not already (handles RGBA, grayscale, etc.)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Validate image has content
        if image.size[0] == 0 or image.size[1] == 0:
            raise ValueError("Image has zero width or height")

        return image

    except Exception as e:
        raise ValueError(f"Failed to preprocess image: {e}")


def generate_embedding(image_path: str) -> List[float]:
    """
    Generate a 512-dimensional embedding vector from an image file.

    This function:
    1. Loads the image from the file path
    2. Preprocesses the image (RGB conversion, validation)
    3. Generates embedding using CLIP model
    4. Returns as Python list for database storage

    Args:
        image_path (str): Path to the image file (JPEG, PNG, etc.)

    Returns:
        list: 512-dimensional embedding vector as list of floats

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If image is invalid or corrupted
        Exception: If embedding generation fails

    Example:
        >>> embedding = generate_embedding('data/product_images/nike_shoe.jpg')
        >>> len(embedding)
        512
        >>> type(embedding[0])
        <class 'float'>
    """
    try:
        # Load image
        image = Image.open(image_path)

        # Preprocess
        image = preprocess_image(image)

        # Get model
        model = get_model()

        # Generate embedding
        embedding = model.encode(image)

        # Convert numpy array to Python list for JSON serialization
        return embedding.tolist()

    except FileNotFoundError:
        raise FileNotFoundError(f"Image file not found: {image_path}")

    except Exception as e:
        raise Exception(f"Failed to generate embedding from '{image_path}': {e}")


def generate_embedding_from_bytes(image_bytes: bytes) -> List[float]:
    """
    Generate embedding from image bytes (for uploaded files).

    This is used when handling image uploads from the frontend,
    where images are sent as byte data rather than file paths.

    Args:
        image_bytes (bytes): Image file bytes (JPEG, PNG, etc.)

    Returns:
        list: 512-dimensional embedding vector as list of floats

    Raises:
        ValueError: If image bytes are invalid or corrupted
        Exception: If embedding generation fails

    Example:
        >>> with open('image.jpg', 'rb') as f:
        ...     image_bytes = f.read()
        >>> embedding = generate_embedding_from_bytes(image_bytes)
        >>> len(embedding)
        512
    """
    try:
        # Convert bytes to PIL Image
        image = Image.open(BytesIO(image_bytes))

        # Preprocess
        image = preprocess_image(image)

        # Get model
        model = get_model()

        # Generate embedding
        embedding = model.encode(image)

        # Convert to list
        return embedding.tolist()

    except Exception as e:
        raise Exception(f"Failed to generate embedding from bytes: {e}")


def generate_embeddings_batch(image_paths: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple images in a single batch.

    Batch processing is more efficient than processing images one by one,
    especially when populating the database with many products.

    Args:
        image_paths (list): List of image file paths

    Returns:
        list: List of 512-dimensional embeddings (one per input image)

    Raises:
        FileNotFoundError: If any image file doesn't exist
        ValueError: If any image is invalid
        Exception: If batch processing fails

    Example:
        >>> paths = ['img1.jpg', 'img2.jpg', 'img3.jpg']
        >>> embeddings = generate_embeddings_batch(paths)
        >>> len(embeddings)
        3
        >>> len(embeddings[0])
        512
    """
    try:
        # Load and preprocess all images
        images = []
        for path in image_paths:
            try:
                image = Image.open(path)
                image = preprocess_image(image)
                images.append(image)
            except FileNotFoundError:
                raise FileNotFoundError(f"Image file not found: {path}")
            except Exception as e:
                raise ValueError(f"Failed to load image '{path}': {e}")

        # Get model
        model = get_model()

        # Generate embeddings in batch (more efficient than one-by-one)
        embeddings = model.encode(images)

        # Convert numpy array to list of lists
        return [emb.tolist() for emb in embeddings]

    except Exception as e:
        raise Exception(f"Failed to generate batch embeddings: {e}")


def compute_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Compute cosine similarity between two embeddings.

    Cosine similarity measures the similarity between two vectors:
    - 1.0 = Identical
    - 0.9+ = Very similar
    - 0.7-0.9 = Similar
    - 0.5-0.7 = Somewhat similar
    - <0.5 = Different

    Args:
        embedding1 (list): First 512-dimensional embedding
        embedding2 (list): Second 512-dimensional embedding

    Returns:
        float: Cosine similarity score between 0 and 1

    Raises:
        ValueError: If embeddings have different dimensions

    Example:
        >>> emb1 = generate_embedding('nike_shoe1.jpg')
        >>> emb2 = generate_embedding('nike_shoe2.jpg')
        >>> similarity = compute_similarity(emb1, emb2)
        >>> print(f"Similarity: {similarity:.4f}")
        Similarity: 0.9234
    """
    # Validate dimensions
    if len(embedding1) != len(embedding2):
        raise ValueError(
            f"Embeddings must have same dimensions. "
            f"Got {len(embedding1)} and {len(embedding2)}"
        )

    # Convert to numpy arrays
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)

    # Compute cosine similarity
    # Formula: (A · B) / (||A|| * ||B||)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    # Avoid division by zero
    if norm1 == 0 or norm2 == 0:
        return 0.0

    similarity = dot_product / (norm1 * norm2)

    # Ensure result is in [0, 1] range (handle floating point errors)
    return float(np.clip(similarity, 0.0, 1.0))


def validate_embedding(embedding: List[float]) -> bool:
    """
    Validate that an embedding has the correct format and dimensions.

    Checks:
    - Is a list
    - Has exactly 512 elements
    - All elements are valid floats (not NaN or Inf)

    Args:
        embedding (list): Embedding to validate

    Returns:
        bool: True if valid, raises ValueError if invalid

    Raises:
        ValueError: If embedding is invalid
    """
    # Check type
    if not isinstance(embedding, list):
        raise ValueError(f"Embedding must be a list, got {type(embedding)}")

    # Check dimensions
    if len(embedding) != 512:
        raise ValueError(f"Embedding must be 512-dimensional, got {len(embedding)}")

    # Check all elements are valid floats
    for i, val in enumerate(embedding):
        if not isinstance(val, (int, float)):
            raise ValueError(f"Element {i} is not a number: {val}")

        if np.isnan(val) or np.isinf(val):
            raise ValueError(f"Element {i} is NaN or Inf: {val}")

    return True


def get_model_info() -> dict:
    """
    Get information about the loaded CLIP model.

    Returns:
        dict: Model information including name, dimensions, and status

    Example:
        >>> info = get_model_info()
        >>> print(info)
        {
            'model_name': 'clip-ViT-B-16',
            'embedding_dimensions': 512,
            'loaded': True
        }
    """
    return {
        'model_name': 'clip-ViT-B-16',
        'embedding_dimensions': 512,
        'loaded': _model is not None,
        'description': 'OpenAI CLIP Vision Transformer (ViT-B/16) - 16x16 patches for better detail',
        'use_case': 'Visual similarity search for products',
        'accuracy': '100% top-1 accuracy on test dataset (11 products)'
    }
