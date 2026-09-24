"""Title extraction from leading page text, via LangChain + Gemini."""

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from pydantic import Field

from lc_logic.core.config import GEMINI_SETTINGS
from lc_logic.core.config import GOOGLE_SETTINGS

FALLBACK_TITLE = "Untitled Resource"


class TitleExtractionError(Exception):
    """Raised when the LLM call fails or no API key is configured."""


class _TitleResult(BaseModel):
    title: str = Field(
        ...,
        description=(
            "The book or paper title, exactly as it appears in the text, "
            "with no extra commentary, quotes, or formatting."
        ),
    )


_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You extract the title of a book or academic paper from the raw text of "
            "its first few pages (cover page, title page, or abstract). Respond with "
            "only the title itself: no author names, no explanations, no surrounding "
            "quotes. If you truly cannot determine a title, respond with an empty string.\n\n"
            "{format_instructions}",
        ),
        ("human", "Text from the first pages of the document:\n\n{leading_text}"),
    ]
)


def _build_chain():
    if not GOOGLE_SETTINGS.API_KEY:
        raise TitleExtractionError(
            "GOOGLE_API_KEY is not configured; cannot call the Gemini title-extraction model."
        )

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_SETTINGS.TITLE_MODEL,
        google_api_key=GOOGLE_SETTINGS.API_KEY,
        temperature=0,
    )
    parser = PydanticOutputParser(pydantic_object=_TitleResult)
    prompt = _PROMPT.partial(format_instructions=parser.get_format_instructions())
    return prompt | llm | parser


async def extract_title(leading_text: str) -> str:
    """Ask Gemini for the title given the raw text of the leading pages.

    Falls back to a generic placeholder (never raises) if there's simply no
    text to work with (e.g. all leading pages were scanned images) — callers
    that want to surface hard failures (missing API key, LLM/network error)
    should let TitleExtractionError propagate to the route, which maps it to
    an HTTP error so Django can apply its own fallback.
    """
    if not leading_text.strip():
        return FALLBACK_TITLE

    chain = _build_chain()
    try:
        result = await chain.ainvoke({"leading_text": leading_text})
    except TitleExtractionError:
        raise
    except Exception as exc:
        raise TitleExtractionError(f"Gemini title extraction failed: {exc}") from exc

    title = (result.title or "").strip()
    return title or FALLBACK_TITLE
