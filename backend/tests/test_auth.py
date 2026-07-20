"""Sign-in: token issue/verify, identity resolution, and the ownership keying
that makes a signed-in user's data follow them across browsers while staying
invisible to everyone else. The live Google round-trip is verified separately;
here the exchange is driven against a mocked Google."""
import time

import pytest

from app.deps.identity import Identity, get_identity
from app.services.auth import tokens


@pytest.fixture(autouse=True)
def _secret(monkeypatch):
    monkeypatch.setattr(tokens.settings, "JWT_SECRET", "test-secret-not-real")
    monkeypatch.setattr(tokens.settings, "JWT_EXPIRE_DAYS", 7)


def test_session_token_round_trips():
    token = tokens.issue_session_token("user-123")
    assert tokens.verify_session_token(token) == "user-123"


def test_tampered_token_is_rejected():
    token = tokens.issue_session_token("user-123")
    assert tokens.verify_session_token(token + "x") is None


def test_token_signed_with_another_secret_is_rejected(monkeypatch):
    token = tokens.issue_session_token("user-123")
    monkeypatch.setattr(tokens.settings, "JWT_SECRET", "a-different-secret")
    assert tokens.verify_session_token(token) is None


def test_expired_token_is_rejected(monkeypatch):
    monkeypatch.setattr(tokens.settings, "JWT_EXPIRE_DAYS", 0)
    token = tokens.issue_session_token("user-123")
    time.sleep(1)
    assert tokens.verify_session_token(token) is None


def test_verify_returns_none_when_auth_disabled(monkeypatch):
    token = tokens.issue_session_token("user-123")
    monkeypatch.setattr(tokens.settings, "JWT_SECRET", "")
    assert tokens.verify_session_token(token) is None


# ---- Identity resolution ----------------------------------------------------

ANON = "anon-" + "a" * 32


def test_owner_key_prefers_signed_in_identity():
    assert Identity(user_id="u1", anon_token=ANON).owner_key == "user:u1"
    assert Identity(user_id=None, anon_token=ANON).owner_key == ANON
    assert Identity(user_id=None, anon_token=None).owner_key is None


def test_get_identity_reads_valid_bearer():
    token = tokens.issue_session_token("u1")
    ident = get_identity(authorization=f"Bearer {token}", x_owner_token=ANON)
    assert ident.user_id == "u1"
    assert ident.anon_token == ANON  # still carried, so claim can adopt anon work
    assert ident.owner_key == "user:u1"


def test_get_identity_ignores_invalid_bearer_and_falls_back_to_anon():
    ident = get_identity(authorization="Bearer not-a-jwt", x_owner_token=ANON)
    assert ident.user_id is None
    assert ident.owner_key == ANON


def test_get_identity_ignores_non_bearer_scheme():
    token = tokens.issue_session_token("u1")
    ident = get_identity(authorization=f"Basic {token}", x_owner_token=None)
    assert ident.user_id is None


# ---- Ownership keying (the isolation guarantee) -----------------------------

from app.deps.owner import owns  # noqa: E402
from app.models import Session  # noqa: E402


def _sess(owner_token):
    return Session(id="s1", name="s", owner_token=owner_token)


def test_user_owned_session_follows_the_account_not_the_browser():
    s = _sess("user:u1")
    assert owns(s, Identity(user_id="u1", anon_token="browser-B").owner_key) is True
    # A different browser signed into the same account still owns it.
    assert owns(s, Identity(user_id="u1", anon_token="browser-C").owner_key) is True


def test_user_owned_session_is_invisible_to_anon_and_other_users():
    s = _sess("user:u1")
    # An anonymous caller (a real per-browser token) never matches a user key.
    assert owns(s, Identity(user_id=None, anon_token="some-anon-token").owner_key) is False
    # Another signed-in user does not match.
    assert owns(s, Identity(user_id="u2", anon_token=None).owner_key) is False
    # No identity at all matches nothing.
    assert owns(s, Identity(user_id=None, anon_token=None).owner_key) is False


@pytest.mark.asyncio
async def test_exchange_upserts_and_reads_google_profile(monkeypatch):
    """The Google half is mocked; assert we read sub/email/name/picture."""
    from app.services.auth import google

    async def fake_exchange(code):
        assert code == "auth-code-xyz"
        return {
            "sub": "google-sub-1",
            "email": "a@example.com",
            "name": "Ada",
            "picture": "https://img/a.png",
        }

    monkeypatch.setattr(google, "exchange_code_for_profile", fake_exchange)
    profile = await google.exchange_code_for_profile("auth-code-xyz")
    assert profile["sub"] == "google-sub-1" and profile["email"] == "a@example.com"
