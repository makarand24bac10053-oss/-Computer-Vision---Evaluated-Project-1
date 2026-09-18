# VisionCart-Inspect

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-5.0.0%20%2F%204.8+-red.svg)](https://opencv.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1+-green.svg)](https://palletsprojects.com/p/flask/)
[![Tests](https://img.shields.io/badge/pytest-19%20passed%20(100%25)-brightgreen.svg)](https://docs.pytest.org/)
[![Academic](https://img.shields.io/badge/VITyarthi-Build%20Your%20Own%20Project-orange.svg)](#)

> **VisionCart-Inspect** is an end-to-end Computer Vision system for **Automated Retail Checkout and Industrial Surface Defect Inspection**, built in strict compliance with the **VITyarthi — Build Your Own Project** course evaluation guidelines.

---

## 1. Overview
In modern manufacturing and smart retail stores, visual quality inspection is essential to ensure defective, cracked, or contaminated items do not reach consumers. At the same time, autonomous retail checkout systems demand ultra-fast item identification.

**VisionCart-Inspect** bridges both challenges into a unified edge-computing architecture:
1. **Identifies** items via optical barcodes, 2D QR codes, and fallback HSV color/shape signatures.
2. **Scans** surface geometry for micro-defects (scratches, dents, cracks, and discoloration) in under 100ms.
3. **Decides** whether the item passes quality standards (`PASS`, `WARNING`, `REJECT`).
4. **Quarantines** damaged items and automatically routes verified goods to an automated point-of-sale billing cart.
5. **Generates** ISO-grade PDF quality certificates and itemized transaction invoices.

---

## 2. Key Features

- **7-Module Decoupled Architecture**: Modular, object-oriented design cleanly separating preprocessing, defect detection, classification, billing, storage, synthetic data generation, and PDF reporting.
- **Advanced Image Preprocessing**: Bilateral edge-preserving filtering, Contrast Limited Adaptive Histogram Equalization (CLAHE), and LAB/HSV color segmentation.
- **Multi-Class Defect Localization**: Identifies and bounds linear scratches, structural hairline cracks, perimeter dents/tears, and chemical discoloration blemishes.
- **Thermal Defect Heatmap**: Computes spatial anomaly density and renders a blended false-color JET heatmap over the product silhouette.
- **Multi-Modal Product Recognition**: Integrates native OpenCV 1D barcode and 2D QR decoders with fallback HSV color and geometric aspect ratio matching.
- **Point-of-Sale Billing & Defect Quarantine**: Prevents rejected items from being added to customer carts; applies configurable promotional discounts and calculates sales tax.
- **Persistent SQLite Telemetry**: Automatically records inspection logs, defect scores, detected bounding boxes, and transaction invoices.
- **Interactive Dark Glassmorphic Dashboard**: Real-time HUD viewport, interactive Canny hysteresis sliders, pipeline step tabs, live cart drawer, and checkout modal.
- **Synthetic Retail Test Suite**: Pre-packaged with 8 clean and defective retail samples (soda cans, oat boxes, milk bottles, disinfectant sprays) so the system can be fully demonstrated offline without a webcam.

---

## 3. Technologies & Tools Used

| Domain | Technology / Library | Purpose |
| :--- | :--- | :--- |
| **Core Language** | Python 3.13 / 3.11+ | Business logic, algorithms, and service controllers |
| **Computer Vision** | OpenCV (`cv2`) 5.0.0 | Image filtering, CLAHE, Canny hysteresis, contour geometry, QR encoding/decoding |
| **Scientific Computing** | NumPy | Array manipulation, color-space distance computations, histogram analysis |
| **Web Server** | Flask 3.1.3 | REST APIs, live webcam streaming, static asset serving |
| **Database** | SQLite 3 | Embedded ACID-compliant relational persistence for telemetry and sales receipts |
| **Document Generation** | ReportLab 5.0.1 | Automated compilation of PDF Quality Certificates and Tax Invoices |
| **Automated Testing** | Pytest 9.1.1 | Comprehensive unit test suite across all functional modules |
| **Frontend UI** | HTML5, Vanilla CSS3, JavaScript | Dark glassmorphism design, responsive grid, dynamic DOM manipulation |

---

## 4. Repository & Project Structure

```
Vityarthi/
├── src/
│   ├── __init__.py               # Package metadata
│   ├── config.py                 # Configuration parameters, thresholds & product catalog
│   ├── preprocessing.py          # Module 1: CLAHE, Bilateral filtering, HSV/LAB conversions
│   ├── defect_detector.py        # Module 2: Edge anomaly, contour analysis, heatmap, quality scoring
│   ├── product_classifier.py     # Module 3: Barcode/QR recognition, color histogram & shape fallback
│   ├── billing_engine.py         # Module 4: Cart state, tax/discount calculation, receipt generation
│   ├── storage.py                # Module 5: SQLite database for inspection telemetry and sales receipts
│   ├── sample_generator.py       # Module 6: Synthetic retail defect image generator
│   └── report_generator.py       # Module 7: Automated PDF quality certificate & tax invoice generator
├── static/
│   ├── css/
│   │   └── style.css             # Vanilla CSS design system (dark glassmorphism, responsive grid)
│   └── js/
│       └── app.js                # Frontend client controller (DOM updates, pipeline viewer, cart actions)
├── templates/
│   └── index.html                # Semantic, modern single-page dashboard
├── tests/
│   ├── __init__.py
│   ├── test_preprocessing.py     # Unit tests for filtering, CLAHE, color transformations
│   ├── test_defect_detector.py   # Unit tests for defect detection, contour extraction, pass/fail grading
│   ├── test_product_classifier.py# Unit tests for QR/barcode decoding and color fallback
│   ├── test_billing.py           # Unit tests for cart additions, discounts, tax, quarantine rules
│   └── test_storage.py           # Unit tests for SQLite audit logging and aggregation queries
├── samples/                      # Directory containing 8 synthetic clean & defective retail packages
├── reports/                      # Generated PDF inspection certificates and invoices
├── statement.md                  # Requirement 5.2: Problem statement, scope, target users, features
├── README.md                     # Requirement 5.1: Complete project guide and instructions
├── PROJECT_REPORT.md             # Requirement 6: Full 15-chapter academic report with Mermaid UML & ER diagrams
├── generate_pdf_report.py        # Automated script compiling PROJECT_REPORT.md into submission PDF
├── requirements.txt              # Project dependencies
└── app.py                        # Central web server and REST API controller
```

---

## 5. Installation & Execution Guide

### Prerequisites
- Python 3.10 or higher (tested on Python 3.13.5)
- Git (optional, for cloning)

### Step 1: Install Dependencies
Open PowerShell or your terminal in this directory and install the requirements:
```bash
pip install -r requirements.txt
```

### Step 2: Generate Offline Test Samples (Optional - automatically run on startup)
```bash
python -m src.sample_generator
```

### Step 3: Run the Web Dashboard
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 6. Testing Instructions

To execute the automated test suite with full verbose output:
```bash
pytest tests/ -v
```

Expected result:
```
============================= 19 passed in 0.82s ==============================
```

---

## 7. Generating Academic Submission PDF

To compile the comprehensive 15-chapter academic project report into a submission-ready PDF for the VITyarthi portal:
```bash
python generate_pdf_report.py
```
This generates:
```
reports/Project_Report_Submission.pdf
```
