from pydantic import BaseModel
from pydantic import Field
from pydantic import HttpUrl


class ExtractTitleRequest(BaseModel):
    # Django sends a single HTTP-fetchable URL to the PDF (e.g.
    # http://django:8000/media/resources/<id>/file/), never a shared
    # filesystem path and never raw file bytes. See CONTEXT.md "پردازش PDF".
    file_url: HttpUrl = Field(
        ...,
        description="HTTP(S) URL FastAPI can GET to download the resource's PDF file.",
    )


class ExtractTitleResponse(BaseModel):
    title: str = Field(..., description="Best-effort extracted title of the book/paper.")
