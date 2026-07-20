"""Google sign-in endpoints.

Flow: the SPA sends the browser to Google, Google returns a `code` to the SPA
callback, the SPA posts it here. We exchange it for the profile, upsert the
user, and hand back our own session token. Sign-in is a strict add-on — every
endpoint here 404s when auth is not configured, and the rest of the app never
depends on being signed in.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.constants import DEMO_SESSION_ID
from app.database import get_db
from app.deps.identity import IdentityDep
from app.models import Session, User
from app.services.auth.google import GoogleAuthError, exchange_code_for_profile
from app.services.auth.tokens import issue_session_token

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger("lumina.auth")


class ExchangeRequest(BaseModel):
    code: str


class UserPublic(BaseModel):
    id: str
    email: str | None
    display_name: str | None
    avatar_url: str | None


class ExchangeResponse(BaseModel):
    token: str
    user: UserPublic


def _public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
    )


def _require_enabled() -> None:
    if not settings.auth_enabled:
        # Indistinguishable from "no such route" when sign-in is switched off.
        raise HTTPException(404, "Not found")


@router.post("/google/exchange", response_model=ExchangeResponse)
async def google_exchange(body: ExchangeRequest, db: AsyncSession = Depends(get_db)):
    _require_enabled()
    try:
        profile = await exchange_code_for_profile(body.code)
    except GoogleAuthError as e:
        logger.info("Sign-in exchange failed: %s", e)
        raise HTTPException(400, "Could not complete sign-in with Google.") from e

    subject = profile["sub"]
    res = await db.execute(
        select(User).where(User.provider == "google", User.provider_subject == subject)
    )
    user = res.scalars().first()
    now = datetime.utcnow()
    if user is None:
        user = User(provider="google", provider_subject=subject, created_at=now)
        db.add(user)
    # Refresh profile fields on every login so a changed name/avatar follows.
    user.email = profile.get("email")
    user.display_name = profile.get("name")
    user.avatar_url = profile.get("picture")
    user.last_login_at = now
    await db.commit()
    await db.refresh(user)

    return ExchangeResponse(token=issue_session_token(user.id), user=_public(user))


@router.get("/me", response_model=UserPublic)
async def me(identity: IdentityDep, db: AsyncSession = Depends(get_db)):
    if not identity.user_id:
        raise HTTPException(401, "Not signed in")
    user = await db.get(User, identity.user_id)
    if user is None:
        # Token references a user that no longer exists.
        raise HTTPException(401, "Not signed in")
    return _public(user)


class ClaimResponse(BaseModel):
    claimed: int


@router.post("/claim", response_model=ClaimResponse)
async def claim(identity: IdentityDep, db: AsyncSession = Depends(get_db)):
    """Adopt the sessions this browser created before signing in, by rewriting
    their anonymous owner token to the account's owner_key. Idempotent: sessions
    already migrated no longer match the anon token."""
    if not identity.user_id:
        raise HTTPException(401, "Not signed in")
    if not identity.anon_token:
        return ClaimResponse(claimed=0)
    result = await db.execute(
        update(Session)
        .where(Session.owner_token == identity.anon_token, Session.id != DEMO_SESSION_ID)
        .values(owner_token=identity.owner_key)
    )
    await db.commit()
    return ClaimResponse(claimed=result.rowcount or 0)
