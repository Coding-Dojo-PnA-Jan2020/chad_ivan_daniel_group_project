# syntax=docker/dockerfile:1

# ---- build stage: install dependencies into an isolated venv -------------
FROM python:3.13-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install -r requirements.txt

# ---- runtime stage: minimal image, non-root user -------------------------
FROM python:3.13-slim

LABEL org.opencontainers.image.title="Whisper" \
      org.opencontainers.image.description="Encrypted whisper social app" \
      org.opencontainers.image.source="https://github.com/Coding-Dojo-PnA-Jan2020/chad_ivan_daniel_group_project"

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_CONFIG=production

# Production config refuses to start without a real SECRET_KEY — always pass
# one (see README). SQLite works in-container for demos; mount a volume or
# point DATABASE_URL at MySQL for anything persistent.
RUN groupadd --system whisper && useradd --system --gid whisper --create-home whisper

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=whisper:whisper wsgi.py ./
COPY --chown=whisper:whisper app/ app/
COPY --chown=whisper:whisper migrations/ migrations/

USER whisper
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "wsgi:app"]
