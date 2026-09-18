"""
Unit tests for Module 1: Image Acquisition & Preprocessing Pipeline.
"""

import pytest
import numpy as np
import cv2
from src.preprocessing import ImagePreprocessor


@pytest.fixture
def preprocessor():
    return ImagePreprocessor()


@pytest.fixture
def sample_bgr_image():
    # Synthetic 100x100 3-channel test image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[20:80, 20:80] = [120, 180, 220]
    return img


def test_to_grayscale(preprocessor, sample_bgr_image):
    gray = preprocessor.to_grayscale(sample_bgr_image)
    assert len(gray.shape) == 2
    assert gray.shape == (100, 100)
    assert gray.dtype == np.uint8


def test_to_hsv_and_lab(preprocessor, sample_bgr_image):
    hsv = preprocessor.to_hsv(sample_bgr_image)
    assert hsv.shape == (100, 100, 3)
    lab = preprocessor.to_lab(sample_bgr_image)
    assert lab.shape == (100, 100, 3)


def test_enhance_contrast_clahe(preprocessor, sample_bgr_image):
    enhanced = preprocessor.enhance_contrast(sample_bgr_image)
    assert enhanced.shape == sample_bgr_image.shape
    assert enhanced.dtype == np.uint8

    # Also test on grayscale
    gray = preprocessor.to_grayscale(sample_bgr_image)
    enhanced_gray = preprocessor.enhance_contrast(gray)
    assert enhanced_gray.shape == (100, 100)


def test_reduce_noise_bilateral(preprocessor, sample_bgr_image):
    noisy = sample_bgr_image.copy()
    noise = np.random.normal(0, 15, sample_bgr_image.shape).astype(np.int16)
    noisy = np.clip(noisy.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    filtered = preprocessor.reduce_noise(noisy, method="bilateral")
    assert filtered.shape == noisy.shape
    assert filtered.dtype == np.uint8


def test_extract_foreground_mask(preprocessor, sample_bgr_image):
    mask, largest_cnt = preprocessor.extract_foreground_mask(sample_bgr_image)
    assert mask.shape == (100, 100)
    assert mask.dtype == np.uint8
    assert largest_cnt is not None
    assert cv2.contourArea(largest_cnt) > 0


def test_compute_gradient_magnitude(preprocessor, sample_bgr_image):
    gray = preprocessor.to_grayscale(sample_bgr_image)
    grad = preprocessor.compute_gradient_magnitude(gray)
    assert grad.shape == (100, 100)
    assert grad.max() > 0
