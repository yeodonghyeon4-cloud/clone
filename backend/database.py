"""
Database module for ZABATDA MVP.

This module handles all PostgreSQL database operations including:
- Connection management to Supabase
- Product insertion with vector embeddings
- Vector similarity search using pgvector

Author: ZABATDA Development Team
Last Updated: November 18, 2025
"""

import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from typing import List, Dict, Optional, Any

# Load environment variables from .env file
load_dotenv()


def get_env_var(key: str) -> str:
    """
    Get environment variable from either Streamlit secrets or os.environ.
    Streamlit Cloud uses st.secrets, local dev uses .env file.
    """
    # Try Streamlit secrets first (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except (ImportError, Exception):
        pass

    # Fall back to environment variables (for local development)
    return os.getenv(key, '')


def get_db_connection():
    """
    Create and return a connection to the Supabase PostgreSQL database.

    Uses environment variables from .env file:
    - SUPABASE_DB_HOST
    - SUPABASE_DB_PORT
    - SUPABASE_DB_NAME
    - SUPABASE_DB_USER
    - SUPABASE_DB_PASSWORD

    Returns:
        psycopg2.connection: Active database connection

    Raises:
        psycopg2.Error: If connection fails
        ValueError: If required environment variables are missing
    """
    # Validate environment variables
    required_vars = [
        'SUPABASE_DB_HOST',
        'SUPABASE_DB_PORT',
        'SUPABASE_DB_NAME',
        'SUPABASE_DB_USER',
        'SUPABASE_DB_PASSWORD'
    ]

    missing_vars = [var for var in required_vars if not get_env_var(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    try:
        conn = psycopg2.connect(
            host=get_env_var('SUPABASE_DB_HOST'),
            port=get_env_var('SUPABASE_DB_PORT'),
            database=get_env_var('SUPABASE_DB_NAME'),
            user=get_env_var('SUPABASE_DB_USER'),
            password=get_env_var('SUPABASE_DB_PASSWORD')
        )
        return conn
    except psycopg2.Error as e:
        raise psycopg2.Error(f"Failed to connect to database: {e}")


def insert_product(
    product_id: str,
    name: str,
    brand: str,
    price: int,
    category: str,
    product_url: str,
    image_url: str,
    embedding: List[float]
) -> bool:
    """
    Insert a product with its embedding into the database.

    If a product with the same ID already exists, it will be updated (UPSERT).

    Args:
        product_id (str): Unique product identifier
        name (str): Product name
        brand (str): Brand name
        price (int): Price in Korean won
        category (str): Product category (e.g., "shoes", "clothing")
        product_url (str): URL to purchase the product
        image_url (str): URL to product image
        embedding (list): 512-dimensional embedding vector from CLIP

    Returns:
        bool: True if insert/update was successful, False otherwise

    Raises:
        ValueError: If embedding is not a 512-dimensional vector
        psycopg2.Error: If database operation fails
    """
    # Validate embedding dimensions
    if len(embedding) != 512:
        raise ValueError(f"Embedding must be 512-dimensional, got {len(embedding)}")

    conn = None
    cur = None

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # UPSERT query: insert or update if product_id already exists
        cur.execute("""
            INSERT INTO products (id, name, brand, price, category, product_url, image_url, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                brand = EXCLUDED.brand,
                price = EXCLUDED.price,
                category = EXCLUDED.category,
                product_url = EXCLUDED.product_url,
                image_url = EXCLUDED.image_url,
                embedding = EXCLUDED.embedding
        """, (product_id, name, brand, price, category, product_url, image_url, embedding))

        conn.commit()
        return True

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        raise psycopg2.Error(f"Failed to insert product '{product_id}': {e}")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def search_similar_products(
    query_embedding: List[float],
    limit: int = 5,
    min_similarity: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Search for products similar to the query embedding using cosine similarity.

    Uses pgvector's cosine distance operator (<=>) for efficient similarity search.
    Similarity score ranges from 0 (completely different) to 1 (identical).

    Similarity Score Interpretation:
    - 0.95+ = Nearly identical
    - 0.85+ = Very similar
    - 0.7+ = Good match
    - <0.7 = Different products

    Args:
        query_embedding (list): 512-dimensional query embedding vector
        limit (int): Maximum number of results to return (default: 5)
        min_similarity (float): Minimum similarity threshold (default: 0.0)

    Returns:
        list: List of dictionaries containing product information and similarity scores.
              Each dictionary has keys: id, name, brand, price, product_url,
              image_url, similarity

    Raises:
        ValueError: If query_embedding is not 512-dimensional
        psycopg2.Error: If database query fails
    """
    # Validate embedding dimensions
    if len(query_embedding) != 512:
        raise ValueError(f"Query embedding must be 512-dimensional, got {len(query_embedding)}")

    # Validate limit
    if limit < 1:
        raise ValueError(f"Limit must be at least 1, got {limit}")

    # Validate min_similarity
    if not 0.0 <= min_similarity <= 1.0:
        raise ValueError(f"min_similarity must be between 0 and 1, got {min_similarity}")

    conn = None
    cur = None

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Perform vector similarity search using cosine distance
        # The <=> operator computes cosine distance (0 = identical, 2 = opposite)
        # We convert to similarity score: similarity = 1 - distance
        cur.execute("""
            SELECT id, name, brand, price, product_url, image_url,
                   1 - (embedding <=> %s::vector) as similarity
            FROM products
            WHERE 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_embedding, query_embedding, min_similarity, query_embedding, limit))

        results = cur.fetchall()

        # Format results as list of dictionaries
        products = []
        for row in results:
            products.append({
                'id': row[0],
                'name': row[1],
                'brand': row[2],
                'price': row[3],
                'product_url': row[4],
                'image_url': row[5],
                'similarity': float(row[6])
            })

        return products

    except psycopg2.Error as e:
        raise psycopg2.Error(f"Failed to search similar products: {e}")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_product_count() -> int:
    """
    Get the total number of products in the database.

    Returns:
        int: Total number of products

    Raises:
        psycopg2.Error: If database query fails
    """
    conn = None
    cur = None

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM products")
        count = cur.fetchone()[0]

        return count

    except psycopg2.Error as e:
        raise psycopg2.Error(f"Failed to get product count: {e}")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a product by its ID.

    Args:
        product_id (str): Product ID to retrieve

    Returns:
        dict: Product information dictionary, or None if not found

    Raises:
        psycopg2.Error: If database query fails
    """
    conn = None
    cur = None

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, name, brand, price, category, product_url, image_url
            FROM products
            WHERE id = %s
        """, (product_id,))

        row = cur.fetchone()

        if row:
            return {
                'id': row[0],
                'name': row[1],
                'brand': row[2],
                'price': row[3],
                'category': row[4],
                'product_url': row[5],
                'image_url': row[6]
            }
        else:
            return None

    except psycopg2.Error as e:
        raise psycopg2.Error(f"Failed to get product '{product_id}': {e}")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def delete_all_products() -> int:
    """
    Delete all products from the database.

    WARNING: This will permanently delete all products!
    Use with caution, typically only for testing or resetting the database.

    Returns:
        int: Number of products deleted

    Raises:
        psycopg2.Error: If database operation fails
    """
    conn = None
    cur = None

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM products")
        deleted_count = cur.rowcount

        conn.commit()
        return deleted_count

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        raise psycopg2.Error(f"Failed to delete products: {e}")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
