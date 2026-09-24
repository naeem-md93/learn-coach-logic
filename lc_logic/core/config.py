from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class ProjectSettings(BaseSettings):
    # Only consulted by local dev tooling (`uvicorn app.main:app --reload`).
    # Optional with dev-friendly defaults so importing settings doesn't
    # hard-fail in production environments that don't set these.
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="PROJECT_",
        extra="ignore",
    )


PROJECT_SETTINGS = ProjectSettings()


class GoogleSettings(BaseSettings):
    # Consumed by langchain-google-genai (ChatGoogleGenerativeAI) to call
    # the Gemini API. Must be set in `.env` for real requests to succeed;
    # left optional here so the app can still import/start without it (the
    # endpoint itself returns a clear 503 if it's missing at request time).
    API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="GOOGLE_",
        extra="ignore",
    )


GOOGLE_SETTINGS = GoogleSettings()


class GeminiSettings(BaseSettings):
    # Model used for the lightweight title-extraction task. Kept
    # configurable/overridable via env without touching code.
    TITLE_MODEL: str = "gemini-2.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="GEMINI_",
        extra="ignore",
    )


GEMINI_SETTINGS = GeminiSettings()
