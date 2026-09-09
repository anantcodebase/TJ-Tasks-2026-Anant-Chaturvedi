import asyncio

import pytest

from app.agent.parser import parse_conversation_output
from app.agent.service import AgentService
from app.config import settings
from app.llm.gemini import GeminiClient
from app.llm.ollama import OllamaClient
from app.models import ChatUIContext
from app.perf import ChatPerfTrace


def test_plain_conversation_accepts_plain_text_without_an_action_protocol():
    message, warnings, recovered = parse_conversation_output("Recursion is a function solving a smaller version of itself.")
    assert message == "Recursion is a function solving a smaller version of itself."
    assert recovered is False
    assert warnings


def test_action_response_is_provisional_until_the_browser_verifies_shared_state(monkeypatch):
    service = AgentService()

    async def planned_action(*args, **kwargs):
        return '{"intent":"action","message":"Accent changed to red.","actions":[{"type":"set_accent_color","accent":"red"}],"analytics":[]}'

    monkeypatch.setattr(service.llm, "generate_json", planned_action)
    result = asyncio.run(service.run("Change the accent color to red"))

    assert result.actions[0].type == "set_accent_color"
    assert result.message == "The requested dashboard action is ready to apply."


@pytest.mark.parametrize("provider", ["gemini", "ollama", "nvidia"])
def test_all_provider_routes_emit_the_same_action_contract(monkeypatch, provider):
    monkeypatch.setattr(settings, "ai_provider", provider)
    service = AgentService()

    async def planned_action(*args, **kwargs):
        return '{"intent":"action","message":"Done.","actions":[{"type":"hide_widget","target":"overview"}],"analytics":[]}'

    monkeypatch.setattr(service.llm, "generate_json", planned_action)
    result = asyncio.run(service.run("Hide widgets", ui_context=ChatUIContext(visible_widgets={"analytics": True, "overview": True})))

    assert result.source == provider
    assert [action.model_dump(exclude_none=True) for action in result.actions] == [{"type": "hide_widget", "target": "overview"}]


def test_ollama_plain_conversation_does_not_request_json_structured_output(monkeypatch):
    client = OllamaClient()
    captured = {}

    async def fake_post(payload):
        captured.update(payload)
        return {"message": {"content": "Hello."}}

    monkeypatch.setattr(client, "_post", fake_post)
    result = asyncio.run(client.generate_message("system", "hello", {}, history=[]))

    assert result == "Hello."
    assert "format" not in captured
    assert captured["messages"][-1] == {"role": "user", "content": "hello"}


def test_gemini_plain_conversation_uses_no_response_schema(monkeypatch):
    client = GeminiClient()
    captured = {}

    async def fake_generate(system_prompt, contents, schema, temperature):
        captured["schema"] = schema
        return "Hello."

    monkeypatch.setattr(client, "_generate", fake_generate)
    result = asyncio.run(client.generate_message("system", "hello", {}, history=[]))

    assert result == "Hello."
    assert captured["schema"] is None


def test_perf_trace_is_visible_in_the_server_terminal(capsys):
    trace = ChatPerfTrace()
    trace.log()
    output = capsys.readouterr().out
    assert "[CHAT PERF]" in output
    assert "provider_ttft=unavailable_non_streaming" in output
