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

# pip is only the installer: the app never imports it, and the HEALTHCHECK
# below uses python's stdlib urllib, not pip. Remove it so the runtime image
# carries no installer at all. pip's vendored urllib3 2.7.0 (inside pip's own
# package tree, in both the base Python install and the copied venv) is what
# the Trivy image scan reports as CVE-2026-97687 and CVE-2026-97689 (both
# HIGH, fixed in urllib3 2.8.0); no pip release vendors a fixed urllib3 yet,
# so upgrading pip cannot clear the findings. Deleting the pip package trees
# is the only remediation today, and the vendored findings disappear from
# future Trivy DB updates once a fixed pip ships.
USER root
RUN rm -rf /usr/local/lib/python3.13/site-packages/pip \
           /usr/local/lib/python3.13/site-packages/pip-*.dist-info \
           /opt/venv/lib/python3.13/site-packages/pip \
           /opt/venv/lib/python3.13/site-packages/pip-*.dist-info \
    && rm -f /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.13 \
             /opt/venv/bin/pip /opt/venv/bin/pip3 /opt/venv/bin/pip3.13

USER whisper
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-"]

