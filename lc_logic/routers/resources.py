from fastapi import APIRouter
from fastapi import HTTPException

from lc_logic.schemas.resource import ExtractTitleRequest
from lc_logic.schemas.resource import ExtractTitleResponse
from lc_logic.services.pdf import PdfFetchError
from lc_logic.services.pdf import download_pdf
from lc_logic.services.pdf import extract_leading_text
from lc_logic.services.title import TitleExtractionError
from lc_logic.services.title import extract_title

router = APIRouter(tags=["resources"])


@router.post("/extract-title", response_model=ExtractTitleResponse)
async def extract_title_endpoint(payload: ExtractTitleRequest) -> ExtractTitleResponse:
    """Sync, lightweight step run once at Resource upload time.

    Downloads the PDF from `file_url` (an HTTP-fetchable URL Django provides
    — see CONTEXT.md), extracts raw text from up to the first 4 pages, and
    asks Gemini (via LangChain) for the book/paper title. Does not persist
    anything and does not touch the page-image cache used by chat/quiz.
    """
    try:
        pdf_bytes = await download_pdf(str(payload.file_url))
        leading_text = extract_leading_text(pdf_bytes)
    except PdfFetchError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        title = await extract_title(leading_text)
    except TitleExtractionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ExtractTitleResponse(title=title)
