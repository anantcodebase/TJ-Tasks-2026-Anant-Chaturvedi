import asyncio

from app.api import chat as chat_api
from app.llm.errors import GeminiRateLimitError
from app.llm.nvidia import (
    NvidiaAuthenticationError,
    NvidiaInvalidRequestError,
    NvidiaModelUnavailableError,
    NvidiaNetworkError,
    NvidiaProviderResponseError,
    NvidiaRateLimitError,
)
from app.models import ChatRequest, ChatResponse


def test_chat_returns_structured_429_for_existing_gemini_contract(monkeypatch):
    async def rate_limited(*args, **kwargs):
        raise GeminiRateLimitError()
    monkeypatch.setattr(chat_api.service, "run", rate_limited)
    response = asyncio.run(chat_api.chat(ChatRequest(message="Show analytics"), "rate-test-1"))
    assert response.status_code == 429
    assert response.body.startswith(b'{"success":false,"error":{"type":"RATE_LIMITED"')
    assert b'"provider":"gemini"' in response.body


def test_chat_maps_nvidia_errors_to_structured_false_response(monkeypatch):
    cases = [
        (NvidiaRateLimitError(), 429, "RATE_LIMITED"),
        (NvidiaAuthenticationError(), 401, "AUTHENTICATION_ERROR"),
        (NvidiaModelUnavailableError(), 404, "MODEL_UNAVAILABLE"),
        (NvidiaInvalidRequestError(), 400, "INVALID_REQUEST"),
        (NvidiaNetworkError(), 503, "NETWORK_ERROR"),
        (NvidiaProviderResponseError(), 502, "PROVIDER_ERROR"),
    ]
    for exc, status, category in cases:
        async def fail(*args, _exc=exc, **kwargs):
            raise _exc
        monkeypatch.setattr(chat_api.service, "run", fail)
        response = asyncio.run(chat_api.chat(ChatRequest(message="hello"), f"nvidia-{category}"))
        assert response.status_code == status
        assert response.body.startswith(b'{"success":false,"error":{"type":')
        assert category.encode() in response.body


def test_chat_success_response_is_distinguished_from_error(monkeypatch):
    async def succeed(*args, **kwargs):
        return ChatResponse(message="hello", actions=[], analytics=[], source="nvidia")
    monkeypatch.setattr(chat_api.service, "run", succeed)
    response = asyncio.run(chat_api.chat(ChatRequest(message="hello"), "nvidia-success"))
    assert response.success is True
    assert response.message == "hello"


def test_duplicate_request_id_is_rejected_while_request_is_in_flight():
    request_id = "duplicate-test"
    chat_api._release_request(request_id)
    assert chat_api._claim_request(request_id) is True
    assert chat_api._claim_request(request_id) is False
    chat_api._release_request(request_id)
    assert chat_api._claim_request(request_id) is True
    chat_api._release_request(request_id)
