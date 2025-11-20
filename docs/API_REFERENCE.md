# ZABATDA API Reference

## Base URL
```
http://localhost:5001
```

**Note:** Port 5001 is used because macOS AirPlay Receiver uses port 5000 by default.

## Endpoints

### 1. Health Check
Check if the API server is running and healthy.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "ZABATDA API",
  "database": "connected",
  "product_count": 30,
  "model": "clip-ViT-B-32",
  "model_loaded": true
}
```

**cURL Example:**
```bash
curl http://localhost:5001/health
```

---

### 2. Get Statistics
Get database and model statistics.

**Endpoint:** `GET /api/stats`

**Response:**
```json
{
  "status": "success",
  "statistics": {
    "total_products": 30,
    "model_name": "clip-ViT-B-32",
    "embedding_dimensions": 512,
    "model_loaded": true
  }
}
```

**cURL Example:**
```bash
curl http://localhost:5001/api/stats
```

---

### 3. Search Similar Products
Upload an image and find visually similar products.

**Endpoint:** `POST /api/search`

**Request:**
- **Method:** POST
- **Content-Type:** multipart/form-data
- **Body Parameters:**
  - `image` (required): Image file (JPEG or PNG)
  - `limit` (optional): Number of results (1-50, default: 5)
  - `min_similarity` (optional): Minimum similarity threshold (0.0-1.0, default: 0.0)

**Response:**
```json
{
  "status": "success",
  "count": 5,
  "results": [
    {
      "id": "nike-001",
      "name": "Nike Air Force 1 '07 White",
      "brand": "Nike",
      "price": 129000,
      "product_url": "https://www.nike.com/kr/t/air-force-1-07",
      "image_url": "/static/product_images/nike_airforce_white.jpg",
      "similarity": 0.9234
    },
    ...
  ],
  "query_info": {
    "limit": 5,
    "min_similarity": 0.0
  }
}
```

**cURL Examples:**

Basic search:
```bash
curl -X POST http://localhost:5001/api/search \
  -F "image=@/path/to/your/image.jpg"
```

Search with custom limit:
```bash
curl -X POST http://localhost:5001/api/search \
  -F "image=@/path/to/your/image.jpg" \
  -F "limit=10"
```

Search with minimum similarity threshold:
```bash
curl -X POST http://localhost:5001/api/search \
  -F "image=@/path/to/your/image.jpg" \
  -F "min_similarity=0.7"
```

Search with both parameters:
```bash
curl -X POST http://localhost:5001/api/search \
  -F "image=@/path/to/your/image.jpg" \
  -F "limit=10" \
  -F "min_similarity=0.7"
```

---

### 4. Frontend
Serves the frontend HTML page (if built).

**Endpoint:** `GET /`

**Response:** HTML page or JSON info message

---

### 5. Serve Product Images
Access product images stored in the database.

**Endpoint:** `GET /static/product_images/<filename>`

**Example:**
```bash
curl http://localhost:5001/static/product_images/nike_airforce_white.jpg --output image.jpg
```

---

## Error Responses

### 400 Bad Request
```json
{
  "status": "error",
  "message": "No image file provided. Please include an image in the request."
}
```

### 404 Not Found
```json
{
  "status": "error",
  "message": "Endpoint not found"
}
```

### 413 Request Entity Too Large
```json
{
  "status": "error",
  "message": "File too large. Maximum size is 16.0MB"
}
```

### 500 Internal Server Error
```json
{
  "status": "error",
  "message": "Internal server error"
}
```

### 503 Service Unavailable
```json
{
  "status": "unhealthy",
  "error": "Database connection failed"
}
```

---

## Similarity Score Interpretation

The `similarity` field in search results ranges from 0.0 to 1.0:

- **0.95+** = Nearly identical
- **0.85+** = Very similar
- **0.7+** = Good match
- **<0.7** = Different products

---

## Configuration

- **Max File Size:** 16MB
- **Allowed Formats:** PNG, JPG, JPEG
- **Default Limit:** 5 results
- **Max Limit:** 50 results
- **Port:** 5000
- **CORS:** Enabled for all origins

---

## Testing the API

### Using cURL
```bash
# Health check
curl http://localhost:5001/health

# Get stats
curl http://localhost:5001/api/stats

# Search with image
curl -X POST http://localhost:5001/api/search \
  -F "image=@test_image.jpg"
```

### Using Python Script
```bash
# Run the test suite
uv run python backend/test_api.py
```

### Using Postman
1. Create a new POST request to `http://localhost:5001/api/search`
2. Go to Body → form-data
3. Add key `image` with type `File`
4. Select an image file
5. Send request

---

## Running the Server

```bash
# Start the Flask development server
uv run python backend/app.py

# The server will start on http://localhost:5001
```

Server output:
```
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
```

---

## Development Notes

- Server runs in **debug mode** for development
- Auto-reloads when code changes
- Detailed error messages in development
- CORS enabled for frontend development
- Logs all requests to console

---

## Next Steps

1. **Populate Database:** Run `uv run python backend/populate_db.py` to add products
2. **Start Server:** Run `uv run python backend/app.py`
3. **Test API:** Run `uv run python backend/test_api.py`
4. **Build Frontend:** Create HTML/CSS/JS interface to use the API
