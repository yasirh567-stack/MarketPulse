# Deployment

The application has no core-logic dependency on any specific hosting platform —
everything platform-specific lives in `Dockerfile`s, `docker-compose.yml`, and this
document, never inside `app/` or `src/`.

> **Note on this repo's verification**: the host used to build this project had no
> local Docker engine, so the Dockerfiles/compose setup below are authored to spec
> and best practice but were not exercised with an actual `docker compose up` on
> this machine. Local verification was done via native `venv` + `npm run dev` /
> `vite build`, which did run successfully end-to-end (see the root README's test
> results). If you have Docker available, `docker compose up --build` from the repo
> root should work as written — please report an issue if it doesn't.

## Local (recommended for development)

```bash
make setup   # backend venv + deps, frontend npm install, .env from .env.example
make demo    # DEMO_MODE=true, both servers, zero API keys needed
```

## Local via Docker Compose

```bash
docker compose up --build
# backend:  http://localhost:8000
# frontend: http://localhost:8080
```

`docker-compose.yml` reads its configuration from environment variables with
sensible demo-mode defaults baked in — copy `.env.example` to `.env` at the repo
root and Compose will pick it up automatically, or export the variables in your
shell before running.

## Free-tier hosting

### Backend (FastAPI)

Any host that can run a long-lived Python/Docker process works — for example
**Render** (free web service tier), **Fly.io** (free allowance), or **Railway**.
General steps:

1. Point the platform at `backend/Dockerfile` (or use its native Python buildpack
   with `pip install -r requirements.txt` and start command
   `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
2. Set environment variables from `.env.example` — at minimum `DEMO_MODE`,
   `DATABASE_URL`, `CORS_ORIGINS` (set to your deployed frontend's origin).
3. For persistence beyond the container's ephemeral disk, either accept that a
   free-tier SQLite file resets on redeploy (fine for a demo), or point
   `DATABASE_URL` at a free-tier Postgres instance (Render, Railway, and Neon all
   offer one) — no application code changes are required, only the connection string.
4. Free tiers often spin down on idle — the health check endpoint
   (`/api/v1/health`) is a reasonable target for a keep-alive ping if desired.

### Frontend (static React build)

Any static host works — **Vercel**, **Netlify**, **GitHub Pages**, or the
`frontend/Dockerfile`'s nginx image behind any container host.

1. Build command: `npm run build` (outputs to `frontend/dist/`).
2. Set `VITE_API_BASE_URL` and `VITE_WS_BASE_URL` to your deployed backend's
   `https://`/`wss://` URL at build time (these are baked into the static bundle,
   not read at runtime — rebuild if the backend URL changes).
3. Configure an SPA fallback (rewrite all paths to `index.html`) so React Router's
   client-side routes work on refresh — see `frontend/nginx.conf` for the
   equivalent nginx config if self-hosting.

## Environment variable reference

See `.env.example` at the repo root for the full list with inline comments. The
only variables that affect a typical free-tier deploy:

| Variable | Purpose |
|---|---|
| `DEMO_MODE` | `true` for zero-config demo; `false` to attempt real providers |
| `DATABASE_URL` | SQLite by default; swap for a Postgres DSN with no code changes |
| `CORS_ORIGINS` | Must include your deployed frontend's exact origin |
| `ENABLE_FINBERT` | Leave `false` unless you've provisioned enough memory/CPU for torch |
| `ENABLE_REDDIT` / `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | Optional social sentiment |
| `MARKET_POLL_INTERVAL_SECONDS` | WebSocket push cadence |
| `VITE_API_BASE_URL` / `VITE_WS_BASE_URL` (frontend, build-time) | Where the SPA calls the API |

## Security notes for a real deployment

- Never commit a real `.env` — it's gitignored; only `.env.example` (with no real
  secrets) is tracked.
- Set `CORS_ORIGINS` to the exact deployed frontend origin(s), not `*`.
- If enabling Reddit, treat `REDDIT_CLIENT_SECRET` as a secret in your host's
  secret manager, not a plain environment variable in a public CI log.
- The rate limiter (`slowapi`) is in-memory per process — fine for a single
  free-tier instance; a multi-instance deployment would need a shared backend
  (e.g. Redis) for rate-limit state to be consistent across instances.
