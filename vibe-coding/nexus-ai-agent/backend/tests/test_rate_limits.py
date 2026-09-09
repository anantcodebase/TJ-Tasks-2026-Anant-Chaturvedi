import asyncio

import pytest

from app.llm.errors import GeminiRateLimitError
from app.llm.gemini import GeminiClient


def test_gemini_retries_429_with_bounded_retries(monkeypatch):
    client = GeminiClient()
    calls = 0
    sleeps = []

    async def fail(*args, **kwargs):
        nonlocal calls
        calls += 1
        error = RuntimeError("429 RESOURCE_EXHAUSTED")
        error.status_code = 429
        raise error

    async def fake_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(client, "_generate_once", fail)
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    with pytest.raises(GeminiRateLimitError):
        asyncio.run(client._generate("system", [], {}, 0.3))

    assert calls == 3
    assert len(sleeps) == 2
    assert all(0 <= delay <= 10 for delay in sleeps)


def test_gemini_honors_retry_after(monkeypatch):
    client = GeminiClient()
    calls = 0
    sleeps = []

    async def fail(*args, **kwargs):
        nonlocal calls
        calls += 1
        error = RuntimeError("429 RESOURCE_EXHAUSTED")
        error.status_code = 429
        error.retry_after = 3.25
        raise error

    async def fake_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(client, "_generate_once", fail)
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    with pytest.raises(GeminiRateLimitError):
        asyncio.run(client._generate("system", [], {}, 0.3))

    assert calls == 3
    assert sleeps == [3.25, 3.25]


def test_rate_limit_stops_after_final_retry(monkeypatch):
    client = GeminiClient()
    calls = 0

    async def fail(*args, **kwargs):
        nonlocal calls
        calls += 1
        error = RuntimeError("429 RESOURCE_EXHAUSTED")
        error.status_code = 429
        raise error

    async def no_wait(_delay):
        return None

    monkeypatch.setattr(client, "_generate_once", fail)
    monkeypatch.setattr(asyncio, "sleep", no_wait)

    with pytest.raises(GeminiRateLimitError) as exc_info:
        asyncio.run(client._generate("system", [], {}, 0.3))

    assert calls == 3
    assert "busy right now" in str(exc_info.value)
