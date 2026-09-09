from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

import httpx

from app.config import settings
from app.llm.errors import ProviderError
from app.models import ConversationMessage
from app.perf import get_trace, record_prompt_components

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 24
MAX_HISTORY_CHARS = 16000
MAX_RETRIES = 2
DEFAULT_RETRY_DELAY = 1.5
MAX_RETRY_DELAY = 10.0
RATE_LIMIT_MESSAGE = "NEXUS is busy right now. Please wait a few seconds and try again."


class NvidiaProviderError(ProviderError):
    """Normalized NVIDIA provider failure that must reach the API layer."""

    def __init__(
        self,
        error_type: str,
        message: str,
        *,
        status_code: int | None = None,
        provider_code: str | None = None,
        provider_message: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(
            "nvidia",
            error_type,
            message,
            status_code=status_code,
            provider_code=provider_code,
            provider_message=provider_message,
            retry_after=retry_after,
        )


class NvidiaRateLimitError(NvidiaProviderError):
    """Raised when NVIDIA rejects a request because the API is rate limited."""

    def __init__(self, message: str = RATE_LIMIT_MESSAGE, retry_after: float | None = None, *, status_code: int = 429, provider_code: str | None = None, provider_message: str | None = None):
        super().__init__(
            "RATE_LIMITED",
            message,
            status_code=status_code,
            provider_code=provider_code,
            provider_message=provider_message,
            retry_after=retry_after,
        )


class NvidiaAuthenticationError(NvidiaProviderError):
    def __init__(self, message: str = "NVIDIA authentication failed.", **kwargs: Any) -> None:
        super().__init__("AUTHENTICATION_ERROR", message, **kwargs)


class NvidiaModelUnavailableError(NvidiaProviderError):
    def __init__(self, message: str = "The configured NVIDIA model is unavailable.", **kwargs: Any) -> None:
        super().__init__("MODEL_UNAVAILABLE", message, **kwargs)


class NvidiaInvalidRequestError(NvidiaProviderError):
    def __init__(self, message: str = "The NVIDIA request was rejected as invalid.", **kwargs: Any) -> None:
        super().__init__("INVALID_REQUEST", message, **kwargs)


class NvidiaNetworkError(NvidiaProviderError):
    def __init__(self, message: str = "NEXUS could not reach the NVIDIA provider.", **kwargs: Any) -> None:
        super().__init__("NETWORK_ERROR", message, **kwargs)


class NvidiaProviderResponseError(NvidiaProviderError):
    def __init__(self, message: str = "NVIDIA returned an unexpected provider response.", **kwargs: Any) -> None:
        super().__init__("PROVIDER_ERROR", message, **kwargs)


class NvidiaClient:
    """NVIDIA hosted API adapter using its OpenAI-compatible chat-completions API."""

    def __init__(self) -> None:
        self.base_url = settings.nvidia_base_url.rstrip("/")
        self.model = settings.nvidia_model
        self.timeout = settings.nvidia_timeout_seconds

    @staticmethod
    def _history_messages(history: list[ConversationMessage] | None) -> list[dict[str, Any]]:
        if not history:
            return []
        recent = history[-MAX_HISTORY_MESSAGES:]
        bounded: list[dict[str, Any]] = []
        chars = 0
        for item in reversed(recent):
            next_chars = chars + len(item.content)
            if bounded and next_chars > MAX_HISTORY_CHARS:
                break
            bounded.append({"role": item.role, "content": item.content})
            chars = next_chars
        bounded.reverse()
        return bounded

    @staticmethod
    def _retry_after(response: httpx.Response) -> float | None:
        value = response.headers.get("Retry-After")
        if not value:
            return None
        try:
            return max(0.0, float(value))
        except ValueError:
            return None

    @staticmethod
    def _response_payload(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except (ValueError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _provider_error_fields(payload: dict[str, Any]) -> tuple[str | None, str | None]:
        error = payload.get("error")
        if isinstance(error, dict):
            code = error.get("code") or error.get("type")
            message = error.get("message") or error.get("detail")
            return (str(code) if code is not None else None, str(message) if message is not None else None)
        if isinstance(error, str):
            return None, error
        detail = payload.get("detail")
        return None, str(detail) if detail is not None else None

    @classmethod
    def _normalize_http_error(cls, response: httpx.Response) -> NvidiaProviderError:
        payload = cls._response_payload(response)
        provider_code, provider_message = cls._provider_error_fields(payload)
        status = response.status_code
        code_text = (provider_code or "").lower()
        message_text = (provider_message or "").lower()

        logger.warning(
            "NVIDIA provider error provider=nvidia model=%s status=%s code=%s message=%s",
            settings.nvidia_model,
            status,
            provider_code,
            provider_message,
        )

        common = {
            "status_code": status,
            "provider_code": provider_code,
            "provider_message": provider_message,
        }
        if status == 429:
            return NvidiaRateLimitError(
                retry_after=cls._retry_after(response),
                provider_code=provider_code,
                provider_message=provider_message,
            )
        if status in {401, 403}:
            return NvidiaAuthenticationError(**common)
        if status == 404 and any(token in f"{code_text} {message_text}" for token in ("model", "not found", "unknown model", "endpoint")):
            return NvidiaModelUnavailableError(**common)
        if status == 400:
            return NvidiaInvalidRequestError(**common)
        if status == 402:
            # NVIDIA 402 responses may be account/credit related. Do not misclassify
            # them as rate limits; preserve the provider payload for server-side logs.
            return NvidiaProviderResponseError(
                "NVIDIA rejected the request with HTTP 402. Check the NVIDIA account, credits, and provider response.",
                **common,
            )
        return NvidiaProviderResponseError(
            f"NVIDIA provider request failed with HTTP {status}.",
            **common,
        )

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not settings.nvidia_api_key:
            raise NvidiaAuthenticationError("NVIDIA_API_KEY is not configured.", provider_code="missing_api_key", provider_message="NVIDIA_API_KEY is not configured.")

        for attempt in range(MAX_RETRIES + 1):
            call = get_trace().provider_start() if get_trace() is not None else None
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.nvidia_api_key}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                    if call is not None:
                        call.end = time.perf_counter()
                        call.status_code = response.status_code
                        call.response_bytes = len(response.content)
            except httpx.TimeoutException as exc:
                if call is not None:
                    call.end = time.perf_counter()
                    call.error_type = "timeout"
                logger.warning("NVIDIA provider network error provider=nvidia model=%s kind=timeout", settings.nvidia_model)
                raise NvidiaNetworkError() from exc
            except httpx.RequestError as exc:
                if call is not None:
                    call.end = time.perf_counter()
                    call.error_type = type(exc).__name__
                logger.warning("NVIDIA provider network error provider=nvidia model=%s kind=%s", settings.nvidia_model, type(exc).__name__)
                raise NvidiaNetworkError() from exc

            if response.status_code == 429 and attempt < MAX_RETRIES:
                retry_after = self._retry_after(response)
                delay = retry_after if retry_after is not None else DEFAULT_RETRY_DELAY * (2 ** attempt)
                await asyncio.sleep(min(max(delay, 0.0), MAX_RETRY_DELAY))
                continue
            if response.status_code >= 400:
                raise self._normalize_http_error(response)

            parse_started = time.perf_counter()
            try:
                data = response.json()
                parse_duration = time.perf_counter() - parse_started
                trace = get_trace()
                if trace is not None:
                    trace.provider_parse += parse_duration
            except (ValueError, json.JSONDecodeError) as exc:
                trace = get_trace()
                if trace is not None:
                    trace.provider_parse += time.perf_counter() - parse_started
                logger.warning("NVIDIA provider malformed JSON response provider=nvidia model=%s status=%s", settings.nvidia_model, response.status_code)
                raise NvidiaProviderResponseError(
                    "NVIDIA returned malformed JSON.",
                    status_code=response.status_code,
                    provider_code="malformed_json",
                ) from exc
            if not isinstance(data, dict):
                raise NvidiaProviderResponseError(
                    "NVIDIA returned an unexpected JSON structure.",
                    status_code=response.status_code,
                    provider_code="invalid_response_shape",
                )
            if call is not None:
                choices = data.get("choices") or []
                message = choices[0].get("message", {}) if choices and isinstance(choices[0], dict) else {}
                content = message.get("content") if isinstance(message, dict) else None
                tool_calls = message.get("tool_calls") if isinstance(message, dict) else None
                tool_args = ""
                if isinstance(tool_calls, list):
                    for tool_call in tool_calls:
                        function = tool_call.get("function") if isinstance(tool_call, dict) else None
                        arguments = function.get("arguments") if isinstance(function, dict) else None
                        if isinstance(arguments, str):
                            tool_args += arguments
                call.output_chars = len(content) if isinstance(content, str) else len(tool_args)
            return data

        raise NvidiaRateLimitError()

    @staticmethod
    def _messages_with_context(
        system_prompt: str,
        user_message: str,
        history: list[ConversationMessage] | None,
        context: dict | None,
    ) -> list[dict[str, Any]]:
        # Keep exactly one leading system message. NVIDIA's hosted endpoint documents
        # system as the first optional message and expects normal user/assistant history
        # after it. Application context is therefore folded into that system message.
        system_content = system_prompt
        context_text = ""
        if context:
            serialized_context = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
            context_text = f"\n\nCurrent application context:\n{serialized_context}"
            system_content += context_text
        bounded_history = NvidiaClient._history_messages(history)
        record_prompt_components(
            system_prompt=len(system_prompt),
            ui_context=len(context_text),
            history=sum(len(item["content"]) for item in bounded_history),
            current_user=len(user_message),
        )
        messages: list[dict[str, Any]] = [{"role": "system", "content": system_content}]
        messages.extend(bounded_history)
        messages.append({"role": "user", "content": user_message})
        return messages

    async def generate_json(
        self,
        system_prompt: str,
        user_message: str,
        schema: dict,
        history: list[ConversationMessage] | None = None,
        context: dict | None = None,
    ) -> str:
        messages = self._messages_with_context(system_prompt, user_message, history, context)
        record_prompt_components(schema=len(json.dumps(schema, separators=(",", ":"), ensure_ascii=False)))
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "stream": False,
            "tool_choice": {"type": "function", "function": {"name": "nexus_plan"}},
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "nexus_plan",
                        "description": "Return the structured NEXUS dashboard agent plan.",
                        "parameters": schema,
                    },
                }
            ],
        }
        data = await self._post(payload)
        choices = data.get("choices") or []
        message = choices[0].get("message", {}) if choices and isinstance(choices[0], dict) else {}
        tool_calls = message.get("tool_calls") or []
        for call in tool_calls:
            function = call.get("function") or {}
            if function.get("name") == "nexus_plan" and isinstance(function.get("arguments"), str):
                return function["arguments"]

        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content
        raise NvidiaProviderResponseError(
            "NVIDIA returned no structured NEXUS plan.",
            status_code=200,
            provider_code="missing_structured_plan",
        )

    async def generate_message(
        self,
        system_prompt: str,
        user_message: str,
        context: dict,
        history: list[ConversationMessage] | None = None,
    ) -> str:
        context_text = json.dumps(context, ensure_ascii=False, separators=(",", ":")) if context else ""
        messages = self._messages_with_context(
            system_prompt,
            user_message if not context_text else f"{user_message}\n\nCurrent application context:\n{context_text}",
            history,
            None,
        )
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.55,
            "stream": False,
        }
        data = await self._post(payload)
        choices = data.get("choices") or []
        message = choices[0].get("message", {}) if choices and isinstance(choices[0], dict) else {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise NvidiaProviderResponseError(
                "NVIDIA returned an empty conversation response.",
                status_code=200,
                provider_code="empty_message",
            )
        return content
