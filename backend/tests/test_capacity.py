"""Capacity controls: the concurrency gate, budget-aware provider selection,
and query normalisation. These avoid a live DB by driving the pure logic and
monkeypatching the ledger; the DB-backed ledger and demo cache are exercised in
the live probe instead."""
import asyncio

import pytest

from app.services import capacity as cap
from app.services.capacity import (
    CapacityExhaustedError,
    CapacityService,
    normalize_query,
    utc_day,
)


def test_normalize_query_is_case_and_whitespace_insensitive():
    assert normalize_query("What IS  Attention?") == normalize_query("what is attention?")
    assert normalize_query("  hello   world  ") == "hello world"


def test_utc_day_is_iso_date():
    d = utc_day()
    assert len(d) == 10 and d[4] == "-" and d[7] == "-"


@pytest.fixture(autouse=True)
def _reset_semaphore():
    # The semaphore is cached on the class; reset it so each test binds a fresh
    # one to its own settings/loop.
    CapacityService._sem = None
    yield
    CapacityService._sem = None


@pytest.mark.asyncio
async def test_generation_slot_serialises_to_the_limit(monkeypatch):
    monkeypatch.setattr(cap.settings, "MAX_CONCURRENT_GENERATIONS", 1)
    monkeypatch.setattr(cap.settings, "GENERATION_ACQUIRE_TIMEOUT_S", 5.0)
    order = []

    async def worker(name):
        async with CapacityService.generation_slot():
            order.append(f"{name}-enter")
            await asyncio.sleep(0.05)
            order.append(f"{name}-exit")

    await asyncio.gather(worker("a"), worker("b"))
    # With a limit of 1, one worker fully completes before the other enters.
    assert order in (
        ["a-enter", "a-exit", "b-enter", "b-exit"],
        ["b-enter", "b-exit", "a-enter", "a-exit"],
    )


@pytest.mark.asyncio
async def test_generation_slot_times_out_into_capacity_error(monkeypatch):
    monkeypatch.setattr(cap.settings, "MAX_CONCURRENT_GENERATIONS", 1)
    monkeypatch.setattr(cap.settings, "GENERATION_ACQUIRE_TIMEOUT_S", 0.05)

    async def hold():
        async with CapacityService.generation_slot():
            await asyncio.sleep(0.3)

    holder = asyncio.create_task(hold())
    await asyncio.sleep(0.01)  # let the holder take the only slot
    with pytest.raises(CapacityExhaustedError):
        async with CapacityService.generation_slot():
            pass
    await holder


@pytest.mark.asyncio
async def test_generation_slot_is_a_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(cap.settings, "MAX_CONCURRENT_GENERATIONS", 0)
    # Should not raise or block regardless of how many run concurrently.
    async with CapacityService.generation_slot():
        async with CapacityService.generation_slot():
            pass


@pytest.mark.asyncio
async def test_router_raises_capacity_when_all_providers_over_budget(monkeypatch):
    from app.services.generation.providers import router as router_mod

    r = object.__new__(router_mod.ProviderRouter)

    class P:
        def __init__(self, name):
            self.name = name

    r.providers = [P("local"), P("gemini")]
    r._health = {}
    r.capacity = CapacityService()

    async def all_healthy(_self, _p):
        return True

    async def exhausted(_self, _name):
        return True

    monkeypatch.setattr(router_mod.ProviderRouter, "_healthy", all_healthy)
    monkeypatch.setattr(CapacityService, "is_exhausted", exhausted)

    with pytest.raises(CapacityExhaustedError):
        await r._affordable_candidates()


@pytest.mark.asyncio
async def test_router_keeps_providers_with_budget_left(monkeypatch):
    from app.services.generation.providers import router as router_mod

    r = object.__new__(router_mod.ProviderRouter)

    class P:
        def __init__(self, name):
            self.name = name

    r.providers = [P("local"), P("gemini")]
    r._health = {}
    r.capacity = CapacityService()

    async def all_healthy(_self, _p):
        return True

    async def only_local_exhausted(_self, name):
        return name == "local"

    monkeypatch.setattr(router_mod.ProviderRouter, "_healthy", all_healthy)
    monkeypatch.setattr(CapacityService, "is_exhausted", only_local_exhausted)

    affordable = await r._affordable_candidates()
    assert [p.name for p in affordable] == ["gemini"]
