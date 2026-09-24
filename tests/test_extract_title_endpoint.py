import httpx
import pytest
from fastapi.testclient import TestClient

from lc_logic.__main__ import app
from lc_logic.services import title as title_module

client = TestClient(app)


def test_extract_title_rejects_invalid_file_url() -> None:
    response = client.post("/extract-title", json={"file_url": "not-a-url"})
    assert response.status_code == 422


def test_extract_title_returns_422_when_download_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    import lc_logic.services.pdf as pdf_module

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, content=b"not found")

    class _PatchedAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(pdf_module.httpx, "AsyncClient", _PatchedAsyncClient)

    response = client.post(
        "/extract-title", json={"file_url": "http://django:8000/media/resources/1/file/"}
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_extract_title_returns_502_when_gemini_unconfigured(
    monkeypatch: pytest.MonkeyPatch, sample_pdf_bytes: bytes
) -> None:
    import lc_logic.services.pdf as pdf_module
    from lc_logic.core.config import GOOGLE_SETTINGS

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=sample_pdf_bytes)

    class _PatchedAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(pdf_module.httpx, "AsyncClient", _PatchedAsyncClient)
    monkeypatch.setattr(GOOGLE_SETTINGS, "API_KEY", None)

    response = client.post(
        "/extract-title", json={"file_url": "http://django:8000/media/resources/1/file/"}
    )
    assert response.status_code == 502
    assert "GOOGLE_API_KEY" in response.json()["detail"]


def test_extract_title_returns_title_on_success(
    monkeypatch: pytest.MonkeyPatch, sample_pdf_bytes: bytes
) -> None:
    import lc_logic.services.pdf as pdf_module

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=sample_pdf_bytes)

    class _PatchedAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(pdf_module.httpx, "AsyncClient", _PatchedAsyncClient)

    async def fake_extract_title(leading_text: str) -> str:
        assert "The Great Example Book" in leading_text
        return "The Great Example Book"

    monkeypatch.setattr(title_module, "extract_title", fake_extract_title)
    # The router imported the function by name, so patch it there too.
    import lc_logic.routers.resources as resources_module

    monkeypatch.setattr(resources_module, "extract_title", fake_extract_title)

    response = client.post(
        "/extract-title", json={"file_url": "http://django:8000/media/resources/1/file/"}
    )
    assert response.status_code == 200
    assert response.json() == {"title": "The Great Example Book"}
