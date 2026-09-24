# learn-coach-logic

Stateless FastAPI service that provides the AI logic for Learn Coach
(chat, quiz generation, PDF page rendering, and lightweight resource-title
extraction). It has no database of its own — `learn-coach-service` (Django)
owns all persistent data and is the only caller of this service.

See `../CONTEXT.md` (repo root of the `learn-coach` workspace) for the full
domain model and service boundaries.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# then edit .env and set GOOGLE_API_KEY
```

## Run

```bash
python -m lc_logic
# or, equivalently:
uvicorn lc_logic.__main__:app --reload --host 0.0.0.0 --port 8001
```

The service listens on port 8001 by default (see `.env` / `PROJECT_PORT`).
No CORS configuration is needed: the request path is always
`UI → Django → FastAPI → Django → UI`, the UI never calls this service
directly.

## Test

```bash
pytest
```

## Endpoints

### `POST /extract-title`

Called once, synchronously, when Django receives a newly uploaded Resource,
to derive a display title from the PDF content.

Request body:

```json
{
  "file_url": "http://django:8000/media/resources/<id>/file/"
}
```

`file_url` must be an HTTP(S) URL that this service can `GET` directly to
retrieve the PDF bytes (not a shared filesystem path, not raw bytes in the
request body).

Response body (`200 OK`):

```json
{
  "title": "Campbell Biology"
}
```

Behavior:
- Downloads the PDF from `file_url`, extracts raw text from up to the first
  4 pages (text only — no OCR/vision at this step), and asks Gemini
  (`gemini-flash-latest` by default via `langchain-google-genai`, see
  `GEMINI_TITLE_MODEL` below) to extract the title.
- If none of the leading pages have extractable text (e.g. a scanned PDF),
  returns a fallback title `"Untitled Resource"` instead of failing.
- Errors are returned as HTTP errors with a clear message, so Django can
  fall back (e.g. to the uploaded filename) instead of crashing:
  - `422 Unprocessable Entity` — `file_url` couldn't be downloaded, or the
    downloaded content isn't a valid PDF.
  - `502 Bad Gateway` — the Gemini call failed (including a missing/invalid
    `GOOGLE_API_KEY`).

### `GET /health`

Trivial liveness check, returns `{"status": "ok"}`.

## Configuration

Environment variables (see `.env.example`):

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `GOOGLE_API_KEY` | yes (for `/extract-title`) | — | Gemini API key used by `langchain-google-genai`. |
| `GEMINI_TITLE_MODEL` | no | `gemini-flash-latest` | Model used for title extraction. Google periodically retires dated Gemini model IDs (e.g. `gemini-2.5-flash` was retired for new users in Sep 2026) — `gemini-flash-latest` is Google's rolling alias for the current stable Flash model, chosen specifically to reduce how often this needs to change. If it ever 404s, check https://ai.google.dev/gemini-api/docs/models for a current ID before overriding — do not trust a model name suggested inside an error message without cross-checking it. |
| `PROJECT_HOST` | no | `0.0.0.0` | Dev-only bind host (`uvicorn --reload`). |
| `PROJECT_PORT` | no | `8001` | Dev-only bind port. |

## Notes for future work (chat / quiz)

Not implemented yet — out of scope for the current "library" feature slice:
- On-demand PDF page → image rendering with caching on the shared Docker
  volume (`resource_id/page_N.png`).
- Chat endpoint (current page + one prior page + session history, vision
  model, non-streaming).
- Quiz generation endpoint (all studied pages' images sent together,
  10 multiple-choice questions, dynamic Concept Tags).
