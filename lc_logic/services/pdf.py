"""PDF fetching helpers.

Stateless by design (see CONTEXT.md): this module never writes the
downloaded PDF to the shared cache — that cache is only for rendered page
images used by the (future) chat/quiz vision pipeline. Title extraction is
a one-off sync step done at upload time, so the PDF bytes are only held in
memory for the duration of the request.
"""

import logging

import httpx
import pymupdf

logger = logging.getLogger(__name__)

MAX_TITLE_PAGES = 4
DOWNLOAD_TIMEOUT_SECONDS = 30.0


class PdfFetchError(Exception):
    """Raised when the PDF at file_url can't be downloaded or isn't a valid PDF."""


def mask_url(url: str) -> str:
    """Return scheme+host+path only, dropping any query string/token.

    Django's file_url carries a signed token as a query param — never log
    that. Falls back to returning the input unchanged if it can't be parsed
    (should not happen for a validated HttpUrl, but never raise from a
    logging helper).
    """
    try:
        parsed = httpx.URL(url)
        return str(parsed.copy_with(query=None, fragment=None))
    except Exception:
        return "<unparseable-url>"


async def download_pdf(file_url: str) -> bytes:
    logger.info("Downloading PDF from %s", mask_url(file_url))
    try:
        async with httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT_SECONDS) as client:
            response = await client.get(file_url)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "PDF download failed with HTTP %d from %s",
            exc.response.status_code,
            mask_url(file_url),
        )
        raise PdfFetchError(
            f"file_url returned HTTP {exc.response.status_code} while downloading the PDF."
        ) from exc
    except httpx.HTTPError as exc:
        logger.warning("PDF download failed for %s: %s", mask_url(file_url), exc)
        raise PdfFetchError(f"Failed to download PDF from file_url: {exc}") from exc

    content = response.content
    if not content:
        logger.warning("PDF download returned an empty body from %s", mask_url(file_url))
        raise PdfFetchError("Downloaded file is empty.")

    logger.info("Downloaded PDF: %d bytes from %s", len(content), mask_url(file_url))
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
        logger.warning("Downloaded file failed to open as a PDF: %s", exc)
        raise PdfFetchError(f"Downloaded file is not a valid PDF: {exc}") from exc

    try:
        total_pages = document.page_count
        page_count = min(max_pages, total_pages)
        pages_text = [document.load_page(i).get_text() or "" for i in range(page_count)]
    finally:
        document.close()

    pages_with_text = sum(1 for text in pages_text if text.strip())
    logger.info(
        "Considered %d leading page(s) of a %d-page PDF (%d had extractable text)",
        page_count,
        total_pages,
        pages_with_text,
    )

    return "\n\n".join(text.strip() for text in pages_text if text.strip())
