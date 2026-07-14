# Architecture

## System overview

```mermaid
flowchart LR
    subgraph Providers["Data Providers (free / demo)"]
        YF[yfinance\nquotes + history]
        RSS[Public RSS feeds\nGoogle News RSS]
        REDDIT[Reddit API\n(optional, off by default)]
        DEMO[Repo-bundled demo\nfixtures]
    end

    subgraph Ingest["Ingestion & Normalization"]
        NORM[Provider adapters\nnormalize + dedupe + sanitize]
        HEALTH[Provider health tracker\ncircuit breaker + retries]
    end

    subgraph Store["Persistence"]
        DB[(SQLite / PostgreSQL\nSQLAlchemy + Alembic)]
        CACHE[(DB-backed TTL cache\noptional Redis)]
    end

    subgraph Intelligence["NLP + Feature Engineering + ML/Backtesting"]
        NLP[VADER / optional FinBERT\nsentiment scoring]
        EVT[Rule-based event detector]
        FEAT[Time-aligned feature builder]
        ML[scikit-learn models\nwalk-forward validation]
        BT[Backtesting engine]
        ASSIST[TF-IDF retrieval\nmarket assistant]
    end

    subgraph API["FastAPI Layer"]
        REST["/api/v1 REST routes"]
        WS["/api/v1/ws/market\nWebSocket"]
    end

    subgraph FE["React Dashboard"]
        UI[Vite + React + TS\nTailwind + Plotly]
    end

    YF --> NORM
    RSS --> NORM
    REDDIT -.optional.-> NORM
    DEMO --> NORM
    NORM --> HEALTH --> DB
    NORM --> CACHE
    DB --> NLP --> DB
    DB --> EVT --> DB
    DB --> FEAT --> ML --> DB
    FEAT --> BT --> DB
    DB --> ASSIST
    DB --> REST
    CACHE --> REST
    ML --> REST
    BT --> REST
    ASSIST --> REST
    DB --> WS
    REST --> UI
    WS --> UI
```

## Layering & responsibilities

| Layer | Responsibility | Key modules |
|---|---|---|
| Providers | Talk to external free sources OR return bundled demo fixtures. All providers implement a common `Protocol` so the rest of the app never branches on "which vendor." | `backend/app/providers/*` |
| Ingestion | Normalize heterogeneous provider payloads into DB rows: consistent field names, timezone-aware timestamps, de-duplication by content hash/URL, HTML/script sanitization. | `backend/app/services/ingestion.py` |
| Persistence | SQLAlchemy models + Alembic migrations. SQLite by default; `DATABASE_URL` swaps to Postgres with no code changes. A DB-backed TTL cache table stands in for Redis when Redis isn't configured. | `backend/app/database/*`, `backend/app/models/*` |
| NLP | VADER always available (pure Python, no download). FinBERT is optional, lazy-loaded once, cached in-process; falls back to VADER on any failure (missing torch/transformers, OOM, no network for weights). Every score row records `model_name` + `model_version`. | `backend/app/nlp/*` |
| Feature engineering | Builds the ML feature matrix with strict "as-of" alignment: a feature for trading day *T* may only use price data through *T* and text published strictly before *T*'s market close. | `backend/app/ml/features.py` |
| ML | Baselines + logistic regression + gradient boosting, `TimeSeriesSplit`/expanding-window walk-forward CV, `CalibratedClassifierCV`, permutation importance (SHAP optional). | `backend/app/ml/*` |
| Backtesting | Event-driven simulation over the same time-aligned features; transaction costs + slippage; compares against buy-and-hold; every metric computed from realized trade fills, no peeking at future bars. | `backend/app/backtesting/*` |
| Assistant | TF-IDF vectorizes recent stored headlines/events/sentiment for a ticker, ranks by cosine similarity to the question, and fills a deterministic template with the top evidence + citations. No generative LLM call is required. | `backend/app/services/assistant.py` |
| API | Versioned REST (`/api/v1`) + one WebSocket endpoint. Pydantic request/response schemas double as OpenAPI docs. | `backend/app/api/v1/*` |
| Frontend | React/TS SPA consuming the REST+WS API. TanStack Query owns server-state caching/retries; component state stays local. | `frontend/src/*` |

## Data status labeling

Every price/news/sentiment payload carries a `data_status` enum:
`live | delayed | historical | cached | demo`. The frontend renders a badge from
this field everywhere data is shown — it is never inferred client-side, so the
backend is the single source of truth for what a number actually is.

## Provider fallback chain

1. **Market data**: `YFinanceMarketDataProvider` → on any exception/rate-limit/timeout,
   falls back to `CachedMarketDataProvider` (last good DB snapshot, marked `cached`) →
   if nothing cached and `DEMO_MODE=true` or no network, `DemoMarketDataProvider`
   (bundled fixtures, marked `demo`).
2. **News**: `RssNewsProvider` (Google News RSS query per ticker, no key) → cached DB
   rows → demo fixtures.
3. **Social**: optional; disabled unless Reddit credentials are present in env. Absence
   never breaks the app — sentiment aggregates simply have zero social rows.
4. **NLP model**: FinBERT (if `ENABLE_FINBERT=true` and transformers/torch import and
   the model loads) → VADER otherwise. The active model is reported at `/api/v1/health`.

## Why these technical choices

- **SQLite by default**: zero-ops local/demo story; `DATABASE_URL` env var is the only
  thing that changes to point at Postgres in a real deployment — no ORM-specific code
  forks.
- **yfinance over paid market-data APIs**: free, no key, good enough granularity for
  daily-bar research; explicitly documented as delayed/unofficial, not exchange-grade.
- **VADER default / FinBERT optional**: VADER needs no download and runs anywhere;
  FinBERT is a genuine upgrade for financial phrasing but pulls in torch + a model
  download, so it's opt-in and lazily loaded to keep startup fast and free-tier-hostable.
- **Walk-forward validation only**: shuffled train/test splits leak future information
  into the past for time series; this project's credibility rests on avoiding that.
- **TF-IDF assistant over an LLM**: fully local, deterministic, free, and — critically —
  cannot hallucinate citations, because it can only ever quote rows that exist in the DB.
