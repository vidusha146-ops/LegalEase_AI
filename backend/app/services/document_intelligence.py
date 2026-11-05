"""
LegalEase AI - Document Intelligence Service (Phase 5)
Handles secure multi-format document ingestion, text extraction (PyMuPDF),
OCR processing (pytesseract/PIL), and encryption/corruption handling.
"""

import io
import os
import re
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import docx

from app.core.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/tiff": ".tiff",
}

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".tiff"}

MAGIC_NUMBERS = {
    b"%PDF": "application/pdf",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"PK\x03\x04": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    b"II*\x00": "image/tiff",
    b"MM\x00*": "image/tiff",
}


class DocumentProcessingError(Exception):
    """Base error for document intelligence processing."""
    pass


class EncryptedDocumentError(DocumentProcessingError):
    """Raised when an uploaded document is password-protected."""
    pass


class CorruptedDocumentError(DocumentProcessingError):
    """Raised when an uploaded document is corrupt or unreadable."""
    pass


class UnsupportedDocumentError(DocumentProcessingError):
    """Raised when document format is not supported."""
    pass


class DocumentIntelligenceService:
    """
    Ingests and validates evidence files, extracts page-level text via PyMuPDF,
    performs OCR on scanned documents/images, and securely records metadata.
    """

    @classmethod
    def validate_file_bytes(
        cls, file_bytes: bytes, original_filename: str
    ) -> Tuple[str, str]:
        """
        Validates file size, extension, and magic header bytes.
        Returns (sanitized_extension, detected_mime_type).
        """
        # 1. Size check
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise DocumentProcessingError(
                f"File exceeds maximum permissible size of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        if len(file_bytes) == 0:
            raise CorruptedDocumentError("Uploaded file is empty (0 bytes).")

        # 2. Extension check
        ext = Path(original_filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise UnsupportedDocumentError(
                f"Unsupported file extension '{ext}'. Supported formats: PDF, DOCX, PNG, JPG, TIFF."
            )

        # 3. Magic header inspection
        detected_mime = None
        for magic, mime in MAGIC_NUMBERS.items():
            if file_bytes.startswith(magic):
                detected_mime = mime
                break

        if not detected_mime:
            # Fallback for docx or generic checks
            if ext == ".docx" and file_bytes.startswith(b"PK"):
                detected_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif ext in (".jpg", ".jpeg") and len(file_bytes) > 2 and file_bytes[0] == 0xFF and file_bytes[1] == 0xD8:
                detected_mime = "image/jpeg"
            else:
                raise CorruptedDocumentError("File content does not match its claimed file extension format.")

        return ext, detected_mime

    @classmethod
    def calculate_sha256(cls, file_bytes: bytes) -> str:
        """Calculates cryptographic SHA-256 digest of the file bytes for integrity."""
        return hashlib.sha256(file_bytes).hexdigest()

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Prevents path traversal and removes unsafe characters from filename."""
        base = Path(filename).name
        sanitized = re.sub(r"[^A-Za-z0-9_.-]", "_", base)
        return sanitized or "evidence_document"

    @classmethod
    def extract_document_text(
        cls,
        file_bytes: bytes,
        filename: str,
    ) -> Dict[str, Any]:
        """
        Extracts structured text and metadata from PDF, DOCX, or Image file.
        Returns a dict containing page-by-page extractions and extraction statistics.
        """
        ext, mime = cls.validate_file_bytes(file_bytes, filename)
        sha256_hash = cls.calculate_sha256(file_bytes)

        if ext == ".pdf":
            return cls._extract_from_pdf(file_bytes, filename, sha256_hash)
        elif ext == ".docx":
            return cls._extract_from_docx(file_bytes, filename, sha256_hash)
        elif ext in (".png", ".jpg", ".jpeg", ".tiff"):
            return cls._extract_from_image(file_bytes, filename, sha256_hash)
        else:
            raise UnsupportedDocumentError(f"Handler for extension '{ext}' not found.")

    @classmethod
    def _extract_from_pdf(
        cls, file_bytes: bytes, filename: str, sha256_hash: str
    ) -> Dict[str, Any]:
        """Extracts text page-by-page from PDF using PyMuPDF with OCR fallback."""
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise CorruptedDocumentError(f"Could not open PDF file. Document may be corrupt: {e}")

        if doc.is_encrypted:
            doc.close()
            raise EncryptedDocumentError(
                "Document is password-encrypted. Please upload a decrypted version for evidence analysis."
            )

        pages_data: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []
        is_scanned = False
        ocr_performed = False

        total_pages = len(doc)
        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_num = page_idx + 1
            text = page.get_text("text").strip()

            # Check if page is an image scan (minimal text content)
            if len(text) < 30:
                # Attempt OCR on the page pixmap
                ocr_text = cls._ocr_pixmap(page)
                if ocr_text and len(ocr_text.strip()) > len(text):
                    text = ocr_text.strip()
                    ocr_performed = True
                    is_scanned = True

            pages_data.append({
                "page_number": page_num,
                "text": text,
                "character_count": len(text),
            })
            if text:
                full_text_parts.append(f"--- [Page {page_num}] ---\n{text}")

        metadata = doc.metadata or {}
        doc.close()

        combined_text = "\n\n".join(full_text_parts)

        return {
            "filename": filename,
            "sha256_hash": sha256_hash,
            "file_type": "PDF",
            "total_pages": total_pages,
            "full_text": combined_text,
            "pages": pages_data,
            "is_scanned": is_scanned,
            "ocr_performed": ocr_performed,
            "author": metadata.get("author") or None,
            "creator": metadata.get("creator") or None,
            "creation_date": metadata.get("creationDate") or None,
        }

    @classmethod
    def _ocr_pixmap(cls, page: fitz.Page) -> str:
        """Renders page as an image and applies pytesseract OCR."""
        try:
            pix = page.get_pixmap(dpi=150)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            logger.debug(f"OCR skipped for page: {e}")
            return ""

    @classmethod
    def _extract_from_docx(
        cls, file_bytes: bytes, filename: str, sha256_hash: str
    ) -> Dict[str, Any]:
        """Extracts text from DOCX files including paragraphs and table contents."""
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
        except Exception as e:
            raise CorruptedDocumentError(f"Could not parse DOCX document: {e}")

        paragraphs_text = []
        for p in doc.paragraphs:
            if p.text.strip():
                paragraphs_text.append(p.text.strip())

        # Extract table data
        tables_text = []
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    tables_text.append(" | ".join(row_cells))

        combined_parts = []
        if paragraphs_text:
            combined_parts.append("\n".join(paragraphs_text))
        if tables_text:
            combined_parts.append("--- [Tables Content] ---\n" + "\n".join(tables_text))

        full_text = "\n\n".join(combined_parts)

        return {
            "filename": filename,
            "sha256_hash": sha256_hash,
            "file_type": "DOCX",
            "total_pages": 1,
            "full_text": full_text,
            "pages": [{
                "page_number": 1,
                "text": full_text,
                "character_count": len(full_text),
            }],
            "is_scanned": False,
            "ocr_performed": False,
        }

    @classmethod
    def _extract_from_image(
        cls, file_bytes: bytes, filename: str, sha256_hash: str
    ) -> Dict[str, Any]:
        """Extracts text from scanned image files (PNG, JPG, TIFF) via OCR."""
        try:
            img = Image.open(io.BytesIO(file_bytes))
            img_format = img.format
            width, height = img.size
        except Exception as e:
            raise CorruptedDocumentError(f"Could not read image file: {e}")

        extracted_text = ""
        ocr_performed = True

        try:
            extracted_text = pytesseract.image_to_string(img).strip()
        except pytesseract.TesseractNotFoundError:
            logger.warning("Tesseract binary not found on PATH; falling back to visual metadata.")
            extracted_text = f"[OCR Notice: Tesseract binary not configured on host. Image dimensions: {width}x{height} {img_format}]"
            ocr_performed = False
        except Exception as e:
            logger.warning(f"Error during image OCR: {e}")
            extracted_text = ""

        return {
            "filename": filename,
            "sha256_hash": sha256_hash,
            "file_type": img_format or "IMAGE",
            "total_pages": 1,
            "full_text": extracted_text,
            "pages": [{
                "page_number": 1,
                "text": extracted_text,
                "character_count": len(extracted_text),
            }],
            "is_scanned": True,
            "ocr_performed": ocr_performed,
            "image_dimensions": f"{width}x{height}",
        }
