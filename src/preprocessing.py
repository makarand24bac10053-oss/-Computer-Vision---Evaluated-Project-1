"""
Module 1: Image Acquisition & Preprocessing Pipeline.
Provides standardized computer vision preprocessing routines including color-space conversions,
edge-preserving bilateral filtering, CLAHE contrast enhancement, and foreground segmentation.
"""

from typing import Dict, Tuple, Optional
import cv2
import numpy as np
from src.config import (
    GAUSSIAN_BLUR_KERNEL,
    BILATERAL_D,
    BILATERAL_SIGMA_COLOR,
    BILATERAL_SIGMA_SPACE,
    CLAHE_CLIP_LIMIT,
    CLAHE_GRID_SIZE,
)


class ImagePreprocessor:
    """
    Encapsulates core preprocessing operations for retail product inspection.
    """

    def __init__(self, clip_limit: float = CLAHE_CLIP_LIMIT, grid_size: Tuple[int, int] = CLAHE_GRID_SIZE):
        self.clip_limit = clip_limit
        self.grid_size = grid_size
        self.clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)

    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert BGR image to single-channel 8-bit grayscale."""
        if len(image.shape) == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def to_hsv(self, image: np.ndarray) -> np.ndarray:
        """Convert BGR image to HSV color space."""
        return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    def to_lab(self, image: np.ndarray) -> np.ndarray:
        """Convert BGR image to CIELAB color space."""
        return cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance localized image contrast using Contrast Limited Adaptive Histogram Equalization (CLAHE).
        If image is color, CLAHE is applied specifically to the Luminance channel in LAB space.
        """
        if len(image.shape) == 2:
            return self.clahe.apply(image)

        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        enhanced_l = self.clahe.apply(l)
        merged = cv2.merge((enhanced_l, a, b))
        return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

    def filter_noise(self, image: np.ndarray, method: str = "bilateral") -> np.ndarray:
        """
        Smooth noise while strictly preserving sharp boundaries and scratch edges.
        Options: 'bilateral' (edge-preserving) or 'gaussian'.
        """
        if method == "bilateral":
            return cv2.bilateralFilter(
                image,
                d=BILATERAL_D,
                sigmaColor=BILATERAL_SIGMA_COLOR,
                sigmaSpace=BILATERAL_SIGMA_SPACE
            )
        return cv2.GaussianBlur(image, GAUSSIAN_BLUR_KERNEL, 0)

    # Convenience alias
    reduce_noise = filter_noise

    def extract_foreground_mask(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Segment the foreground retail package from the neutral background.
        Returns:
            Tuple[binary_mask, foreground_contour]
        """
        gray = self.to_grayscale(image)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)

        # Otsu thresholding with inverse logic assuming standard light or dark backdrop
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Morphological opening and closing to remove isolated specs & fill object interior
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=3)

        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            # Fallback full mask if no distinct contour found
            mask = np.ones(gray.shape, dtype=np.uint8) * 255
            return mask, np.array([])

        largest_contour = max(contours, key=cv2.contourArea)
        mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.drawContours(mask, [largest_contour], -1, 255, thickness=cv2.FILLED)

        return mask, largest_contour

    def compute_gradient_magnitude(self, gray_image: np.ndarray) -> np.ndarray:
        """
        Compute Sobel gradient magnitude to evaluate high-frequency surface structural transitions.
        """
        sobel_x = cv2.Sobel(gray_image, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray_image, cv2.CV_64F, 0, 1, ksize=3)
        grad_mag = np.sqrt(sobel_x**2 + sobel_y**2)
        normalized = cv2.normalize(grad_mag, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        return normalized

    def compute_color_histogram(self, image_hsv: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Generate a 2D Hue-Saturation color histogram for product profile matching.
        """
        hist = cv2.calcHist([image_hsv], [0, 1], mask, [18, 25], [0, 180, 0, 256])
        cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        return hist

    def process_pipeline(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Executes full preprocessing pipeline and returns a dictionary of all intermediate views.
        """
        if image is None or image.size == 0:
            raise ValueError("Input image is empty or invalid.")

        gray = self.to_grayscale(image)
        enhanced_color = self.enhance_contrast(image)
        enhanced_gray = self.to_grayscale(enhanced_color)
        filtered_gray = self.filter_noise(enhanced_gray, method="bilateral")
        foreground_mask, largest_cnt = self.extract_foreground_mask(image)
        gradient_mag = self.compute_gradient_magnitude(filtered_gray)

        return {
            "original": image,
            "grayscale": gray,
            "clahe_enhanced": enhanced_color,
            "filtered_gray": filtered_gray,
            "foreground_mask": foreground_mask,
            "gradient_magnitude": gradient_mag
        }
