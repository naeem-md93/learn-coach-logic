import uvicorn
from fastapi import FastAPI

from lc_logic.core.config import PROJECT_SETTINGS
from lc_logic.routers import resources


app = FastAPI(
    title="learn-coach-logic",
    description=(
        "Stateless AI-logic service for Learn Coach. Called only by "
        "learn-coach-service (Django) — never directly by the UI. "
        "See CONTEXT.md at the repo root of the learn-coach workspace."
    ),
    version="0.1.0",
)

app.include_router(resources.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    """Dev entrypoint: `python -m lc_logic` runs the app under uvicorn."""
    uvicorn.run(
        "lc_logic.__main__:app",
        host=PROJECT_SETTINGS.HOST,
        port=PROJECT_SETTINGS.PORT,
        reload=True,
    )


if __name__ == "__main__":
    main()
