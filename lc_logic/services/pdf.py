"""PDF fetching helpers.

Stateless by design (see CONTEXT.md): this module never writes the
downloaded PDF to the shared cache — that cache is only for rendered page
images used by the (future) chat/quiz vision pipeline. Title extraction is
a one-off sync step done at upload time, so the PDF bytes are only held in
memory for the duration of the request.
"""

import httpx
import pymupdf

MAX_TITLE_PAGES = 4
DOWNLOAD_TIMEOUT_SECONDS = 30.0


class PdfFetchError(Exception):
    """Raised when the PDF at file_url can't be downloaded or isn't a valid PDF."""


async def download_pdf(file_url: str) -> bytes:
    try:
        async with httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT_SECONDS) as client:
            response = await client.get(file_url)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise PdfFetchError(
            f"file_url returned HTTP {exc.response.status_code} while downloading the PDF."
        ) from exc
    except httpx.HTTPError as exc:
        raise PdfFetchError(f"Failed to download PDF from file_url: {exc}") from exc

    content = response.content
    if not content:
        raise PdfFetchError("Downloaded file is empty.")

    return content


def extract_leading_text(pdf_bytes: bytes, max_pages: int = MAX_TITLE_PAGES) -> str:
    """Extract raw text from up to `max_pages` first pages of the PDF.

    This is a quick, text-only pass used only for title detection at
    upload time — NOT the vision pipeline (see CONTEXT.md: chat/quiz always
    render pages to images and use the vision model, regardless of whether
    the page is text or scanned). If a page has no extractable text (e.g.
    it's a scanned image), it simply contributes an empty string — no OCR
    fallback here.
    """
    try:
        document = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:  # PyMuPDF raises its own exceptions on bad files
        raise PdfFetchError(f"Downloaded file is not a valid PDF: {exc}") from exc

    try:
        page_count = min(max_pages, document.page_count)
        pages_text = [document.load_page(i).get_text() or "" for i in range(page_count)]
    finally:
        document.close()

    return "\n\n".join(text.strip() for text in pages_text if text.strip())
