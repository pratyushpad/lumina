from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class UsageDaily(Base):
    """One row per (UTC day, provider): the running free-tier spend for the day.

    `day` is a plain YYYY-MM-DD string so "today" is a trivial, index-friendly
    equality with no timezone math at query time — the free tiers reset at
    00:00 UTC, which is what this string is. Old rows are harmless history; a
    nightly cleanup is not worth the moving part at this scale.
    """

    __tablename__ = "usage_daily"

    day = Column(String, primary_key=True)  # "2026-07-20" (UTC)
    provider = Column(String, primary_key=True)  # "local" | "gemini"
    tokens_used = Column(BigInteger, nullable=False, default=0)
    requests_used = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class DemoAnswerCache(Base):
    """A previously generated answer to a normalised demo question.

    The demo library is shared and its suggested questions are a fixed list, so
    repeat traffic replays a stored answer at zero token cost. Only demo,
    non-refusal turns are cached; the cache is truncated whenever the demo is
    re-seeded (a new corpus would make old answers stale).
    """

    __tablename__ = "demo_answer_cache"

    query_norm = Column(String, primary_key=True)
    answer = Column(String, nullable=False)
    citations = Column(JSONB, nullable=True)
    model_used = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
