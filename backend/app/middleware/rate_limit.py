"""slowapi rate limiter (in-memory).

Keyed by owner token when the caller sends one (fair per-browser limiting that a
shared office IP can't trip for everyone), falling back to client IP otherwise.

Deriving the client IP behind a proxy is the security-sensitive part.
X-Forwarded-For is a list the client can *prepend* to — anything the real proxy
didn't add is attacker-controlled. Only the last `TRUSTED_PROXY_HOPS` entries
were appended by infrastructure we trust, so the real client is the entry that
many positions from the right. Trusting the leftmost entry (the old behaviour)
lets a client spoof its own key by sending a forged XFF header, which both
evades limiting and lets it poison another IP's bucket.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.config import settings


def client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    hops = settings.TRUSTED_PROXY_HOPS
    if xff and hops > 0:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            # The (hops)-th entry from the right is the address our nearest
            # trusted proxy observed; clamp so a short/forged header can't index
            # past the list into a client-controlled value.
            idx = min(hops, len(parts))
            return parts[-idx]
    # No trusted proxy in front (local/dev), or none configured: the socket peer
    # is the real client.
    return get_remote_address(request)


def client_key(request: Request) -> str:
    """Prefer the browser's owner token so limits are per-user, not per-IP; fall
    back to the trusted client IP for callers that send no token."""
    token = request.headers.get("x-owner-token")
    if token:
        token = token.strip()
        if token:
            return f"owner:{token}"
    return f"ip:{client_ip(request)}"


limiter = Limiter(
    key_func=client_key,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
)
