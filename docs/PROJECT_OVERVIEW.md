# ZABATDA MVP - Project Overview

## 🎯 What This Project Does

**ZABATDA (위조품수거반)** is an AI-powered platform that helps consumers identify counterfeit products and find genuine OEM/ODM alternatives through image similarity search.

### Core Functionality
1. **User uploads a product image** (e.g., a Nike shoe from an online store)
2. **AI analyzes the image** and generates a visual embedding (512-dimensional vector)
3. **System searches database** for visually similar products using vector similarity
4. **Returns top 5 matches** with similarity scores, prices, and purchase links

### Business Value
- **For Consumers:** Verify if a product is genuine or find cheaper OEM alternatives
- **For Brands:** Protect against counterfeit products through verification badges
- **Market Gap:** Combines counterfeit detection + OEM sourcing + price comparison in one platform

---

## 🏗️ Architecture Overview

```
User Browser
    ↓
[Frontend: HTML/CSS/JS]
    ↓
[Flask Backend API]
    ↓
[CLIP Model] → Generate embeddings
    ↓
[PostgreSQL + pgvector] → Vector similarity search
    ↓
Return matched products
```

### Why This Architecture?

**Problem with Initial Approach:**
- ❌ Google Cloud Vision API only provides labels/tags (not similarity ranking)
- ❌ JSON file cannot scale or perform efficient similarity search
- ❌ No actual "matching" logic - just basic categorization

**Our Solution:**
- ✅ CLIP model converts images to numerical vectors (embeddings)
- ✅ pgvector enables efficient similarity search in PostgreSQL
- ✅ Cosine similarity mathematically ranks product matches
- ✅ Scalable from 30 products (MVP) to millions (production)

---

## 🛠️ Tech Stack

### Backend (Python)

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.11+ | Core backend language |
| **Flask** | 3.0+ | Web framework for API endpoints |
| **sentence-transformers** | 2.2+ | Load and run CLIP model |
| **PostgreSQL** | 16+ | Relational database |
| **pgvector** | 0.5+ | PostgreSQL extension for vector storage/search |
| **psycopg2-binary** | 2.9+ | PostgreSQL adapter for Python |
| **Pillow** | 10.1+ | Image processing |
| **NumPy** | 1.24+ | Numerical computations |
| **scikit-learn** | 1.3+ | Cosine similarity calculations |
| **python-dotenv** | 1.0+ | Environment variable management |
| **flask-cors** | 4.0+ | Handle cross-origin requests |

### Frontend

| Technology | Purpose |
|-----------|---------|
| **HTML5** | Structure |
| **CSS3** | Styling |
| **JavaScript (Vanilla)** | User interactions & API calls |

### Infrastructure

| Technology | Purpose |
|-----------|---------|
| **UV Package Manager** | Python dependency management (faster than pip) |
| **Supabase** | Hosted PostgreSQL with pgvector (managed database) |
| **Git/GitHub** | Version control |

---

## 🧠 How the AI Works

### 1. Image Embeddings (CLIP Model)

**What is CLIP?**
- Contrastive Language-Image Pre-training model by OpenAI
- Converts images into 512-dimensional numerical vectors
- Captures visual features (shape, color, pattern, style)

**Example:**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('clip-ViT-B-32')
embedding = model.encode(image)  # Returns [0.23, -0.45, 0.67, ...]
```

**Why CLIP instead of Google Vision API?**

| Feature | Google Vision API | CLIP |
|---------|------------------|------|
| Output | Text labels ("shoe", "nike", "white") | 512 numbers representing visual features |
| Can rank similarity? | ❌ No - same labels for all white Nike shoes | ✅ Yes - 94% vs 67% match scores |
| Cost | $1.50 per 1,000 images | Free (self-hosted) |
| Use case | "What objects are in this image?" | "Which product looks most similar?" |

### 2. Vector Similarity Search (pgvector)

**Database Schema:**
```sql
CREATE TABLE products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    brand TEXT,
    price INTEGER,
    category TEXT,
    product_url TEXT,
    image_url TEXT,
    embedding VECTOR(512)  -- 512 numbers from CLIP
);
```

**Search Query:**
```sql
SELECT id, name, brand, price, product_url, image_url,
       1 - (embedding <=> %s) as similarity
FROM products
ORDER BY embedding <=> %s  -- <=> is cosine distance operator
LIMIT 5;
```

**Cosine Similarity:**
- Mathematical measure of similarity between vectors
- Range: 0 (completely different) to 1 (identical)
- 0.7+ = Good match
- 0.85+ = Very similar
- 0.95+ = Nearly identical

### 3. Workflow Example

**User uploads Nike Airforce 1 White shoe image:**

```
1. CLIP generates embedding: [0.23, -0.45, 0.67, ..., 0.12]
2. PostgreSQL compares with all stored embeddings
3. Results:
   - Nike Airforce 07 White (95% similarity)
   - Nike Airforce 1 Shadow (87% similarity)
   - Nike Airmax White (78% similarity)
   - Adidas Stan Smith (42% similarity) ← Filtered out
```

---

## 📦 Package Explanations

### Core Dependencies

**`sentence-transformers`** (~600MB)
- Pre-trained CLIP model: `clip-ViT-B-32`
- Handles image encoding to embeddings
- Alternative models available if accuracy needs improvement

**`pgvector`** (PostgreSQL extension)
- Adds `VECTOR` data type to PostgreSQL
- Enables efficient similarity search with indexing
- Supports cosine distance, L2 distance, inner product

**`Flask`**
- Lightweight Python web framework
- Creates API endpoints for frontend to call
- Serves static files (HTML/CSS/JS)

**`Pillow`**
- Image loading and preprocessing
- Resize, normalize, convert formats
- Ensures consistent input for CLIP

**`scikit-learn`**
- Cosine similarity calculations
- Data preprocessing utilities
- May be replaced by direct NumPy operations later

---

## 🗂️ Project Structure

```
zabatda-mvp/
│
├── backend/
│   ├── app.py                    # Flask main application & API routes
│   ├── embedding_service.py      # CLIP model loading & embedding generation
│   ├── database.py               # PostgreSQL connection & queries
│   └── populate_db.py            # Script to populate 30 products initially
│
├── frontend/
│   ├── index.html               # Main page with upload interface
│   ├── styles.css               # Styling
│   └── app.js                   # JavaScript for image upload & results display
│
├── data/
│   ├── product_images/          # 30 product images for MVP
│   └── product_metadata.json    # Product info (name, brand, price, URLs)
│
├── pyproject.toml               # UV/Python dependencies
├── uv.lock                      # Dependency lock file
├── .python-version              # Python version (3.11)
├── .env                         # Environment variables (Supabase credentials)
├── .gitignore
└── README.md                    # Setup instructions
```

---

## 🚀 Development Flow (10 Days)

### **Phase 1: Setup (Days 1-2)**
- Install UV, setup Supabase account and project
- Enable pgvector extension in Supabase
- Create database schema
- Test database connection
- Load CLIP model and test embedding generation

**Checkpoint:** Can generate embeddings from test images

---

### **Phase 2: Backend Core (Days 3-5)**

**Day 3:** Build embedding generation pipeline
```python
# embedding_service.py
def generate_embedding(image_path):
    model = SentenceTransformer('clip-ViT-B-32')
    embedding = model.encode(Image.open(image_path))
    return embedding.tolist()
```

**Day 4:** Populate database with 30 products
```python
# populate_db.py
for product in products:
    embedding = generate_embedding(product['image_path'])
    db.execute("""
        INSERT INTO products VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (id, name, brand, price, category, url, img_url, embedding))
```

**Day 5:** Build search API endpoint
```python
# app.py
@app.route('/api/search', methods=['POST'])
def search_product():
    user_embedding = generate_embedding(uploaded_image)
    results = search_similar_products(user_embedding, limit=5)
    return jsonify(results)
```

**Checkpoint:** API returns similar products when called with test image

---

### **Phase 3: Frontend (Days 6-7)**

**Day 6:** HTML structure
```html
<input type="file" id="imageUpload" accept="image/*">
<button onclick="searchProduct()">검색</button>
<div id="results"></div>
```

**Day 7:** JavaScript integration
```javascript
async function searchProduct() {
    const formData = new FormData();
    formData.append('image', fileInput.files[0]);
    
    const response = await fetch('/api/search', {
        method: 'POST',
        body: formData
    });
    
    displayResults(await response.json());
}
```

**Checkpoint:** User can upload image and see results in browser

---

### **Phase 4: Testing & Refinement (Days 8-9)**

**Day 8:** End-to-end testing
- Test with various product images
- Measure accuracy (similar products ranked high?)
- Measure speed (< 10 seconds acceptable)
- Test edge cases (blurry images, wrong angles)

**Day 9:** Improvements
- Tune similarity threshold (0.7 vs 0.8)
- Add image preprocessing (resize, normalize)
- Error handling (no matches found, invalid image)
- UI polish (loading spinner, error messages)

**Checkpoint:** Stable MVP with good user experience

---

### **Phase 5: Documentation (Day 10)**

- Document setup instructions
- API documentation
- Demo script with best test cases
- Known limitations and future improvements

---

## 🎯 MVP Scope (30 Products)

### What's Included:
✅ Image upload interface
✅ AI-powered similarity search
✅ Top 5 product matches with scores
✅ Product info display (name, brand, price, link)
✅ Basic error handling

### What's NOT Included (Yet):
❌ User authentication
❌ Search history
❌ Filtering by brand/price
❌ Multiple image uploads
❌ Mobile app
❌ OEM crawler for Chinese platforms
❌ Counterfeit detection logic (just similarity)
❌ Brand verification badges

**MVP Goal:** Prove the core matching concept works before building advanced features.

---

## 📊 Success Metrics for MVP

1. **Accuracy:** When uploading a Nike shoe, top 3 results should be Nike shoes (not Adidas)
2. **Speed:** Search results in < 10 seconds
3. **Similarity Scores:** Good matches should score 0.75+
4. **User Experience:** Simple, clear interface that non-technical users can use

---

## 🔧 Setup Instructions

### 1. Prerequisites
```bash
# Install UV (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a Supabase account
# https://supabase.com/
```

### 2. Clone & Setup Project
```bash
# Initialize project
mkdir zabatda-mvp && cd zabatda-mvp
uv init --name zabatda-mvp --python 3.11

# Create structure
mkdir backend frontend data data/product_images

# Add dependencies
uv add flask sentence-transformers psycopg2-binary pillow numpy flask-cors python-dotenv scikit-learn
```

### 3. Setup Supabase Database
```bash
# 1. Create new project in Supabase dashboard
# 2. Go to SQL Editor in Supabase dashboard
# 3. Enable pgvector extension:
CREATE EXTENSION IF NOT EXISTS vector;

# 4. Create products table:
CREATE TABLE products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    brand TEXT,
    price INTEGER,
    category TEXT,
    product_url TEXT,
    image_url TEXT,
    embedding VECTOR(512)
);

# 5. Copy connection details from Settings > Database
```

### 4. Configure Environment Variables
```bash
# Create .env file with Supabase credentials
SUPABASE_DB_HOST=db.xxxxxxxxxxxxx.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your-database-password
```

### 5. Run Backend
```bash
# Populate database with 30 products
uv run python backend/populate_db.py

# Start Flask server
uv run python backend/app.py
```

### 6. Access Application
- Frontend: `http://localhost:5000/`
- API: `http://localhost:5000/api/search`

---

## 🔍 Key Technical Decisions

### Why Supabase (PostgreSQL + pgvector) over alternatives?

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| JSON file | Simple | Not scalable, no indexing | ❌ Rejected |
| Pinecone | Vector-optimized | Costs money, limited free tier | ❌ Overkill for MVP |
| Self-hosted PostgreSQL | Full control | Complex setup, maintenance overhead | ⚠️ Too complex for MVP |
| Supabase | Scalable, managed, generous free tier, pgvector support | External dependency | ✅ **Selected** |

### Why CLIP over other models?

| Model | Pros | Cons | Decision |
|-------|------|------|----------|
| Google Vision API | Easy to use | Can't rank similarity, costs money | ❌ Wrong tool |
| ResNet | Fast | Less accurate for products | ⚠️ Backup option |
| CLIP | Best accuracy | 600MB model size | ✅ **Selected** |

### Why Flask over FastAPI/Django?

| Framework | Pros | Cons | Decision |
|-----------|------|------|----------|
| Django | Full-featured | Too heavy for MVP | ❌ Overkill |
| FastAPI | Modern, fast | More complex setup | ⚠️ Consider later |
| Flask | Simple, lightweight | Less features | ✅ **Selected** for MVP |

---

## 🚨 Critical Technical Risks & Mitigation

### Risk 1: Poor Embedding Quality
**Problem:** CLIP returns bad matches (e.g., Nike shoe matched with Adidas)

**Mitigation:**
- Test multiple CLIP variants (`clip-ViT-B-32` vs `clip-ViT-L-14`)
- Curate high-quality reference images (clear, well-lit, white background)
- Tune similarity threshold (0.7 vs 0.8)
- Implement image preprocessing (resize, normalize colors)

### Risk 2: Slow Search Performance
**Problem:** Search takes > 10 seconds

**Mitigation:**
- Use pgvector indexing (IVFFlat index)
- Optimize embedding generation (batch processing)
- Consider caching frequently searched items
- Profile code to find bottlenecks

### Risk 3: Database Setup Complexity
**Problem:** Team struggles with PostgreSQL + pgvector setup

**Mitigation:**
- Use Supabase for managed database (no local installation needed)
- Provide step-by-step setup guide with screenshots
- pgvector extension available with one-click in Supabase
- Free tier sufficient for MVP (500MB database, 2GB bandwidth)
- Have backup: SQLite with manual similarity search (slower but works)

### Risk 4: Expectation Mismatch
**Problem:** Stakeholders expect features not in MVP (user accounts, mobile app, counterfeit detection)

**Mitigation:**
- Clear demo script showing ONLY what works
- Document "What's NOT included"
- Focus on core value: "Does similarity search work?"
- Plan phased rollout for additional features

---

## 📈 Future Scaling Path

### Phase 1: MVP (Current)
- 30 products
- Local deployment
- Basic similarity search

### Phase 2: Alpha (Month 1)
- 500+ products
- Cloud deployment (Heroku/AWS)
- User feedback iteration

### Phase 3: Beta (Months 2-3)
- 5,000+ products
- User authentication
- Premium features
- Marketing launch

### Phase 4: Production (Months 4-6)
- OEM/ODM data crawler
- B2B features (reports, API)
- Recommendation engine
- Mobile app

---

## 🤝 Team Roles

| Role | Responsibilities |
|------|------------------|
| **Backend Developer** | Flask API, CLIP integration, database setup |
| **Frontend Developer** | HTML/CSS/JS interface, user experience |
| **Data Curator** | Collect 30 product images, metadata |
| **QA/Tester** | Test accuracy, edge cases, performance |

---

## 📚 Additional Resources

### Documentation
- [sentence-transformers docs](https://www.sbert.net/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [CLIP paper](https://arxiv.org/abs/2103.00020)
- [Flask documentation](https://flask.palletsprojects.com/)

### Learning Resources
- [Understanding Vector Embeddings](https://www.youtube.com/watch?v=5MaWmXwxFNQ)
- [Cosine Similarity Explained](https://www.machinelearningplus.com/nlp/cosine-similarity/)
- [Building Image Search with CLIP](https://huggingface.co/blog/fine-tune-clip-rsicd)

---

## ❓ FAQ

**Q: Why not use Google Lens or similar tools?**
A: They don't provide similarity scores or connect to OEM databases. We need programmatic control over matching logic.

**Q: How accurate will 30 products be?**
A: Not production-ready, but enough to validate the concept. If Nike shoe → Nike results, the approach works.

**Q: Can we add more products later?**
A: Yes! That's why we use PostgreSQL + pgvector. The architecture scales from 30 to millions.

**Q: What if CLIP doesn't work well?**
A: We'll know by Day 5. Can switch to ResNet or fine-tune CLIP on fashion products.

**Q: Do we need GPU for CLIP?**
A: No for MVP (30 products). CPU is fine. GPU helpful when scaling to thousands of searches/day.

---

## 📝 Next Steps for New Developers

1. **Read this document fully**
2. **Review the context handover document** (previous conversation summary)
3. **Set up local environment** (UV) and create Supabase account
4. **Set up Supabase database** with pgvector extension
5. **Test CLIP model** with sample images to understand embeddings
6. **Start with Day 1 tasks** (database schema creation)
7. **Ask questions early** if anything is unclear

---

**Document Version:** 1.0  
**Last Updated:** November 18, 2025  
**Author:** ZABATDA Development Team  
**Contact:** [Team Lead - Heesoo Lee]

---

## 🎓 Glossary

- **Embedding/Vector:** Numerical representation of data (512 numbers representing image features)
- **CLIP:** Contrastive Language-Image Pre-training model by OpenAI
- **Cosine Similarity:** Mathematical measure of similarity between vectors (0-1 range)
- **pgvector:** PostgreSQL extension enabling vector storage and similarity search
- **Supabase:** Managed PostgreSQL hosting platform with built-in pgvector support
- **OEM:** Original Equipment Manufacturer
- **ODM:** Original Design Manufacturer
- **MVP:** Minimum Viable Product
- **API Endpoint:** URL that accepts requests and returns data
- **Flask:** Lightweight Python web framework

---

**Good luck building ZABATDA! 🚀**
