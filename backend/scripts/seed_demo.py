"""Idempotent demo-session seeding: `python scripts/seed_demo.py` or at startup.

Reuses the deterministic ingest from scripts/ingest_corpus.py against the
demo_docs/ folder (baked into the Docker image, so the source PDFs survive
ephemeral-storage restarts on HF Spaces). Chunks/embeddings live in Postgres;
if every demo document is already `ready` there with chunks, seeding is a
cheap no-op — safe to run on every boot.
"""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.ingest_corpus import doc_id_for, ingest  # noqa: E402

logger = logging.getLogger("lumina.seed_demo")

DEMO_DOCS_DIR = Path(__file__).resolve().parents[1] / "demo_docs"
DEMO_SESSION_ID = "demo"


async def demo_already_seeded() -> bool:
    from app.config import settings
    from app.database import AsyncSessionLocal
    from app.models import Document

    files = sorted(
        p.name for p in DEMO_DOCS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in settings.ALLOWED_EXTENSIONS
    )
    if not files:
        return True  # nothing to seed
    async with AsyncSessionLocal() as db:
        for name in files:
            doc = await db.get(Document, doc_id_for(name))
            if doc is None or doc.status != "ready" or not doc.num_chunks:
                return False
    return True


async def seed_demo(force: bool = False) -> None:
    if not force and await demo_already_seeded():
        logger.info("Demo session already seeded — skipping")
        return
    logger.info("Seeding demo session %r from %s", DEMO_SESSION_ID, DEMO_DOCS_DIR)
    manifest = await ingest(
        DEMO_DOCS_DIR, DEMO_SESSION_ID, strategy=None, session_name="Demo — ask these papers anything"
    )
    logger.info("Demo seeded: %d documents", len(manifest["documents"]))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    asyncio.run(seed_demo(force="--force" in sys.argv))
