from __future__ import annotations

import re
import time

from app.agent.fallback import fallback_plan
from app.agent.parser import parse_conversation_output, parse_model_output
from app.agent.prompts import build_plan_system_prompt, build_conversation_system_prompt, plan_schema, compact_ui_context
from app.config import settings
from app.llm.factory import create_llm_client
from app.llm.errors import ProviderError
from app.models import AgentPlan, AnalyticsResult, ChatResponse, ChatUIContext, ConversationMessage
from app.tools.analytics import query_analytics
from app.perf import get_trace

EXECUTABLE_ACTION_TYPES = {
    "set_accent_color", "set_model", "show_widget", "hide_widget",
    "set_metric_focus", "set_analytics_range", "set_analytics_filter",
    "open_panel", "close_panel", "maximize_panel", "minimize_panel",
    "reset_dashboard", "create_dashboard", "compose_widgets",
    "remove_generated_section", "show_metric", "show_chart",
}


UI_TERMS = re.compile(r"\b(background|theme|dashboard|revenue|font|text|chart|card|metric|comic\s+sans|accent|color|colour|buttons?|interface|ui|midnight|cyberpunk|dark\s+mode|violet\s+theme|purple\s+theme|widgets?|panel|model\s+usage|response\s*time|latency|active\s+users|system\s+status|system\s+performance|model\s+comparison|activity|telemetry|session|compare\s+models|performance|usage\s+trends)\b", re.I)
UI_VERBS = re.compile(r"\b(make|change|set|hide|show|increase|decrease|enlarge|shrink|reset|switch|highlight|turn|apply|use|give)\b", re.I)
ANALYTICS_TERMS = re.compile(r"\b(analytics|sales|engagement|sessions|conversion|metrics|data|revenue|model\s+usage|usage\s+data|usage\s+trends|response\s*time|latency|active\s+users|today(?:'|’)?s\s+activity)\b", re.I)
ANALYTICS_CUES = re.compile(r"\b(show|give|tell|summar(?:y|ize|ise)|how|what|analy(?:ze|sis)|doing|this\s+week|week)\b", re.I)
UNSUPPORTED_REQUEST = re.compile(
    r"\b(write|build|create|run|execute|open|send|download)\b.*(?:c\+\+|python|javascript|shell|database|github|instagram|linkedin|file|email|program)",
    re.I,
)


ACCENT_WORDS = re.compile(r"\b(lime|green|blue|violet|purple|cyan|teal|red|orange|yellow|pink|magenta)\b", re.I)
THEME_WORDS = re.compile(r"\b(midnight|cyberpunk|dark\s+mode)\b", re.I)

UNSUPPORTED_DATA_REQUEST = re.compile(
    r"\b(delete|remove|wipe|purge)\b.*\b(?:analytics|data|database)\b",
    re.I,
)


def request_has_ui_intent(text: str) -> bool:
    value = text.strip()
    if re.search(r"\b(reset|show|display|reveal|hide|close|open|switch|change|set|make|use|give|add|remove|bring|load|build|create|maximize|minimize)\b", value, re.I):
        if UI_TERMS.search(value):
            return True
    if request_has_accent_intent(value):
        return True
    if re.search(r"\b(switch|change|set|use|make)\b.*\b(nexus(?:\s+deep)?|deep|model)\b", value, re.I):
        return True
    return bool(re.search(r"\b(show|open|hide|close|display)\b.*\b(analytics|widgets?|panel)\b", value, re.I))


def request_has_analytics_intent(text: str) -> bool:
    value = text.strip()
    if re.search(r"\b(show|open|display|give|see|view|hide|close|summar(?:y|ize|ise)|analy(?:ze|sis)|compare)\b.*\b(analytics|usage|metrics|data|response\s*time|latency|active\s+users|activity|performance|trend)\b", value, re.I):
        return True
    return bool(ANALYTICS_TERMS.search(value) and ANALYTICS_CUES.search(value))


def request_is_unsupported(text: str) -> bool:
    return bool(UNSUPPORTED_REQUEST.search(text) or UNSUPPORTED_DATA_REQUEST.search(text))


def request_has_accent_intent(text: str) -> bool:
    if not ACCENT_WORDS.search(text):
        return False
    direct = re.search(r"\b(?:use|choose|pick|switch(?:\s+to)?)\s+(?:an?\s+)?(?:lime|green|blue|violet|purple|cyan|teal|red|orange|yellow|pink|magenta)\b", text, re.I)
    explicit = re.search(r"\b(?:accent|accents|color|colors|colour|colours|button|buttons|dashboard|interface|ui|everything)\b", text, re.I)
    verb = re.search(r"\b(?:make|change|set|use|apply|switch|give|turn|choose|pick)\b", text, re.I)
    return bool(direct or (explicit and verb))


def request_has_theme_intent(text: str) -> bool:
    # NEXUS currently exposes accent color, not a general theme editor. Only
    # explicit supported environment themes count as theme intent. Phrases
    # like "theme color" stay mapped to the accent-color capability.
    return bool(re.search(r"\b(?:switch|change|set|use|make)\b.*\b(?:cyberpunk|midnight|dark\s+mode)\b", text, re.I) or re.search(r"\b(?:cyberpunk|midnight|dark\s+mode)\b", text, re.I))


def enforce_request_boundary(
    plan: AgentPlan,
    user_message: str,
    history: list[ConversationMessage] | None = None,
    ui_context: ChatUIContext | None = None,
) -> tuple[AgentPlan, list[str]]:
    warnings: list[str] = []
    ui_intent = request_has_ui_intent(user_message)
    analytics_intent = request_has_analytics_intent(user_message)
    accent_intent = request_has_accent_intent(user_message)
    theme_intent = request_has_theme_intent(user_message)
    unsupported = request_is_unsupported(user_message)
    history = [item if isinstance(item, ConversationMessage) else ConversationMessage.model_validate(item) for item in (history or [])]
    last_user = next((item.content for item in reversed(history) if item.role == "user"), "")
    contextual_reference = bool(re.search(r"\b(?:it|this|that|its|their|same|again)\b", user_message, re.I)) and (request_has_ui_intent(last_user) or request_has_analytics_intent(last_user))
    referential_action_allowed = contextual_reference and bool(plan.actions)

    if plan.actions:
        if accent_intent and not theme_intent:
            filtered_theme = [action for action in plan.actions if action.type != "set_theme"]
            if len(filtered_theme) != len(plan.actions):
                warnings.append("Theme actions were removed because the user requested an accent without changing the theme.")
                plan.actions = filtered_theme
        if theme_intent and not accent_intent:
            filtered_accent = [action for action in plan.actions if action.type != "set_accent_color"]
            if len(filtered_accent) != len(plan.actions):
                warnings.append("Accent actions were removed because the user requested a theme change without an accent change.")
                plan.actions = filtered_accent

    if plan.actions and not ui_intent and not analytics_intent and not referential_action_allowed:
        warnings.append("UI actions were removed because the user did not request a dashboard operation.")
        plan.actions = []

    if plan.actions and analytics_intent:
        analytics_visual_actions = {
            "show_widget:analytics",
            "hide_widget:analytics",
            "open_panel:analytics",
            "close_panel:analytics",
            "show_widget:model-usage",
            "show_widget:response-time",
            "show_widget:active-users",
            "show_widget:activity",
            "show_widget:performance",
            "show_widget:usage-trends",
            "show_widget:model-comparison",
            "hide_widget:model-usage",
            "hide_widget:response-time",
            "hide_widget:active-users",
            "hide_widget:activity",
            "hide_widget:performance",
            "hide_widget:usage-trends",
            "hide_widget:model-comparison",
            "set_metric_focus:engagement",
            "set_metric_focus:sessions",
            "set_metric_focus:conversion",
            "set_metric_focus:sales",
            "set_analytics_range:",
            "set_analytics_filter:",
        }
        explicit_reset = bool(re.search(r"\breset\b", user_message, re.I))
        retained_actions = []
        removed_actions = 0
        for action in plan.actions:
            key = f"{action.type}:{action.target or action.metric or ''}"
            analytics_action = action.type in {"set_analytics_range", "set_analytics_filter"}
            permitted = key in analytics_visual_actions or analytics_action
            if action.type == "reset_dashboard":
                permitted = explicit_reset
            # A model/accent request can legitimately be combined with analytics.
            if action.type in {"set_model", "set_accent_color"}:
                permitted = ui_intent or referential_action_allowed
            if action.type in {"create_dashboard", "compose_widgets", "remove_generated_section", "show_metric", "show_chart"}:
                permitted = ui_intent or referential_action_allowed
            if analytics_intent and action.type in {"show_metric", "show_chart"}:
                permitted = True
            if analytics_intent and action.type in {"show_widget", "hide_widget", "open_panel", "close_panel"} and action.target in {"analytics", "model-usage", "response-time", "active-users", "activity", "performance", "usage-trends", "model-comparison", "system-status", "session-information", "telemetry", "engagement-chart"}:
                permitted = True
            if permitted:
                retained_actions.append(action)
            else:
                removed_actions += 1
        if removed_actions:
            warnings.append("UI actions unrelated to the user's analytics request were removed.")
        plan.actions = retained_actions

    if not analytics_intent and plan.analytics:
        warnings.append("Analytics requests were removed because the user did not explicitly request dashboard data.")
        plan.analytics = []

    if unsupported and not ui_intent and not analytics_intent:
        plan.intent = "unsupported"
    elif ui_intent and analytics_intent:
        non_analytics_actions = [
            action for action in plan.actions
            if action.type not in {
                "show_widget", "hide_widget", "open_panel", "close_panel",
                "set_metric_focus", "set_analytics_range", "set_analytics_filter",
                "show_metric", "show_chart", "create_dashboard", "compose_widgets", "remove_generated_section",
            }
        ]
        plan.intent = "mixed" if non_analytics_actions else "analytics"
    elif ui_intent:
        plan.intent = "action"
    elif analytics_intent:
        plan.intent = "analytics"
    else:
        plan.intent = "conversation"

    return plan, warnings


def ensure_message(plan: AgentPlan, user_message: str, analytics: list[AnalyticsResult]) -> str:
    # The backend can validate an action, but it cannot know whether the
    # browser committed the shared UI state. Action success language belongs
    # exclusively to the frontend executor after that verification.
    if plan.actions:
        return "The requested dashboard action is ready to apply."

    if analytics:
        return " ".join(item.summary for item in analytics[:2]).strip()

    message = plan.message.strip()
    if message:
        return message

    if plan.intent == "unsupported":
        return "I don't have a capability for that request yet."

    return "I understood the request."


class AgentService:
    def __init__(self) -> None:
        self.llm = create_llm_client()

    async def run(
        self,
        user_message: str,
        history: list[ConversationMessage] | None = None,
        ui_context: ChatUIContext | None = None,
    ) -> ChatResponse:
        context_started = time.perf_counter()
        history = [item if isinstance(item, ConversationMessage) else ConversationMessage.model_validate(item) for item in (history or [])][-24:]
        if ui_context is not None and not isinstance(ui_context, ChatUIContext):
            ui_context = ChatUIContext.model_validate(ui_context)
        trace = get_trace()
        if trace is not None:
            trace.context_build = time.perf_counter() - context_started
            trace.history_messages = len(history)
            trace.history_chars = sum(len(item.content) for item in history)
        agent_started = time.perf_counter()
        warnings: list[str] = []
        source = settings.ai_provider.lower() if settings.ai_provider.lower() in {"ollama", "nvidia"} else "gemini"
        recovered = False

        # Avoid the expensive structured-planning call for ordinary conversation.
        # UI/analytics requests still go through the strict planner.
        needs_planner = (
            request_has_ui_intent(user_message)
            or request_has_analytics_intent(user_message)
            or request_is_unsupported(user_message)
            or bool(re.search(r"\b(?:hide|close|dismiss|remove|change|switch|set|show|open|continue|again|same|it|that|this|its|their)\b", user_message, re.I) and history and any(item.role == "user" for item in history))
        )

        plan: AgentPlan | None = None
        if not needs_planner:
            try:
                raw = await self.llm.generate_message(
                    build_conversation_system_prompt(),
                    user_message,
                    compact_ui_context(ui_context.model_dump(mode="json") if ui_context else None, user_message),
                    history=history,
                )
                message, parser_warnings, recovered = parse_conversation_output(raw)
                warnings.extend(parser_warnings)
                if message is None:
                    raise ValueError("Conversation response could not be parsed safely.")
                if trace is not None:
                    trace.agent = time.perf_counter() - agent_started
                return ChatResponse(
                    message=message, actions=[], analytics=[], source=source,
                    recovered=recovered, warnings=warnings,
                )
            except ProviderError:
                if trace is not None:
                    trace.agent = time.perf_counter() - agent_started
                raise
            except Exception as exc:
                if not settings.allow_fallback:
                    raise ProviderError(
                        source,
                        "PROVIDER_ERROR",
                        f"{source.title()} returned an unusable conversation response.",
                        provider_code=type(exc).__name__,
                    ) from exc
                # The recovery planner is an explicitly configured local mode,
                # never a silent substitute for a remote provider. It cannot
                # execute UI changes itself; browser verification still decides
                # whether any proposed action is confirmed.
                recovered_plan = fallback_plan(user_message, history=history, ui_context=ui_context)
                return ChatResponse(
                    message=ensure_message(recovered_plan, user_message, []), actions=[], analytics=[], source="fallback", recovered=True,
                    warnings=[f"Local recovery mode was used after {source} failed: {type(exc).__name__}"],
                )
        else:
            try:
                raw = await self.llm.generate_json(
                    build_plan_system_prompt(user_message),
                    user_message,
                    plan_schema(),
                    history=history,
                    context=compact_ui_context(ui_context.model_dump(mode="json") if ui_context else None, user_message),
                )
                plan, parser_warnings, recovered = parse_model_output(raw)
                warnings.extend(parser_warnings)
                if plan is None:
                    raise ValueError("The LLM output could not be converted into a safe plan.")
            except ProviderError:
                if trace is not None:
                    trace.agent = time.perf_counter() - agent_started
                raise
            except Exception as exc:
                if not settings.allow_fallback:
                    raise ProviderError(
                        source,
                        "PROVIDER_ERROR",
                        f"{source.title()} returned an unusable structured response.",
                        provider_code=type(exc).__name__,
                    ) from exc
                source = "fallback"
                recovered = True
                warnings.append(f"Local recovery mode was used after the provider failed: {type(exc).__name__}.")
                plan = fallback_plan(user_message, history=history, ui_context=ui_context)

        plan, boundary_warnings = enforce_request_boundary(plan, user_message, history=history, ui_context=ui_context)
        warnings.extend(boundary_warnings)

        # Only executable capabilities leave the backend. Unsupported/legacy
        # action types are stripped before the frontend ever sees them.
        executable = []
        for action in plan.actions:
            if action.type in EXECUTABLE_ACTION_TYPES:
                executable.append(action)
            else:
                warnings.append(f"Action {action.type!r} was rejected because it is not executable.")
        plan.actions = executable

        analytics_results: list[AnalyticsResult] = []
        tools_started = time.perf_counter()
        for request in plan.analytics:
            try:
                analytics_results.append(await query_analytics(request.metric))
            except Exception as exc:
                warnings.append(f"Analytics request failed for {request.metric}: {type(exc).__name__}.")

        if trace is not None:
            trace.tools = time.perf_counter() - tools_started
            trace.agent = time.perf_counter() - agent_started
        response_build_started = time.perf_counter()
        final_message = ensure_message(plan, user_message, analytics_results)

        result = ChatResponse(
            message=final_message.strip() or "The request completed, but the agent did not produce a usable message.",
            actions=plan.actions,
            analytics=analytics_results,
            source=source,
            recovered=recovered,
            warnings=warnings,
        )
        if trace is not None:
            trace.response_build = time.perf_counter() - response_build_started
        return result
