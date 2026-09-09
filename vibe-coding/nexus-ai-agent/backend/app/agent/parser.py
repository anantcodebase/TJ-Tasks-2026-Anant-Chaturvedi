from __future__ import annotations

import ast
import json
import re
from typing import Any

from pydantic import ValidationError

from app.models import AgentPlan, AnalyticsRequest, UIAction


JSON_OBJECT_RE = re.compile(r"\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}", re.DOTALL)


def strip_fences(text: str) -> str:
    value = text.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\s*```$", "", value)
    return value.strip()


def extract_json_object(text: str) -> str | None:
    cleaned = strip_fences(text)
    if cleaned.startswith("{") and cleaned.endswith("}"):
        return cleaned
    match = JSON_OBJECT_RE.search(cleaned)
    return match.group(0) if match else None


def remove_trailing_commas(value: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", value)


def decode_json(text: str) -> tuple[Any | None, list[str]]:
    warnings: list[str] = []
    candidate = extract_json_object(text)
    if not candidate:
        return None, ["No JSON object could be extracted from the model output."]

    try:
        return json.loads(candidate), warnings
    except json.JSONDecodeError:
        warnings.append("Direct JSON parsing failed; recovery was attempted.")

    repaired = remove_trailing_commas(candidate)
    try:
        value = json.loads(repaired)
        warnings.append("Trailing-comma repair succeeded.")
        return value, warnings
    except json.JSONDecodeError:
        pass

    try:
        value = ast.literal_eval(candidate)
        if isinstance(value, dict):
            warnings.append("Python-literal recovery succeeded.")
            return value, warnings
    except (SyntaxError, ValueError, TypeError):
        pass

    return None, warnings + ["JSON recovery failed."]


def sanitize_action(value: Any) -> UIAction | None:
    if not isinstance(value, dict):
        return None

    action_types = {
        "set_accent_color": {"type", "accent"},
        "set_theme": {"type", "theme"},
        "set_model": {"type", "model"},
        "show_widget": {"type", "target"},
        "hide_widget": {"type", "target"},
        "highlight_element": {"type", "target"},
        "set_text_size": {"type", "size"},
        "set_metric_focus": {"type", "metric"},
        "set_analytics_range": {"type", "range"},
        "set_analytics_filter": {"type", "filter"},
        "set_font": {"type", "font"},
        "set_dashboard_view": {"type", "view"},
        "open_panel": {"type", "target"},
        "close_panel": {"type", "target"},
        "maximize_panel": {"type", "target"},
        "minimize_panel": {"type", "target"},
        "reset_dashboard": {"type"},
        "create_dashboard": {"type", "widgets", "title"},
        "compose_widgets": {"type", "widgets", "title"},
        "remove_generated_section": {"type"},
        "show_metric": {"type", "target"},
        "show_chart": {"type", "target"},
    }

    action_type = value.get("type")
    allowed_fields = action_types.get(action_type)
    if not allowed_fields or set(value.keys()) != allowed_fields:
        return None

    try:
        return UIAction.model_validate(value)
    except ValidationError:
        return None


def sanitize_analytics(value: Any) -> AnalyticsRequest | None:
    if not isinstance(value, dict):
        return None

    allowed_fields = {"operation", "metric", "period"}
    if set(value.keys()) - allowed_fields:
        return None

    try:
        return AnalyticsRequest.model_validate(value)
    except ValidationError:
        return None


def validate_plan(raw: Any) -> tuple[AgentPlan | None, list[str], bool]:
    warnings: list[str] = []
    recovered = False

    if not isinstance(raw, dict):
        return None, ["Model JSON root must be an object."], False

    try:
        plan = AgentPlan.model_validate(raw)
        return plan, warnings, False
    except ValidationError:
        warnings.append("Schema validation failed; safe field-level recovery was attempted.")
        recovered = True

    allowed_plan_fields = {"intent", "message", "actions", "analytics"}
    if set(raw.keys()) - allowed_plan_fields:
        warnings.append("Unexpected top-level model fields were ignored during recovery.")

    intent = raw.get("intent", "conversation")
    if intent not in {"action", "analytics", "conversation", "unsupported", "mixed"}:
        intent = "conversation"
        warnings.append("Unknown intent was replaced with conversation.")

    message = raw.get("message", "")
    message = message if isinstance(message, str) else str(message)

    actions: list[UIAction] = []
    raw_actions = raw.get("actions", [])
    if not isinstance(raw_actions, list):
        warnings.append("Invalid actions container was dropped.")
        raw_actions = []

    for item in raw_actions:
        action = sanitize_action(item)
        if action:
            actions.append(action)
        else:
            warnings.append("An invalid or unknown UI action was dropped.")

    analytics: list[AnalyticsRequest] = []
    raw_analytics = raw.get("analytics", [])
    if not isinstance(raw_analytics, list):
        warnings.append("Invalid analytics container was dropped.")
        raw_analytics = []

    for item in raw_analytics:
        request = sanitize_analytics(item)
        if request:
            analytics.append(request)
        else:
            warnings.append("An invalid analytics request was dropped.")

    try:
        plan = AgentPlan(
            intent=intent,
            message=message[:1000],
            actions=actions[:12],
            analytics=analytics[:4],
        )
        return plan, warnings, recovered
    except ValidationError:
        return None, warnings + ["Recovered fields could not form a valid plan."], recovered


def parse_model_output(text: str) -> tuple[AgentPlan | None, list[str], bool]:
    raw, warnings = decode_json(text)
    if raw is None:
        return None, warnings, True
    plan, validation_warnings, recovered = validate_plan(raw)
    return plan, warnings + validation_warnings, recovered


def parse_conversation_output(text: str) -> tuple[str | None, list[str], bool]:
    """Accept plain conversational text while retaining compatibility with JSON.

    Dashboard actions require strict structured output. Ordinary conversation
    does not, so forcing a JSON schema on every greeting or explanation adds
    avoidable provider work. Existing JSON-capable models remain compatible.
    """
    value = text.strip()
    if not value:
        return None, ["The provider returned an empty conversation response."], True

    plan, warnings, recovered = parse_model_output(value)
    if plan is not None:
        if plan.actions or plan.analytics:
            return None, warnings + ["Conversation output contained executable fields and was rejected."], True
        if plan.message.strip():
            return plan.message.strip(), warnings, recovered

    # A normal answer is not an action protocol. Bound it to the same response
    # size as AgentPlan.message and never interpret its prose as UI commands.
    return value[:1000], ["Plain-text conversation response accepted."], False
