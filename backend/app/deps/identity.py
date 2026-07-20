"""Who is making this request, unified across anonymous and signed-in callers.

Everything downstream cares about one thing: the caller's `owner_key`, the
string written into sessions.owner_token / messages.owner_token. Anonymous
callers key on their per-browser token; signed-in callers key on "user:<id>".
Because both collapse to one key, the ownership check from Phase 3 is reused
unchanged — signing in just swaps which key you carry.

A signed-in caller still sends its browser token too, so `claim` can adopt the
sessions created before sign-in.
"""
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header

from app.deps.owner import owner_token
from app.services.auth.tokens import verify_session_token


@dataclass(frozen=True)
class Identity:
    user_id: str | None
    anon_token: str | None

    @property
    def owner_key(self) -> str | None:
        """The value this caller's data is tagged with. Signed-in identity wins
        over the browser token, so a user sees the same sessions from any
        browser; falls back to the raw anon token (Phase 3-compatible)."""
        if self.user_id:
            return f"user:{self.user_id}"
        return self.anon_token


def _bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def get_identity(
    authorization: Annotated[str | None, Header()] = None,
    x_owner_token: Annotated[str | None, Header()] = None,
) -> Identity:
    user_id = None
    bearer = _bearer(authorization)
    if bearer:
        # An invalid/expired token is treated as "not signed in", not an error,
        # so a stale token just degrades to anonymous rather than locking the
        # app until the user clears storage.
        user_id = verify_session_token(bearer)
    return Identity(user_id=user_id, anon_token=owner_token(x_owner_token))


IdentityDep = Annotated[Identity, Depends(get_identity)]
