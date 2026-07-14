.PHONY: setup demo dev dev-backend dev-frontend test test-backend test-frontend test-e2e \
        lint lint-backend lint-frontend format format-backend format-frontend \
        train seed migrate build build-backend build-frontend clean

PYTHON := python3.11
BACKEND_VENV := backend/.venv
BACKEND_PY := $(BACKEND_VENV)/bin/python
BACKEND_PIP := $(BACKEND_VENV)/bin/pip

## setup: create backend venv + install deps, install frontend deps, copy .env
setup:
	@test -d $(BACKEND_VENV) || $(PYTHON) -m venv $(BACKEND_VENV)
	$(BACKEND_PIP) install --upgrade pip
	$(BACKEND_PIP) install -r backend/requirements.txt -r backend/requirements-dev.txt
	cd frontend && npm install
	@test -f .env || cp .env.example .env
	@echo "Setup complete. Edit .env if needed, then run 'make demo' or 'make dev'."

## demo: one-command demo startup (DEMO_MODE=true, no API keys needed)
demo: migrate
	@echo "Starting MarketPulse AI in demo mode..."
	@echo "Backend:  http://localhost:8000 (docs at /docs)"
	@echo "Frontend: http://localhost:5173"
	DEMO_MODE=true $(MAKE) -j2 dev-backend dev-frontend

## dev: run backend + frontend concurrently using whatever DEMO_MODE is set in .env
dev: migrate
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	cd backend && DATABASE_URL=$${DATABASE_URL:-sqlite:///./marketpulse.db} $(PWD)/$(BACKEND_PY) -m uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

## migrate: apply Alembic migrations
migrate:
	cd backend && $(PWD)/$(BACKEND_PY) -m alembic upgrade head

## seed: (re)generate the bundled demo fixtures under data/demo/
seed:
	$(BACKEND_PY) scripts/generate_demo_fixtures.py

## train: run the standalone training CLI for one or more tickers
train:
	cd backend && $(PWD)/$(BACKEND_PY) -m scripts.train_models $(TICKERS)

## test: run both backend and frontend test suites
test: test-backend test-frontend

test-backend:
	cd backend && $(PWD)/$(BACKEND_PY) -m pytest -q --cov=app --cov-report=term-missing

test-frontend:
	cd frontend && npm run test

## test-e2e: Playwright smoke test (requires dev servers already running)
test-e2e:
	cd frontend && npm run test:e2e

## lint: ruff + mypy (backend), eslint (frontend)
lint: lint-backend lint-frontend

lint-backend:
	cd backend && $(PWD)/$(BACKEND_VENV)/bin/ruff check app tests
	cd backend && $(PWD)/$(BACKEND_VENV)/bin/mypy app

lint-frontend:
	cd frontend && npm run lint

## format: black (backend), prettier (frontend)
format: format-backend format-frontend

format-backend:
	cd backend && $(PWD)/$(BACKEND_VENV)/bin/black app tests
	cd backend && $(PWD)/$(BACKEND_VENV)/bin/ruff check app tests --fix

format-frontend:
	cd frontend && npm run format

## build: production build for the frontend, sanity-import the backend
build: build-backend build-frontend

build-backend:
	cd backend && $(PWD)/$(BACKEND_PY) -c "from app.main import app; print('backend imports OK')"

build-frontend:
	cd frontend && npm run build

## clean: remove local databases, caches, and build artifacts (keeps source + fixtures)
clean:
	rm -rf backend/.pytest_cache backend/.mypy_cache backend/.ruff_cache backend/htmlcov backend/.coverage
	rm -f backend/*.db
	rm -rf frontend/dist frontend/coverage frontend/playwright-report frontend/test-results
