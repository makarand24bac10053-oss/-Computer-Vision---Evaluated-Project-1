"""
Module 6: Synthetic Retail Sample & Defect Image Generator.
Generates realistic simulated retail product packages (pristine and defective)
complete with embedded optical QR/barcodes, texture, and surface anomalies
(scratches, dents, cracks, and chemical discoloration).
"""

from typing import Dict, List, Tuple
from pathlib import Path
import os
import cv2
import numpy as np
from src.config import SAMPLES_DIR, PRODUCT_CATALOG


class SampleDataGenerator:
    """
    Synthesizes retail product inspection images for automated testing and demonstrations.
    """

    def __init__(self, output_dir: Path = SAMPLES_DIR):
        self.output_dir = Path(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        try:
            self.qr_encoder = cv2.QRCodeEncoder.create()
        except Exception:
            self.qr_encoder = None

    def render_qr_badge(self, data_str: str, target_size: int = 90) -> np.ndarray:
        """
        Generate a high-contrast QR code patch using OpenCV's native QRCodeEncoder.
        """
        if self.qr_encoder is not None:
            try:
                qr_matrix = self.qr_encoder.encode(data_str)
                # Normalize values if 0/1 or 0/255
                if qr_matrix.max() <= 1:
                    qr_img = (qr_matrix * 255).astype(np.uint8)
                else:
                    qr_img = qr_matrix.astype(np.uint8)
                
                # Invert if white/black inverted
                # Ensure 3-channel
                qr_resized = cv2.resize(qr_img, (target_size, target_size), interpolation=cv2.INTER_NEAREST)
                qr_bgr = cv2.cvtColor(qr_resized, cv2.COLOR_GRAY2BGR)
                # Add quiet zone border (5px white border)
                bordered = cv2.copyMakeBorder(qr_bgr, 6, 6, 6, 6, cv2.BORDER_CONSTANT, value=[255, 255, 255])
                return cv2.resize(bordered, (target_size, target_size), interpolation=cv2.INTER_NEAREST)
            except Exception:
                pass

        # Fallback QR pattern generator if encoder fails
        badge = np.ones((target_size, target_size, 3), dtype=np.uint8) * 255
        cv2.rectangle(badge, (4, 4), (target_size - 4, target_size - 4), (0, 0, 0), 2)
        cv2.rectangle(badge, (12, 12), (32, 32), (0, 0, 0), -1)
        cv2.rectangle(badge, (target_size - 32, 12), (target_size - 12, 32), (0, 0, 0), -1)
        cv2.rectangle(badge, (12, target_size - 32), (32, target_size - 12), (0, 0, 0), -1)
        cv2.putText(badge, "CODE", (18, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
        cv2.putText(badge, data_str[-4:], (16, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        return badge

    def overlay_patch(self, base_img: np.ndarray, patch: np.ndarray, x: int, y: int) -> None:
        """Helper to overlay patch within bounds."""
        h, w = patch.shape[:2]
        bh, bw = base_img.shape[:2]
        if x + w <= bw and y + h <= bh:
            base_img[y : y + h, x : x + w] = patch

    def add_scratch_defects(self, img: np.ndarray, count: int = 3) -> None:
        """Draw jagged linear scratches with high edge response."""
        for _ in range(count):
            start_x = np.random.randint(140, 360)
            start_y = np.random.randint(120, 380)
            points = [(start_x, start_y)]
            curr_x, curr_y = start_x, start_y
            
            steps = np.random.randint(4, 8)
            for _ in range(steps):
                curr_x += np.random.randint(-18, 25)
                curr_y += np.random.randint(15, 45)
                points.append((curr_x, curr_y))

            pts_arr = np.array(points, np.int32).reshape((-1, 1, 2))
            # Dark scratch groove
            cv2.polylines(img, [pts_arr], isClosed=False, color=(25, 25, 30), thickness=2, lineType=cv2.LINE_AA)
            # High-contrast specular reflection edge
            pts_shifted = pts_arr + np.array([1, 1])
            cv2.polylines(img, [pts_shifted], isClosed=False, color=(230, 230, 240), thickness=1, lineType=cv2.LINE_AA)

    def add_crack_defects(self, img: np.ndarray, origin: Tuple[int, int]) -> None:
        """Simulate branching spiderweb structural crack."""
        branches = 4
        for _ in range(branches):
            cx, cy = origin
            for _ in range(np.random.randint(5, 10)):
                nx = cx + np.random.randint(-20, 20)
                ny = cy + np.random.randint(10, 35)
                cv2.line(img, (cx, cy), (nx, ny), (15, 15, 20), thickness=2, lineType=cv2.LINE_AA)
                cv2.line(img, (cx + 1, cy), (nx + 1, ny), (220, 220, 230), thickness=1, lineType=cv2.LINE_AA)
                cx, cy = nx, ny

    def add_stain_defects(self, img: np.ndarray, center: Tuple[int, int], radius: int = 35) -> None:
        """Simulate chemical discoloration / oil stain."""
        overlay = img.copy()
        cv2.circle(overlay, center, radius, (40, 70, 45), -1)
        cv2.ellipse(overlay, center, (radius + 15, radius - 8), 35, 0, 360, (30, 60, 40), -1)
        cv2.addWeighted(overlay, 0.65, img, 0.35, 0, img)

    def generate_soda_can(self, defective: bool = False) -> np.ndarray:
        """
        Generate Citrus Sparkling Soda (330ml Can) - SKU-BEV-001 (Yellow/Gold body).
        """
        img = np.ones((500, 500, 3), dtype=np.uint8) * 245  # Clean conveyor background
        # Can body: Rounded rectangle / cylinder
        cv2.rectangle(img, (170, 90), (330, 410), (30, 185, 230), -1)  # Warm Golden Yellow (BGR)
        # Silver can rim top and bottom
        cv2.ellipse(img, (250, 90), (80, 20), 0, 0, 360, (200, 200, 205), -1)
        cv2.ellipse(img, (250, 410), (80, 18), 0, 0, 360, (175, 175, 180), -1)
        cv2.ellipse(img, (250, 90), (60, 12), 0, 0, 360, (150, 150, 155), 2)
        # Gradient shading band for 3D metallic feel
        shading = np.zeros_like(img)
        cv2.rectangle(shading, (170, 90), (200, 410), (30, 30, 30), -1)
        cv2.rectangle(shading, (300, 90), (330, 410), (40, 40, 40), -1)
        img = cv2.subtract(img, shading)

        # Label graphics
        cv2.rectangle(img, (185, 160), (315, 290), (20, 140, 210), -1)
        cv2.putText(img, "SPARK", (200, 200), cv2.FONT_HERSHEY_DUPLEX, 0.9, (255, 255, 255), 2)
        cv2.putText(img, "CITRUS", (200, 235), cv2.FONT_HERSHEY_DUPLEX, 0.75, (255, 255, 255), 2)
        cv2.putText(img, "330 ml", (215, 265), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        # Embedded Optical QR Code
        qr = self.render_qr_badge("890103000101", target_size=75)
        self.overlay_patch(img, qr, 212, 310)

        if defective:
            # Add heavy scratches and dents
            self.add_scratch_defects(img, count=4)
            # Add dent defect on left edge
            cv2.ellipse(img, (170, 240), (20, 45), 0, 0, 360, (245, 245, 245), -1)
            cv2.ellipse(img, (170, 240), (20, 45), 0, 0, 360, (40, 40, 40), 2)

        return img

    def generate_oat_flakes_box(self, defective: bool = False) -> np.ndarray:
        """
        Generate Artisan Oat Flakes (500g Box) - SKU-SNK-002 (Warm Amber Box).
        """
        img = np.ones((500, 500, 3), dtype=np.uint8) * 242
        # Box body
        cv2.rectangle(img, (130, 80), (370, 420), (55, 120, 200), -1)  # Warm amber/brown
        cv2.rectangle(img, (130, 80), (370, 420), (30, 80, 150), 3)

        # Front banner
        cv2.rectangle(img, (145, 120), (355, 220), (240, 245, 250), -1)
        cv2.putText(img, "ARTISAN", (190, 155), cv2.FONT_HERSHEY_DUPLEX, 0.8, (20, 60, 120), 2)
        cv2.putText(img, "ORGANIC OATS", (160, 185), cv2.FONT_HERSHEY_DUPLEX, 0.65, (30, 90, 170), 2)
        cv2.putText(img, "100% Whole Grain - 500g", (160, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 80, 80), 1)

        # Illustration window
        cv2.circle(img, (250, 275), 45, (80, 160, 230), -1)
        cv2.circle(img, (250, 275), 45, (255, 255, 255), 3)

        # Embedded Optical QR Code
        qr = self.render_qr_badge("890103000202", target_size=80)
        self.overlay_patch(img, qr, 210, 330)

        if defective:
            # Punctured corner / tear
            cv2.fillPoly(img, [np.array([[340, 80], [370, 80], [370, 130], [330, 110]])], (242, 242, 242))
            cv2.polylines(img, [np.array([[340, 80], [330, 110], [370, 130]])], isClosed=False, color=(20, 20, 20), thickness=3)
            self.add_scratch_defects(img, count=2)

        return img

    def generate_milk_bottle(self, defective: bool = False) -> np.ndarray:
        """
        Generate Pure Alpine Milk (1L Bottle) - SKU-DAI-003 (Pale Blue/White).
        """
        img = np.ones((500, 500, 3), dtype=np.uint8) * 240
        # Bottle neck and body
        cv2.rectangle(img, (220, 60), (280, 120), (230, 235, 240), -1)  # Neck
        cv2.rectangle(img, (215, 45), (285, 60), (200, 100, 50), -1)    # Blue Cap
        # Taper to body
        taper_pts = np.array([[220, 120], [150, 180], [350, 180], [280, 120]], np.int32)
        cv2.fillPoly(img, [taper_pts], (235, 240, 245))
        # Main body
        cv2.rectangle(img, (150, 180), (350, 440), (240, 245, 250), -1)
        cv2.rectangle(img, (150, 180), (350, 440), (180, 185, 190), 2)

        # Bottle Label
        cv2.rectangle(img, (160, 230), (340, 320), (210, 150, 60), -1)
        cv2.putText(img, "ALPINE MILK", (175, 270), cv2.FONT_HERSHEY_DUPLEX, 0.75, (255, 255, 255), 2)
        cv2.putText(img, "Fresh Pasteurized 1L", (180, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Embedded Optical QR Code
        qr = self.render_qr_badge("890103000303", target_size=75)
        self.overlay_patch(img, qr, 212, 340)

        if defective:
            # Add structural spiderweb glass crack
            self.add_crack_defects(img, origin=(250, 210))

        return img

    def generate_disinfectant_bottle(self, defective: bool = False) -> np.ndarray:
        """
        Generate EcoClean Disinfectant (750ml) - SKU-CLN-004 (Green/Teal).
        """
        img = np.ones((500, 500, 3), dtype=np.uint8) * 242
        # Spray trigger head
        cv2.rectangle(img, (220, 50), (275, 120), (220, 220, 220), -1)
        cv2.rectangle(img, (275, 60), (320, 90), (180, 50, 40), -1)     # Nozzle
        # Body
        body_pts = np.array([[220, 120], [160, 190], [160, 430], [340, 430], [340, 190], [275, 120]], np.int32)
        cv2.fillPoly(img, [body_pts], (160, 200, 60))                    # Teal-Green (BGR)
        cv2.polylines(img, [body_pts], True, (110, 150, 40), 2)

        # Label
        cv2.rectangle(img, (180, 220), (320, 310), (255, 255, 255), -1)
        cv2.putText(img, "ECO CLEAN", (195, 255), cv2.FONT_HERSHEY_DUPLEX, 0.7, (40, 120, 30), 2)
        cv2.putText(img, "Disinfectant 750ml", (190, 285), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 60), 1)

        # QR Code
        qr = self.render_qr_badge("890103000404", target_size=75)
        self.overlay_patch(img, qr, 212, 335)

        if defective:
            # Chemical stain and label blotch
            self.add_stain_defects(img, center=(240, 270), radius=45)
            self.add_scratch_defects(img, count=2)

        return img

    def generate_all_samples(self) -> Dict[str, str]:
        """
        Batch generate all baseline pristine and defective retail sample images.
        """
        samples = {
            "soda_can_clean.png": self.generate_soda_can(defective=False),
            "soda_can_scratched.png": self.generate_soda_can(defective=True),
            "oat_flakes_clean.png": self.generate_oat_flakes_box(defective=False),
            "oat_flakes_dented.png": self.generate_oat_flakes_box(defective=True),
            "milk_bottle_clean.png": self.generate_milk_bottle(defective=False),
            "milk_bottle_cracked.png": self.generate_milk_bottle(defective=True),
            "disinfectant_clean.png": self.generate_disinfectant_bottle(defective=False),
            "disinfectant_stained.png": self.generate_disinfectant_bottle(defective=True),
        }

        generated_paths = {}
        for filename, img in samples.items():
            out_path = self.output_dir / filename
            cv2.imwrite(str(out_path), img)
            generated_paths[filename] = str(out_path)

        return generated_paths


if __name__ == "__main__":
    generator = SampleDataGenerator()
    results = generator.generate_all_samples()
    print(f"Successfully generated {len(results)} retail test samples in {generator.output_dir}")
