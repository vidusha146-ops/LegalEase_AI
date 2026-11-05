"""
LegalEase AI - Document Export Engine (Phase 6)
Exports structured legal drafts into formatted PDF and DOCX formats.
Includes Navy Blue (#0B132B) & Gold (#D4AF37) styling, margin controls,
exhibit tables, verification clauses, and Advocates Act, 1961 statutory disclaimers.
"""

import io
import os
import re
import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

import fitz  # PyMuPDF
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

logger = logging.getLogger(__name__)

# Canonical Storage Directory for Drafts
STORAGE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "storage", "drafts")
)
os.makedirs(STORAGE_DIR, exist_ok=True)

# Brand Color Palette
COLOR_NAVY = (11 / 255.0, 19 / 255.0, 43 / 255.0)      # #0B132B
COLOR_GOLD = (212 / 255.0, 175 / 255.0, 55 / 255.0)    # #D4AF37
COLOR_CHARCOAL = (31 / 255.0, 41 / 255.0, 55 / 255.0)  # #1F2937
COLOR_MUTED = (107 / 255.0, 114 / 255.0, 128 / 255.0)  # #6B7280

DOCX_NAVY = RGBColor(11, 19, 43)
DOCX_GOLD = RGBColor(212, 175, 55)
DOCX_CHARCOAL = RGBColor(31, 41, 55)
DOCX_MUTED = RGBColor(107, 114, 128)

NON_ADVOCACY_DISCLAIMER = (
    "DISCLAIMER UNDER ADVOCATES ACT, 1961: This legal draft is computer-generated for educational "
    "and procedural assistance only. It does not constitute formal legal representation, legal advice, "
    "or advocacy. Citizens are strongly advised to have this document reviewed and settled by a "
    "qualified advocate enrolled with the Bar Council before formal filing."
)


class DocumentExportService:
    """
    Renders structured legal drafts into court-ready, printable PDF and DOCX files.
    """

    @classmethod
    def calculate_sha256(cls, content_bytes: bytes) -> str:
        return hashlib.sha256(content_bytes).hexdigest()

    # =========================================================================
    # 1. PDF EXPORT GENERATION (PyMuPDF)
    # =========================================================================

    @classmethod
    def generate_pdf(
        cls,
        draft_id: int,
        title: str,
        content_markdown: str,
        draft_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        save_to_disk: bool = True,
    ) -> Tuple[bytes, str, str]:
        """
        Renders markdown legal draft into a styled, paginated PDF.
        Returns: (pdf_bytes, file_sha256, file_path_if_saved)
        """
        metadata = metadata or {}
        doc = fitz.open()

        page_width = 595.32   # A4 width in points
        page_height = 841.92  # A4 height in points
        margin_x = 54.0       # 0.75 in
        margin_top = 54.0
        margin_bottom = 60.0
        content_width = page_width - (margin_x * 2)

        # Parse text into lines/paragraphs
        raw_lines = content_markdown.splitlines()

        curr_page = doc.new_page(width=page_width, height=page_height)
        y_cursor = margin_top

        # Top decorative rule on cover page
        curr_page.draw_rect(
            fitz.Rect(margin_x, y_cursor, margin_x + content_width, y_cursor + 3),
            color=COLOR_NAVY,
            fill=COLOR_NAVY,
        )
        y_cursor += 12

        # Header Title
        clean_title = title.upper()
        curr_page.insert_textbox(
            fitz.Rect(margin_x, y_cursor, margin_x + content_width, y_cursor + 45),
            clean_title,
            fontsize=13,
            fontname="helv",
            color=COLOR_NAVY,
            align=fitz.TEXT_ALIGN_CENTER,
        )
        y_cursor += 45

        # Gold dividing rule
        curr_page.draw_rect(
            fitz.Rect(margin_x + 50, y_cursor, margin_x + content_width - 50, y_cursor + 1.5),
            color=COLOR_GOLD,
            fill=COLOR_GOLD,
        )
        y_cursor += 15

        def check_page_break(needed_height: float):
            nonlocal curr_page, y_cursor
            if y_cursor + needed_height > (page_height - margin_bottom):
                curr_page = doc.new_page(width=page_width, height=page_height)
                y_cursor = margin_top

        # Process lines
        for raw_line in raw_lines:
            line = raw_line.strip()
            if not line:
                y_cursor += 8
                continue

            # Heading 1 or 2
            if line.startswith("# ") or line.startswith("## "):
                heading_text = line.lstrip("# ").strip().upper()
                check_page_break(32)
                y_cursor += 10
                curr_page.insert_textbox(
                    fitz.Rect(margin_x, y_cursor, margin_x + content_width, y_cursor + 20),
                    heading_text,
                    fontsize=10.5,
                    fontname="helv",
                    color=COLOR_NAVY,
                    align=fitz.TEXT_ALIGN_LEFT,
                )
                curr_page.draw_line(
                    fitz.Point(margin_x, y_cursor + 18),
                    fitz.Point(margin_x + 180, y_cursor + 18),
                    color=COLOR_GOLD,
                    width=1,
                )
                y_cursor += 24

            elif line.startswith("### "):
                sub_heading = line.lstrip("# ").strip()
                check_page_break(24)
                y_cursor += 6
                curr_page.insert_textbox(
                    fitz.Rect(margin_x, y_cursor, margin_x + content_width, y_cursor + 16),
                    sub_heading,
                    fontsize=9.5,
                    fontname="helv",
                    color=COLOR_CHARCOAL,
                    align=fitz.TEXT_ALIGN_LEFT,
                )
                y_cursor += 18

            elif line.startswith("- ") or line.startswith("* "):
                bullet_text = "• " + line[2:].strip()
                # Estimate height based on length
                approx_lines = max(1, len(bullet_text) // 75 + 1)
                item_h = approx_lines * 13 + 4
                check_page_break(item_h)
                curr_page.insert_textbox(
                    fitz.Rect(margin_x + 10, y_cursor, margin_x + content_width, y_cursor + item_h),
                    bullet_text,
                    fontsize=9.0,
                    fontname="helv",
                    color=COLOR_CHARCOAL,
                    align=fitz.TEXT_ALIGN_LEFT,
                )
                y_cursor += item_h

            elif line.startswith(">"):
                quote_text = line.lstrip("> ").strip()
                approx_lines = max(1, len(quote_text) // 75 + 1)
                quote_h = approx_lines * 13 + 8
                check_page_break(quote_h)
                curr_page.draw_rect(
                    fitz.Rect(margin_x, y_cursor, margin_x + 3, y_cursor + quote_h - 2),
                    color=COLOR_GOLD,
                    fill=COLOR_GOLD,
                )
                curr_page.insert_textbox(
                    fitz.Rect(margin_x + 12, y_cursor + 2, margin_x + content_width, y_cursor + quote_h),
                    quote_text,
                    fontsize=8.5,
                    fontname="helv",
                    color=COLOR_MUTED,
                    align=fitz.TEXT_ALIGN_LEFT,
                )
                y_cursor += quote_h

            else:
                # Regular paragraph text
                approx_lines = max(1, len(line) // 80 + 1)
                para_h = approx_lines * 13 + 6
                check_page_break(para_h)
                curr_page.insert_textbox(
                    fitz.Rect(margin_x, y_cursor, margin_x + content_width, y_cursor + para_h),
                    line,
                    fontsize=9.0,
                    fontname="helv",
                    color=COLOR_CHARCOAL,
                    align=fitz.TEXT_ALIGN_LEFT,
                )
                y_cursor += para_h

        # Verification & Signature Block
        check_page_break(90)
        y_cursor += 15
        curr_page.insert_textbox(
            fitz.Rect(margin_x, y_cursor, margin_x + 200, y_cursor + 35),
            "Date: ____________________\nPlace: ____________________",
            fontsize=9.0,
            fontname="helv",
            color=COLOR_CHARCOAL,
        )
        curr_page.insert_textbox(
            fitz.Rect(margin_x + content_width - 200, y_cursor, margin_x + content_width, y_cursor + 35),
            "_____________________________\nSignature of Complainant / Applicant",
            fontsize=9.0,
            fontname="helv",
            color=COLOR_CHARCOAL,
            align=fitz.TEXT_ALIGN_RIGHT,
        )
        y_cursor += 45

        # Footer on every page
        total_pages = len(doc)
        for idx, page in enumerate(doc, start=1):
            # Page number
            page.insert_textbox(
                fitz.Rect(margin_x, page_height - 35, margin_x + content_width, page_height - 20),
                f"Page {idx} of {total_pages} | LegalEase AI Drafting Studio | Advocates Act, 1961 Non-Advocacy Educational Draft",
                fontsize=7.5,
                fontname="helv",
                color=COLOR_MUTED,
                align=fitz.TEXT_ALIGN_CENTER,
            )
            # Subtle bottom rule
            page.draw_line(
                fitz.Point(margin_x, page_height - 38),
                fitz.Point(margin_x + content_width, page_height - 38),
                color=COLOR_GOLD,
                width=0.5,
            )

        pdf_bytes = doc.tobytes()
        doc.close()

        sha256 = cls.calculate_sha256(pdf_bytes)
        file_path = ""
        if save_to_disk:
            safe_type = re.sub(r"[^A-Za-z0-9_-]", "", draft_type).lower()
            file_name = f"draft_{draft_id}_{safe_type}.pdf"
            file_path = os.path.join(STORAGE_DIR, file_name)
            with open(file_path, "wb") as f:
                f.write(pdf_bytes)

        return pdf_bytes, sha256, file_path

    # =========================================================================
    # 2. DOCX EXPORT GENERATION (python-docx)
    # =========================================================================

    @classmethod
    def generate_docx(
        cls,
        draft_id: int,
        title: str,
        content_markdown: str,
        draft_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        save_to_disk: bool = True,
    ) -> Tuple[bytes, str, str]:
        """
        Renders markdown legal draft into a styled, court-ready DOCX document.
        Returns: (docx_bytes, file_sha256, file_path_if_saved)
        """
        metadata = metadata or {}
        doc = docx.Document()

        # Set 0.75-inch margins
        for section in doc.sections:
            section.top_margin = Inches(0.75)
            section.bottom_margin = Inches(0.75)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)

        # Document Header Title
        title_p = doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_title = title_p.add_run(title.upper())
        run_title.font.name = "Arial"
        run_title.font.size = Pt(14)
        run_title.font.bold = True
        run_title.font.color.rgb = DOCX_NAVY

        # Sub-title / Forum
        sub_p = doc.add_paragraph()
        sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_sub = sub_p.add_run(f"Type of Draft: {draft_type.replace('_', ' ').title()}")
        run_sub.font.name = "Arial"
        run_sub.font.size = Pt(10)
        run_sub.font.italic = True
        run_sub.font.color.rgb = DOCX_MUTED

        # Statutory Disclaimer Banner
        disc_p = doc.add_paragraph()
        disc_run = disc_p.add_run(f"[NON-ADVOCACY ADVISORY]: {NON_ADVOCACY_DISCLAIMER}")
        disc_run.font.name = "Arial"
        disc_run.font.size = Pt(8.5)
        disc_run.font.italic = True
        disc_run.font.color.rgb = DOCX_MUTED

        # Parse markdown lines into DOCX elements
        raw_lines = content_markdown.splitlines()
        for raw_line in raw_lines:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("# ") or line.startswith("## "):
                h = doc.add_heading(level=1)
                h_run = h.add_run(line.lstrip("# ").strip().upper())
                h_run.font.name = "Arial"
                h_run.font.size = Pt(11)
                h_run.font.bold = True
                h_run.font.color.rgb = DOCX_NAVY

            elif line.startswith("### "):
                h2 = doc.add_heading(level=2)
                h2_run = h2.add_run(line.lstrip("# ").strip())
                h2_run.font.name = "Arial"
                h2_run.font.size = Pt(10)
                h2_run.font.bold = True
                h2_run.font.color.rgb = DOCX_CHARCOAL

            elif line.startswith("- ") or line.startswith("* "):
                p = doc.add_paragraph(style="List Bullet")
                p_run = p.add_run(line[2:].strip())
                p_run.font.name = "Arial"
                p_run.font.size = Pt(9.5)
                p_run.font.color.rgb = DOCX_CHARCOAL

            elif line.startswith(">"):
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.25)
                q_run = p.add_run(line.lstrip("> ").strip())
                q_run.font.name = "Arial"
                q_run.font.size = Pt(9)
                q_run.font.italic = True
                q_run.font.color.rgb = DOCX_MUTED

            else:
                p = doc.add_paragraph()
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(6)
                p_run = p.add_run(line)
                p_run.font.name = "Arial"
                p_run.font.size = Pt(9.5)
                p_run.font.color.rgb = DOCX_CHARCOAL

        # Verification & Signature Block
        doc.add_paragraph()
        sig_p = doc.add_paragraph()
        sig_p.paragraph_format.space_before = Pt(12)
        sig_run1 = sig_p.add_run("Date: ____________________\nPlace: ____________________\t\t\t\t")
        sig_run1.font.name = "Arial"
        sig_run1.font.size = Pt(9.5)

        sig_run2 = sig_p.add_run("_____________________________\n\t\t\t\tSignature of Complainant / Applicant")
        sig_run2.font.name = "Arial"
        sig_run2.font.size = Pt(9.5)
        sig_run2.font.bold = True

        buffer = io.BytesIO()
        doc.save(buffer)
        docx_bytes = buffer.getvalue()

        sha256 = cls.calculate_sha256(docx_bytes)
        file_path = ""
        if save_to_disk:
            safe_type = re.sub(r"[^A-Za-z0-9_-]", "", draft_type).lower()
            file_name = f"draft_{draft_id}_{safe_type}.docx"
            file_path = os.path.join(STORAGE_DIR, file_name)
            with open(file_path, "wb") as f:
                f.write(docx_bytes)

        return docx_bytes, sha256, file_path
