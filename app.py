"""
VisionCart-Inspect: Central Web Application & API Controller.
Provides real-time computer vision inspection, sample telemetry,
interactive shopping cart billing, and quality assurance auditing.
"""

import os
import base64
from pathlib import Path
from typing import Dict, Any
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory

from src.config import BASE_DIR, SAMPLES_DIR, REPORTS_DIR, DEFAULT_CANNY_LOW, DEFAULT_CANNY_HIGH
from src.preprocessing import ImagePreprocessor
from src.defect_detector import DefectInspectionEngine
from src.product_classifier import ProductClassifier
from src.billing_engine import BillingSystem
from src.storage import DatabaseManager
from src.sample_generator import SampleDataGenerator
from src.report_generator import ReportGenerator

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = "visioncart-secret-key-2026"

# Core service instances
preprocessor = ImagePreprocessor()
defect_detector = DefectInspectionEngine()
product_classifier = ProductClassifier()
billing_system = BillingSystem(discount_rate=0.05)  # 5% promotional discount
db_manager = DatabaseManager()
sample_generator = SampleDataGenerator()
report_generator = ReportGenerator()

# Ensure baseline sample images exist on startup
if not list(SAMPLES_DIR.glob("*.png")):
    sample_generator.generate_all_samples()


def mat_to_base64_data_uri(image: np.ndarray, format_ext: str = ".jpg") -> str:
    """Encode OpenCV BGR image matrix into browser-renderable base64 Data URI."""
    success, buffer = cv2.imencode(format_ext, image, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not success:
        return ""
    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"


@app.route("/")
def index():
    """Main application dashboard."""
    return render_template("index.html")


@app.route("/samples/<path:filename>")
def serve_sample_image(filename):
    """Directly serve simulated retail sample images."""
    return send_from_directory(SAMPLES_DIR, filename)


@app.route("/api/samples", methods=["GET"])
def get_sample_list():
    """List available simulated retail testing samples."""
    sample_files = sorted(list(SAMPLES_DIR.glob("*.png")))
    sample_data = []
    for f in sample_files:
        name_clean = f.stem.replace("_", " ").title()
        is_defective = any(term in f.stem.lower() for term in ["scratched", "dented", "cracked", "stained"])
        sample_data.append({
            "filename": f.name,
            "display_name": name_clean,
            "expected_verdict": "REJECT / WARNING" if is_defective else "PASS",
            "is_defective": is_defective
        })
    return jsonify({"samples": sample_data})


@app.route("/api/inspect_sample", methods=["POST"])
def inspect_sample():
    """Run CV inspection on a pre-generated retail sample image."""
    data = request.get_json() or {}
    filename = data.get("filename")
    canny_low = int(data.get("canny_low", DEFAULT_CANNY_LOW))
    canny_high = int(data.get("canny_high", DEFAULT_CANNY_HIGH))

    if not filename:
        return jsonify({"error": "No filename specified"}), 400

    image_path = SAMPLES_DIR / filename
    if not image_path.exists():
        return jsonify({"error": f"Sample file '{filename}' not found"}), 404

    image = cv2.imread(str(image_path))
    if image is None:
        return jsonify({"error": "Failed to read image"}), 500

    return process_and_package_inspection(image, canny_low, canny_high, filename=filename)


@app.route("/api/inspect_upload", methods=["POST"])
def inspect_upload():
    """Run CV inspection on uploaded image file or base64 frame from webcam."""
    canny_low = int(request.form.get("canny_low", DEFAULT_CANNY_LOW))
    canny_high = int(request.form.get("canny_high", DEFAULT_CANNY_HIGH))

    image = None
    filename = "uploaded_scan.jpg"

    if "file" in request.files:
        file = request.files["file"]
        if file.filename:
            file_bytes = np.frombuffer(file.read(), np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            filename = file.filename
    elif request.is_json:
        json_data = request.get_json()
        b64_data = json_data.get("image_base64", "")
        canny_low = int(json_data.get("canny_low", DEFAULT_CANNY_LOW))
        canny_high = int(json_data.get("canny_high", DEFAULT_CANNY_HIGH))
        if b64_data:
            if "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]
            img_bytes = base64.b64decode(b64_data)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if image is None:
        return jsonify({"error": "No valid image payload received"}), 400

    return process_and_package_inspection(image, canny_low, canny_high, filename=filename)


def process_and_package_inspection(image: np.ndarray, canny_low: int, canny_high: int, filename: str = ""):
    """Core workflow helper: classification -> defect inspection -> database telemetry -> visualization."""
    # 1. Product recognition
    product = product_classifier.identify_product(image)

    # 2. Defect analysis
    qc_result = defect_detector.detect_surface_defects(
        image, canny_low=canny_low, canny_high=canny_high
    )

    # 3. Database persistence
    rec_id = db_manager.log_inspection(product, qc_result, image_filename=filename)

    # 4. Generate visual step images
    pipeline_steps = preprocessor.process_pipeline(image)

    response_payload = {
        "inspection_id": rec_id,
        "product": product,
        "qc_result": {
            "status": qc_result["status"],
            "defect_score": qc_result["defect_score"],
            "defect_count": qc_result["defect_count"],
            "defects": qc_result["defects"],
            "metrics": qc_result["metrics"]
        },
        "images": {
            "annotated": mat_to_base64_data_uri(qc_result["annotated_image"]),
            "original": mat_to_base64_data_uri(image),
            "clahe_enhanced": mat_to_base64_data_uri(pipeline_steps["clahe_bgr"]),
            "edges": mat_to_base64_data_uri(qc_result["defect_mask"]),
            "heatmap": mat_to_base64_data_uri(qc_result["heatmap"])
        }
    }
    return jsonify(response_payload)


@app.route("/api/cart/add", methods=["POST"])
def add_to_cart():
    """Add verified inspected item to active cart or route to quarantine."""
    payload = request.get_json() or {}
    product = payload.get("product")
    qc_result = payload.get("qc_result")
    allow_override = payload.get("allow_override", False)

    if not product or not qc_result:
        return jsonify({"error": "Missing product or inspection data"}), 400

    result = billing_system.process_inspected_item(product, qc_result, allow_defective_override=allow_override)
    return jsonify(result)


@app.route("/api/cart", methods=["GET"])
def get_cart():
    """Retrieve active cart financial summary and quarantined incidents."""
    return jsonify(billing_system.get_cart_summary())


@app.route("/api/cart/remove", methods=["POST"])
def remove_from_cart():
    """Remove item from cart by SKU."""
    payload = request.get_json() or {}
    sku = payload.get("sku")
    success = billing_system.remove_item(sku)
    return jsonify({"success": success, "cart": billing_system.get_cart_summary()})


@app.route("/api/cart/clear", methods=["POST"])
def clear_cart():
    """Empty cart."""
    billing_system.clear_cart()
    return jsonify({"success": True, "cart": billing_system.get_cart_summary()})


@app.route("/api/cart/checkout", methods=["POST"])
def checkout_cart():
    """Finalize point-of-sale transaction, generate PDF invoice, and save to DB."""
    payload = request.get_json() or {}
    payment_method = payload.get("payment_method", "Digital Payment / UPI")

    try:
        receipt = billing_system.generate_receipt(payment_method=payment_method)
        # Save to SQLite
        db_manager.save_transaction(receipt)
        # Generate PDF Invoice
        pdf_path = report_generator.generate_invoice_receipt(receipt)
        pdf_filename = Path(pdf_path).name

        # Clear cart for next customer
        billing_system.clear_cart()

        return jsonify({
            "status": "SUCCESS",
            "receipt": receipt,
            "invoice_pdf_url": f"/reports/{pdf_filename}"
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/certificate", methods=["POST"])
def generate_cert():
    """Generate on-demand PDF Quality Certificate for current inspection."""
    payload = request.get_json() or {}
    product = payload.get("product")
    qc_result = payload.get("qc_result")

    if not product or not qc_result:
        return jsonify({"error": "Missing inspection details"}), 400

    pdf_path = report_generator.generate_inspection_certificate(product, qc_result)
    pdf_filename = Path(pdf_path).name
    return jsonify({"certificate_url": f"/reports/{pdf_filename}"})


@app.route("/reports/<path:filename>")
def download_report(filename):
    """Download generated PDF audit certificates or customer invoices."""
    return send_from_directory(REPORTS_DIR, filename, as_attachment=True)


@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    """Return quality compliance statistics."""
    return jsonify(db_manager.get_qc_analytics())


@app.route("/api/history", methods=["GET"])
def get_history():
    """Return recent inspection audit telemetry."""
    limit = int(request.args.get("limit", 20))
    return jsonify({"history": db_manager.get_recent_inspections(limit=limit)})


if __name__ == "__main__":
    print("=================================================================")
    print(" VisionCart-Inspect: Computer Vision Industrial & Retail Server   ")
    print(" Serving at: http://127.0.0.1:5000                               ")
    print("=================================================================")
    app.run(host="0.0.0.0", port=5000, debug=True)
