"""Free-tier capacity: daily budgets, a concurrency gate, and the demo cache.

The whole point is to make "hundreds of prompts a day" honest on $0 hosting.
Three levers:

- A per-provider daily budget (usage_daily). A provider that has spent its free
  quota is skipped rather than 429'd mid-answer, and when every provider is
  exhausted the caller gets a calm capacity signal instead of a raw 503.
- A concurrency gate. Free tiers rate-limit hard, so a burst that opens dozens
  of parallel streams just gets them all rejected; serialising to a handful
  turns that into a short wait.
- A demo answer cache. The demo corpus and its suggested questions are fixed,
  so repeat demo traffic replays a stored answer at zero token cost — this is
  what actually stretches a small daily quota across many visitors.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import DemoAnswerCache, UsageDaily

logger = logging.getLogger("lumina.capacity")


class CapacityExhaustedError(Exception):
    """Every provider is over its daily free-tier budget, or no generation slot
    came free in time. Distinct from AllProvidersFailedError (providers actually
    erroring) so the API can show a calm "capacity reached, resets 00:00 UTC"
    message rather than a generic failure."""


def utc_day() -> str:
    """Today as YYYY-MM-DD in UTC — the boundary the free tiers reset on."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def normalize_query(q: str) -> str:
    """Collapse a question to a cache key: case- and whitespace-insensitive, so
    'What is  attention?' and 'what is attention?' share one cached answer."""
    return " ".join(q.lower().split())


# How each provider's free tier is metered. Groq occupies the "local" slot in
# production and is billed by tokens; Gemini's free tier is billed by requests.
_METRIC = {"local": "tokens", "gemini": "requests"}


def _daily_limit(provider: str) -> int:
    """Configured daily budget for a provider; 0 (or unknown) means unlimited."""
    return {
        "local": settings.BUDGET_LOCAL_TOKENS_PER_DAY,
        "gemini": settings.BUDGET_GEMINI_REQUESTS_PER_DAY,
    }.get(provider, 0)


class CapacityService:
    # One process-wide semaphore, created lazily so it binds to the running loop.
    _sem: asyncio.Semaphore | None = None

    @classmethod
    def _semaphore(cls) -> asyncio.Semaphore | None:
        if settings.MAX_CONCURRENT_GENERATIONS <= 0:
            return None
        if cls._sem is None:
            cls._sem = asyncio.Semaphore(settings.MAX_CONCURRENT_GENERATIONS)
        return cls._sem

    @classmethod
    @asynccontextmanager
    async def generation_slot(cls):
        """Hold a generation slot for the duration of the block, or raise
        CapacityExhaustedError if none frees up within the acquire timeout."""
        sem = cls._semaphore()
        if sem is None:
            yield
            return
        try:
            await asyncio.wait_for(
                sem.acquire(), timeout=settings.GENERATION_ACQUIRE_TIMEOUT_S
            )
        except (asyncio.TimeoutError, TimeoutError) as e:
            raise CapacityExhaustedError("no generation slot available") from e
        try:
            yield
        finally:
            sem.release()

    async def is_exhausted(self, provider: str) -> bool:
        limit = _daily_limit(provider)
        if limit <= 0:
            return False
        metric = _METRIC.get(provider, "requests")
        async with AsyncSessionLocal() as db:
            row = await db.get(UsageDaily, (utc_day(), provider))
        used = getattr(row, f"{metric}_used", 0) if row else 0
        return used >= limit

    async def record(self, provider: str, completion_tokens: int) -> None:
        """Add one generation's spend to today's ledger for a provider."""
        now = datetime.utcnow()
        stmt = (
            insert(UsageDaily)
            .values(
                day=utc_day(),
                provider=provider,
                tokens_used=max(completion_tokens, 0),
                requests_used=1,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["day", "provider"],
                set_={
                    "tokens_used": UsageDaily.tokens_used + max(completion_tokens, 0),
                    "requests_used": UsageDaily.requests_used + 1,
                    "updated_at": now,
                },
            )
        )
        async with AsyncSessionLocal() as db:
            await db.execute(stmt)
            await db.commit()


# ---- demo answer cache ------------------------------------------------------


async def cached_demo_answer(query: str) -> dict | None:
    """A stored answer for this demo question, or None. Returns citations as the
    stored list of dicts so the caller can replay them without re-retrieving."""
    if not settings.DEMO_ANSWER_CACHE_ENABLED:
        return None
    async with AsyncSessionLocal() as db:
        row = await db.get(DemoAnswerCache, normalize_query(query))
    if row is None:
        return None
    return {
        "answer": row.answer,
        "citations": row.citations or [],
        "model_used": row.model_used,
    }


async def store_demo_answer(
    query: str, answer: str, citations: list[dict], model_used: str | None
) -> None:
    if not settings.DEMO_ANSWER_CACHE_ENABLED or not answer.strip():
        return
    stmt = (
        insert(DemoAnswerCache)
        .values(
            query_norm=normalize_query(query),
            answer=answer,
            citations=citations,
            model_used=model_used,
            created_at=datetime.utcnow(),
        )
        # First writer wins: a later identical question is already served from
        # the cache, so there is nothing to update.
        .on_conflict_do_nothing(index_elements=["query_norm"])
    )
    async with AsyncSessionLocal() as db:
        await db.execute(stmt)
        await db.commit()


async def clear_demo_answer_cache() -> None:
    """Drop every cached demo answer — used on re-seed, since a new corpus would
    make the stored answers and their citations stale."""
    from sqlalchemy import delete

    async with AsyncSessionLocal() as db:
        await db.execute(delete(DemoAnswerCache))
        await db.commit()
