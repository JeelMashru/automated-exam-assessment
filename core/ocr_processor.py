"""
OCR Processor for image-based or scanned PDFs.
Provides graceful fallbacks when Tesseract or pytesseract is not installed.
"""

import shutil
from typing import Dict, Any


class OCRProcessor:
    """Manages OCR execution and system capability checks."""

    @classmethod
    def is_ocr_available(cls) -> Dict[str, Any]:
        """Checks whether pytesseract and tesseract executable are available on the system."""
        pytesseract_installed = False
        try:
            import pytesseract
            pytesseract_installed = True
        except ImportError:
            pass

        tesseract_binary_found = (
            shutil.which("tesseract") is not None or
            shutil.which("tesseract.exe") is not None
        )

        return {
            "available": pytesseract_installed and tesseract_binary_found,
            "pytesseract_installed": pytesseract_installed,
            "tesseract_binary_found": tesseract_binary_found,
            "instructions": (
                "To enable OCR for scanned handwritten or printed exam papers:\n"
                "1. Install Tesseract OCR: on Windows, install from UB-Mannheim/tesseract wiki or winget.\n"
                "2. Ensure 'tesseract' is added to your system PATH.\n"
                "3. Install python wrapper: pip install pytesseract"
            )
        }

    @classmethod
    def process_image(cls, image_bytes_or_pil) -> Dict[str, Any]:
        """Performs OCR if available, else returns advisory error."""
        status = cls.is_ocr_available()
        if not status["available"]:
            return {
                "success": False,
                "text": "",
                "error": "OCR engine (Tesseract) is not configured on this host machine.",
                "details": status["instructions"]
            }

        try:
            import pytesseract
            text = pytesseract.image_to_string(image_bytes_or_pil)
            return {
                "success": True,
                "text": text.strip(),
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "text": "",
                "error": f"OCR processing failed: {str(e)}"
            }
