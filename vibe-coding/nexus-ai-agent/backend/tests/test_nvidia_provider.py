import asyncio
import json

import httpx
import pytest

from app.agent.prompts import plan_schema
from app.agent.service import AgentService
from app.config import settings
from app.llm.factory import create_llm_client
from app.llm.nvidia import (
    NvidiaAuthenticationError,
    NvidiaClient,
    NvidiaInvalidRequestError,
    NvidiaModelUnavailableError,
    NvidiaNetworkError,
    NvidiaProviderResponseError,
    NvidiaRateLimitError,
)
from app.models import ChatUIContext, ConversationMessage


def _response(status: int, payload: dict, headers: dict | None = None) -> httpx.Response:
    return httpx.Response(status, json=payload, headers=headers or {}, request=httpx.Request("POST", "https://example.test/v1/chat/completions"))


def test_nvidia_provider_is_selected(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "nvidia")
    client = create_llm_client()
    assert isinstance(client, NvidiaClient)
    assert client.model == "nvidia/nemotron-3.5-lightning-30b-a3b"


def test_nvidia_generate_json_uses_native_tool_call_and_history(monkeypatch):
    monkeypatch.setattr(settings, "nvidia_api_key", "test-key")
    monkeypatch.setattr(settings, "nvidia_model", "nvidia/nemotron-3.5-lightning-30b-a3b")
    client = NvidiaClient()
    captured = {}

    async def fake_post(payload):
        captured.update(payload)
        return {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "function": {
                            "name": "nexus_plan",
                            "arguments": '{"intent":"action","message":"Analytics opened.","actions":[{"type":"show_widget","target":"analytics"}],"analytics":[]}',
                        }
                    }]
                }
            }]
        }

    monkeypatch.setattr(client, "_post", fake_post)
    history = [
        ConversationMessage(role="user", content="show analytics"),
        ConversationMessage(role="assistant", content="Analytics opened."),
    ]
    context = {"model": "nexus", "accent": "lime", "analytics_range": "7D", "analytics_filter": "ALL", "visible_widgets": {"analytics": False}}
    result = asyncio.run(client.generate_json("system", "hide it", plan_schema(), history=history, context=context))

    assert json.loads(result)["actions"][0] == {"type": "show_widget", "target": "analytics"}
    assert captured["model"] == "nvidia/nemotron-3.5-lightning-30b-a3b"
    assert captured["tool_choice"] == {"type": "function", "function": {"name": "nexus_plan"}}
    assert captured["messages"][0]["role"] == "system"
    assert "Current application context:" in captured["messages"][0]["content"]
    assert captured["messages"][1:3] == [
        {"role": "user", "content": "show analytics"},
        {"role": "assistant", "content": "Analytics opened."},
    ]


def test_nvidia_missing_key_is_authentication_error(monkeypatch):
    monkeypatch.setattr(settings, "nvidia_api_key", "")
    client = NvidiaClient()
    with pytest.raises(NvidiaAuthenticationError) as exc_info:
        asyncio.run(client._post({"model": client.model, "messages": []}))
    assert exc_info.value.error_type == "AUTHENTICATION_ERROR"


def test_nvidia_429_retries_and_raises_typed_error(monkeypatch):
    monkeypatch.setattr(settings, "nvidia_api_key", "test-key")
    client = NvidiaClient()
    calls = 0
    sleeps = []

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False
        async def post(self, *args, **kwargs):
            nonlocal calls
            calls += 1
            return _response(429, {"error": {"code": "rate_limit", "message": "too many requests"}}, {"Retry-After": "0"})

    monkeypatch.setattr("app.llm.nvidia.httpx.AsyncClient", FakeAsyncClient)
    async def fake_sleep(delay): sleeps.append(delay)
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    with pytest.raises(NvidiaRateLimitError) as exc_info:
        asyncio.run(client._post({"model": client.model, "messages": []}))
    assert calls == 3
    assert sleeps == [0.0, 0.0]
    assert exc_info.value.error_type == "RATE_LIMITED"
    assert exc_info.value.provider_code == "rate_limit"


@pytest.mark.parametrize(
    ("status", "payload", "error_class", "error_type"),
    [
        (401, {"error": {"code": "invalid_api_key", "message": "bad key"}}, NvidiaAuthenticationError, "AUTHENTICATION_ERROR"),
        (403, {"error": {"code": "forbidden", "message": "forbidden"}}, NvidiaAuthenticationError, "AUTHENTICATION_ERROR"),
        (404, {"error": {"code": "model_not_found", "message": "model not found"}}, NvidiaModelUnavailableError, "MODEL_UNAVAILABLE"),
        (400, {"error": {"code": "invalid_request", "message": "bad request"}}, NvidiaInvalidRequestError, "INVALID_REQUEST"),
    ],
)
def test_nvidia_http_errors_are_classified(monkeypatch, status, payload, error_class, error_type):
    monkeypatch.setattr(settings, "nvidia_api_key", "test-key")
    client = NvidiaClient()

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False
        async def post(self, *args, **kwargs): return _response(status, payload)

    monkeypatch.setattr("app.llm.nvidia.httpx.AsyncClient", FakeAsyncClient)
    with pytest.raises(error_class) as exc_info:
        asyncio.run(client._post({"model": client.model, "messages": []}))
    assert exc_info.value.error_type == error_type
    assert exc_info.value.status_code == status
    assert exc_info.value.provider_code == payload["error"]["code"]


def test_nvidia_402_is_not_rate_limited(monkeypatch):
    monkeypatch.setattr(settings, "nvidia_api_key", "test-key")
    client = NvidiaClient()

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False
        async def post(self, *args, **kwargs): return _response(402, {"error": {"code": "payment_required", "message": "insufficient credits"}})

    monkeypatch.setattr("app.llm.nvidia.httpx.AsyncClient", FakeAsyncClient)
    with pytest.raises(NvidiaProviderResponseError) as exc_info:
        asyncio.run(client._post({"model": client.model, "messages": []}))
    assert exc_info.value.error_type == "PROVIDER_ERROR"
    assert exc_info.value.status_code == 402
    assert exc_info.value.provider_code == "payment_required"


def test_nvidia_network_failure_is_typed(monkeypatch):
    monkeypatch.setattr(settings, "nvidia_api_key", "test-key")
    client = NvidiaClient()

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False
        async def post(self, *args, **kwargs): raise httpx.ConnectError("connection refused")

    monkeypatch.setattr("app.llm.nvidia.httpx.AsyncClient", FakeAsyncClient)
    with pytest.raises(NvidiaNetworkError) as exc_info:
        asyncio.run(client._post({"model": client.model, "messages": []}))
    assert exc_info.value.error_type == "NETWORK_ERROR"


def test_nvidia_malformed_json_response_is_typed(monkeypatch):
    monkeypatch.setattr(settings, "nvidia_api_key", "test-key")
    client = NvidiaClient()

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False
        async def post(self, *args, **kwargs):
            return httpx.Response(200, content=b"{not-json", request=httpx.Request("POST", "https://example.test"))

    monkeypatch.setattr("app.llm.nvidia.httpx.AsyncClient", FakeAsyncClient)
    with pytest.raises(NvidiaProviderResponseError) as exc_info:
        asyncio.run(client._post({"model": client.model, "messages": []}))
    assert exc_info.value.error_type == "PROVIDER_ERROR"
    assert exc_info.value.provider_code == "malformed_json"


def test_nvidia_empty_success_shape_is_typed():
    client = NvidiaClient()
    async def fake_post(*args, **kwargs): return {"choices": [{"message": {}}]}
    client._post = fake_post
    with pytest.raises(NvidiaProviderResponseError) as exc_info:
        asyncio.run(client.generate_message("system", "hello", {}, history=[]))
    assert exc_info.value.error_type == "PROVIDER_ERROR"


def test_nvidia_provider_preserves_agent_memory_and_contextual_actions(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "nvidia")
    service = AgentService()
    calls = []

    async def fake_generate_json(system_prompt, user_message, schema, history=None, context=None):
        calls.append({"user_message": user_message, "history": history, "context": context})
        return '{"intent":"action","message":"Analytics hidden.","actions":[{"type":"hide_widget","target":"analytics"}],"analytics":[]}'

    monkeypatch.setattr(service.llm, "generate_json", fake_generate_json)
    context = ChatUIContext(visible_widgets={"analytics": True})
    history = [
        ConversationMessage(role="user", content="Show analytics."),
        ConversationMessage(role="assistant", content="Analytics opened."),
    ]
    result = asyncio.run(service.run("Hide it.", history=history, ui_context=context))
    assert result.source == "nvidia"
    assert [(a.type, a.target) for a in result.actions] == [("hide_widget", "analytics")]
    assert calls[0]["history"] == history
    assert calls[0]["context"]["visible_widgets"]["analytics"] is True


def test_nvidia_provider_keeps_accent_deep_and_compound_structured_actions(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "nvidia")
    service = AgentService()
    async def fake_generate_json(*args, **kwargs):
        return '{"intent":"mixed","message":"Done.","actions":[{"type":"set_model","model":"deep"},{"type":"set_accent_color","accent":"red"},{"type":"show_widget","target":"analytics"}],"analytics":[]}'
    monkeypatch.setattr(service.llm, "generate_json", fake_generate_json)
    result = asyncio.run(service.run("Switch to Deep and make the accent red, then show analytics"))
    assert [a.model_dump(exclude_none=True) for a in result.actions] == [
        {"type": "set_model", "model": "deep"},
        {"type": "set_accent_color", "accent": "red"},
        {"type": "show_widget", "target": "analytics"},
    ]


def test_nvidia_provider_handles_normal_conversation_and_parsing(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "nvidia")
    service = AgentService()
    async def fake_generate_message(*args, **kwargs):
        return '{"message":"I just said analytics are ready."}'
    monkeypatch.setattr(service.llm, "generate_message", fake_generate_message)
    result = asyncio.run(service.run("What did you just say?", history=[
        ConversationMessage(role="user", content="show analytics"),
        ConversationMessage(role="assistant", content="Analytics are ready."),
        ConversationMessage(role="user", content="What did you just say?"),
    ]))
    assert result.source == "nvidia"
    assert result.message == "I just said analytics are ready."
    assert result.actions == []


def test_nvidia_provider_executes_analytics_through_existing_executor(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "nvidia")
    service = AgentService()
    async def fake_generate_json(*args, **kwargs):
        return '{"intent":"analytics","message":"","actions":[{"type":"show_widget","target":"analytics"}],"analytics":[{"operation":"fetch","metric":"sales","period":"7d"}]}'
    monkeypatch.setattr(service.llm, "generate_json", fake_generate_json)
    result = asyncio.run(service.run("Show analytics."))
    assert result.source == "nvidia"
    assert result.actions[0].type == "show_widget"
    assert len(result.analytics) == 1


def test_nvidia_provider_preserves_contextual_analytics_range_command(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "nvidia")
    service = AgentService()
    calls = []
    async def fake_generate_json(*args, **kwargs):
        calls.append(kwargs)
        return '{"intent":"analytics","message":"Range changed.","actions":[{"type":"set_analytics_range","range":"30D"}],"analytics":[]}'
    monkeypatch.setattr(service.llm, "generate_json", fake_generate_json)
    history = [ConversationMessage(role="user", content="Show analytics.")]
    context = ChatUIContext(analytics_range="7D")
    result = asyncio.run(service.run("Make it 30 days.", history=history, ui_context=context))
    assert result.source == "nvidia"
    assert [a.model_dump(exclude_none=True) for a in result.actions] == [{"type": "set_analytics_range", "range": "30D"}]
    assert calls[0]["history"] == history
