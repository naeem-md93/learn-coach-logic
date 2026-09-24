FROM python:3.13-slim

# Prevent .pyc files and enable unbuffered stdout/stderr (so logs show up
# immediately in Railway's log stream).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements.txt
# changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# NOTE: this service is stateless (no DB, no Railway private network
# dependency), so there is nothing that must run at container boot other
# than the app server itself. Still, per convention, the start command
# lives here (runtime) rather than anything being baked in at build time.
# Railway assigns $PORT at runtime — it must NOT be hardcoded (e.g. 8001).
CMD ["sh", "-c", "uvicorn lc_logic.__main__:app --host 0.0.0.0 --port $PORT"]
