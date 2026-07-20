"""Our own session tokens.

After Google confirms who someone is, we hand the browser a short-lived HS256
JWT that says only "you are user <id>". It is sent as `Authorization: Bearer` on
later requests. The Google tokens are used once, at exchange time, and discarded
— we never store or forward them.

Bearer + localStorage (not a cookie) is deliberate: the SPA on vercel.app and
the API on hf.space are different sites, and third-party cookies are unreliable
(Safari blocks them outright). The tradeoff is XSS exposure of the token, which
is why the app ships no third-party script and the token expires in days.
"""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings

_ALGO = "HS256"
_SESSION_TYP = "session"


def issue_session_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": user_id,
            "typ": _SESSION_TYP,
            "iat": now,
            "exp": now + timedelta(days=settings.JWT_EXPIRE_DAYS),
        },
        settings.JWT_SECRET,
        algorithm=_ALGO,
    )


def verify_session_token(token: str) -> str | None:
    """Return the user id a token vouches for, or None if it is missing,
    expired, tampered with, or not one of ours."""
    if not settings.JWT_SECRET:
        return None
    try:
        claims = jwt.decode(token, settings.JWT_SECRET, algorithms=[_ALGO])
    except JWTError:
        return None
    if claims.get("typ") != _SESSION_TYP:
        return None
    sub = claims.get("sub")
    return sub if isinstance(sub, str) and sub else None
