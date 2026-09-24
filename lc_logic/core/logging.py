"""Logging configuration for learn-coach-logic.

Stdout-only (Railway and most PaaS collect logs from stdout/stderr, and
`docker logs` does the same locally), readable timestamped format, level
controlled by the `LOG_LEVEL` env var (default INFO).

Uses `logging.config.dictConfig` so we fully own the formatter/handler setup
for our own `lc_logic.*` loggers while still letting uvicorn's own loggers
(`uvicorn`, `uvicorn.access`, `uvicorn.error`) emit through the same kind of
handler/formatter — this avoids the common "duplicate log lines" problem
where both uvicorn's default config and a naive `logging.basicConfig()` call
each attach their own handler to the root logger.

`configure_logging()` must be called once, before the FastAPI app/uvicorn
loggers are used (i.e. at the top of `lc_logic/__main__.py`, before
`uvicorn.run(...)`). When running under `uvicorn.run(..., reload=True)` in
dev, uvicorn spawns a subprocess per reload and re-imports this module, so
this just re-applies the same config each time — that's fine and expected.
"""

import logging
import logging.config
import os

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _log_level() -> str:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    return level if level in logging._nameToLevel else "INFO"


def configure_logging() -> None:
    level = _log_level()

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": LOG_FORMAT,
                    "datefmt": DATE_FORMAT,
                },
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "handlers": ["stdout"],
                "level": level,
            },
            "loggers": {
                # Reuse the same stdout handler/formatter for uvicorn's own
                # loggers instead of uvicorn's default config, so every line
                # (ours + uvicorn's) has a consistent, timestamped format.
                "uvicorn": {"handlers": ["stdout"], "level": level, "propagate": False},
                "uvicorn.error": {"handlers": ["stdout"], "level": level, "propagate": False},
                # uvicorn.access logs one line per request on its own; we log
                # requests ourselves via middleware with more detail (status
                # + duration together), so silence the built-in access log to
                # avoid duplicate/noisy lines. Still available at DEBUG if
                # someone wants uvicorn's raw version too.
                "uvicorn.access": {"handlers": ["stdout"], "level": "WARNING", "propagate": False},
                "lc_logic": {"handlers": ["stdout"], "level": level, "propagate": False},
                # httpx logs one INFO line per request with the *full* URL,
                # including query string — that would leak the signed token
                # Django puts on file_url (see mask_url() in services/pdf.py,
                # which is how we log the same URL safely ourselves). Capped
                # at WARNING so it never leaks the token regardless of
                # LOG_LEVEL; still available if someone bumps this logger
                # specifically for local debugging.
                "httpx": {"handlers": ["stdout"], "level": "WARNING", "propagate": False},
            },
        }
    )
