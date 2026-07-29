SHELL := /bin/bash

.PHONY: install dev-backend dev-frontend db-up db-down db-logs migrate migration \
	dataset-generate dataset-review dataset-analyze preprocessing-examples \
	nlp-data-artifacts nlp-train nlp-artifacts lint format format-check typecheck \
	test test-e2e build check

install:
	uv sync --project apps/backend --dev
	bun install

dev-backend:
	uv run --project apps/backend uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	bun run --cwd apps/frontend dev

db-up:
	docker compose up -d mysql

db-down:
	docker compose down

db-logs:
	docker compose logs -f mysql

migrate:
	uv run --project apps/backend alembic -c apps/backend/alembic.ini upgrade head

migration:
	uv run --project apps/backend alembic -c apps/backend/alembic.ini revision --autogenerate -m "$(message)"

dataset-generate:
	uv run --project apps/backend python apps/backend/scripts/generate_intents_dataset.py

dataset-review: dataset-generate
	uv run --project apps/backend python apps/backend/scripts/review_intents_dataset.py

dataset-analyze: dataset-generate
	uv run --project apps/backend python apps/backend/scripts/analyze_intents_dataset.py

preprocessing-examples:
	uv run --project apps/backend python apps/backend/scripts/export_preprocessing_examples.py

nlp-data-artifacts: dataset-review dataset-analyze preprocessing-examples

nlp-train: dataset-generate
	uv run --project apps/backend python apps/backend/scripts/train_intent_classifier.py

nlp-artifacts: nlp-data-artifacts nlp-train

lint:
	uv run --project apps/backend ruff check apps/backend
	bun run --cwd apps/frontend lint

format:
	uv run --project apps/backend ruff format apps/backend
	bun run format

format-check:
	uv run --project apps/backend ruff format --check apps/backend
	bun run format:check

typecheck:
	uv run --project apps/backend mypy --config-file apps/backend/pyproject.toml apps/backend/app
	bun run --cwd apps/frontend typecheck

test:
	uv run --project apps/backend pytest apps/backend/tests
	bun run --cwd apps/frontend test

test-e2e:
	bun run --cwd apps/frontend test:e2e

build:
	bun run --cwd apps/frontend build

check: lint format-check typecheck test test-e2e build
