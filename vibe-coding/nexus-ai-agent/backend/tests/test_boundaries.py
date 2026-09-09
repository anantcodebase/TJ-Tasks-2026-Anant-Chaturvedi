import asyncio

from app.agent.fallback import fallback_plan
from app.agent.service import enforce_request_boundary
from app.models import AgentPlan
from app.tools.analytics import query_analytics


def test_general_question_does_not_produce_actions():
    plan = AgentPlan(
        intent="action",
        message="A response",
        actions=[{"type": "set_text_size", "size": "lg"}],
        analytics=[],
    )
    filtered, warnings = enforce_request_boundary(plan, "who is the prime minister of india")
    assert filtered.actions == []
    assert filtered.analytics == []
    assert filtered.intent == "conversation"
    assert warnings


def test_joke_does_not_trigger_action():
    plan = fallback_plan("tell me a joke")
    assert plan.actions == []
    assert plan.analytics == []
    assert plan.intent == "conversation"
    assert plan.message


def test_comic_sans_opinion_does_not_trigger_action():
    plan = fallback_plan("what do you think of Comic Sans?")
    assert plan.intent == "conversation"
    assert plan.actions == []
    assert plan.message


def test_accent_commands_are_explicit_and_separate_from_theme():
    red = fallback_plan("make the dashboard red")
    assert red.intent == "action"
    assert any(action.type == "set_accent_color" and action.accent == "red" for action in red.actions)
    assert not any(action.type == "set_theme" for action in red.actions)

    combo = fallback_plan("make it cyberpunk with red accents")
    assert any(action.type == "set_theme" and action.theme == "cyberpunk" for action in combo.actions)
    assert any(action.type == "set_accent_color" and action.accent == "red" for action in combo.actions)

    midnight = fallback_plan("switch to midnight")
    assert [action.type for action in midnight.actions] == ["set_theme"]

def test_all_supported_accent_colors_are_mapped():
    expected = {
        "red": "red",
        "blue": "blue",
        "purple": "violet",
        "violet": "violet",
        "cyan": "cyan",
        "green": "lime",
        "orange": "orange",
        "yellow": "yellow",
        "pink": "pink",
    }
    for phrase, accent in expected.items():
        plan = fallback_plan(f"make the dashboard {phrase}")
        assert any(action.type == "set_accent_color" and action.accent == accent for action in plan.actions), phrase

    use_purple = fallback_plan("use purple")
    assert [action.model_dump(exclude_none=True) for action in use_purple.actions] == [{"type": "set_accent_color", "accent": "violet"}]

def test_accent_action_rejects_arbitrary_css():
    from app.agent.parser import parse_model_output
    raw = '{"intent":"action","message":"bad","actions":[{"type":"set_accent_color","accent":"red; body { color: blue }"}],"analytics":[]}'
    plan, warnings, recovered = parse_model_output(raw)
    assert plan is not None
    assert plan.actions == []
    assert warnings
    assert recovered


def test_supported_multi_action_fallback():
    plan = fallback_plan(
        "make the dashboard background red, hide the revenue card, increase the font size, and tell me how sales are doing"
    )
    assert len(plan.actions) == 4
    assert {action.type for action in plan.actions} == {
        "set_accent_color",
        "hide_widget",
        "set_text_size",
        "set_metric_focus",
    }
    assert len(plan.analytics) == 1
    assert plan.analytics[0].metric == "sales"


def test_comic_sans_can_be_explicitly_applied():
    plan = fallback_plan("make everything Comic Sans")
    assert plan.intent == "action"
    assert any(action.type == "set_font" and action.font == "comic" for action in plan.actions)


def test_revenue_only_view_is_explicit():
    plan = fallback_plan("hide everything except revenue")
    assert plan.intent == "action"
    assert [action.model_dump(exclude_none=True) for action in plan.actions] == [{"type": "set_dashboard_view", "view": "revenue_only"}]


def test_reset_everything_is_explicit():
    plan = fallback_plan("reset everything")
    assert plan.intent == "action"
    assert [action.model_dump(exclude_none=True) for action in plan.actions] == [{"type": "reset_dashboard"}]


def test_identity_uses_known_operator():
    plan = fallback_plan("who made you?")
    assert plan.intent == "conversation"
    assert plan.actions == []
    assert "Anant Chaturvedi" in plan.message
    assert "XlaMus" in plan.message


def test_color_reset_uses_default_accent_without_resetting_dashboard():
    plan = fallback_plan("reset the color")
    assert plan.intent == "action"
    assert [action.model_dump(exclude_none=True) for action in plan.actions] == [{"type": "set_accent_color", "accent": "violet"}]

def test_analytics_question_can_control_the_requested_visualization():
    plan = fallback_plan("show me the sales analytics")
    assert plan.intent == "analytics"
    assert any(action.type == "set_metric_focus" and action.metric == "sales" for action in plan.actions)
    assert any(action.type == "show_widget" and action.target == "analytics" for action in plan.actions)
    assert plan.analytics[0].metric == "sales"


def test_analytics_boundary_keeps_only_metric_visualization_actions():
    plan = AgentPlan(
        intent="analytics",
        message="Sales are up.",
        actions=[
            {"type": "set_metric_focus", "metric": "sales"},
            {"type": "reset_dashboard"},
        ],
        analytics=[{"operation": "fetch", "metric": "sales", "period": "7d"}],
    )
    filtered, warnings = enforce_request_boundary(plan, "show me the sales analytics")
    assert [action.type for action in filtered.actions] == ["set_metric_focus"]
    assert warnings


def test_unsupported_request_has_no_dashboard_action():
    plan = fallback_plan("write me a C++ calculator")
    assert plan.intent == "unsupported"
    assert plan.actions == []
    assert plan.analytics == []
    assert plan.message


def test_analytics_execution_is_deterministic():
    first = asyncio.run(query_analytics("sales"))
    second = asyncio.run(query_analytics("sales"))
    assert first.model_dump() == second.model_dump()
