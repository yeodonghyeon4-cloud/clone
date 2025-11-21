# ZABATDA MVP: Embedding Strategy Testing & Implementation Plan

**Created:** 2025-11-21
**Status:** ✅ COMPLETE - Decision Made
**Owner:** Heesoo Jung
**Timeline:** 2-3 days (Completed in 1 day)
**Completion Date:** 2025-11-21

---

## Executive Summary

This plan addresses a critical challenge in ZABATDA's product similarity matching: **current CLIP embeddings capture entire images (product + background + people), causing mismatches between clean database images and messy user uploads.**

**✅ COMPLETED:** Comprehensive testing of three embedding approaches across all 11 database products.

**🎯 DECISION:** Option 2 (Baseline CLIP ViT-B-16) selected - achieved 100% top-1 accuracy with 20x faster processing.

**Original Options Tested:**
1. **Option 1: Background Removal (rembg)** - AI-based background removal before embedding ❌ Not selected
2. **Option 2: Product-Focused CLIP Model** - Standard CLIP ViT-B-16 (no preprocessing) ✅ SELECTED
3. **Option 3: Hybrid** - Combination (skipped - fashion models had bugs)

**Testing Approach:** Tested all 11 database products as queries, measured top-1 accuracy, processing speed, and category separation.

**Success Achieved:** 100% top-1 accuracy (11/11 products correctly matched), perfect category separation, 20x faster than alternative approaches.

**Next Step:** Implementation of ViT-B-16 model in backend code (documented in EMBEDDING_DECISION.md)

---

## Problem Statement

### Current Situation

**Database Images:**
- 10 products currently in database (5 Diesel tops, 5 UGG shoes)
- Clean product photos with white/neutral backgrounds
- Professional e-commerce style images

**The Challenge:**
- If user uploads photo wearing a Diesel top → Will it match our database Diesel tops?
- If background is messy, will similarity score drop too much?
- Current CLIP model may focus on background/person instead of product

**Expected Behavior:**
```
Query: Diesel Black Top (clean) vs. Database Diesel Black Tops
→ Similarity should be HIGH (>0.85)

Query: Diesel Black Top (clean) vs. Database UGG Shoes
→ Similarity should be LOW (<0.60)

Query: Diesel Top worn by person vs. Database Diesel Tops
→ Similarity should still be GOOD (>0.75) even with background/person
```

### Business Impact

**If Not Fixed:**
- Real user photos (with backgrounds/people) won't match database products
- Poor user experience and low accuracy
- MVP demo fails with realistic images

**If Fixed:**
- Accurate matching regardless of photo quality
- Better user experience
- MVP validation successful

---

## Testing Strategy

### Use Existing Database Products

**Current Database (10 products):**
- 5 Diesel tops (black clothing, similar style)
- 5 UGG shoes/slippers (footwear, various colors)

**Testing Approach:**
Instead of collecting new images, we'll:
1. Take one product from database (e.g., `diesel_m_caddix_top_black_001.jpg`)
2. Compare it against all 10 database products
3. Check similarity scores intuitively:
   - Other Diesel tops should score HIGH (>0.80)
   - UGG shoes should score LOW (<0.60)
   - Rankings should make visual sense

**Test Variations:**
- Test with all 3 embedding approaches (Option 1, 2, 3)
- Compare how each approach handles:
  - Same product category matches
  - Different product category matches
  - Subtle differences within same brand

### Evaluation Criteria (Intuition-Based)

**Instead of formal metrics, we'll judge:**

1. **Does it make sense?**
   - Do visually similar products rank higher?
   - Do different products rank lower?

2. **Category separation**
   - Are Diesel tops clearly separated from UGG shoes?
   - Can the model distinguish clothing from footwear?

3. **Within-category ranking**
   - Within Diesel tops, do similar styles rank higher?
   - Within UGG products, are boots vs. slippers distinguished?

4. **Processing speed**
   - Is it fast enough for real-time use (<5 seconds)?
   - Does it feel responsive?

**Decision Framework:**
- If approach produces nonsensical rankings → REJECT
- If approach produces intuitive rankings + fast → SELECT
- Between multiple good options → Pick fastest/simplest

---

## Day 1: Setup & Script Creation

### Task 1.1: Install Dependencies (30 minutes)

**For Option 1 (Background Removal):**
```bash
uv add rembg
```

**For Option 2 (Product-Focused Model):**
```bash
# No additional dependencies needed
# Will download model on first use (~600-800MB)
```

**For Option 3 (Hybrid):**
```bash
uv add rembg
```

**Verify Installation:**
```bash
# Test rembg
uv run python -c "from rembg import remove; print('rembg OK')"

# Test sentence-transformers
uv run python -c "from sentence_transformers import SentenceTransformer; print('sentence-transformers OK')"
```

### Task 1.2: Create Test Scripts (2 hours)

**Create three test scripts based on `test_similarity.py` pattern:**

**1. `backend/test_option1_rembg.py`**
```python
"""
Test Option 1: Background Removal + Standard CLIP
Compares one database image against all others using rembg preprocessing
"""
import os
from pathlib import Path
from rembg import remove
from sentence_transformers import SentenceTransformer
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

MODEL = SentenceTransformer('clip-ViT-B-32')
IMAGE_DIR = 'data/product_images'

def preprocess_image(image_path):
    """Remove background and convert to RGB."""
    image = Image.open(image_path)
    # Remove background
    image = remove(image)
    # Convert RGBA to RGB (transparent -> white background)
    if image.mode == 'RGBA':
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background
    return image

def generate_embedding(image_path):
    """Generate embedding with background removal."""
    image = preprocess_image(image_path)
    embedding = MODEL.encode(image)
    return embedding

def test_similarity():
    """Compare first product against all products."""
    print("=" * 70)
    print("OPTION 1: Background Removal + Standard CLIP")
    print("=" * 70)

    # Get all product images
    image_files = sorted(Path(IMAGE_DIR).glob('*.jpg'))
    print(f"\nFound {len(image_files)} product images")

    # Generate embeddings for all products
    print("\nGenerating embeddings (with background removal)...")
    embeddings = []
    for i, img_path in enumerate(image_files, 1):
        print(f"  [{i}/{len(image_files)}] {img_path.name}...", end=" ")
        emb = generate_embedding(str(img_path))
        embeddings.append(emb)
        print("✓")

    # Compare first product against all
    query_embedding = embeddings[0]
    query_name = image_files[0].name

    print(f"\nQuery Product: {query_name}")
    print("-" * 70)

    # Calculate similarities
    similarities = cosine_similarity([query_embedding], embeddings)[0]

    # Create results with names and scores
    results = [(image_files[i].name, similarities[i]) for i in range(len(image_files))]
    results.sort(key=lambda x: x[1], reverse=True)

    print("\nSimilarity Rankings:")
    for i, (name, score) in enumerate(results, 1):
        print(f"{i:2d}. {name:45s} {score:.4f} ({score*100:.1f}%)")

    print("\n" + "=" * 70)
    print("INTUITIVE EVALUATION:")
    print("- Do similar products (same brand/category) rank high?")
    print("- Do different products (different category) rank low?")
    print("- Does the ranking make visual sense?")
    print("=" * 70)

if __name__ == "__main__":
    test_similarity()
```

**2. `backend/test_option2_product_model.py`**
```python
"""
Test Option 2: Product-Focused CLIP Model
Compares one database image against all others using Marqo fashion CLIP
"""
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

MODEL = SentenceTransformer('Marqo/marqo-fashion-clip')
IMAGE_DIR = 'data/product_images'

def generate_embedding(image_path):
    """Generate embedding with product-focused model."""
    image = Image.open(image_path)
    embedding = MODEL.encode(image)
    return embedding

def test_similarity():
    """Compare first product against all products."""
    print("=" * 70)
    print("OPTION 2: Product-Focused CLIP Model (Marqo Fashion)")
    print("=" * 70)

    # Get all product images
    image_files = sorted(Path(IMAGE_DIR).glob('*.jpg'))
    print(f"\nFound {len(image_files)} product images")

    # Generate embeddings for all products
    print("\nGenerating embeddings (product-focused model)...")
    embeddings = []
    for i, img_path in enumerate(image_files, 1):
        print(f"  [{i}/{len(image_files)}] {img_path.name}...", end=" ")
        emb = generate_embedding(str(img_path))
        embeddings.append(emb)
        print("✓")

    # Compare first product against all
    query_embedding = embeddings[0]
    query_name = image_files[0].name

    print(f"\nQuery Product: {query_name}")
    print("-" * 70)

    # Calculate similarities
    similarities = cosine_similarity([query_embedding], embeddings)[0]

    # Create results with names and scores
    results = [(image_files[i].name, similarities[i]) for i in range(len(image_files))]
    results.sort(key=lambda x: x[1], reverse=True)

    print("\nSimilarity Rankings:")
    for i, (name, score) in enumerate(results, 1):
        print(f"{i:2d}. {name:45s} {score:.4f} ({score*100:.1f}%)")

    print("\n" + "=" * 70)
    print("INTUITIVE EVALUATION:")
    print("- Do similar products (same brand/category) rank high?")
    print("- Do different products (different category) rank low?")
    print("- Does the ranking make visual sense?")
    print("=" * 70)

if __name__ == "__main__":
    test_similarity()
```

**3. `backend/test_option3_hybrid.py`**
```python
"""
Test Option 3: Hybrid (Background Removal + Product-Focused Model)
Compares one database image against all others using both techniques
"""
import os
from pathlib import Path
from rembg import remove
from sentence_transformers import SentenceTransformer
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

MODEL = SentenceTransformer('Marqo/marqo-fashion-clip')
IMAGE_DIR = 'data/product_images'

def preprocess_image(image_path):
    """Remove background and convert to RGB."""
    image = Image.open(image_path)
    # Remove background
    image = remove(image)
    # Convert RGBA to RGB (transparent -> white background)
    if image.mode == 'RGBA':
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background
    return image

def generate_embedding(image_path):
    """Generate embedding with background removal + product model."""
    image = preprocess_image(image_path)
    embedding = MODEL.encode(image)
    return embedding

def test_similarity():
    """Compare first product against all products."""
    print("=" * 70)
    print("OPTION 3: Hybrid (Background Removal + Product-Focused Model)")
    print("=" * 70)

    # Get all product images
    image_files = sorted(Path(IMAGE_DIR).glob('*.jpg'))
    print(f"\nFound {len(image_files)} product images")

    # Generate embeddings for all products
    print("\nGenerating embeddings (hybrid approach)...")
    embeddings = []
    for i, img_path in enumerate(image_files, 1):
        print(f"  [{i}/{len(image_files)}] {img_path.name}...", end=" ")
        emb = generate_embedding(str(img_path))
        embeddings.append(emb)
        print("✓")

    # Compare first product against all
    query_embedding = embeddings[0]
    query_name = image_files[0].name

    print(f"\nQuery Product: {query_name}")
    print("-" * 70)

    # Calculate similarities
    similarities = cosine_similarity([query_embedding], embeddings)[0]

    # Create results with names and scores
    results = [(image_files[i].name, similarities[i]) for i in range(len(image_files))]
    results.sort(key=lambda x: x[1], reverse=True)

    print("\nSimilarity Rankings:")
    for i, (name, score) in enumerate(results, 1):
        print(f"{i:2d}. {name:45s} {score:.4f} ({score*100:.1f}%)")

    print("\n" + "=" * 70)
    print("INTUITIVE EVALUATION:")
    print("- Do similar products (same brand/category) rank high?")
    print("- Do different products (different category) rank low?")
    print("- Does the ranking make visual sense?")
    print("=" * 70)

if __name__ == "__main__":
    test_similarity()
```

**Day 1 Deliverables:**
- [ ] Dependencies installed and verified
- [ ] Three test scripts created and syntax-checked
- [ ] Scripts tested for basic functionality (no errors)

---

## Day 2: Testing & Comparison

### Task 2.1: Baseline Test (Current Approach)

**First, test current approach for reference:**
```bash
uv run python test_similarity.py
```

**Record baseline results:**
- Note similarity scores between Diesel tops
- Note similarity scores between UGG shoes
- Note similarity scores between Diesel and UGG (should be low)

### Task 2.2: Test Option 1 (Background Removal)

**Run test:**
```bash
uv run python backend/test_option1_rembg.py
```

**Expected output:**
```
======================================================================
OPTION 1: Background Removal + Standard CLIP
======================================================================

Found 11 product images

Generating embeddings (with background removal)...
  [1/11] diesel_m_caddix_top_black_001.jpg... ✓
  [2/11] diesel_m_caddix_top_black_002.jpg... ✓
  ...

Query Product: diesel_m_caddix_top_black_001.jpg
----------------------------------------------------------------------

Similarity Rankings:
 1. diesel_m_caddix_top_black_001.jpg           1.0000 (100.0%)
 2. diesel_m_caddix_top_black_002.jpg           0.8234 (82.3%)
 3. diesel_m_caddix_top_black_003.jpg           0.8156 (81.6%)
 4. UGG_001.jpg                                  0.5423 (54.2%)
 5. UGG_002.jpg                                  0.5312 (53.1%)
 ...

======================================================================
INTUITIVE EVALUATION:
- Do similar products (same brand/category) rank high?
- Do different products (different category) rank low?
- Does the ranking make visual sense?
======================================================================
```

**Evaluation Questions:**
1. Are other Diesel tops in top 3-5 positions?
2. Are UGG shoes ranked below Diesel tops?
3. Is there clear separation between categories?
4. Did background removal take too long (~2-3s per image)?

### Task 2.3: Test Option 2 (Product-Focused Model)

**Run test:**
```bash
uv run python backend/test_option2_product_model.py
```

**Evaluation Questions:**
1. Are similarity scores higher for same-category products?
2. Is processing faster than Option 1?
3. Does ranking look more intuitive than baseline?

### Task 2.4: Test Option 3 (Hybrid)

**Run test:**
```bash
uv run python backend/test_option3_hybrid.py
```

**Evaluation Questions:**
1. Are similarity scores the highest for same-category products?
2. Is processing time acceptable (<5s total)?
3. Is ranking improvement worth the extra time?

### Task 2.5: Compare Results Side-by-Side

**Create comparison table manually:**

| Product Pair | Baseline | Option 1 | Option 2 | Option 3 | Notes |
|--------------|----------|----------|----------|----------|-------|
| Diesel 001 vs Diesel 002 | 0.XX | 0.XX | 0.XX | 0.XX | Should be HIGH |
| Diesel 001 vs Diesel 003 | 0.XX | 0.XX | 0.XX | 0.XX | Should be HIGH |
| Diesel 001 vs UGG 001 | 0.XX | 0.XX | 0.XX | 0.XX | Should be LOW |
| Diesel 001 vs UGG 002 | 0.XX | 0.XX | 0.XX | 0.XX | Should be LOW |

**Intuitive Assessment:**
- Which option produces the most sensible rankings?
- Which option clearly separates categories?
- Which option is fast enough for real-time use?

**Day 2 Deliverables:**
- [ ] All four tests executed (baseline + 3 options)
- [ ] Results recorded in comparison table
- [ ] Intuitive evaluation notes documented
- [ ] Processing time noted for each approach

---

## Day 3: Decision & Implementation

### Task 3.1: Make Decision Based on Intuition

**Decision Criteria:**

1. **Category Separation** (Most Important)
   - Do Diesel tops clearly separate from UGG shoes?
   - Is there obvious visual logic to rankings?

2. **Within-Category Accuracy**
   - Are similar Diesel tops grouped together?
   - Are different UGG products reasonably separated?

3. **Processing Speed**
   - Is it fast enough (<5s)?
   - Does it feel responsive?

4. **Implementation Complexity**
   - How hard to integrate?
   - How likely to cause issues?

**Expected Decision:**

Based on research, **Option 2 (Product-Focused Model)** is likely winner:
- Designed specifically for product/fashion images
- No preprocessing needed (faster)
- Should handle backgrounds naturally
- Simple to implement (just change model name)

**However, make decision based on YOUR actual test results, not predictions.**

### Task 3.2: Document Decision

**Create `/docs/EMBEDDING_DECISION.md`:**

```markdown
# ZABATDA MVP: Embedding Strategy Decision

**Test Date:** 2025-11-21
**Decision Maker:** Heesoo Jung

## Test Results Summary

**Baseline (Current clip-ViT-B-32):**
- Diesel vs Diesel similarity: [X.XX]
- Diesel vs UGG similarity: [X.XX]
- Ranking makes sense: [Yes/No]

**Option 1 (Background Removal + Standard CLIP):**
- Diesel vs Diesel similarity: [X.XX]
- Diesel vs UGG similarity: [X.XX]
- Ranking makes sense: [Yes/No]
- Processing time: [X.X]s per image

**Option 2 (Product-Focused Model):**
- Diesel vs Diesel similarity: [X.XX]
- Diesel vs UGG similarity: [X.XX]
- Ranking makes sense: [Yes/No]
- Processing time: [X.X]s per image

**Option 3 (Hybrid):**
- Diesel vs Diesel similarity: [X.XX]
- Diesel vs UGG similarity: [X.XX]
- Ranking makes sense: [Yes/No]
- Processing time: [X.X]s per image

## Selected Approach

**Winner:** Option [X] - [Name]

## Reasoning (Intuition-Based)

[Explain why this option was selected based on how the results "felt" right]

Key observations:
1. [What looked good about the rankings]
2. [What made sense visually]
3. [Speed considerations]
4. [Implementation simplicity]

## Trade-offs Accepted

[Any downsides of chosen approach]

## Next Steps

Proceed to implementation (Task 3.3-3.5)
```

### Task 3.3: Implement Selected Approach

**If Option 1 selected:**
```bash
# Add dependency
uv add rembg

# Update embedding_service.py to add background removal
# Update populate_db.py
```

**If Option 2 selected:**
```bash
# No new dependencies needed

# Update embedding_service.py to change model name:
# OLD: SentenceTransformer('clip-ViT-B-32')
# NEW: SentenceTransformer('Marqo/marqo-fashion-clip')
```

**If Option 3 selected:**
```bash
# Add dependency
uv add rembg

# Update embedding_service.py with both changes
```

### Task 3.4: Update embedding_service.py

**Example for Option 2 (most likely):**

Find this line in `backend/embedding_service.py`:
```python
model = SentenceTransformer('clip-ViT-B-32')
```

Change to:
```python
model = SentenceTransformer('Marqo/marqo-fashion-clip')
```

**That's it! No other changes needed for Option 2.**

### Task 3.5: Regenerate Database Embeddings

```bash
# Clear existing embeddings
uv run python backend/populate_db.py --clear

# Regenerate with new approach
uv run python backend/populate_db.py

# Verify products loaded
uv run python -c "from backend.database import get_product_count; print(f'Products: {get_product_count()}')"
```

### Task 3.6: Test End-to-End

```bash
# Start API server
uv run python backend/app.py

# In another terminal, test similarity search
uv run python test_similarity.py
```

**Verify:**
- API starts without errors
- Model loads successfully
- Similarity scores look reasonable
- Rankings make intuitive sense

**Day 3 Deliverables:**
- [ ] Decision documented in EMBEDDING_DECISION.md
- [ ] Code updated with selected approach
- [ ] Database embeddings regenerated
- [ ] End-to-end testing passed
- [ ] Ready for frontend development

---

## Success Criteria

### Must Have

- [ ] Selected approach produces intuitive similarity rankings
- [ ] Same-brand/category products score noticeably higher than different products
- [ ] Processing time acceptable (<5 seconds)
- [ ] Implementation completed within 3 days
- [ ] No crashes or errors

### Nice to Have

- [ ] Very clear category separation (>0.80 same category, <0.60 different category)
- [ ] Processing time <2 seconds
- [ ] Works well with both clean and messy images (if tested)

---

## Risk Mitigation

### Risk 1: All Options Produce Similar Results

**If baseline is already good enough:**
- Keep current approach (clip-ViT-B-32)
- Save time on implementation
- Focus on frontend development instead

### Risk 2: Processing Too Slow

**If Option 3 is best but too slow:**
- Accept slower time for MVP
- Plan GPU acceleration for production
- Use Option 2 as acceptable compromise

### Risk 3: No Clear Winner

**If results are ambiguous:**
- Default to Option 2 (product-focused model)
- Simplest to implement
- Industry standard for e-commerce

---

## Rollback Plan

**If implementation causes issues:**

```bash
# Restore original embedding_service.py
git checkout backend/embedding_service.py

# Regenerate embeddings with original approach
uv run python backend/populate_db.py --clear
uv run python backend/populate_db.py

# Test that it works
uv run python test_similarity.py
```

---

## Next Steps After Completion

1. **Frontend Development** - Build image upload UI and results display
2. **Expand Product Database** - Add remaining products to reach 30-product MVP
3. **Real User Testing** - Get feedback on match quality
4. **Performance Optimization** - Profile and optimize if needed

---

## Appendix: Current Database Products

**5 Diesel Tops:**
- diesel_m_caddix_top_black_001.jpg
- diesel_m_caddix_top_black_002.jpg
- diesel_m_caddix_top_black_003.jpg
- diesel_m_caddix_top_black_004.jpg
- diesel_m_caddix_top_black_005.jpg

**6 UGG Shoes:**
- UGG_001.jpg
- UGG_002.jpg
- UGG_003.jpg
- UGG_004.jpg
- UGG_005.jpg
- UGG_006.jpg

**Expected Similarity Patterns:**
- Diesel top vs another Diesel top: HIGH (>0.75)
- UGG shoe vs another UGG shoe: MEDIUM-HIGH (>0.65)
- Diesel top vs UGG shoe: LOW (<0.60)

---

## Appendix: Resources

**Documentation:**
- rembg: https://github.com/danielgatis/rembg
- Marqo Fashion CLIP: https://huggingface.co/Marqo/marqo-fashion-clip
- CLIP Paper: https://arxiv.org/abs/2103.00020

**Test Script Pattern:**
- Based on existing `test_similarity.py`
- Simple, intuitive, fast to run
- Focus on visual/intuitive evaluation

---

**END OF PLAN**

*This simplified plan uses existing database images and intuition-based evaluation for faster testing and decision-making. Follow the 3-day timeline for optimal results.*

**Plan Status:** ✅ Ready for Execution
**Start Date:** 2025-11-21
**Expected Completion:** 2025-11-23 (2-3 days)
**Owner:** Heesoo Jung
