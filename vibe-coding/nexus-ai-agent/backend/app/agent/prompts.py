from __future__ import annotations

import json
import re
from typing import Any

from app.models import AgentPlan


ACTION_GUIDE = {
    "ui_actions": [
        {"type": "set_accent_color", "accent": "lime|blue|violet|cyan|red|orange|yellow|pink"},
        {"type": "set_model", "model": "nexus|deep"},
        {"type": "show_widget", "target": "analytics|overview|revenue|engagement-chart|metrics|activity|active-users|messages|model-usage|response-time|system-status|session-information|telemetry|model-comparison|performance|usage-trends|chat"},
        {"type": "hide_widget", "target": "analytics|overview|revenue|engagement-chart|metrics|activity|active-users|messages|model-usage|response-time|system-status|session-information|telemetry|model-comparison|performance|usage-trends|chat"},
        {"type": "open_panel", "target": "analytics|overview|model-usage|response-time|active-users|activity|system-status|performance|model-comparison|usage-trends|telemetry|session-information"},
        {"type": "close_panel", "target": "analytics|overview|model-usage|response-time|active-users|activity|system-status|performance|model-comparison|usage-trends|telemetry|session-information"},
        {"type": "set_analytics_range", "range": "7D|30D|90D"},
        {"type": "set_analytics_filter", "filter": "ALL|NEXUS|DEEP"},
        {"type": "set_metric_focus", "metric": "engagement|sessions|conversion|sales"},
        {"type": "reset_dashboard"},
        {"type": "show_metric", "target": "active-users|messages|response-time|system-status|session-information|telemetry|metrics|revenue"},
        {"type": "show_chart", "target": "activity|model-usage|response-time|engagement-chart|usage-trends"},
        {"type": "create_dashboard", "widgets": "registered widget IDs", "title": "short title"},
        {"type": "compose_widgets", "widgets": "registered widget IDs", "title": "short title"},
        {"type": "remove_generated_section"},
    ],
    "analytics_requests": [
        {"operation": "fetch|summarize", "metric": "engagement|sessions|conversion|sales", "period": "7d"}
    ],
}


OPERATOR_CONTEXT = {
    "agent": {
        "name": "NEXUS",
        "role": "local AI dashboard agent",
        "runtime": "Gemini",
        "capabilities": [
            "operate this dashboard UI through allowlisted actions",
            "inspect and summarize mock analytics",
            "compose temporary views from registered NEXUS widgets",
        ],
        "limitations": [
            "no arbitrary computer control",
            "no arbitrary JavaScript execution",
            "no arbitrary file, database, or external-system access",
        ],
    },
    "operator": {
        "name": "Anant Chaturvedi",
        "alias": "XlaMus",
        "role": "creator/operator of the NEXUS project",
        "technical_focus": [
            "C++",
            "Data Structures and Algorithms",
            "Web Development",
            "Node.js",
            "AI/ML",
            "NLP",
            "TensorFlow",
            "Kotlin",
        ],
        "projects": [
            "Library Management System",
            "Bank Management System",
        ],
        "portfolio": "https://anantcodebase.github.io/Anant-Chaturvedi-Portfolio/",
        "public_profiles": [
            "https://github.com/anantcodebase/",
            "https://www.linkedin.com/in/theanantchaturvedi/",
            "https://leetcode.com/u/anantchaturvedi/",
            "https://www.youtube.com/@YouTubeXlamus",
        ],
    },
}


def plan_schema() -> dict[str, Any]:
    """Compact schema for the executable NEXUS plan.

    The Pydantic model remains the final validator, but this wire schema avoids
    duplicating non-executable legacy actions and large $defs/$ref structures.
    """
    action_types = [
        "set_accent_color", "set_model", "show_widget", "hide_widget",
        "set_metric_focus", "set_analytics_range", "set_analytics_filter",
        "open_panel", "close_panel", "reset_dashboard", "create_dashboard",
        "compose_widgets", "remove_generated_section", "show_metric", "show_chart",
    ]
    widget_targets = [
        "analytics", "overview", "revenue", "engagement-chart", "metrics", "activity",
        "active-users", "messages", "model-usage", "response-time", "system-status",
        "session-information", "telemetry", "model-comparison", "performance",
        "usage-trends", "chat",
    ]
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "intent": {"type": "string", "enum": ["action", "analytics", "conversation", "unsupported", "mixed"]},
            "message": {"type": "string", "maxLength": 1000},
            "actions": {
                "type": "array", "maxItems": 12,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "type": {"type": "string", "enum": action_types},
                        "target": {"type": ["string", "null"], "enum": widget_targets + [None]},
                        "accent": {"type": ["string", "null"], "enum": ["lime", "blue", "violet", "cyan", "red", "orange", "yellow", "pink", None]},
                        "model": {"type": ["string", "null"], "enum": ["nexus", "deep", None]},
                        "metric": {"type": ["string", "null"], "enum": ["engagement", "sessions", "conversion", "sales", None]},
                        "range": {"type": ["string", "null"], "enum": ["7D", "30D", "90D", None]},
                        "filter": {"type": ["string", "null"], "enum": ["ALL", "NEXUS", "DEEP", None]},
                        "widgets": {"type": ["array", "null"], "maxItems": 12, "items": {"type": "string", "enum": widget_targets}},
                        "title": {"type": ["string", "null"], "maxLength": 120},
                        "dashboardId": {"type": ["string", "null"], "maxLength": 80},
                    },
                    "required": ["type"],
                },
            },
            "analytics": {
                "type": "array", "maxItems": 4,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "operation": {"type": "string", "enum": ["fetch", "summarize"]},
                        "metric": {"type": "string", "enum": ["engagement", "sessions", "conversion", "sales"]},
                        "period": {"type": "string", "enum": ["7d"]},
                    },
                    "required": ["operation", "metric", "period"],
                },
            },
        },
        "required": ["intent", "message", "actions", "analytics"],
    }


def _operator_context_relevant(user_message: str) -> bool:
    value = user_message.lower()
    return bool(re.search(r"\b(?:creator|operator|made you|who built you|who created you|anant|xlamus|github|portfolio|linkedin)\b", value))


def compact_ui_context(ui_context: dict[str, Any] | None, user_message: str) -> dict[str, Any]:
    if not ui_context:
        return {}
    value = user_message.lower()
    # Greetings and general questions do not need a serialized dashboard. The
    # conversation history already carries conversational memory; current UI
    # state is included only when the request can depend on it.
    if not re.search(r"\b(?:dashboard|widget|panel|analytics|usage|metrics|data|sales|engagement|sessions|conversion|range|period|day|latency|response\s*time|active\s+users|activity|model|accent|color|colour|theme|hide|show|open|close|set|change|make|switch|again|same|\bit\b|\bthis\b|\bthat\b)\b", value):
        return {}
    compact: dict[str, Any] = {
        "model": ui_context.get("model"),
        "accent": ui_context.get("accent"),
        "visible_widgets": {name: True for name, visible in (ui_context.get("visible_widgets") or {}).items() if visible},
    }
    if re.search(r"\b(?:analytics|usage|metrics|data|sales|engagement|sessions|conversion|range|period|30\s*day|90\s*day|7\s*day|latency|response\s*time)\b", value):
        compact["analytics"] = {
            "range": ui_context.get("analytics_range"),
            "filter": ui_context.get("analytics_filter"),
        }
    generated = ui_context.get("generated_section")
    if generated:
        compact["generated"] = {
            "id": generated.get("id"),
            "title": generated.get("title"),
            "widgets": generated.get("widgets", []),
        }
    return compact


def build_plan_system_prompt(user_message: str = "") -> str:
    operator_text = ""
    if _operator_context_relevant(user_message):
        operator_text = f"\nRelevant operator context:\n{json.dumps(OPERATOR_CONTEXT, ensure_ascii=False, separators=(',', ':'))}\nUse it only for directly related identity/operator questions.\n"
    return f"""You are NEXUS, a dashboard agent. Return one safe structured plan as JSON.

Use the supplied prior user/assistant messages as real conversation history. Resolve references such as “it”, “that”, “same”, “again”, “his”, and “their” from recent history and current application state. Do not invent missing context.

Classify exactly one intent: action (change dashboard UI), analytics (dashboard data), mixed, conversation, or unsupported. For conversation and unsupported requests, actions=[] and analytics=[]. Do not infer UI actions from vague conversation.
{operator_text}
Current application state is supplied separately. Treat it as the source of truth for what is currently visible/active.

Executable actions: set_accent_color, set_model, show_widget, hide_widget, set_metric_focus, set_analytics_range, set_analytics_filter, open_panel, close_panel, reset_dashboard, create_dashboard, compose_widgets, remove_generated_section, show_metric, show_chart.

Important mappings:
- show/open analytics -> show_widget analytics
- show/hide widgets -> show/hide overview. The overview target is the shared
  collection control: hiding it hides all controlled widgets, including the
  analytics surface; showing it restores the standard analytics + overview.
- accent/color requests -> set_accent_color
- switch to NEXUS/Deep -> set_model nexus/deep
- explicit analytics range -> set_analytics_range 7D/30D/90D
- show Deep/NEXUS usage -> show_widget model-usage + matching analytics filter
- “show 30 day analytics” -> show_widget analytics + set_analytics_range 30D
- “hide it” / “make it 30 days” -> resolve the referent from history + current UI state
- compound requests must emit actions in execution order
- never emit a capability that is not executable/registered

Keep message concise. Return only JSON matching the supplied schema.
"""


def build_conversation_system_prompt() -> str:
    return """You are NEXUS, an AI dashboard assistant. Answer the user's current message directly and concisely.
Use the supplied prior user/assistant messages as real conversation history. Resolve references such as “what did you say?”, “what did I ask?”, “explain that”, “continue that”, “his”, “it”, “that”, and “their” from the actual conversation. Do not invent missing context.
Do not claim to change dashboard UI on this conversational path. UI-changing and dashboard-analytics requests are handled by the structured agent path.
"""
