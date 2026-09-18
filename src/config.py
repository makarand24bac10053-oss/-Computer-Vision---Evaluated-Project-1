"""
Configuration settings, threshold parameters, and product catalog for VisionCart-Inspect.
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLES_DIR = BASE_DIR / "samples"
DATABASE_PATH = BASE_DIR / "inspection_store.db"
REPORTS_DIR = BASE_DIR / "reports"

# Ensure runtime directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Preprocessing & Vision Parameters
DEFAULT_CANNY_LOW = 50
DEFAULT_CANNY_HIGH = 150
GAUSSIAN_BLUR_KERNEL = (5, 5)
BILATERAL_D = 9
BILATERAL_SIGMA_COLOR = 75
BILATERAL_SIGMA_SPACE = 75
CLAHE_CLIP_LIMIT = 2.0
CLAHE_GRID_SIZE = (8, 8)

# Defect Detection Sensitivity Parameters
MIN_DEFECT_AREA_PX = 45          # Minimum contour area to qualify as a defect (filters noise)
MAX_DEFECT_AREA_PX = 25000       # Maximum individual defect area
SCRATCH_ASPECT_RATIO_MIN = 2.8   # High aspect ratio indicates linear scratch or hairline crack
DENT_CIRCULARITY_THRESHOLD = 0.65# Low circularity + high perimeter irregularity indicates dent
DEFECT_SCORE_PASS_LIMIT = 8.0    # Defect score <= 8.0% is marked PASS
DEFECT_SCORE_WARN_LIMIT = 22.0   # Defect score 8.1 - 22.0% is WARNING, > 22.0% is REJECT

# Product Catalog & Barcode Database
PRODUCT_CATALOG = {
    "890103000101": {
        "sku": "SKU-BEV-001",
        "name": "Sparkling Citrus Soda (330ml)",
        "category": "Beverages",
        "price": 2.49,
        "tax_rate": 0.08,
        "primary_color_hsv": (35, 180, 200),  # Yellow/Gold
        "expected_shape": "cylinder"
    },
    "890103000202": {
        "sku": "SKU-SNK-002",
        "name": "Artisan Organic Oat Flakes (500g)",
        "category": "Breakfast & Pantry",
        "price": 4.99,
        "tax_rate": 0.05,
        "primary_color_hsv": (18, 120, 190),  # Warm amber/brown
        "expected_shape": "box"
    },
    "890103000303": {
        "sku": "SKU-DAI-003",
        "name": "Pure Alpine Milk Bottle (1L)",
        "category": "Dairy",
        "price": 3.19,
        "tax_rate": 0.05,
        "primary_color_hsv": (105, 30, 240),  # White / Pale Cyan
        "expected_shape": "bottle"
    },
    "890103000404": {
        "sku": "SKU-CLN-004",
        "name": "EcoClean Surface Disinfectant (750ml)",
        "category": "Household",
        "price": 5.75,
        "tax_rate": 0.10,
        "primary_color_hsv": (85, 160, 180),  # Green/Teal
        "expected_shape": "spray_bottle"
    },
    "890103000505": {
        "sku": "SKU-BAK-005",
        "name": "Belgian Dark Chocolate Bar (100g)",
        "category": "Confectionery",
        "price": 3.49,
        "tax_rate": 0.08,
        "primary_color_hsv": (12, 190, 80),   # Deep brown/burgundy
        "expected_shape": "rectangle"
    }
}

# Fallback catalog for unidentified items
UNKNOWN_PRODUCT = {
    "sku": "SKU-GEN-999",
    "name": "Unidentified Retail Item",
    "category": "General Goods",
    "price": 1.99,
    "tax_rate": 0.08,
    "primary_color_hsv": (0, 0, 128),
    "expected_shape": "unknown"
}
