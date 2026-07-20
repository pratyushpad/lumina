import json
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    GEMINI_API_KEY: str = ""
    DATABASE_URL: str = "postgresql+asyncpg://lumina:lumina@localhost:5433/lumina"
    UPLOAD_DIR: str = "./storage/uploads"
    PROCESSED_DIR: str = "./storage/processed"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Ingestion
    CHUNKING_STRATEGY: str = "recursive"  # fixed | recursive | semantic
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150

    # Retrieval pipeline defaults (per-request overridable via RetrievalConfig)
    RETRIEVAL_MODE: str = "hybrid_rrf"  # dense | sparse | hybrid_rrf
    SPARSE_METHOD: str = "bm25"  # bm25 (true BM25, in-process) | fts (Postgres ts_rank_cd)
    QUERY_TRANSFORM: str = "none"  # none | multi_query | hyde
    RRF_K: int = 60
    TOP_K_CANDIDATES: int = 50
    TOP_K_RERANKED: int = 5

    # Guardrails
    GUARDRAIL_REFUSAL_ENABLED: bool = True
    # Calibrated via the sweep in docs/eval.md: 0.25 gave 0% false refusals and
    # 0% false answers on the 42+10 question eval set (0.35 caused one false refusal).
    MIN_RERANK_SCORE: float = 0.25
    # Second-chance gate: refusal requires the bi-encoder to also score the top
    # candidates below this cosine similarity (catches synonym phrasings the
    # cross-encoder under-scores, e.g. "salary" vs "compensation").
    MIN_BIENCODER_SIM: float = 0.25
    PII_SCRUB_ON_INGEST: bool = False

    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_MAX_TOKENS: int = 2048

    # Provider routing: try providers in order, fall back on failure/unhealthy.
    # "local" = OpenAI-compatible endpoint (Ollama/vLLM on the GPU box or this machine).
    LLM_PROVIDER_ORDER: str = "local,gemini"
    LOCAL_LLM_BASE_URL: str = "http://localhost:11434/v1"
    # Optional Bearer token for hosted OpenAI-compatible endpoints (Groq, Cerebras, …).
    LOCAL_LLM_API_KEY: str = ""
    LOCAL_LLM_MODEL: str = "qwen2.5:7b-instruct-q4_K_M"
    LOCAL_LLM_TIMEOUT_S: float = 120.0
    # slowapi rate limits (per client key: owner token if present, else IP)
    RATE_LIMIT_CHAT: str = "20/minute"
    RATE_LIMIT_UPLOAD: str = "10/minute"
    RATE_LIMIT_DEFAULT: str = "60/minute"
    # How many proxies sit in front of the app. X-Forwarded-For is client-
    # appendable, so only the last N hops are trustworthy: the real client IP is
    # the (N+1)-th entry counting from the right. HF Spaces adds exactly one hop;
    # direct/local access has zero. Getting this wrong lets a client spoof its
    # rate-limit key by sending its own XFF header.
    TRUSTED_PROXY_HOPS: int = 0

    # Daily free-tier budgets, counted in usage_daily and reset at 00:00 UTC.
    # 0 = unlimited (a real local GPU has no quota). In production the "local"
    # slot is Groq's free tier (metered by tokens) and "gemini" is Gemini's free
    # tier (metered by requests); a provider over budget is skipped, and when
    # every provider is exhausted the client sees a capacity banner, never a 503.
    BUDGET_LOCAL_TOKENS_PER_DAY: int = 0
    BUDGET_GEMINI_REQUESTS_PER_DAY: int = 0
    # Concurrent LLM generations allowed at once. Free tiers rate-limit hard, so
    # letting a burst open dozens of parallel streams just gets them all 429'd;
    # serialising to a small number degrades to a short wait instead. 0 = no cap.
    MAX_CONCURRENT_GENERATIONS: int = 4
    # How long a request waits for a generation slot before giving up with a
    # capacity signal rather than hanging.
    GENERATION_ACQUIRE_TIMEOUT_S: float = 30.0
    # Serve repeat demo questions from demo_answer_cache at zero token cost. The
    # demo corpus and its suggested questions are fixed, so this is what makes
    # "hundreds of demo prompts/day" true on a free tier.
    DEMO_ANSWER_CACHE_ENABLED: bool = True
    # Seed the public demo session at startup (prod: baked demo_docs/ + persistent DB
    # make this a cheap no-op after the first boot).
    SEED_DEMO_ON_STARTUP: bool = False

    # Google sign-in (optional). Self-rolled OAuth authorization-code flow: the
    # SPA sends the browser to Google, Google returns a code to the SPA callback,
    # and the backend exchanges it (client secret stays server-side). Sign-in is
    # hidden entirely unless all three are set — the app is fully usable signed
    # out. JWT_SECRET signs our own 7-day session tokens; it must be a fixed,
    # secret value in production (a random per-boot default would log everyone
    # out on every restart).
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    # Where Google returns the browser — the SPA's callback route. Must exactly
    # match an authorised redirect URI on the Google OAuth client.
    OAUTH_REDIRECT_URI: str = "http://localhost:5173/auth/callback"
    JWT_SECRET: str = ""
    JWT_EXPIRE_DAYS: int = 7

    @property
    def auth_enabled(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET and self.JWT_SECRET)

    # Comma-separated origins in env (e.g. "https://app.example.com,https://example.com").
    # Wildcards are rejected: allow_credentials=True + "*" would be an open CORS policy.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v):
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):  # legacy JSON-array form
                v = json.loads(s)
            else:
                v = [o.strip() for o in s.split(",") if o.strip()]
        if any(o == "*" for o in v):
            raise ValueError("CORS_ORIGINS must list explicit origins; '*' is not allowed")
        return v
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".txt", ".md", ".png", ".jpg", ".jpeg"]


settings = Settings()
