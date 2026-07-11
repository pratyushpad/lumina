# Lumina — Multimodal RAG

Production-grade multimodal document intelligence. Upload PDFs / images / text, then chat with cited, grounded answers powered by Claude.

## Architecture

```
PDF/IMG/TXT → Parser (PyMuPDF + pdfplumber) → Chunker → Embedder (MiniLM)
            → ChromaDB → Retriever (top-15) → Cross-encoder Reranker (top-5)
            → VisionService (Claude vision, image enrichment)
            → PromptBuilder → Claude (SSE stream) → React frontend
```

- **Backend**: FastAPI, SQLAlchemy + aiosqlite, ChromaDB, sentence-transformers (MiniLM), cross-encoder reranker, Anthropic SDK, sse-starlette
- **Frontend**: React 18 + Vite + TS, TailwindCSS, Framer Motion, Zustand, TanStack Query, react-dropzone, react-markdown

## Quickstart (Docker)

```bash
cp backend/.env.example backend/.env
# put your Anthropic key in backend/.env
docker-compose up --build
# UI: http://localhost:5173
# API: http://localhost:8000  (docs at /docs)
```

## Local dev

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
```

## End-to-end test

1. Open http://localhost:5173, click "Start for free".
2. Click "New Session".
3. Drop a PDF into the document panel — watch the status badge go `processing → ready`.
4. Ask a question. Tokens stream in. Citation chips appear below the answer; click one to expand the chunk.

## Project layout

```
backend/app/
  config.py, database.py, main.py
  models/         # Session, Document, Message (SQLAlchemy)
  schemas/        # Pydantic I/O
  services/
    ingestion/    # parser (PyMuPDF + pdfplumber), chunker (recursive), extractor
    embedding/    # sentence-transformer singleton
    vectorstore/  # Chroma persistent client
    retrieval/    # retriever + cross-encoder reranker
    multimodal/   # Claude vision describe + cache
    generation/   # prompt builder + LLM (stream + non-stream)
  routers/        # sessions, documents, chat (SSE), health
  middleware/     # error handler
  utils/          # file, image, text helpers
frontend/src/
  pages/          # LandingPage, AppPage
  components/     # ui, layout, chat, upload, sessions
  stores/         # zustand (session, chat, document)
  hooks/          # useDocumentStatus polling
  lib/            # api client (+ streamChat via EventSource)
```

## API Surface

- `POST /api/sessions/` · `GET /api/sessions/` · `PATCH /api/sessions/{id}` · `DELETE /api/sessions/{id}`
- `POST /api/documents/upload` (multipart: session_id, file) · `GET /api/documents/session/{id}` · `GET /api/documents/{id}/status` · `DELETE /api/documents/{id}`
- `POST /api/chat/{session_id}` (non-streaming) · `GET /api/chat/{session_id}/stream?query=...` (SSE) · `GET /api/chat/{session_id}/history`
- `GET /health`

## Notes

- LLM model defaults to `claude-sonnet-4-6`; override via `LLM_MODEL` in `.env`.
- All RAG components are implemented from scratch — no LangChain / LlamaIndex.
- The reranker maps cross-encoder scores through a sigmoid for friendlier 0–1 relevance display.
- Vectors are L2-normalized; cosine similarity is used in ChromaDB.

## Tests

```bash
cd backend && pytest -q
```
