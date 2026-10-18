"""
Unit tests for PDF text processor and corrupted/empty file handling.
"""

import os
import pytest
try:
    import pymupdf
except ImportError:
    import fitz as pymupdf
from core.pdf_processor import PDFProcessor


@pytest.fixture
def sample_pdf(tmp_path):
    """Creates a temporary valid PDF document for testing."""
    pdf_path = tmp_path / "valid_test_exam.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (50, 72),
        "Virtual memory creates an illusion of a large contiguous address space. "
        "Paging breaks virtual memory into pages and physical memory into frames. "
        "The MMU translates page numbers using the page table."
    )
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)


@pytest.fixture
def corrupted_pdf(tmp_path):
    """Creates a corrupted non-PDF file with a .pdf extension."""
    bad_pdf_path = tmp_path / "corrupted.pdf"
    with open(bad_pdf_path, "wb") as f:
        f.write(b"NOT_A_VALID_PDF_HEADER_CORRUPTED_BYTES_1234567890")
    return str(bad_pdf_path)


def test_pdf_extraction_success(sample_pdf):
    result = PDFProcessor.extract_text_from_pdf(sample_pdf)
    assert result["success"] is True
    assert result["page_count"] == 1
    assert result["word_count"] > 15
    assert "Virtual memory" in result["text"]
    assert result["is_scanned"] is False
    assert result["error"] is None


def test_corrupted_pdf_handling(corrupted_pdf):
    result = PDFProcessor.extract_text_from_pdf(corrupted_pdf)
    assert result["success"] is False
    assert "corrupted" in result["error"].lower() or "failed" in result["error"].lower()


def test_nonexistent_pdf_handling():
    result = PDFProcessor.extract_text_from_pdf("nonexistent_file_path_12345.pdf")
    assert result["success"] is False
    assert "not found" in result["error"].lower()
