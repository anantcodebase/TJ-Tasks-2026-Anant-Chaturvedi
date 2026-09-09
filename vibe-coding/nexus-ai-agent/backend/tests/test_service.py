import asyncio

from app.agent.fallback import fallback_plan
from app.agent.service import AgentService, enforce_request_boundary
from app.models import AgentPlan, ChatRequest


def test_empty_message_is_rejected():
    try:
        ChatRequest(message="   ")
    except Exception:
        return
    raise AssertionError("Whitespace-only message should be rejected")


def test_delete_analytics_is_unsupported():
    plan = fallback_plan("delete all my analytics")
    assert plan.intent == "unsupported"
    assert plan.actions == []
    assert plan.analytics == []


def test_agent_service_falls_back_when_ollama_fails(monkeypatch):
    service = AgentService()
    monkeypatch.setattr("app.config.settings.allow_fallback", True)

    async def fail_generate_json(*args, **kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr(service.llm, "generate_json", fail_generate_json)
    result = asyncio.run(service.run("make the dashboard red"))
    assert result.source == "fallback"
    assert result.actions
    assert result.message


def test_conversation_fallback_has_no_actions():
    plan = fallback_plan("bruh")
    assert plan.actions == []
    assert plan.analytics == []
    assert plan.message


def test_theme_and_accent_boundary_stay_separate():
    accent_plan = AgentPlan(
        intent="action",
        message="done",
        actions=[
            {"type": "set_accent_color", "accent": "red"},
            {"type": "set_theme", "theme": "cyberpunk"},
        ],
        analytics=[],
    )
    filtered, warnings = enforce_request_boundary(accent_plan, "make the dashboard red")
    assert [action.type for action in filtered.actions] == ["set_accent_color"]
    assert warnings

    theme_plan = AgentPlan(
        intent="action",
        message="done",
        actions=[
            {"type": "set_theme", "theme": "midnight"},
            {"type": "set_accent_color", "accent": "red"},
        ],
        analytics=[],
    )
    filtered, warnings = enforce_request_boundary(theme_plan, "switch to midnight")
    assert [action.type for action in filtered.actions] == ["set_theme"]
    assert warnings


def test_chat_request_accepts_bounded_conversation_context():
    request = ChatRequest(
        message="What did you just say?",
        history=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Online. Give me a dashboard problem worth solving."},
        ],
    )
    assert len(request.history) == 2
    assert request.history[-1].role == "assistant"


def test_fallback_uses_previous_assistant_turn_for_references():
    history = [
        {"role": "user", "content": "what are you yapping about?"},
        {"role": "assistant", "content": "Just warming up the dashboard."},
    ]
    plan = fallback_plan("what did you just say?", history=history)
    assert "Just warming up the dashboard." in plan.message
    assert plan.actions == []


def test_fallback_resolves_hide_it_from_visible_ui_context():
    history = [
        {"role": "user", "content": "show analytics"},
        {"role": "assistant", "content": "Analytics panel opened."},
    ]
    context = {
        "model": "nexus",
        "accent": "lime",
        "visible_widgets": {"analytics": True},
        "analytics_range": "7D",
        "analytics_filter": "ALL",
    }
    plan = fallback_plan("hide it", history=history, ui_context=context)
    assert [(action.type, action.target) for action in plan.actions] == [("hide_widget", "analytics")]


def test_agent_service_passes_history_and_ui_context_to_llm(monkeypatch):
    service = AgentService()
    captured = {}

    async def fake_generate_message(system_prompt, user_message, context, history=None):
        captured["history"] = history
        captured["context"] = context
        return '{"message":"You just said hello."}'

    monkeypatch.setattr(service.llm, "generate_message", fake_generate_message)
    result = asyncio.run(service.run(
        "What did I just say?",
        history=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Online."},
        ],
        ui_context={
            "model": "deep",
            "accent": "blue",
            "visible_widgets": {"analytics": True},
            "analytics_range": "30D",
            "analytics_filter": "DEEP",
        },
    ))
    assert result.message == "You just said hello."
    assert [item.content for item in captured["history"]] == ["Hello", "Online."]
    # General conversation no longer serializes irrelevant dashboard state.
    assert captured["context"] == {}




def test_simple_conversation_uses_one_llm_call(monkeypatch):
    service = AgentService()
    calls = []

    async def fake_generate_message(system_prompt, user_message, context, history=None):
        calls.append((system_prompt, user_message, history))
        return '{"message":"Python is a programming language."}'

    async def fail_generate_json(*args, **kwargs):
        raise AssertionError("Simple conversation should not invoke the action planner")

    monkeypatch.setattr(service.llm, "generate_message", fake_generate_message)
    monkeypatch.setattr(service.llm, "generate_json", fail_generate_json)
    result = asyncio.run(service.run("What is Python?"))
    assert result.message == "Python is a programming language."
    assert len(calls) == 1
    assert result.actions == []


def test_action_path_does_not_perform_second_confirmation_llm_call(monkeypatch):
    service = AgentService()
    planner_calls = []
    confirmation_calls = []

    async def fake_generate_json(system_prompt, user_message, schema, history=None, context=None):
        planner_calls.append(user_message)
        return '{"intent":"action","message":"Done.","actions":[{"type":"set_accent_color","accent":"violet"}],"analytics":[]}'

    async def fake_generate_message(*args, **kwargs):
        confirmation_calls.append(True)
        raise AssertionError("Action execution must not invoke a second confirmation generation call")

    monkeypatch.setattr(service.llm, "generate_json", fake_generate_json)
    monkeypatch.setattr(service.llm, "generate_message", fake_generate_message)
    result = asyncio.run(service.run("Change the accent to purple"))
    assert len(planner_calls) == 1
    assert confirmation_calls == []
    assert [action.type for action in result.actions] == ["set_accent_color"]


def test_theme_color_is_accent_not_theme():
    plan = fallback_plan("change the theme color to purple")
    assert [action.model_dump(exclude_none=True) for action in plan.actions] == [{"type": "set_accent_color", "accent": "violet"}]


def test_legacy_non_executable_action_is_rejected_before_response(monkeypatch):
    service = AgentService()

    async def fake_generate_json(*args, **kwargs):
        return '{"intent":"action","message":"Theme changed.","actions":[{"type":"set_theme","theme":"midnight"}],"analytics":[]}'

    monkeypatch.setattr(service.llm, "generate_json", fake_generate_json)
    result = asyncio.run(service.run("change the theme to midnight"))
    assert result.actions == []
    assert any("not executable" in warning for warning in result.warnings)


def test_fallback_compound_deep_response_time_executes_in_order():
    plan = fallback_plan("switch to Deep and show its response time")
    assert [action.model_dump(exclude_none=True) for action in plan.actions] == [
        {"type": "set_model", "model": "deep"},
        {"type": "set_analytics_filter", "filter": "DEEP"},
        {"type": "show_widget", "target": "response-time"},
    ]


def test_fallback_compound_accent_and_analytics_executes_both_actions():
    plan = fallback_plan("make the accent purple and open analytics")
    assert [action.model_dump(exclude_none=True) for action in plan.actions] == [
        {"type": "set_accent_color", "accent": "violet"},
        {"type": "show_widget", "target": "analytics"},
    ]


def test_model_comparison_is_a_controlled_composition():
    plan = fallback_plan("build me a model comparison panel")
    assert len(plan.actions) == 1
    action = plan.actions[0]
    assert action.type == "compose_widgets"
    assert action.title == "Model comparison"
    assert action.widgets == ["model-comparison", "model-usage", "response-time", "system-status"]


def test_activity_dashboard_is_a_controlled_composition():
    plan = fallback_plan("create an activity dashboard")
    assert len(plan.actions) == 1
    action = plan.actions[0]
    assert action.type == "create_dashboard"
    assert action.widgets == ["activity", "messages", "active-users", "model-usage"]


def test_contextual_hide_it_is_not_stripped_by_boundary():
    history = [
        {"role": "user", "content": "show analytics"},
        {"role": "assistant", "content": "Analytics panel opened."},
    ]
    context = {
        "model": "nexus",
        "accent": "lime",
        "visible_widgets": {"analytics": True},
        "analytics_range": "7D",
        "analytics_filter": "ALL",
    }
    plan = AgentPlan(
        intent="action",
        message="Analytics hidden.",
        actions=[{"type": "hide_widget", "target": "analytics"}],
        analytics=[],
    )
    filtered, warnings = enforce_request_boundary(plan, "hide it", history=history, ui_context=context)
    assert [(a.type, a.target) for a in filtered.actions] == [("hide_widget", "analytics")]
    assert not warnings


def test_default_provider_is_gemini(monkeypatch):
    from app.llm.gemini import GeminiClient
    monkeypatch.setattr("app.config.settings.ai_provider", "gemini")
    service = AgentService()
    assert isinstance(service.llm, GeminiClient)


def test_gemini_rate_limit_error_is_not_converted_to_fallback(monkeypatch):
    from app.llm.errors import GeminiRateLimitError
    service = AgentService()

    async def fail_generate_message(*args, **kwargs):
        raise GeminiRateLimitError()

    monkeypatch.setattr(service.llm, "generate_message", fail_generate_message)
    try:
        asyncio.run(service.run("Hello"))
    except GeminiRateLimitError:
        return
    raise AssertionError("Rate-limit errors must propagate to the API layer")


def test_conversation_provider_failure_does_not_use_dashboard_fallback(monkeypatch):
    from app.llm.errors import ProviderError
    service = AgentService()

    async def fail_generate_message(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(service.llm, "generate_message", fail_generate_message)
    try:
        asyncio.run(service.run("Who is Anant?"))
    except ProviderError as exc:
        assert exc.error_type == "PROVIDER_ERROR"
        assert exc.provider == "gemini"
        return
    raise AssertionError("Provider failures must reach the API layer rather than become a fake success response")


def test_contextual_range_fallback_uses_shared_analytics_state():
    history = [
        {"role": "user", "content": "Show the analytics section."},
        {"role": "assistant", "content": "Analytics panel opened."},
    ]
    context = {
        "model": "nexus",
        "accent": "lime",
        "visible_widgets": {"analytics": True},
        "analytics_range": "7D",
        "analytics_filter": "ALL",
    }
    plan = fallback_plan("Make it 30 days", history=history, ui_context=context)
    assert [(a.type, a.range) for a in plan.actions] == [("set_analytics_range", "30D")]


def test_plan_prompt_is_compact_and_keeps_action_schema():
    import json
    from app.agent.prompts import build_plan_system_prompt, plan_schema
    prompt = build_plan_system_prompt("change the accent color to red")
    schema = plan_schema()
    assert len(prompt) < 2500
    assert len(json.dumps(schema, separators=(",", ":"))) < 3000
    assert "set_accent_color" in prompt
    assert "hide_widget" in prompt


def test_compact_ui_context_preserves_visible_state_without_false_widgets():
    from app.agent.prompts import compact_ui_context
    value = compact_ui_context({
        "model": "nexus", "accent": "lime",
        "visible_widgets": {"analytics": True, "overview": False},
        "analytics_range": "7D", "analytics_filter": "ALL",
    }, "hide it")
    assert value["visible_widgets"] == {"analytics": True}
    assert "analytics" not in value.get("analytics", {})
