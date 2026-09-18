"""
Module 7: Automated PDF Report & Inspection Certificate Generator.
Utilizes ReportLab to generate professional inspection certificates
and transaction invoices with tabular metrics and styling.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from src.config import REPORTS_DIR


class ReportGenerator:
    """
    Produces formal PDF documents for retail quality audits and customer sales receipts.
    """

    def __init__(self, output_dir: Path = REPORTS_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()

        # Custom header & body styles
        self.title_style = ParagraphStyle(
            "DocTitle",
            parent=self.styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=8,
        )
        self.subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=12,
        )
        self.section_style = ParagraphStyle(
            "SectionTitle",
            parent=self.styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=6,
        )
        self.body_style = ParagraphStyle(
            "BodyTextCustom",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
        )

    def generate_inspection_certificate(
        self,
        product: Dict[str, Any],
        qc_result: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        Generate a comprehensive Computer Vision Quality Assurance Certificate.
        """
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        sku = product.get("sku", "UNKNOWN")
        if not filename:
            filename = f"QC_Cert_{sku}_{timestamp_str}.pdf"

        pdf_path = self.output_dir / filename
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        elements = []

        # Header Title
        elements.append(Paragraph("VisionCart-Inspect Quality Audit Certificate", self.title_style))
        elements.append(
            Paragraph(
                f"Automated Industrial Surface & Retail Inspection Telemetry | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                self.subtitle_style,
            )
        )
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=14))

        # Status Banner Color
        status = qc_result.get("status", "PASS")
        status_color = colors.HexColor("#16a34a") if status == "PASS" else (
            colors.HexColor("#ca8a04") if status == "WARNING" else colors.HexColor("#dc2626")
        )

        status_table_data = [
            [
                Paragraph(f"<b>INSPECTION VERDICT:</b> <font size='14' color='{status_color.hexval()}'><b>{status}</b></font>", self.section_style),
                Paragraph(f"<b>Defect Score:</b> {qc_result.get('defect_score', 0.0)}%<br/><b>Defects Detected:</b> {qc_result.get('defect_count', 0)}", self.body_style)
            ]
        ]
        status_table = Table(status_table_data, colWidths=[300, 230])
        status_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("PADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        elements.append(status_table)
        elements.append(Spacer(1, 14))

        # Product Information Table
        elements.append(Paragraph("1. Product Identification", self.section_style))
        prod_data = [
            ["SKU Identifier", product.get("sku", "N/A"), "Product Name", product.get("name", "N/A")],
            ["Category", product.get("category", "General"), "Optical Barcode", product.get("barcode", "N/A")],
            ["Detection Method", product.get("detection_method", "VISION"), "Scan Confidence", f"{round(product.get('confidence', 1.0)*100, 1)}%"],
            ["Unit Price", f"${product.get('price', 0.0):.2f}", "Tax Rate", f"{round(product.get('tax_rate', 0.08)*100, 1)}%"],
        ]
        t_prod = Table(prod_data, colWidths=[120, 145, 120, 145])
        t_prod.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f1f5f9")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1e293b")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ])
        )
        elements.append(t_prod)
        elements.append(Spacer(1, 14))

        # Detected Defect Table
        elements.append(Paragraph("2. Anomaly Breakdown & Quantitative Metrics", self.section_style))
        defects = qc_result.get("defects", [])
        if defects:
            defect_rows = [["#", "Defect Type", "Severity", "Area (px)", "Aspect Ratio", "Bounding Box [x,y,w,h]"]]
            for idx, d in enumerate(defects[:12], 1):
                defect_rows.append([
                    str(idx),
                    d.get("type", "ANOMALY"),
                    d.get("severity", "MEDIUM"),
                    str(d.get("area_px", "0")),
                    str(d.get("aspect_ratio", "1.0")),
                    str(d.get("bbox", []))
                ])
            t_defects = Table(defect_rows, colWidths=[25, 140, 70, 75, 80, 140])
            t_defects.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ])
            )
            elements.append(t_defects)
        else:
            elements.append(Paragraph("<i>No surface defects or structural anomalies exceeded sensitivity thresholds. Surface verified pristine.</i>", self.body_style))

        elements.append(Spacer(1, 18))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
        elements.append(Paragraph("Certified by Autonomous VisionCart Edge Inspection AI | Compliance: ISO 9001 / Retail Automation Standard", self.subtitle_style))

        doc.build(elements)
        return str(pdf_path)

    def generate_invoice_receipt(
        self,
        receipt: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        Generate itemized sales receipt PDF for completed customer checkout.
        """
        receipt_id = receipt.get("receipt_id", "REC-000")
        if not filename:
            filename = f"Invoice_{receipt_id}.pdf"

        pdf_path = self.output_dir / filename
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        elements = []
        elements.append(Paragraph("VisionCart Autonomous Checkout — Tax Invoice", self.title_style))
        elements.append(Paragraph(f"Receipt ID: {receipt_id} | Issued: {receipt.get('timestamp', '')}", self.subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#10b981"), spaceAfter=14))

        # Items Table
        items_data = [["SKU", "Item Description", "Unit Price", "Qty", "Tax Rate", "Total"]]
        for item in receipt.get("items", []):
            items_data.append([
                item.get("sku", "N/A"),
                item.get("name", "N/A"),
                f"${item.get('unit_price', 0.0):.2f}",
                str(item.get("quantity", 1)),
                f"{round(item.get('tax_rate', 0.08)*100)}%",
                f"${item.get('total_price', 0.0):.2f}"
            ])

        # Summary rows
        items_data.append(["", "", "", "", "Subtotal:", f"${receipt.get('subtotal', 0.0):.2f}"])
        items_data.append(["", "", "", "", "Discounts:", f"-${receipt.get('discount', 0.0):.2f}"])
        items_data.append(["", "", "", "", "Tax:", f"${receipt.get('tax', 0.0):.2f}"])
        items_data.append(["", "", "", "", "Grand Total:", f"${receipt.get('grand_total', 0.0):.2f}"])

        t_invoice = Table(items_data, colWidths=[80, 200, 65, 45, 65, 75])
        t_invoice.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -5), 0.5, colors.HexColor("#e2e8f0")),
                ("LINEABOVE", (4, -4), (-1, -1), 1, colors.HexColor("#0f172a")),
                ("FONTNAME", (4, -1), (-1, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (4, -1), (-1, -1), colors.HexColor("#0f172a")),
                ("BACKGROUND", (4, -1), (-1, -1), colors.HexColor("#dcfce7")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ])
        )
        elements.append(t_invoice)
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"Payment Method: {receipt.get('payment_method', 'UPI / Card')} | Status: {receipt.get('payment_status', 'PAID')}", self.body_style))
        elements.append(Paragraph("Thank you for shopping with VisionCart Autonomous Checkout! All items inspected for quality.", self.subtitle_style))

        doc.build(elements)
        return str(pdf_path)
