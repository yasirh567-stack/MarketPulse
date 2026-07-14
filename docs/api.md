# API Reference

Full interactive OpenAPI docs are always available from a running backend at
`/docs` (Swagger UI) and `/redoc`. This document is a human-readable index —
for exact request/response schemas, use the running `/docs` page, which is
generated directly from the Pydantic models and therefore never drifts out of
sync with the code.

Base path: **`/api/v1`**. All responses are JSON. Errors follow
`{"error": "<code>", "message": "<human-readable>"}` with an appropriate HTTP
status (422 for validation/insufficient-data, 503 for provider outages, 429 for
rate limiting, 500 for unexpected errors — never a raw stack trace).

## Health

`GET /health` — API/DB/provider status, active sentiment model, FinBERT
availability. No auth, not rate-limited, safe to poll.

## Instruments

- `GET /instruments/search?q=` — ticker/company-name search. Debounce on the
  client (the frontend does this at 300ms).
- `GET /instruments/screener?tickers=AAPL,MSFT` — batched price + aggregate
  sentiment overview for several tickers in one call; omit `tickers` to get the
  bundled demo tickers. Powers the Dashboard's watchlist sidebar and any future
  "which of my stocks look bullish" view.

## Macro

`GET /macro/buffett-indicator` — market-cap-to-GDP valuation gauge (the
"Buffett Indicator"), with historical series and a percentile-rank-based
interpretation. Real data requires a free FRED API key (`ENABLE_FRED` +
`FRED_API_KEY`); falls back to a clearly-labeled demo series otherwise. See
`docs/data-sources.md` for methodology.

## Market data

- `GET /market/{ticker}/quote` — current/delayed/demo quote.
- `GET /market/{ticker}/history?interval=1d&period_days=180` — OHLCV bars.
  `interval` ∈ `{1d, 1h, 1wk}`; the response is downsampled to at most 500 points
  for chart rendering (raw stored data is unaffected).

## News

`GET /news/{ticker}?page=1&page_size=10` — paginated, deduplicated headlines.
Ingests fresh headlines (subject to provider fallback) on each call, then scores
and event-detects any newly seen articles.

## Sentiment

`GET /sentiment/{ticker}?window_days=30` — daily aggregated timeline
(avg. compound score, bullish/neutral/bearish counts), plus a source-type and
model comparison (news vs. social; VADER vs. FinBERT, whichever actually scored
the text).

## Events

`GET /events/{ticker}` — recently detected events (category, matched keywords,
confidence, source headline). Always includes a disclaimer that detection is
correlational keyword matching, not proof of causality.

## Predictions & models

- `GET /predictions/{ticker}` — the current next-day direction estimate.
  Trains a model on demand if none exists or the existing one is stale (>12h);
  returns `422 insufficient_data` if the ticker doesn't have enough aligned
  history yet.
- `POST /models/train` `{"ticker": "AAPL", "model_name": "gradient_boosting"}` —
  force a (re)train and return full validation metrics.
- `GET /models/{ticker}/latest` — the most recent trained model's full metrics
  (combined/price-only/sentiment-only, baselines, confusion matrix, feature
  importance). 422 if nothing has been trained yet for that ticker.

## Backtests

- `POST /backtests` — run a new backtest (see `docs/backtesting-methodology.md`
  for the request fields and what they mean); returns the full result inline.
- `GET /backtests/{run_id}` — re-fetch a previously run backtest's stored result.

## Assistant

`POST /assistant/query` `{"ticker": "AAPL", "question": "Why is this moving?"}` —
retrieval-based, cited, deterministic answer. See `docs/architecture.md` for how
this avoids ever fabricating a citation.

## Watchlists

No authentication — each browser generates and persists its own anonymous
identifier (`watchlist_id` in these paths), then the backend gets-or-creates a
`Watchlist` row keyed by that string.

- `GET /watchlists/{watchlist_id}`
- `POST /watchlists/{watchlist_id}/items` `{"ticker": "AAPL"}`
- `DELETE /watchlists/{watchlist_id}/items/{ticker}`

## WebSocket

`WS /api/v1/ws/market` — JSON text-frame protocol:

```
Client -> Server: {"action": "subscribe", "ticker": "AAPL"}
                   {"action": "unsubscribe", "ticker": "AAPL"}
                   {"action": "ping"}
Server -> Client:  {"type": "quote", "ticker": "AAPL", "data": {...}}
                    {"type": "subscribed" | "unsubscribed", "ticker": "AAPL"}
                    {"type": "pong"}
                    {"type": "error", "message": "..."}
```

Quotes are pushed on a fixed interval (`MARKET_POLL_INTERVAL_SECONDS`, default 15s)
— this is explicitly polling, not tick-level streaming, and every quote payload
carries `data_status` so the client never mistakes a push for a live tick.

## Rate limiting

Resource-intensive routes (`POST /models/train`, `POST /backtests`,
`POST /assistant/query`) are rate-limited per client IP
(`RATE_LIMIT_PER_MINUTE`, default 120/min) via `slowapi`. Exceeding the limit
returns `429 {"error": "rate_limited", ...}`.
