.PHONY: dev dev-backend dev-frontend up down test ingest eval eval-retrieval

# --- Run ---
up:
	docker compose up --build

down:
	docker compose down

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

# --- Quality ---
test:
	cd backend && python -m pytest -q

# --- Data / Eval (targets grow in later phases) ---
ingest:
	cd backend && python scripts/ingest_corpus.py

eval:
	cd backend && python -m eval.run_eval

eval-retrieval:
	cd backend && python -m eval.run_eval --retrieval-only
