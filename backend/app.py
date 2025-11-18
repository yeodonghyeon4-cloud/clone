"""
Flask API for ZABATDA MVP - AI-Powered Product Similarity Search

This application provides REST API endpoints for:
- Image similarity search using CLIP embeddings
- Health monitoring
- Database statistics

Endpoints:
- POST /api/search - Upload image and get similar products
- GET /health - Health check
- GET /api/stats - Database statistics
- GET / - Serve frontend

Author: ZABATDA Development Team
Last Updated: November 18, 2025
"""

import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from io import BytesIO
from PIL import Image

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from embedding_service import generate_embedding_from_bytes, get_model_info
from database import search_similar_products, get_product_count

# Initialize Flask app
app = Flask(__name__,
            static_folder='../frontend',
            static_url_path='')

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Enable CORS for all routes
CORS(app)


def allowed_file(filename):
    """
    Check if uploaded file has an allowed extension.

    Args:
        filename (str): Name of the uploaded file

    Returns:
        bool: True if extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def validate_image(file):
    """
    Validate uploaded image file.

    Args:
        file: FileStorage object from Flask request

    Returns:
        tuple: (is_valid, error_message)
    """
    # Check if file exists
    if not file:
        return False, "No file provided"

    # Check if file has a filename
    if file.filename == '':
        return False, "No file selected"

    # Check file extension
    if not allowed_file(file.filename):
        return False, f"Invalid file type. Allowed types: {', '.join(app.config['ALLOWED_EXTENSIONS'])}"

    # Try to open as image
    try:
        file_bytes = file.read()
        file.seek(0)  # Reset file pointer for later use
        Image.open(BytesIO(file_bytes))
        return True, None
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"


@app.route('/')
def index():
    """
    Serve the frontend HTML page.

    Returns:
        HTML file or JSON message if frontend not built yet
    """
    frontend_path = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(frontend_path):
        return send_from_directory(app.static_folder, 'index.html')
    else:
        return jsonify({
            'status': 'info',
            'message': 'ZABATDA API is running',
            'endpoints': {
                'search': 'POST /api/search',
                'health': 'GET /health',
                'stats': 'GET /api/stats'
            },
            'note': 'Frontend not built yet. Use API endpoints directly.'
        })


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring.

    Returns:
        JSON: Service health status
    """
    try:
        # Check database connection
        count = get_product_count()

        # Check if CLIP model info is accessible
        model_info = get_model_info()

        return jsonify({
            'status': 'healthy',
            'service': 'ZABATDA API',
            'database': 'connected',
            'product_count': count,
            'model': model_info['model_name'],
            'model_loaded': model_info['loaded']
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get database statistics.

    Returns:
        JSON: Database and model statistics
    """
    try:
        product_count = get_product_count()
        model_info = get_model_info()

        return jsonify({
            'status': 'success',
            'statistics': {
                'total_products': product_count,
                'model_name': model_info['model_name'],
                'embedding_dimensions': model_info['embedding_dimensions'],
                'model_loaded': model_info['loaded']
            }
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get statistics: {str(e)}'
        }), 500


@app.route('/api/search', methods=['POST'])
def search_products():
    """
    Search for similar products based on uploaded image.

    Expects:
        - multipart/form-data with 'image' file field
        - Optional: 'limit' (default: 5), 'min_similarity' (default: 0.0)

    Returns:
        JSON: {
            'status': 'success',
            'count': int,
            'results': [
                {
                    'id': str,
                    'name': str,
                    'brand': str,
                    'price': int,
                    'product_url': str,
                    'image_url': str,
                    'similarity': float
                },
                ...
            ]
        }
    """
    try:
        # Check if file is in request
        if 'image' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No image file provided. Please include an image in the request.'
            }), 400

        file = request.files['image']

        # Validate image
        is_valid, error_message = validate_image(file)
        if not is_valid:
            return jsonify({
                'status': 'error',
                'message': error_message
            }), 400

        # Get optional parameters
        limit = request.form.get('limit', 5, type=int)
        min_similarity = request.form.get('min_similarity', 0.0, type=float)

        # Validate parameters
        if limit < 1 or limit > 50:
            return jsonify({
                'status': 'error',
                'message': 'Limit must be between 1 and 50'
            }), 400

        if not 0.0 <= min_similarity <= 1.0:
            return jsonify({
                'status': 'error',
                'message': 'min_similarity must be between 0.0 and 1.0'
            }), 400

        # Read image bytes
        image_bytes = file.read()

        # Generate embedding from uploaded image
        try:
            embedding = generate_embedding_from_bytes(image_bytes)
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Failed to process image: {str(e)}'
            }), 500

        # Search for similar products
        try:
            results = search_similar_products(
                query_embedding=embedding,
                limit=limit,
                min_similarity=min_similarity
            )
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Database search failed: {str(e)}'
            }), 500

        # Return results
        return jsonify({
            'status': 'success',
            'count': len(results),
            'results': results,
            'query_info': {
                'limit': limit,
                'min_similarity': min_similarity
            }
        }), 200

    except Exception as e:
        # Catch-all for unexpected errors
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }), 500


@app.route('/static/product_images/<path:filename>')
def serve_product_image(filename):
    """
    Serve product images from data/product_images directory.

    Args:
        filename (str): Image filename

    Returns:
        Image file or 404 error
    """
    images_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'product_images')
    return send_from_directory(images_dir, filename)


@app.errorhandler(413)
def request_entity_too_large(error):
    """
    Handle file too large error.

    Returns:
        JSON: Error message with file size limit
    """
    max_size_mb = app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)
    return jsonify({
        'status': 'error',
        'message': f'File too large. Maximum size is {max_size_mb}MB'
    }), 413


@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 errors.

    Returns:
        JSON: Error message
    """
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 errors.

    Returns:
        JSON: Error message
    """
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║              ZABATDA Flask API Server                    ║
║        AI-Powered Product Similarity Search              ║
╚═══════════════════════════════════════════════════════════╝

Starting server...

Available endpoints:
  POST   /api/search        - Upload image and search for similar products
  GET    /health            - Health check
  GET    /api/stats         - Database statistics
  GET    /                  - Frontend (if built)

Server will start on http://localhost:5001
Press CTRL+C to stop the server
    """)

    # Run Flask development server
    # Note: Using port 5001 because macOS AirPlay uses port 5000
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )
