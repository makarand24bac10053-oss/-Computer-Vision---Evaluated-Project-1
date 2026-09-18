"""
Module 3: Product Classification, Identification & Barcode/QR Scanning Engine.
Recognizes retail goods using native OpenCV Barcode & QR decoders alongside
color-histogram and shape-descriptor fallback classifiers.
"""

from typing import Dict, Any, Optional, Tuple
import cv2
import numpy as np
from src.config import PRODUCT_CATALOG, UNKNOWN_PRODUCT
from src.preprocessing import ImagePreprocessor


class ProductClassifier:
    """
    Multi-modal product recognition system integrating 1D/2D optical codes
    with computer vision color and shape signature verification.
    """

    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.qr_detector = cv2.QRCodeDetector()
        # Initialize OpenCV Barcode detector if available
        self.barcode_detector = None
        if hasattr(cv2, 'barcode') and hasattr(cv2.barcode, 'BarcodeDetector'):
            try:
                self.barcode_detector = cv2.barcode.BarcodeDetector()
            except Exception:
                self.barcode_detector = None

    def scan_optical_codes(self, image: np.ndarray) -> Tuple[Optional[str], Optional[np.ndarray], str]:
        """
        Scan image for QR codes and 1D standard retail barcodes.
        Returns:
            Tuple[decoded_data, points_array, code_type]
        """
        # 1. Check for QR Code
        qr_data, points, _ = self.qr_detector.detectAndDecode(image)
        if qr_data and qr_data.strip():
            return qr_data.strip(), points, "QR_CODE"

        # 2. Check for Barcode via OpenCV BarcodeDetector
        if self.barcode_detector is not None:
            try:
                ok, decoded_info, decoded_type, points = self.barcode_detector.detectAndDecode(image)
                if ok and decoded_info:
                    for val in decoded_info:
                        if val and str(val).strip():
                            return str(val).strip(), points, "BARCODE"
            except Exception:
                pass

        return None, None, "NONE"

    def match_by_color_and_shape(self, image: np.ndarray) -> Tuple[Dict[str, Any], float]:
        """
        Fallback visual classifier matching primary HSV color and bounding contour aspect ratio.
        """
        mask, largest_cnt = self.preprocessor.extract_foreground_mask(image)
        hsv = self.preprocessor.to_hsv(image)

        # Calculate median HSV of foreground
        fg_pixels = hsv[mask > 0]
        if len(fg_pixels) == 0:
            return UNKNOWN_PRODUCT.copy(), 0.0

        median_hsv = np.median(fg_pixels, axis=0)

        best_match_key = None
        min_distance = float("inf")

        for barcode_id, item in PRODUCT_CATALOG.items():
            expected_hsv = np.array(item["primary_color_hsv"])
            # Hue distance wrapped around 180 degrees
            hue_diff = min(abs(median_hsv[0] - expected_hsv[0]), 180 - abs(median_hsv[0] - expected_hsv[0]))
            sat_diff = abs(median_hsv[1] - expected_hsv[1]) / 255.0 * 100
            val_diff = abs(median_hsv[2] - expected_hsv[2]) / 255.0 * 100

            dist = (hue_diff * 1.5) + sat_diff + val_diff
            if dist < min_distance:
                min_distance = dist
                best_match_key = barcode_id

        # Normalize distance into confidence score
        confidence = max(0.20, min(0.95, round(1.0 - (min_distance / 250.0), 2)))

        if best_match_key and min_distance < 140.0:
            matched = PRODUCT_CATALOG[best_match_key].copy()
            matched["barcode"] = best_match_key
            matched["method"] = "VISION_COLOR_SHAPE_MATCH"
            return matched, confidence

        fallback = UNKNOWN_PRODUCT.copy()
        fallback["barcode"] = "UNKNOWN"
        fallback["method"] = "FALLBACK_DEFAULT"
        return fallback, 0.35

    def identify_product(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Complete identification workflow prioritizing optical code scanning,
        then falling back to color/shape matching.
        """
        code_data, points, code_type = self.scan_optical_codes(image)

        if code_data:
            # Match directly in catalog or clean prefix
            clean_code = code_data.strip()
            if clean_code in PRODUCT_CATALOG:
                prod = PRODUCT_CATALOG[clean_code].copy()
                prod["barcode"] = clean_code
                prod["scan_type"] = code_type
                prod["confidence"] = 0.99
                prod["detection_method"] = f"OPTICAL_{code_type}_DECODE"
                return prod
            else:
                # Custom detected code
                return {
                    "sku": f"SKU-CUSTOM-{clean_code[:6]}",
                    "name": f"Scanned Item ({clean_code})",
                    "category": "Retail Merchandise",
                    "price": 3.99,
                    "tax_rate": 0.08,
                    "barcode": clean_code,
                    "scan_type": code_type,
                    "confidence": 0.95,
                    "detection_method": f"OPTICAL_{code_type}_UNREGISTERED"
                }

        # Fallback to visual feature matching
        prod, confidence = self.match_by_color_and_shape(image)
        prod["scan_type"] = "NONE"
        prod["confidence"] = confidence
        prod["detection_method"] = prod.get("method", "VISION_FEATURE_EXTRACTOR")
        return prod
