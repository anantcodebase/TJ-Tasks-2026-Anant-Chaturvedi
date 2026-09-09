from __future__ import annotations

import time
from threading import Lock

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from app.agent.service import AgentService
from app.llm.errors import ProviderError
from app.models import ChatRequest, ChatResponse
from app.perf import ChatPerfTrace, reset_trace, set_trace

router = APIRouter(prefix="/api", tags=["agent"])
service = AgentService()

_ACTIVE_REQUESTS: dict[str, float] = {}
_REQUEST_LOCK = Lock()
_REQUEST_TTL_SECONDS = 120.0


def _claim_request(request_id: str | None) -> bool:
    if not request_id:
        return True
    now = time.monotonic()
    with _REQUEST_LOCK:
        expired = [key for key, timestamp in _ACTIVE_REQUESTS.items() if now - timestamp > _REQUEST_TTL_SECONDS]
        for key in expired:
            _ACTIVE_REQUESTS.pop(key, None)
        if request_id in _ACTIVE_REQUESTS:
            return False
        _ACTIVE_REQUESTS[request_id] = now
        return True


def _release_request(request_id: str | None) -> None:
    if request_id:
        with _REQUEST_LOCK:
            _ACTIVE_REQUESTS.pop(request_id, None)


def _provider_error_response(exc: ProviderError) -> JSONResponse:
    status = exc.status_code if exc.status_code in {400, 401, 403, 404, 408, 409, 429} else 502
    if exc.error_type == "AUTHENTICATION_ERROR":
        status = 401
    elif exc.error_type == "MODEL_UNAVAILABLE":
        status = 404
    elif exc.error_type == "INVALID_REQUEST":
        status = 400
    elif exc.error_type == "RATE_LIMITED":
        status = 429
    elif exc.error_type == "NETWORK_ERROR":
        status = 503

    return JSONResponse(
        status_code=status,
        content={
            "success": False,
            "error": {
                "type": exc.error_type,
                "message": str(exc),
                "provider": exc.provider,
                "provider_code": exc.provider_code,
            },
        },
        headers={
            "Retry-After": str(int(exc.retry_after)) if exc.retry_after is not None and exc.retry_after >= 0 else None,
        } if exc.retry_after is not None else None,
    )


@router.post("/chat", response_model=ChatResponse, response_model_exclude_none=True)
async def chat(request: ChatRequest, x_nexus_request_id: str | None = Header(default=None)) -> ChatResponse | JSONResponse:
    if not _claim_request(x_nexus_request_id):
        return JSONResponse(
            status_code=409,
            content={"success": False, "error": {"type": "DUPLICATE_REQUEST", "message": "That message is already being processed."}},
        )

    trace = ChatPerfTrace()
    token = set_trace(trace)
    try:
        try:
            response = await service.run(request.message, request.history, request.ui_context)
            return response
        except ProviderError as exc:
            return _provider_error_response(exc)
    finally:
        trace.log()
        reset_trace(token)
        _release_request(x_nexus_request_id)
