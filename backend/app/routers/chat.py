import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.constants import DEMO_SESSION_ID
from app.database import AsyncSessionLocal, get_db
from app.deps.identity import IdentityDep
from app.deps.owner import load_session
from app.middleware.rate_limit import limiter
from app.models import Message
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger("lumina.chat")


@router.post("/{session_id}", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_CHAT)
async def chat(
    request: Request,
    session_id: str,
    body: ChatRequest,
    identity: IdentityDep,
    db: AsyncSession = Depends(get_db),
):
    service = ChatService()
    key = identity.owner_key
    document_ids = await service.resolve_documents(db, session_id, key)
    (
        message_id,
        content,
        citations,
        retrieval_ms,
        gen_ms,
        model_used,
    ) = await service.answer(body.query, session_id, document_ids, key)
    return ChatResponse(
        message_id=message_id,
        content=content,
        citations=citations,
        retrieval_time_ms=retrieval_ms,
        generation_time_ms=gen_ms,
        model_used=model_used,
    )


@router.get("/{session_id}/stream")
@limiter.limit(settings.RATE_LIMIT_CHAT)
async def chat_stream(
    request: Request, session_id: str, query: str, identity: IdentityDep
):
    service = ChatService()
    key = identity.owner_key
    # Validate access + docs before opening the stream, so failures surface as
    # a normal HTTP error rather than an SSE error event.
    async with AsyncSessionLocal() as db:
        document_ids = await service.resolve_documents(db, session_id, key)
    return EventSourceResponse(service.stream(query, session_id, document_ids, key))


@router.get("/{session_id}/history", response_model=list[MessageResponse])
async def history(
    session_id: str, identity: IdentityDep, db: AsyncSession = Depends(get_db)
):
    key = identity.owner_key
    await load_session(db, session_id, key, write=False)
    where = [Message.session_id == session_id]
    if session_id == DEMO_SESSION_ID:
        # The demo session is shared. Without this filter every visitor would
        # read every other visitor's questions.
        where.append(Message.owner_token == key)
    res = await db.execute(
        select(Message).where(*where).order_by(Message.created_at.asc())
    )
    return list(res.scalars().all())
