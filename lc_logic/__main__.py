from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from lc_logic.core.config import PROJECT_SETTINGS
from lc_logic.core.logging import configure_logging
from lc_logic.core.middleware import RequestLoggingMiddleware
from lc_logic.routers import resources

# Applied at import time so it's already active for any request handled
# after startup. This alone is enough for `python -m lc_logic` (see
# log_config=None below) but NOT enough when uvicorn is launched via its own
# CLI (as the Dockerfile/Procfile do: `uvicorn lc_logic.__main__:app ...`) —
# in that case uvicorn re-applies its own default dictConfig *after*
# importing this module, which would silently override ours. The lifespan
# handler below re-applies configure_logging() one more time, after uvicorn
# has finished its own setup, so our format/handler wins regardless of how
# the process was launched.
configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Re-apply our logging config after uvicorn's own startup. uvicorn
    # (whether launched via its CLI or uvicorn.run(..., log_config=<its
    # default>)) calls logging.config.dictConfig() with its own formatters
    # during startup, which happens after this module is imported. Running
    # configure_logging() again here — guaranteed to run after uvicorn's own
    # logging setup — makes sure our stdout format is the one actually in
    # effect, no matter which entrypoint (CLI, `main()` below, Docker CMD,
    # Railway) started the process.
    configure_logging()
    yield


app = FastAPI(
    title="learn-coach-logic",
    description=(
        "Stateless AI-logic service for Learn Coach. Called only by "
        "learn-coach-service (Django) — never directly by the UI. "
        "See CONTEXT.md at the repo root of the learn-coach workspace."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)

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
        # Belt-and-suspenders for this specific entrypoint: skip uvicorn's
        # own dictConfig entirely so there's nothing to re-override. The
        # startup event above is what makes this work for every entrypoint
        # (including the Docker/Railway CLI form, which can't pass this).
        log_config=None,
    )


if __name__ == "__main__":
    main()
