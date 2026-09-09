from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any

from app.config import settings
from app.llm.errors import (
    GeminiAuthenticationError,
    GeminiInvalidRequestError,
    GeminiModelUnavailableError,
    GeminiNetworkError,
    GeminiProviderResponseError,
    GeminiRateLimitError,
    ProviderError,
)
from app.models import ConversationMessage
from app.perf import get_trace, record_prompt_components

MAX_HISTORY_MESSAGES = 24
MAX_HISTORY_CHARS = 16000
MAX_RETRIES = 2
DEFAULT_RETRY_DELAY = 1.5
MAX_RETRY_DELAY = 10.0
RATE_LIMIT_MESSAGE = "NEXUS is busy right now. Please wait a few seconds and try again."


class GeminiClient:
    """Gemini implementation of the provider contract used by AgentService."""

    def __init__(self) -> None:
        self.model = settings.gemini_model
        self.timeout = settings.gemini_timeout_seconds
        self.client = None

    @staticmethod
    def _history_contents(history: list[ConversationMessage] | None):
        from google.genai import types
        if not history:
            return []
        recent = history[-MAX_HISTORY_MESSAGES:]
        bounded: list[ConversationMessage] = []
        chars = 0
        for item in reversed(recent):
            next_chars = chars + len(item.content)
            if bounded and next_chars > MAX_HISTORY_CHARS:
                break
            bounded.append(item)
            chars = next_chars
        bounded.reverse()
        return [
            types.Content(
                role="model" if item.role == "assistant" else "user",
                parts=[types.Part.from_text(text=item.content)],
            )
            for item in bounded
        ]

    @staticmethod
    def _retry_after_from_exception(exc: Exception) -> float | None:
        """Extract retry timing from different google-genai exception shapes."""
        candidates: list[Any] = [
            getattr(exc, "retry_after", None),
            getattr(exc, "retry_delay", None),
        ]
        response = getattr(exc, "response", None)
        if response is not None:
            candidates.extend([
                getattr(response, "headers", {}).get("Retry-After") if getattr(response, "headers", None) else None,
                getattr(response, "retry_after", None),
            ])

        for value in candidates:
            if value is None:
                continue
            if isinstance(value, (int, float)):
                return max(0.0, float(value))
            if isinstance(value, str):
                match = re.search(r"(?:retry[-_ ]?after|delay)?\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)?", value, re.I)
                if match:
                    return max(0.0, float(match.group(1)))
            seconds = getattr(value, "seconds", None)
            nanos = getattr(value, "nanos", 0)
            if seconds is not None:
                return max(0.0, float(seconds) + float(nanos or 0) / 1_000_000_000)

        return None

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        status = getattr(exc, "status_code", None) or getattr(exc, "status", None) or getattr(exc, "code", None)
        if str(status).lower() in {"429", "resource_exhausted", "resource exhausted"}:
            return True
        response = getattr(exc, "response", None)
        response_status = getattr(response, "status_code", None) if response is not None else None
        if response_status == 429:
            return True
        text = str(exc).lower()
        return "429" in text or "resource_exhausted" in text or "rate limit" in text or "quota exceeded" in text

    @staticmethod
    def _exception_status(exc: Exception) -> int | None:
        status = getattr(exc, "status_code", None) or getattr(exc, "status", None) or getattr(exc, "code", None)
        if isinstance(status, int):
            return status
        response = getattr(exc, "response", None)
        response_status = getattr(response, "status_code", None) if response is not None else None
        return response_status if isinstance(response_status, int) else None

    @classmethod
    def _normalize_error(cls, exc: Exception) -> ProviderError:
        if isinstance(exc, ProviderError):
            return exc
        status = cls._exception_status(exc)
        text = str(exc).lower()
        common = {"status_code": status, "provider_code": str(status) if status is not None else type(exc).__name__}
        if cls._is_rate_limit_error(exc):
            return GeminiRateLimitError(retry_after=cls._retry_after_from_exception(exc), **common)
        if status in {401, 403} or "api key" in text or "authentication" in text or "permission denied" in text:
            return GeminiAuthenticationError(**common)
        if status == 404 or "model not found" in text or "unknown model" in text:
            return GeminiModelUnavailableError(**common)
        if status == 400 or "invalid argument" in text or "invalid request" in text:
            return GeminiInvalidRequestError(**common)
        if isinstance(exc, (TimeoutError, OSError)) or "timeout" in text or "connection" in text or "network" in text:
            return GeminiNetworkError(**common)
        return GeminiProviderResponseError(**common)

    async def _generate_once(self, system_prompt: str, contents, schema: dict | None, temperature: float) -> str:
        from google import genai
        from google.genai import types
        if not settings.gemini_api_key:
            raise GeminiAuthenticationError("GEMINI_API_KEY is not configured.", provider_code="missing_api_key")
        if self.client is None:
            self.client = genai.Client(
                api_key=settings.gemini_api_key,
                http_options=types.HttpOptions(timeout=int(self.timeout * 1000)),
            )
        config: dict[str, Any] = {
            "system_instruction": system_prompt,
            "temperature": temperature,
        }
        if schema is not None:
            config["response_mime_type"] = "application/json"
            config["response_schema"] = schema
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(**config),
        )
        text = response.text
        if not text:
            raise RuntimeError("Gemini returned an empty response.")
        return text

    async def _generate(self, system_prompt: str, contents, schema: dict | None, temperature: float) -> str:
        for attempt in range(MAX_RETRIES + 1):
            trace = get_trace()
            call = trace.provider_start() if trace is not None else None
            try:
                result = await self._generate_once(system_prompt, contents, schema, temperature)
                if call is not None:
                    call.end = time.perf_counter()
                    call.output_chars = len(result)
                return result
            except Exception as exc:
                normalized = self._normalize_error(exc)
                if call is not None:
                    call.end = time.perf_counter()
                    call.error_type = normalized.error_type
                    call.status_code = normalized.status_code
                if not isinstance(normalized, GeminiRateLimitError):
                    raise normalized from exc

                retry_after = self._retry_after_from_exception(exc)
                if attempt >= MAX_RETRIES:
                    raise normalized from exc

                delay = retry_after if retry_after is not None else DEFAULT_RETRY_DELAY * (2 ** attempt)
                await asyncio.sleep(min(max(delay, 0.0), MAX_RETRY_DELAY))

        raise GeminiRateLimitError()

    async def generate_json(
        self,
        system_prompt: str,
        user_message: str,
        schema: dict,
        history: list[ConversationMessage] | None = None,
        context: dict | None = None,
    ) -> str:
        from google.genai import types
        contents = self._history_contents(history)
        history_chars = sum(len(item.parts[0].text or "") for item in contents)
        context_text = ""
        if context:
            context_text = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"Current application context:\n{context_text}")],
            ))
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))
        record_prompt_components(
            system_prompt=len(system_prompt), history=history_chars,
            ui_context=len(context_text), current_user=len(user_message),
            schema=len(json.dumps(schema, separators=(",", ":"), ensure_ascii=False)),
        )
        return await self._generate(system_prompt, contents, schema, temperature=0.3)

    async def generate_message(
        self,
        system_prompt: str,
        user_message: str,
        context: dict,
        history: list[ConversationMessage] | None = None,
    ) -> str:
        from google.genai import types
        contents = self._history_contents(history)
        history_chars = sum(len(item.parts[0].text or "") for item in contents)
        context_text = json.dumps(context, ensure_ascii=False, separators=(",", ":")) if context else ""
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message if not context_text else f"{user_message}\n\nCurrent application context:\n{context_text}")],
        ))
        record_prompt_components(
            system_prompt=len(system_prompt), history=history_chars,
            ui_context=len(context_text), current_user=len(user_message),
        )
        return await self._generate(system_prompt, contents, None, temperature=0.55)
