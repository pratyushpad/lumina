"""Access rules for per-browser session ownership.

These assert the security-relevant behaviour directly against `load_session`,
so they hold no matter which router calls it: another visitor's session must be
indistinguishable from a missing one, and the shared demo must be readable by
everyone and writable by nobody.
"""
import pytest
from fastapi import HTTPException

from app.constants import DEMO_SESSION_ID
from app.deps.owner import (
    MAX_TOKEN_LEN,
    MIN_TOKEN_LEN,
    load_session,
    owner_token,
    owns,
)
from app.models import Session

ALICE = "a" * 36
BOB = "b" * 36


class FakeDB:
    """Stands in for AsyncSession.get, which is all load_session uses."""

    def __init__(self, session: Session | None):
        self._session = session

    async def get(self, _model, _pk):
        return self._session


def make_session(session_id: str, token: str | None) -> Session:
    return Session(id=session_id, name="s", owner_token=token)


def test_owner_token_normalises_and_rejects_junk():
    assert owner_token(ALICE) == ALICE
    assert owner_token(f"  {ALICE}  ") == ALICE
    assert owner_token(None) is None
    assert owner_token("") is None
    # Too short to be unguessable, and too long to be a sane header.
    assert owner_token("x" * (MIN_TOKEN_LEN - 1)) is None
    assert owner_token("x" * (MAX_TOKEN_LEN + 1)) is None


def test_unowned_session_is_not_owned_by_a_tokenless_caller():
    """The NULL == None trap: a pre-ownership row must not become public."""
    assert owns(make_session("s1", None), None) is False
    assert owns(make_session("s1", None), ALICE) is False
    assert owns(make_session("s1", ALICE), None) is False


@pytest.mark.asyncio
async def test_owner_can_read_and_write_own_session():
    db = FakeDB(make_session("s1", ALICE))
    assert (await load_session(db, "s1", ALICE, write=False)).id == "s1"
    assert (await load_session(db, "s1", ALICE, write=True)).id == "s1"


@pytest.mark.asyncio
@pytest.mark.parametrize("write", [False, True])
async def test_other_visitors_session_looks_missing_not_forbidden(write):
    """403 would confirm the id exists, turning a guess into an existence oracle."""
    db = FakeDB(make_session("s1", ALICE))
    with pytest.raises(HTTPException) as exc:
        await load_session(db, "s1", BOB, write=write)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_pre_ownership_rows_are_invisible_to_everyone():
    db = FakeDB(make_session("legacy", None))
    for token in (None, ALICE, BOB):
        with pytest.raises(HTTPException) as exc:
            await load_session(db, "legacy", token, write=False)
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_demo_is_readable_by_anyone():
    db = FakeDB(make_session(DEMO_SESSION_ID, None))
    for token in (None, ALICE, BOB):
        assert (await load_session(db, DEMO_SESSION_ID, token, write=False)).id == DEMO_SESSION_ID


@pytest.mark.asyncio
async def test_demo_writes_are_forbidden_for_everyone():
    db = FakeDB(make_session(DEMO_SESSION_ID, None))
    for token in (None, ALICE, BOB):
        with pytest.raises(HTTPException) as exc:
            await load_session(db, DEMO_SESSION_ID, token, write=True)
        # 403 rather than 404 here: the demo is public, so there is nothing to
        # hide, and the user deserves to know why the button did not work.
        assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_missing_session_is_404():
    with pytest.raises(HTTPException) as exc:
        await load_session(FakeDB(None), "nope", ALICE, write=False)
    assert exc.value.status_code == 404
