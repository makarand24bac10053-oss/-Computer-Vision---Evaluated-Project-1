"""
Unit tests for Module 2: Defect Detection & Surface Anomaly Inspection Engine.
"""

import pytest
import numpy as np
import cv2
from src.defect_detector import DefectInspectionEngine


@pytest.fixture
def detector():
    return DefectInspectionEngine(canny_low=40, canny_high=120, min_defect_area=30)


@pytest.fixture
def pristine_sample():
    """Clean simulated product package."""
    img = np.ones((400, 400, 3), dtype=np.uint8) * 240
    # Clean smooth blue rectangle
    cv2.rectangle(img, (80, 80), (320, 320), (200, 100, 40), -1)
    return img


@pytest.fixture
def defective_sample(pristine_sample):
    """Simulated product package with scratch and crack defects."""
    img = pristine_sample.copy()
    # Deep scratch line
    cv2.line(img, (100, 120), (260, 280), (20, 20, 20), thickness=3)
    cv2.line(img, (180, 150), (280, 160), (10, 10, 10), thickness=2)
    # Stain blotch
    cv2.circle(img, (200, 200), 30, (30, 40, 50), -1)
    return img


def test_pristine_sample_passes(detector, pristine_sample):
    result = detector.detect_surface_defects(pristine_sample)
    assert result["status"] in ["PASS", "WARNING"]
    assert result["defect_score"] < 15.0
    assert "annotated_image" in result
    assert "defect_mask" in result
    assert "heatmap" in result


def test_defective_sample_flagged(detector, defective_sample):
    result = detector.detect_surface_defects(defective_sample)
    assert result["defect_count"] > 0
    assert result["defect_score"] > 8.0
    assert result["status"] in ["WARNING", "REJECT"]
    assert len(result["defects"]) >= 1

    # Check defect structure
    first_defect = result["defects"][0]
    assert "type" in first_defect
    assert "severity" in first_defect
    assert "bbox" in first_defect
    assert len(first_defect["bbox"]) == 4


def test_custom_canny_thresholds(detector, pristine_sample):
    result = detector.detect_surface_defects(pristine_sample, canny_low=10, canny_high=50)
    assert "status" in result
    assert "metrics" in result
    assert result["metrics"]["product_area_px"] > 0
