# Product Data Directory

This directory contains product metadata and images for the ZABATDA MVP.

## Directory Structure

```
data/
├── product_metadata.json       # Product information (JSON)
└── product_images/            # Product image files
    ├── nike_airforce_white.jpg
    ├── nike_airmax_black.jpg
    └── ...
```

## Adding Products

### 1. Add Product Images

Place product images in `data/product_images/`:
- **Supported formats:** JPEG (.jpg, .jpeg), PNG (.png)
- **Recommended:** Clear product photos on white/neutral background
- **Size:** Any size (will be automatically processed by CLIP)
- **Naming:** Use descriptive filenames (e.g., `nike_airforce_white.jpg`)

### 2. Update product_metadata.json

Add product information to `product_metadata.json`:

```json
{
  "id": "unique-product-id",
  "name": "Product Name",
  "brand": "Brand Name",
  "price": 120000,
  "category": "shoes",
  "product_url": "https://example.com/product-page",
  "image_filename": "product_image.jpg"
}
```

**Required Fields:**
- `id` - Unique product identifier (e.g., "nike-001")
- `name` - Product name
- `brand` - Brand name
- `price` - Price in Korean won (integer)
- `category` - Product category (e.g., "shoes", "clothing", "accessories")
- `product_url` - URL to purchase the product
- `image_filename` - Filename of the image in `product_images/` directory

### 3. Run Population Script

After adding products, run:

```bash
# Populate database with all products
uv run python backend/populate_db.py

# Clear existing products and repopulate
uv run python backend/populate_db.py --clear

# Test run without inserting
uv run python backend/populate_db.py --dry-run
```

## MVP Goal: 30 Products

For the MVP, aim to add 30 high-quality product images across different categories:
- Shoes: 15 products (Nike, Adidas, Puma, etc.)
- Clothing: 10 products (T-shirts, jackets, etc.)
- Accessories: 5 products (bags, watches, etc.)

## Tips for Best Results

1. **Clear images:** Use well-lit, clear product photos
2. **Consistent backgrounds:** White or neutral backgrounds work best
3. **Similar products:** Include variations (e.g., same shoe in different colors)
4. **Authentic sources:** Use official brand images when possible
5. **Image quality:** Higher quality images produce better embeddings
