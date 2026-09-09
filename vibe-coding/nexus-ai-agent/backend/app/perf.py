from __future__ import annotations

import contextvars
import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ProviderCall:
    index: int
    start: float
    end: float | None = None
    status_code: int | None = None
    response_bytes: int | None = None
    output_chars: int | None = None
    error_type: str | None = None

    @property
    def duration(self) -> float | None:
        return None if self.end is None else self.end - self.start


@dataclass
class ChatPerfTrace:
    started: float = field(default_factory=time.perf_counter)
    request_received_wall: float = field(default_factory=time.time)
    context_build: float = 0.0
    agent: float = 0.0
    tools: float = 0.0
    response_build: float = 0.0
    provider_parse: float = 0.0
    history_messages: int = 0
    history_chars: int = 0
    provider_calls: list[ProviderCall] = field(default_factory=list)
    prompt_components: dict[str, int] = field(default_factory=dict)

    def provider_start(self) -> ProviderCall:
        call = ProviderCall(index=len(self.provider_calls) + 1, start=time.perf_counter())
        self.provider_calls.append(call)
        return call

    def log(self) -> None:
        total = time.perf_counter() - self.started
        parts = [
            "[CHAT PERF]",
            f"request_total={total:.3f}s",
            f"context_build={self.context_build:.3f}s",
            f"agent={self.agent:.3f}s",
            f"provider_calls={len(self.provider_calls)}",
            f"provider_retries={max(0, len(self.provider_calls) - 1)}",
            "provider_ttft=unavailable_non_streaming",
            f"tools={self.tools:.3f}s",
            f"response_build={self.response_build:.3f}s",
            f"provider_parse={self.provider_parse:.3f}s",
            f"history_messages={self.history_messages}",
            f"history_chars={self.history_chars}",
        ]
        for call in self.provider_calls:
            duration = call.duration if call.duration is not None else 0.0
            parts.append(f"provider_{call.index}={duration:.3f}s")
            if call.status_code is not None:
                parts.append(f"provider_{call.index}_status={call.status_code}")
            if call.response_bytes is not None:
                parts.append(f"provider_{call.index}_bytes={call.response_bytes}")
            if call.output_chars is not None:
                parts.append(f"provider_{call.index}_output_chars={call.output_chars}")
            if call.error_type:
                parts.append(f"provider_{call.index}_error={call.error_type}")
        for name, chars in self.prompt_components.items():
            parts.append(f"prompt_{name}_chars={chars}")
            parts.append(f"prompt_{name}_tokens_est={max(1, round(chars / 4))}")
        from datetime import datetime, timezone
        record = " ".join(parts)
        # Uvicorn does not configure this module's logger at INFO by default,
        # which used to make the existing timing record invisible in a normal
        # development terminal. Keep the logger for deployments and print one
        # flush-backed record for local measurement.
        logger.info("[CHAT PERF] request_received=%s %s", datetime.fromtimestamp(self.request_received_wall, timezone.utc).isoformat(), " ".join(parts[1:]))
        print(f"request_received={datetime.fromtimestamp(self.request_received_wall, timezone.utc).isoformat()} {record}", flush=True)


_current_trace: contextvars.ContextVar[ChatPerfTrace | None] = contextvars.ContextVar("chat_perf_trace", default=None)


def set_trace(trace: ChatPerfTrace | None) -> contextvars.Token:
    return _current_trace.set(trace)


def reset_trace(token: contextvars.Token) -> None:
    _current_trace.reset(token)


def record_prompt_components(**components: str | int | None) -> None:
    trace = get_trace()
    if trace is None:
        return
    for name, value in components.items():
        if value is None:
            continue
        trace.prompt_components[name] = int(value)


def get_trace() -> ChatPerfTrace | None:
    return _current_trace.get()
