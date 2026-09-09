from __future__ import annotations

from typing import Protocol

from app.models import ConversationMessage


class LLMClient(Protocol):
    async def generate_json(self, system_prompt: str, user_message: str, schema: dict, history: list[ConversationMessage] | None = None, context: dict | None = None) -> str: ...
    async def generate_message(self, system_prompt: str, user_message: str, context: dict, history: list[ConversationMessage] | None = None) -> str: ...
