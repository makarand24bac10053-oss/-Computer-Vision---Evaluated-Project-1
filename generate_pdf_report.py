"""
Compiles PROJECT_REPORT.md into a formal academic PDF document
for direct submission to the VITyarthi portal using ReportLab.
Features executive styling, XML-safe entity handling, equation rendering,
and automated layout pagination.
"""

import os
import re
import html
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    PageBreak,
    Preformatted,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from src.config import REPORTS_DIR, BASE_DIR


class NumberedCanvas(canvas.Canvas):
    """Adds running headers and 'Page X of Y' footers to all pages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(40, 760, "VisionCart-Inspect | VITyarthi Academic Project Report")
            self.drawRightString(572, 760, "Flipped Course Evaluation")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(40, 754, 572, 754)

        # Footer
        footer_text = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(572, 28, footer_text)
        self.drawString(40, 28, "VisionCart-Inspect: Autonomous Retail & Industrial Defect Quality Control")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(40, 38, 572, 38)

        self.restoreState()


def format_latex_math(text: str) -> str:
    """Convert common LaTeX mathematical notations into clean readable representations."""
    # Remove text{} wrappers
    text = re.sub(r"\\text\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\mathbf\{([^}]+)\}", r"<b>\1</b>", text)
    text = re.sub(r"\\mathcal\{C\}", "Circularity", text)
    # Greek letters & symbols
    text = text.replace(r"\le", "&le;").replace(r"\ge", "&ge;")
    text = text.replace(r"\times", "&times;").replace(r"\cdot", "&bull;")
    text = text.replace(r"\to", "&rarr;").replace(r"\implies", " &rArr; ")
    text = text.replace(r"\in", "&isin;").replace(r"\Omega", "&Omega;")
    text = text.replace(r"\sigma", "&sigma;").replace(r"\theta", "&theta;")
    text = text.replace(r"\pi", "&pi;").replace(r"\sum", "&sum;")
    # Fractions: \frac{A}{B} -> (A / B)
    text = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1 / \2)", text)
    # Square root: \sqrt{X} -> √(X)
    text = re.sub(r"\\sqrt\{([^}]+)\}", r"&radic;(\1)", text)
    text = re.sub(r"\\min\b", "min", text)
    text = re.sub(r"\\max\b", "max", text)
    text = re.sub(r"\\arctan\b", "arctan", text)
    text = text.replace(r"\|", "|")
    return text


def sanitize_markdown_inline(text: str) -> str:
    """Safely converts markdown inline formatting to ReportLab XML tags."""
    if not text:
        return ""

    # 1. First format inline math expressions ($...$)
    def math_sub(match):
        inner = match.group(1)
        cleaned = format_latex_math(inner)
        return f"<i><b>{cleaned}</b></i>"

    text = re.sub(r"\$([^$]+)\$", math_sub, text)

    # 2. Extract code blocks (`...`) temporarily to preserve them
    code_placeholders = []
    def code_sub(match):
        code_placeholders.append(html.escape(match.group(1)))
        return f"__CODE_PLACEHOLDER_{len(code_placeholders)-1}__"

    text = re.sub(r"`([^`]+)`", code_sub, text)

    # 3. Escape raw XML characters from general text
    # Avoid double escaping already converted entities like &le; &ge; &times; &bull; &rarr; &rArr; &isin; &Omega; &sigma; &theta; &pi; &sum; &radic;
    text = text.replace("&", "&amp;")
    # Revert intentionally formed entities
    for ent in ["le", "ge", "times", "bull", "rarr", "rArr", "isin", "Omega", "sigma", "theta", "pi", "sum", "radic"]:
        text = text.replace(f"&amp;{ent};", f"&{ent};")

    text = text.replace("<", "&lt;").replace(">", "&gt;")

    # 4. Convert bold **text** to <b>text</b>
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)

    # 5. Convert italic *text* to <i>text</i>
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)

    # 6. Reinsert styled code tags
    for idx, c_text in enumerate(code_placeholders):
        replacement = f'<font name="Courier-Bold" color="#0369a1" size="8">{c_text}</font>'
        text = text.replace(f"__CODE_PLACEHOLDER_{idx}__", replacement)

    return text


def compile_markdown_to_pdf():
    report_md_path = BASE_DIR / "PROJECT_REPORT.md"
    pdf_out_path = REPORTS_DIR / "Project_Report_Submission.pdf"
    os.makedirs(REPORTS_DIR, exist_ok=True)

    if not report_md_path.exists():
        print(f"Error: {report_md_path} not found.")
        return

    with open(report_md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    doc = SimpleDocTemplate(
        str(pdf_out_path),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=45,
        bottomMargin=45,
    )

    styles = getSampleStyleSheet()

    # Document Styles
    title_style = ParagraphStyle(
        "CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=10,
        alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "CoverSubTitle",
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#0284c7"),
        spaceAfter=16,
        alignment=1,
    )
    h1_style = ParagraphStyle(
        "Header1",
        fontName="Helvetica-Bold",
        fontSize=13.5,
        leading=17,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "Header2",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#0369a1"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )
    h3_style = ParagraphStyle(
        "Header3",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=5,
    )
    bullet_style = ParagraphStyle(
        "ReportBullet",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#334155"),
        leftIndent=14,
        spaceAfter=3,
    )
    math_style = ParagraphStyle(
        "MathDisplay",
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
        spaceBefore=4,
        spaceAfter=4,
    )
    code_style = ParagraphStyle(
        "CodeSnippet",
        fontName="Courier",
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f8fafc"),
        borderColor=colors.HexColor("#cbd5e1"),
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=6,
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#334155"),
    )
    table_header_style = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.white,
    )

    story = []

    # Insert Title & Metadata Cover Page
    story.append(Spacer(1, 15))
    story.append(Paragraph("VisionCart-Inspect", title_style))
    story.append(
        Paragraph(
            "Automated Retail Checkout & Vision-Based Surface Defect Inspection System",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0284c7"), spaceAfter=14))

    # Executive Overview Callout
    exec_summary_html = (
        "<b>Executive Academic Summary:</b> VisionCart-Inspect is an end-to-end industrial machine vision and "
        "autonomous retail checkout architecture engineered for the <b>VITyarthi — Build Your Own Project</b> "
        "course evaluation. The platform unifies edge image filtering (CLAHE, Bilateral filtering, LAB/HSV transforms), "
        "multi-scale Canny edge hysteresis, contour geometric analysis, optical QR/barcode reading with fallback "
        "color-signature classification, defect quarantine gates, and relational SQLite telemetry with full PDF documentation."
    )
    summary_table = Table(
        [[Paragraph(exec_summary_html, body_style)]],
        colWidths=[532],
    )
    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#86efac")),
            ("PADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(summary_table)
    story.append(Spacer(1, 12))

    lines = md_text.split("\n")
    i = 0
    in_code_block = False
    code_buffer = []

    # Major chapters where a PageBreak improves layout
    page_break_chapters = [
        "# 2. Introduction",
        "# 6. System Architecture",
        "# 9. Implementation Details",
        "# 11. Testing Approach",
        "# 14. Future Enhancements",
    ]

    while i < len(lines):
        line = lines[i]

        # Handle Code and Diagram blocks
        if line.strip().startswith("```"):
            if in_code_block:
                code_text = "\n".join(code_buffer)
                story.append(Preformatted(code_text[:1200], code_style))
                story.append(Spacer(1, 4))
                code_buffer = []
                in_code_block = False
            else:
                in_code_block = True
                code_buffer = []
            i += 1
            continue

        if in_code_block:
            code_buffer.append(line)
            i += 1
            continue

        # Mathematical Display Equations: $$...$$
        if line.strip().startswith("$$") and line.strip().endswith("$$") and len(line.strip()) > 4:
            raw_eq = line.strip()[2:-2].strip()
            cleaned_eq = format_latex_math(raw_eq)
            math_box = Table(
                [[Paragraph(f"<b>[Equation]</b>&nbsp;&nbsp;&nbsp;&nbsp;{cleaned_eq}", math_style)]],
                colWidths=[532],
            )
            math_box.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ])
            )
            story.append(math_box)
            story.append(Spacer(1, 4))
            i += 1
            continue

        # Tables (Markdown format: | Header | Header |)
        if line.strip().startswith("|") and "|" in line:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1

            if len(table_lines) >= 2:
                parsed_data = []
                for row_idx, t_line in enumerate(table_lines):
                    if re.match(r"^\|[\s:\-]+(?:\|[\s:\-]+)*\|?$", t_line):
                        continue
                    cols = [c.strip() for c in t_line.strip("|").split("|")]
                    if not parsed_data:
                        # Header row
                        row_cells = [
                            Paragraph(sanitize_markdown_inline(c), table_header_style) for c in cols
                        ]
                    else:
                        row_cells = [
                            Paragraph(sanitize_markdown_inline(c), table_cell_style) for c in cols
                        ]
                    parsed_data.append(row_cells)

                if parsed_data:
                    num_cols = len(parsed_data[0])
                    available_width = 532

                    # Tailored column proportions
                    if num_cols == 2:
                        col_widths = [140, 392]
                    elif num_cols == 4:
                        col_widths = [55, 125, 272, 80]
                    elif num_cols == 7:
                        col_widths = [105, 80, 115, 55, 55, 55, 67]
                    else:
                        col_widths = [available_width / num_cols] * num_cols

                    t = Table(parsed_data, colWidths=col_widths, repeatRows=1)
                    t.setStyle(
                        TableStyle([
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                            ("PADDING", (0, 0), (-1, -1), 4),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ])
                    )
                    story.append(t)
                    story.append(Spacer(1, 6))
            continue

        # Page Breaks before major chapters
        for trigger in page_break_chapters:
            if line.strip().startswith(trigger):
                story.append(PageBreak())
                break

        # Headings
        if line.startswith("# "):
            title_text = sanitize_markdown_inline(line[2:].strip())
            if "Cover Page" in title_text or "Project Report" in title_text:
                story.append(Paragraph(title_text, h1_style))
                story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0284c7"), spaceAfter=8))
            else:
                story.append(Paragraph(title_text, h1_style))
                story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#0284c7"), spaceAfter=5))
        elif line.startswith("## "):
            story.append(Paragraph(sanitize_markdown_inline(line[3:].strip()), h2_style))
        elif line.startswith("### "):
            story.append(Paragraph(sanitize_markdown_inline(line[4:].strip()), h3_style))
        elif line.startswith("---"):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=6))
        elif line.strip().startswith("- ") or line.strip().startswith("* "):
            bullet_raw = line.strip()[2:].strip()
            bullet_html = sanitize_markdown_inline(bullet_raw)
            story.append(Paragraph(f"&bull; {bullet_html}", bullet_style))
        elif line.strip():
            p_html = sanitize_markdown_inline(line.strip())
            story.append(Paragraph(p_html, body_style))
        else:
            story.append(Spacer(1, 3))

        i += 1

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Successfully compiled academic PDF report to: {pdf_out_path}")


if __name__ == "__main__":
    compile_markdown_to_pdf()
