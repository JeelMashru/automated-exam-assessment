"""
PDF text extraction engine with fallback and scanned-PDF detection.
"""

import os
from pathlib import Path
from typing import Dict, Any, Tuple
try:
    import pymupdf
except ImportError:
    import fitz as pymupdf


class PDFProcessor:
    """Handles PDF ingestion, multi-page text extraction, and scan detection."""

    MIN_WORDS_PER_PAGE_THRESHOLD = 15  # If less than this, page is likely a scan or image

    @classmethod
    def extract_text_from_pdf(cls, file_path: str) -> Dict[str, Any]:
        """
        Extracts structured text from a PDF file.
        Returns:
            {
                "success": bool,
                "text": str,
                "pages": list[dict],
                "page_count": int,
                "word_count": int,
                "is_scanned": bool,
                "error": str | None
            }
        """
        if not os.path.exists(file_path):
            return {
                "success": False,
                "text": "",
                "pages": [],
                "page_count": 0,
                "word_count": 0,
                "is_scanned": False,
                "error": f"File not found: {file_path}",
            }

        try:
            doc = pymupdf.open(file_path)
        except Exception as e:
            return {
                "success": False,
                "text": "",
                "pages": [],
                "page_count": 0,
                "word_count": 0,
                "is_scanned": False,
                "error": f"Failed to open PDF document (possibly corrupted or unsupported format): {str(e)}",
            }

        page_count = len(doc)
        if page_count == 0:
            doc.close()
            return {
                "success": False,
                "text": "",
                "pages": [],
                "page_count": 0,
                "word_count": 0,
                "is_scanned": False,
                "error": "The PDF file contains 0 pages.",
            }

        pages_data = []
        full_text_parts = []
        total_word_count = 0
        scanned_pages_count = 0

        try:
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                text = page.get_text("text").strip()
                words = text.split()
                w_count = len(words)
                total_word_count += w_count

                # Check if page has images
                image_list = page.get_images(full=True)
                has_images = len(image_list) > 0
                is_scanned_page = (w_count < cls.MIN_WORDS_PER_PAGE_THRESHOLD) and has_images

                if is_scanned_page:
                    scanned_pages_count += 1

                pages_data.append({
                    "page_number": page_num + 1,
                    "text": text,
                    "word_count": w_count,
                    "has_images": has_images,
                    "is_scanned": is_scanned_page,
                })
                if text:
                    full_text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

            doc.close()
        except Exception as e:
            try:
                doc.close()
            except Exception:
                pass
            return {
                "success": False,
                "text": "",
                "pages": [],
                "page_count": page_count,
                "word_count": 0,
                "is_scanned": False,
                "error": f"Error parsing PDF content: {str(e)}",
            }

        full_extracted_text = "\n\n".join(full_text_parts)
        is_document_scanned = (
            (scanned_pages_count > 0 and total_word_count < 30) or
            (total_word_count == 0 and page_count > 0)
        )

        return {
            "success": True,
            "text": full_extracted_text,
            "pages": pages_data,
            "page_count": page_count,
            "word_count": total_word_count,
            "is_scanned": is_document_scanned,
            "error": None if not is_document_scanned else (
                "Scanned or image-based PDF detected. Embedded text is minimal or missing."
            ),
        }
