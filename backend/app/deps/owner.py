"""Session ownership.

A session belongs to an `owner_key`: an anonymous browser's opaque token, or —
for a signed-in user — "user:<id>" (see deps/identity.py). Both are opaque
capabilities carried in a header, never in the URL (query strings end up in
proxy logs, browser history, and Referer). This module only cares about the
key; how it is derived is identity.py's job.

Access rules:

- A session whose owner_token equals the caller's key is fully theirs.
- The seeded demo session is readable by everyone and writable by no one.
- Everything else 404s, including sessions that exist but belong to someone
  else. Answering 403 there would confirm the id is real, which turns a guess
  into an existence oracle; the client cannot tell "not yours" from "not there".
"""
from typing import Annotated

from fastapi import Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import DEMO_SESSION_ID
from app.models import Session

# Long enough that tokens cannot be enumerated, bounded so a caller cannot use
# the header to push arbitrary-sized values into query parameters.
MIN_TOKEN_LEN = 16
MAX_TOKEN_LEN = 200

DEMO_READ_ONLY_MESSAGE = (
    "The demo library is shared and read-only. Create your own session to upload "
    "or change documents."
)


def owner_token(
    x_owner_token: Annotated[str | None, Header()] = None,
) -> str | None:
    """The caller's token, or None if absent or malformed.

    A malformed token is treated as no token rather than an error: it only ever
    means "you see nothing but the demo", and failing the request instead would
    break the app for anyone whose storage got into a bad state.
    """
    if not x_owner_token:
        return None
    token = x_owner_token.strip()
    if not (MIN_TOKEN_LEN <= len(token) <= MAX_TOKEN_LEN):
        return None
    return token

def owns(session: Session, token: str | None) -> bool:
    """True if `token` owns `session`. Untokened callers own nothing, and a
    session with no owner (pre-ownership rows) is owned by nobody — an unowned
    row must never fall through to "matches None"."""
    return bool(token) and session.owner_token == token


async def load_session(
    db: AsyncSession, session_id: str, token: str | None, *, write: bool
) -> Session:
    """Fetch a session the caller may access, or raise the right HTTP error."""
    session = await db.get(Session, session_id)
    if session is None:
        raise HTTPException(404, "Session not found")

    if owns(session, token):
        return session

    if session_id == DEMO_SESSION_ID:
        if write:
            raise HTTPException(403, DEMO_READ_ONLY_MESSAGE)
        return session

    # Exists, but not yours: indistinguishable from missing, on purpose.
    raise HTTPException(404, "Session not found")
