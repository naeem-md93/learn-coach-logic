import pymupdf
import pytest


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """A tiny real single-page PDF with extractable text, built in-memory."""
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "The Great Example Book")
    page.insert_text((72, 100), "An Introduction to Testing")
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes
