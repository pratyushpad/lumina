import os

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.constants import DEMO_SESSION_ID
from app.database import get_db
from app.deps.owner import OwnerToken, load_session
from app.models import Document, Message, Session
from app.schemas.session import (
    SessionCreate,
    SessionListResponse,
    SessionRename,
    SessionResponse,
)
from app.services.retrieval.sparse import BM25Index
from app.services.vectorstore.pgvector import PgVectorStore
from app.utils.file_handler import cleanup_document_files, rmtree_safe

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


async def _to_response(
    db: AsyncSession, s: Session, token: str | None = None
) -> SessionResponse:
    doc_count = await db.scalar(
        select(func.count(Document.id)).where(Document.session_id == s.id)
    )
    msg_filter = [Message.session_id == s.id]
    if s.id == DEMO_SESSION_ID:
        # Everyone shares the demo row, so an unfiltered count would show each
        # visitor the total traffic through it rather than their own history.
        msg_filter.append(Message.owner_token == token)
    msg_count = await db.scalar(select(func.count(Message.id)).where(*msg_filter))
    return SessionResponse(
        id=s.id,
        name=s.name,
        created_at=s.created_at,
        updated_at=s.updated_at,
        document_count=doc_count or 0,
        message_count=msg_count or 0,
    )


@router.post("/", response_model=SessionResponse)
async def create_session(
    body: SessionCreate, token: OwnerToken, db: AsyncSession = Depends(get_db)
):
    s = Session(name=body.name or "New Session", owner_token=token)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return await _to_response(db, s, token)


@router.get("/", response_model=SessionListResponse)
async def list_sessions(token: OwnerToken, db: AsyncSession = Depends(get_db)):
    # Yours plus the shared demo. A caller with no token sees only the demo.
    visible = Session.id == DEMO_SESSION_ID
    if token:
        visible = or_(visible, Session.owner_token == token)
    res = await db.execute(
        select(Session).where(visible).order_by(Session.updated_at.desc())
    )
    items = [await _to_response(db, s, token) for s in res.scalars().all()]
    return SessionListResponse(sessions=items, total=len(items))


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str, token: OwnerToken, db: AsyncSession = Depends(get_db)
):
    s = await load_session(db, session_id, token, write=False)
    return await _to_response(db, s, token)


@router.patch("/{session_id}", response_model=SessionResponse)
async def rename_session(
    session_id: str,
    body: SessionRename,
    token: OwnerToken,
    db: AsyncSession = Depends(get_db),
):
    s = await load_session(db, session_id, token, write=True)
    s.name = body.name
    await db.commit()
    await db.refresh(s)
    return await _to_response(db, s, token)


@router.delete("/{session_id}")
async def delete_session(
    session_id: str, token: OwnerToken, db: AsyncSession = Depends(get_db)
):
    s = await load_session(db, session_id, token, write=True)

    # Cascade vectors + files
    docs_res = await db.execute(select(Document).where(Document.session_id == session_id))
    docs = docs_res.scalars().all()
    store = PgVectorStore.get()
    for d in docs:
        await store.delete_by_document_id(d.id)
        BM25Index.get().invalidate(d.id)
        cleanup_document_files(d.stored_path, d.id, settings.PROCESSED_DIR)

    # Remove session-scoped upload dir
    session_upload_dir = os.path.join(settings.UPLOAD_DIR, session_id)
    rmtree_safe(session_upload_dir)

    await db.delete(s)
    await db.commit()
    return {"message": "Session deleted", "session_id": session_id}
