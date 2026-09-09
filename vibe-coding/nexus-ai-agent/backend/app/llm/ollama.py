from __future__ import annotations

import httpx
import json
import time
from app.config import settings
from app.llm.errors import OllamaProviderError
from app.models import ConversationMessage
from app.perf import get_trace, record_prompt_components


MAX_HISTORY_MESSAGES = 24
MAX_HISTORY_CHARS = 16000


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout_seconds

    @staticmethod
    def _history_messages(history: list[ConversationMessage] | None) -> list[dict[str, str]]:
        if not history:
            return []
        recent = history[-MAX_HISTORY_MESSAGES:]
        bounded: list[dict[str, str]] = []
        chars = 0
        for item in reversed(recent):
            next_chars = chars + len(item.content)
            if bounded and next_chars > MAX_HISTORY_CHARS:
                break
            bounded.append({"role": item.role, "content": item.content})
            chars = next_chars
        bounded.reverse()
        return bounded

    async def _post(self, payload: dict) -> dict:
        trace = get_trace()
        call = trace.provider_start() if trace is not None else None
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
        except httpx.TimeoutException as exc:
            if call is not None:
                call.end = time.perf_counter()
                call.error_type = "timeout"
            raise OllamaProviderError("NETWORK_ERROR", "NEXUS timed out while waiting for Ollama.") from exc
        except httpx.RequestError as exc:
            if call is not None:
                call.end = time.perf_counter()
                call.error_type = type(exc).__name__
            raise OllamaProviderError("NETWORK_ERROR", "NEXUS could not reach Ollama.") from exc

        if call is not None:
            call.end = time.perf_counter()
            call.status_code = response.status_code
            call.response_bytes = len(response.content)
        if response.status_code >= 400:
            error_type = "INVALID_REQUEST" if response.status_code == 400 else "MODEL_UNAVAILABLE" if response.status_code == 404 else "PROVIDER_ERROR"
            raise OllamaProviderError(
                error_type,
                f"Ollama returned HTTP {response.status_code}.",
                status_code=response.status_code,
            )

        parse_started = time.perf_counter()
        try:
            data = response.json()
        except ValueError as exc:
            if trace is not None:
                trace.provider_parse += time.perf_counter() - parse_started
            raise OllamaProviderError("PROVIDER_ERROR", "Ollama returned malformed JSON.", status_code=response.status_code) from exc
        if trace is not None:
            trace.provider_parse += time.perf_counter() - parse_started
        if not isinstance(data, dict):
            raise OllamaProviderError("PROVIDER_ERROR", "Ollama returned an unexpected JSON response.", status_code=response.status_code)
        content = data.get("message", {}).get("content", "") if isinstance(data.get("message"), dict) else ""
        if call is not None and isinstance(content, str):
            call.output_chars = len(content)
        return data

    async def generate_json(
        self,
        system_prompt: str,
        user_message: str,
        schema: dict,
        history: list[ConversationMessage] | None = None,
        context: dict | None = None,
    ) -> str:
        history_messages = self._history_messages(history)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history_messages)
        context_text = ""
        if context:
            context_text = f"Current application context:\n{context}"
            messages.append({"role": "system", "content": context_text})
        messages.append({"role": "user", "content": user_message})
        record_prompt_components(system_prompt=len(system_prompt), history=sum(len(item["content"]) for item in history_messages), ui_context=len(context_text), current_user=len(user_message), schema=len(json.dumps(schema, separators=(",", ":"), ensure_ascii=False)))
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": schema,
            "options": {"temperature": 0.3}
        }
        data = await self._post(payload)
        return str(data.get("message", {}).get("content", ""))

    async def generate_message(
        self,
        system_prompt: str,
        user_message: str,
        context: dict,
        history: list[ConversationMessage] | None = None,
    ) -> str:
        history_messages = self._history_messages(history)
        context_text = json.dumps(context, separators=(",", ":"), ensure_ascii=False) if context else ""
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history_messages)
        messages.append({"role": "user", "content": user_message if not context_text else f"{user_message}\n\nCurrent application context:\n{context_text}"})
        record_prompt_components(
            system_prompt=len(system_prompt),
            history=sum(len(item["content"]) for item in history_messages),
            ui_context=len(context_text),
            current_user=len(user_message),
        )
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.55}
        }
        data = await self._post(payload)
        content = str(data.get("message", {}).get("content", ""))
        return content
