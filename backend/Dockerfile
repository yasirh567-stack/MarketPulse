# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

# Build arg to optionally install the heavier FinBERT/SHAP extras
# (torch + transformers + shap). Off by default to keep the image small and
# the free-tier deploy story fast; set to "true" to bake them in instead of
# installing at runtime.
ARG INSTALL_ML_EXTRAS=false

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$INSTALL_ML_EXTRAS" = "true" ]; then pip install --no-cache-dir -r requirements-ml.txt; fi

COPY . .

# Pre-create the data dir (mount point for the SQLite volume) so it exists
# with the right ownership before the named volume is first attached —
# otherwise Docker creates it as root and the non-root user below can't write.
RUN mkdir -p /app/data

# Non-root user for defense in depth.
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run migrations then start the API. Alembic is the source of truth for
# schema; the app's own startup also auto-creates tables as a zero-config
# fallback, so this remains safe even against a brand-new empty database.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
