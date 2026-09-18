"""
Module 2: Defect Detection & Surface Anomaly Inspection Engine.
Performs surface edge anomaly analysis, scratch/crack detection, morphological defect segmentation,
convexity defect evaluation, and automated quality grading (PASS / WARNING / REJECT).
"""

from typing import Dict, List, Any, Tuple, Optional
import cv2
import numpy as np
from src.config import (
    DEFAULT_CANNY_LOW,
    DEFAULT_CANNY_HIGH,
    MIN_DEFECT_AREA_PX,
    MAX_DEFECT_AREA_PX,
    SCRATCH_ASPECT_RATIO_MIN,
    DEFECT_SCORE_PASS_LIMIT,
    DEFECT_SCORE_WARN_LIMIT
)
from src.preprocessing import ImagePreprocessor


class DefectInspectionEngine:
    """
    Industrial-grade surface inspection engine combining edge anomaly analysis,
    morphological filtering, contour geometry, and heatmapping.
    """

    def __init__(
        self,
        canny_low: int = DEFAULT_CANNY_LOW,
        canny_high: int = DEFAULT_CANNY_HIGH,
        min_defect_area: int = MIN_DEFECT_AREA_PX,
        max_defect_area: int = MAX_DEFECT_AREA_PX,
    ):
        self.canny_low = canny_low
        self.canny_high = canny_high
        self.min_defect_area = min_defect_area
        self.max_defect_area = max_defect_area
        self.preprocessor = ImagePreprocessor()

    def detect_edge_anomalies(self, filtered_gray: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Extract high-frequency boundary and surface anomalies using Canny edge hysteresis.
        Masks out image borders to focus exclusively on the inspected product surface.
        """
        edges = cv2.Canny(filtered_gray, self.canny_low, self.canny_high)
        if mask is not None:
            # Erode mask slightly to avoid false positives along legitimate product outer boundary
            eroded_mask = cv2.erode(mask, cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7)), iterations=2)
            edges = cv2.bitwise_and(edges, edges, mask=eroded_mask)
        return edges

    def detect_surface_defects(
        self,
        image: np.ndarray,
        canny_low: Optional[int] = None,
        canny_high: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute end-to-end defect inspection on an input image.
        Returns:
            Dict containing:
                - status: 'PASS' | 'WARNING' | 'REJECT'
                - defect_score: float (0.0 to 100.0)
                - defect_count: int
                - defects: List of detected defect metadata
                - annotated_image: BGR image with bounding boxes & labels
                - defect_mask: Binary mask of anomaly pixels
                - heatmap: False-color thermal heatmap of defect density
                - metrics: Dictionary of quantitative dimensions
        """
        if canny_low is not None:
            self.canny_low = canny_low
        if canny_high is not None:
            self.canny_high = canny_high

        # 1. Preprocess
        pipe = self.preprocessor.process_pipeline(image)
        filtered_gray = pipe["filtered_gray"]
        foreground_mask = pipe["foreground_mask"]
        product_area = max(1.0, float(cv2.countNonZero(foreground_mask)))

        # 2. Extract surface edge anomalies
        raw_edges = self.detect_edge_anomalies(filtered_gray, foreground_mask)

        # 3. Morphological dilation to bridge hairline cracks and scratches
        kernel_line = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        dilated_edges = cv2.dilate(raw_edges, kernel_line, iterations=1)

        # 4. Color / Stain Anomaly Analysis in LAB space (identifies discolored blemishes)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        blurred_l = cv2.GaussianBlur(l_channel, (25, 25), 0)
        l_diff = cv2.absdiff(l_channel, blurred_l)
        _, stain_mask = cv2.threshold(l_diff, 28, 255, cv2.THRESH_BINARY)
        if foreground_mask is not None:
            eroded_fg = cv2.erode(foreground_mask, np.ones((9, 9), np.uint8), iterations=2)
            stain_mask = cv2.bitwise_and(stain_mask, stain_mask, mask=eroded_fg)

        # Combined defect mask
        combined_defect_mask = cv2.bitwise_or(dilated_edges, stain_mask)

        # 5. Contour extraction and geometric classification
        contours, _ = cv2.findContours(combined_defect_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        annotated = image.copy()
        defects_list: List[Dict[str, Any]] = []
        total_defect_pixel_area = 0.0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.min_defect_area or area > self.max_defect_area:
                continue

            total_defect_pixel_area += area
            x, y, w, h = cv2.boundingRect(cnt)
            perimeter = cv2.arcLength(cnt, True)
            aspect_ratio = float(max(w, h)) / max(1.0, float(min(w, h)))
            circularity = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0

            # Classification heuristic
            if aspect_ratio >= SCRATCH_ASPECT_RATIO_MIN:
                defect_type = "SCRATCH / CRACK"
                box_color = (0, 0, 255)  # Red
                severity = "HIGH"
            elif circularity < 0.35 and area > 100:
                defect_type = "SURFACE DENT / TEAR"
                box_color = (0, 140, 255)  # Orange
                severity = "MEDIUM"
            else:
                defect_type = "STAIN / BLEMISH"
                box_color = (0, 215, 255)  # Yellow-Orange
                severity = "LOW"

            defects_list.append({
                "type": defect_type,
                "severity": severity,
                "bbox": [int(x), int(y), int(w), int(h)],
                "area_px": float(round(area, 2)),
                "aspect_ratio": float(round(aspect_ratio, 2)),
                "circularity": float(round(circularity, 2))
            })

            # Draw bounding box and label
            cv2.rectangle(annotated, (x, y), (x + w, y + h), box_color, 2)
            label = f"{defect_type.split()[0]} ({int(area)}px)"
            cv2.putText(annotated, label, (x, max(15, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, box_color, 1, cv2.LINE_AA)

        # 6. Quantitative Defect Scoring
        # Defect ratio against visible product area
        defect_area_ratio = (total_defect_pixel_area / product_area) * 100.0
        # Severity weighting
        high_sev_count = sum(1 for d in defects_list if d["severity"] == "HIGH")
        med_sev_count = sum(1 for d in defects_list if d["severity"] == "MEDIUM")
        defect_score = min(100.0, (defect_area_ratio * 4.5) + (high_sev_count * 8.0) + (med_sev_count * 3.5))
        defect_score = float(round(defect_score, 2))

        # Status determination
        if defect_score <= DEFECT_SCORE_PASS_LIMIT and len(defects_list) <= 1:
            status = "PASS"
            status_color = (0, 200, 0)
        elif defect_score <= DEFECT_SCORE_WARN_LIMIT and high_sev_count == 0:
            status = "WARNING"
            status_color = (0, 215, 255)
        else:
            status = "REJECT"
            status_color = (0, 0, 255)

        # Overall status overlay on annotated image
        overlay_text = f"QC STATUS: {status} | Score: {defect_score}% | Defects: {len(defects_list)}"
        cv2.rectangle(annotated, (10, 10), (int(len(overlay_text) * 11) + 20, 42), (20, 20, 20), -1)
        cv2.putText(annotated, overlay_text, (16, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, status_color, 2, cv2.LINE_AA)

        # 7. False-color Heatmap generation
        density_blur = cv2.GaussianBlur(combined_defect_mask, (31, 31), 0)
        norm_density = cv2.normalize(density_blur, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        heatmap = cv2.applyColorMap(norm_density, cv2.COLORMAP_JET)

        # Alpha blend heatmap over original image
        alpha = 0.45
        blended_heatmap = cv2.addWeighted(heatmap, alpha, image, 1 - alpha, 0)

        return {
            "status": status,
            "defect_score": defect_score,
            "defect_count": len(defects_list),
            "defects": defects_list,
            "annotated_image": annotated,
            "defect_mask": combined_defect_mask,
            "heatmap": blended_heatmap,
            "metrics": {
                "product_area_px": float(round(product_area, 2)),
                "total_defect_area_px": float(round(total_defect_pixel_area, 2)),
                "defect_coverage_pct": float(round(defect_area_ratio, 3)),
                "high_severity_anomalies": high_sev_count,
                "medium_severity_anomalies": med_sev_count
            }
        }

    def evaluate_quality(self, image: np.ndarray) -> Dict[str, Any]:
        """Convenience alias for detect_surface_defects."""
        return self.detect_surface_defects(image)
