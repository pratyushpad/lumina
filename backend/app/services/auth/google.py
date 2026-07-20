"""Google OAuth: turn an authorization code into a verified profile.

The SPA runs the browser-facing half (redirect to Google, receive the code at
its callback). This module runs the confidential half on the server, where the
client secret lives: swap the code for an access token, then read the profile.
Reading userinfo with the freshly minted access token means we never have to
verify Google's id_token signature ourselves.
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger("lumina.auth.google")

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


class GoogleAuthError(Exception):
    """The code could not be exchanged for a profile (bad/expired code, config
    mismatch, or Google returned no subject)."""


async def exchange_code_for_profile(code: str) -> dict:
    """Return the Google profile {sub, email, name, picture} for an auth code."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            token_resp = await client.post(
                TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.OAUTH_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
        except httpx.HTTPError as e:
            raise GoogleAuthError(f"token endpoint unreachable: {e}") from e
        if token_resp.status_code != 200:
            # Google echoes the reason (redirect_uri_mismatch, invalid_grant …)
            # to the logs; the client just learns sign-in failed.
            logger.warning("Google token exchange failed: %s", token_resp.text[:300])
            raise GoogleAuthError("token exchange rejected")
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise GoogleAuthError("no access token in response")

        info_resp = await client.get(
            USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
        )
        if info_resp.status_code != 200:
            raise GoogleAuthError("userinfo request rejected")
        profile = info_resp.json()

    if not profile.get("sub"):
        raise GoogleAuthError("profile has no subject")
    return profile
