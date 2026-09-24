import httpx
import pytest

from lc_logic.services.pdf import PdfFetchError
from lc_logic.services.pdf import download_pdf
from lc_logic.services.pdf import extract_leading_text


def test_extract_leading_text_returns_text(sample_pdf_bytes: bytes) -> None:
    text = extract_leading_text(sample_pdf_bytes)
    assert "The Great Example Book" in text
    assert "An Introduction to Testing" in text


def test_extract_leading_text_rejects_invalid_pdf() -> None:
    with pytest.raises(PdfFetchError):
        extract_leading_text(b"not a real pdf")


def _patch_async_client(monkeypatch: pytest.MonkeyPatch, transport: httpx.MockTransport) -> None:
    import lc_logic.services.pdf as pdf_module

    class _PatchedAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(pdf_module.httpx, "AsyncClient", _PatchedAsyncClient)


@pytest.mark.asyncio
async def test_download_pdf_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, content=b"not found")

    _patch_async_client(monkeypatch, httpx.MockTransport(handler))

    with pytest.raises(PdfFetchError):
        await download_pdf("http://example.com/missing.pdf")


@pytest.mark.asyncio
async def test_download_pdf_raises_on_empty_body(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"")

    _patch_async_client(monkeypatch, httpx.MockTransport(handler))

    with pytest.raises(PdfFetchError):
        await download_pdf("http://example.com/empty.pdf")


@pytest.mark.asyncio
async def test_download_pdf_returns_bytes_on_success(
    monkeypatch: pytest.MonkeyPatch, sample_pdf_bytes: bytes
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=sample_pdf_bytes)

    _patch_async_client(monkeypatch, httpx.MockTransport(handler))

    result = await download_pdf("http://example.com/sample.pdf")
    assert result == sample_pdf_bytes
