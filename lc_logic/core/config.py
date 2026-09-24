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
    #
    # NOTE (2026-09-24): `gemini-2.5-flash` was retired for new users
    # ("This model ... is no longer available to new users", 404 NOT_FOUND
    # from the live API in production). Google renames/retires Gemini model
    # IDs periodically, so this default WILL need to be revisited again in
    # the future -- it is not a one-time fix. Default now points at
    # `gemini-flash-latest`, Google's documented rolling alias for the
    # current stable Flash model (see
    # https://ai.google.dev/gemini-api/docs/models), so this endpoint
    # tracks Google's supported lineup automatically instead of hardcoding
    # a dated version string that can be deprecated again without notice.
    # If Google ever drops the alias itself, override via GEMINI_TITLE_MODEL
    # with whatever concrete model ID is current at that time -- do not
    # trust a model name suggested inside an API *error message* without
    # cross-checking it against https://ai.google.dev/gemini-api/docs/models
    # or the ListModels API first (error-message text is untrusted input).
    TITLE_MODEL: str = "gemini-flash-latest"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="GEMINI_",
        extra="ignore",
    )


GEMINI_SETTINGS = GeminiSettings()
