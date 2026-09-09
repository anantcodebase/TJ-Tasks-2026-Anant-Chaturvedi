from __future__ import annotations

import re

from app.models import AgentPlan, AnalyticsRequest, ChatUIContext, ConversationMessage, UIAction


ACCENT_ALIASES = {
    "lime": "lime", "acid green": "lime", "green": "lime",
    "blue": "blue", "electric blue": "blue",
    "violet": "violet", "purple": "violet",
    "cyan": "cyan", "teal": "cyan",
    "red": "red", "orange": "orange", "yellow": "yellow",
    "pink": "pink", "magenta": "pink",
}

WIDGET_ALIASES = {
    "analytics": "analytics",
    "widgets": "overview",
    "widget": "overview",
    "dashboard stats": "analytics",
    "usage data": "analytics",
    "activity": "activity",
    "today's activity": "activity",
    "todays activity": "activity",
    "activity overview": "activity",
    "active users": "active-users",
    "users online": "active-users",
    "messages": "messages",
    "messages today": "messages",
    "model usage": "model-usage",
    "model mix": "model-usage",
    "usage distribution": "model-usage",
    "model distribution": "model-usage",
    "deep usage": "model-usage",
    "response time": "response-time",
    "response-time": "response-time",
    "latency": "response-time",
    "system status": "system-status",
    "status": "system-status",
    "session information": "session-information",
    "session info": "session-information",
    "telemetry": "telemetry",
    "system telemetry": "telemetry",
    "model comparison": "model-comparison",
    "compare models": "model-comparison",
    "performance": "performance",
    "performance dashboard": "performance",
    "system performance": "performance",
    "usage trends": "usage-trends",
    "trend": "usage-trends",
}


def _detect_accent(value: str) -> str | None:
    for alias, accent in ACCENT_ALIASES.items():
        if not re.search(rf"\b{re.escape(alias)}\b", value):
            continue
        explicit = re.search(r"\b(?:accent|accents|color|colors|colour|colours)\b", value)
        target = re.search(r"\b(?:dashboard|interface|ui|buttons|button|theme|everything)\b", value)
        verb = re.search(r"\b(?:make|change|set|use|apply|switch|give|turn|choose|pick)\b", value)
        direct = re.search(rf"\b(?:use|choose|pick)\s+(?:an?\s+)?{re.escape(alias)}\b", value)
        if explicit and (verb or target): return accent
        if verb and target: return accent
        if direct: return accent
    return None


def _has_ui_intent(value: str) -> bool:
    if re.search(r"\breset\s+(?:(?:the)\s+)?(?:everything|all|dashboard|color|colour|accent)\b", value): return True
    if re.search(r"\b(?:show|open|display|hide|close|reveal|load|add|bring)\b.*\b(?:analytics|widgets?|panels?|model usage|response[- ]?time|active users|system status|activity|performance|telemetry|session information|model comparison|usage trends)\b", value): return True
    if _detect_accent(value): return True
    verbs = r"make|change|set|hide|show|open|display|build|create|increase|decrease|enlarge|shrink|reset|switch|highlight|turn|apply|use|add|bring|load"
    targets = r"background|theme|dashboard|revenue|font|text|chart|metric|card|comic\s+sans|buttons?|dark\s+mode|midnight|cyberpunk|violet\s+theme|purple\s+theme|widgets?|panel|model|nexus(?:\s+deep)?|system\s+status|session\s+information|model\s+comparison|usage\s+trends|performance|telemetry"
    return bool(re.search(rf"\b(?:{verbs})\b", value) and re.search(rf"\b(?:{targets})\b", value))


def _has_analytics_intent(value: str) -> bool:
    metric = r"analytics|sales|engagement|sessions|conversion|metrics|data|revenue|usage|response\s*time|latency|active\s+users|activity|performance|trend"
    if re.search(r"\b(?:hide|close|get rid of|dismiss|remove)\b", value) and not re.search(r"\b(?:show|open|display|give|tell|see|view|summar(?:y|ize|ise)|how|what|analy(?:ze|sis)|doing|compare|today|week)\b", value):
        return False
    cue = r"show|open|display|hide|close|give|tell|see|view|summar(?:y|ize|ise)|how|what|analy(?:ze|sis)|doing|compare|today|this\s+week|week"
    return bool(re.search(rf"\b(?:{metric})\b", value) and re.search(rf"\b(?:{cue})\w*\b", value))


def _has_unsupported_request(value: str) -> bool:
    return bool(
        re.search(r"\b(?:write|build|create|run|execute|open|send|download)\b.*(?:c\+\+|cpp|python|javascript|shell|database|github|instagram|linkedin|file|email|program)", value)
        or re.search(r"\b(?:delete|remove|wipe|purge)\b.*\b(?:analytics|data|database)\b", value)
    )


def _request_intent(value: str) -> str:
    ui, analytics, unsupported = _has_ui_intent(value), _has_analytics_intent(value), _has_unsupported_request(value)
    pure_analytics = bool(re.search(r"\b(?:show|open|display|give|see|view)\b.*\b(?:analytics|stats|data)\b", value)) and not _detect_accent(value)
    if ui and analytics: return "analytics" if pure_analytics else "mixed"
    if ui: return "action"
    if analytics: return "analytics"
    if unsupported: return "unsupported"
    return "conversation"


def _operator_response(value: str) -> str | None:
    if re.search(r"\b(?:who|what)\s+(?:made|built|created|owns?)\s+(?:you|this)\b", value): return "Anant Chaturvedi — aka XlaMus. He's the one who built me."
    if re.search(r"\b(?:who\s+is|tell\s+me\s+about)\s+(?:your\s+)?(?:owner|operator|creator|anant|xlamus)\b", value): return "My operator is Anant Chaturvedi, aka XlaMus. The Operator link in the header leads to his portfolio."
    if re.search(r"\b(?:who\s+is\s+anant|who\s+is\s+xlamus)\b", value): return "Anant Chaturvedi, aka XlaMus, is the creator/operator of NEXUS."
    return None


def _show_hide_widget(value: str, actions: list[UIAction]) -> None:
    hidden = bool(re.search(r"\b(?:hide|close|get rid of|dismiss|remove)\b", value))
    if re.search(r"\b(?:widgets?|all widgets|dashboard widgets)\b", value) and not hidden:
        actions.append(UIAction(type="show_widget", target="overview")); return
    if re.search(r"\b(?:widgets?|all widgets|dashboard widgets)\b", value) and hidden:
        actions.append(UIAction(type="hide_widget", target="overview")); return

    phrases = sorted(WIDGET_ALIASES.items(), key=lambda item: len(item[0]), reverse=True)
    for phrase, target in phrases:
        if not re.search(rf"\b{re.escape(phrase)}\b", value):
            continue
        if target == "analytics" and re.search(r"\b(?:data|usage data|stats)\b", value) and not _has_analytics_intent(value):
            continue
        actions.append(UIAction(type="hide_widget" if hidden else "show_widget", target=target))
        if target in {"active-users", "messages", "model-usage", "response-time", "activity", "performance", "usage-trends"}:
            break
        if target in {"analytics", "overview", "model-comparison", "system-status", "session-information", "telemetry"}:
            break




def _last_message(history: list[ConversationMessage], role: str) -> str | None:
    for item in reversed(history):
        if item.role == role:
            return item.content
    return None

def _contextual_fallback(value: str, history: list[ConversationMessage], ui_context: ChatUIContext | None) -> AgentPlan | None:
    last_user = _last_message(history, "user")
    last_assistant = _last_message(history, "assistant")

    if not history:
        return None

    if re.search(r"\b(?:what did you just say|what did you say|what were you talking about|what did you just tell me)\b", value):
        if last_assistant:
            return AgentPlan(intent="conversation", message=f'I just said: "{last_assistant}"')
        return AgentPlan(intent="conversation", message="I don't have an earlier response in this conversation.")

    if re.search(r"\b(?:what did i just ask|what did i ask|what was my last question)\b", value):
        if last_user:
            return AgentPlan(intent="conversation", message=f'You just asked: "{last_user}"')
        return AgentPlan(intent="conversation", message="You haven't asked me anything earlier in this conversation.")

    if re.search(r"\b(?:explain (?:that|this)|go deeper|continue that)\b", value) and last_assistant:
        return AgentPlan(intent="conversation", message=f'You are referring to my previous point: "{last_assistant}". I can continue from there.')

    if re.search(r"\b(?:hide|close|dismiss|remove)\s+it\b", value):
        if ui_context:
            visible = [target for target, is_visible in ui_context.visible_widgets.items() if is_visible]
            if len(visible) == 1:
                return AgentPlan(intent="action", message=f"{visible[0].replace('-', ' ').capitalize()} hidden.", actions=[UIAction(type="hide_widget", target=visible[0])])
        for previous in reversed(history):
            if previous.role == "user":
                match = re.search(r"\b(?:show|open|display|reveal|add)\s+(?:me\s+)?(?:the\s+)?([a-z0-9][a-z0-9 -]+)", previous.content, re.I)
                if match:
                    target = WIDGET_ALIASES.get(match.group(1).strip().lower())
                    if target:
                        return AgentPlan(intent="action", message=f"{target.replace('-', ' ').capitalize()} hidden.", actions=[UIAction(type="hide_widget", target=target)])
        if last_assistant:
            target = next((target for phrase, target in WIDGET_ALIASES.items() if phrase in last_assistant.lower()), None)
            if target:
                return AgentPlan(intent="action", message=f"{target.replace('-', ' ').capitalize()} hidden.", actions=[UIAction(type="hide_widget", target=target)])
        return AgentPlan(intent="conversation", message="I can't resolve what “it” refers to from the current context.")

    # Resolve short follow-up controls from the actual shared state. This is a
    # generic state/context fallback for provider/parser failures; it does not
    # contain phrase-specific answers. The normal Gemini path still receives
    # the complete history and UI context.
    range_match = re.search(r"\b(7|30|90)\s*(?:day|days|d)\b", value)
    if range_match and re.search(r"\b(?:make|change|set|switch|go|back|use)\b", value):
        target_range = f"{range_match.group(1)}D"
        analytics_context = bool(
            ui_context and (
                ui_context.visible_widgets.get("analytics", False)
                or ui_context.analytics_range in {"7D", "30D", "90D"}
            )
        ) or any(
            item.role == "user" and bool(re.search(r"\b(?:analytics|usage|metrics|response\s*time|latency|data|activity)\b", item.content, re.I))
            for item in history
        )
        if analytics_context:
            return AgentPlan(
                intent="action",
                message=f"Analytics range set to {target_range}.",
                actions=[UIAction(type="set_analytics_range", range=target_range)],
            )

    if re.search(r"\b(?:show|bring|open|display)\s+(?:it|that|this)(?:\s+again)?\b", value) or re.search(r"\b(?:show|bring|open|display)\s+it\s+again\b", value):
        hidden_candidates = []
        if ui_context:
            hidden_candidates = [target for target, is_visible in ui_context.visible_widgets.items() if not is_visible]
        if len(hidden_candidates) == 1:
            target = hidden_candidates[0]
            return AgentPlan(intent="action", message=f"{target.replace('-', ' ').capitalize()} is now visible.", actions=[UIAction(type="show_widget", target=target)])
        for previous in reversed(history):
            if previous.role != "user":
                continue
            match = re.search(r"\b(?:show|open|display|reveal|add)\s+(?:me\s+)?(?:the\s+)?([a-z0-9][a-z0-9 -]+)", previous.content, re.I)
            if match:
                target = WIDGET_ALIASES.get(match.group(1).strip().lower())
                if target:
                    return AgentPlan(intent="action", message=f"{target.replace('-', ' ').capitalize()} is now visible.", actions=[UIAction(type="show_widget", target=target)])

    if re.search(r"\b(?:only|just)\s+(?:show|use)\s+(?:the\s+)?(?:deep|nexus)\b", value):
        requested_filter = "DEEP" if re.search(r"\bdeep\b", value) else "NEXUS"
        filter_context = bool(ui_context and (ui_context.visible_widgets.get("model-usage", False) or ui_context.visible_widgets.get("analytics", False))) or any(
            item.role == "user" and bool(re.search(r"\b(?:model\s+usage|usage|distribution|mix|analytics)\b", item.content, re.I))
            for item in history
        )
        if filter_context:
            return AgentPlan(intent="action", message=f"Analytics filter set to {requested_filter}.", actions=[UIAction(type="set_analytics_filter", filter=requested_filter)])

    if re.search(r"\b(?:make|change|set|switch|use)\b.*\b(?:purple|violet|red|blue|green|lime|cyan|teal|orange|yellow|pink|magenta)\b", value) and re.search(r"\b(?:instead|it|that|this)\b", value):
        accent = _detect_accent(value)
        if accent and any(
            item.role == "user" and bool(re.search(r"\b(?:accent|color|colour|button|dashboard|interface|ui)\b", item.content, re.I))
            for item in history
        ):
            return AgentPlan(intent="action", message=f"{accent.capitalize()} accent applied.", actions=[UIAction(type="set_accent_color", accent=accent)])

    if re.search(r"\b(?:show|give)\s+me\s+(?:its|their)\s+response\s*time\b", value):
        if ui_context and ui_context.model == "deep":
            return AgentPlan(intent="action", message="Response-time chart added for NEXUS Deep.", actions=[UIAction(type="show_widget", target="response-time"), UIAction(type="set_analytics_filter", filter="DEEP")])
        return AgentPlan(intent="action", message="Response-time chart added.", actions=[UIAction(type="show_widget", target="response-time")])

    return None




def _compose_plan(value: str) -> AgentPlan | None:
    if re.search(r"\bswitch\s+to\s+(?:nexus\s+)?deep\b", value) and re.search(r"\b(?:show|give)\s+(?:me\s+)?(?:its|the)\s+response\s*time\b", value):
        return AgentPlan(
            intent="action",
            message="NEXUS Deep is now active. Response-time view opened for Deep.",
            actions=[
                UIAction(type="set_model", model="deep"),
                UIAction(type="set_analytics_filter", filter="DEEP"),
                UIAction(type="show_widget", target="response-time"),
            ],
        )
    if re.search(r"\b(?:make|change|set|use)\b.*\b(?:purple|violet)\b", value) and re.search(r"\b(?:open|show)\b.*\banalytics\b", value):
        return AgentPlan(
            intent="mixed",
            message="Violet accent applied and analytics opened.",
            actions=[
                UIAction(type="set_accent_color", accent="violet"),
                UIAction(type="show_widget", target="analytics"),
            ],
        )
    if re.search(r"\b(?:build|create|make)\b.*\bmodel\s+comparison\b", value):
        widgets = ["model-comparison", "model-usage", "response-time", "system-status"]
        return AgentPlan(intent="action", message="Model comparison composed from registered NEXUS signals.", actions=[UIAction(type="compose_widgets", title="Model comparison", widgets=widgets)])
    if re.search(r"\b(?:build|create|give\s+me|make)\b.*\b(?:activity\s+dashboard|dashboard.*today's\s+activity|today's\s+activity.*dashboard)\b", value):
        widgets = ["activity", "messages", "active-users", "model-usage"]
        return AgentPlan(intent="action", message="Today's activity dashboard composed from registered widgets.", actions=[UIAction(type="create_dashboard", title="Today's activity", widgets=widgets)])
    if re.search(r"\b(?:build|create|give\s+me|make)\b.*\bperformance\s+dashboard\b", value):
        widgets = ["response-time", "active-users", "system-status", "telemetry"]
        return AgentPlan(intent="action", message="Performance dashboard composed from registered widgets.", actions=[UIAction(type="create_dashboard", title="Performance dashboard", widgets=widgets)])
    if re.search(r"\b(?:remove|close|delete|hide)\b.*\b(?:temporary|generated)\s+dashboard\b", value):
        return AgentPlan(intent="action", message="Temporary dashboard removed.", actions=[UIAction(type="remove_generated_section")])
    return None

def fallback_plan(text: str, history: list[ConversationMessage] | None = None, ui_context: ChatUIContext | None = None) -> AgentPlan:
    value = text.strip().lower()
    history = [item if isinstance(item, ConversationMessage) else ConversationMessage.model_validate(item) for item in (history or [])]
    if ui_context is not None and not isinstance(ui_context, ChatUIContext):
        ui_context = ChatUIContext.model_validate(ui_context)
    composed = _compose_plan(value)
    if composed is not None:
        return composed
    contextual = _contextual_fallback(value, history, ui_context)
    if contextual is not None:
        return contextual
    intent = _request_intent(value)
    operator_message = _operator_response(value)
    if operator_message: return AgentPlan(intent="conversation", message=operator_message)

    if intent in {"conversation", "unsupported"}:
        if re.search(r"\b(?:hello|hi|hey)\b", value): message = "Online. Give me a dashboard problem worth solving."
        elif "joke" in value: message = "Why did the dashboard cross the server? To get to the other API. Terrible joke. Functional endpoint."
        elif "comic sans" in value and "think" in value: message = "Visually offensive. Technically harmless. I have no objection to the font existing."
        elif "prime minister of india" in value: message = "That is outside my dashboard scope. I can inspect Nexus's mock analytics, not act as a general knowledge service."
        elif "you are stupid" in value or value in {"tf", "bruh"}: message = "Noted. The dashboard remains untouched, which is more restraint than the average UI framework gets."
        elif intent == "unsupported": message = "I can operate this dashboard and its mock analytics, but I do not have a safe capability for that request."
        else: message = "I can handle conversation without touching the dashboard. No invented actions, no mystery button clicks."
        return AgentPlan(intent=intent, message=message)

    actions: list[UIAction] = []
    analytics: list[AnalyticsRequest] = []

    if re.search(r"\breset\s+(everything|all|dashboard)\b", value): actions.append(UIAction(type="reset_dashboard"))
    if re.search(r"\breset\s+(?:the\s+)?(?:color|colour|accent)\b", value): actions.append(UIAction(type="set_accent_color", accent="violet"))

    accent = _detect_accent(value)
    if accent and not any(a.type == "set_accent_color" for a in actions): actions.append(UIAction(type="set_accent_color", accent=accent))

    if re.search(r"\b(?:switch|change|set|use|make)\b.*\b(?:nexus\s+deep|deep)\b|\bdeep\s+mode\b", value):
        actions.append(UIAction(type="set_model", model="deep"))
    elif re.search(r"\b(?:switch|change|set|use|make)\b.*\b(?:nexus|balanced)\b", value):
        actions.append(UIAction(type="set_model", model="nexus"))

    if "cyberpunk" in value: actions.append(UIAction(type="set_theme", theme="cyberpunk"))
    elif "midnight" in value or "dark mode" in value: actions.append(UIAction(type="set_theme", theme="midnight"))
    elif "violet theme" in value or "purple theme" in value: actions.append(UIAction(type="set_theme", theme="violet"))
    if "comic sans" in value and re.search(r"\b(?:make|use|set|apply)\b", value): actions.append(UIAction(type="set_font", font="comic"))

    if "hide" in value and "everything" in value and "except" in value and "revenue" in value: actions.append(UIAction(type="set_dashboard_view", view="revenue_only"))
    else:
        if "hide" in value and "revenue" in value: actions.append(UIAction(type="hide_widget", target="revenue"))
        if re.search(r"\b(?:show|display|open)\b", value) and "revenue" in value: actions.append(UIAction(type="show_widget", target="revenue"))

    if re.search(r"\b(?:bigger|larger|increase)\b", value) and re.search(r"\b(?:font|text)\b", value): actions.append(UIAction(type="set_text_size", size="lg"))
    elif re.search(r"\b(?:smaller|compact)\b", value): actions.append(UIAction(type="set_text_size", size="sm"))

    _show_hide_widget(value, actions)

    if "highlight" in value and "chart" in value: actions.append(UIAction(type="highlight_element", target="engagement-chart"))

    metric: str | None = None
    for candidate in ("sales", "engagement", "sessions", "conversion"):
        if candidate in value: metric = candidate; break

    range_match = re.search(r"\b(7|30|90)\s*(?:day|days|d)\b", value)
    if range_match and _has_analytics_intent(value):
        actions.append(UIAction(type="set_analytics_range", range=f"{range_match.group(1)}D"))

    if re.search(r"\bdeep\b", value) and re.search(r"\b(?:usage|analytics|distribution|mix)\b", value):
        actions.append(UIAction(type="set_analytics_filter", filter="DEEP"))
        if not any(a.type == "show_widget" and a.target == "model-usage" for a in actions): actions.append(UIAction(type="show_widget", target="model-usage"))
    elif re.search(r"\bnexus\b", value) and re.search(r"\b(?:usage|analytics|distribution|mix)\b", value):
        actions.append(UIAction(type="set_analytics_filter", filter="NEXUS"))
        if not any(a.type == "show_widget" and a.target == "model-usage" for a in actions): actions.append(UIAction(type="show_widget", target="model-usage"))

    if metric and _has_analytics_intent(value):
        analytics.append(AnalyticsRequest(operation="fetch", metric=metric))
        if not any(a.type == "set_metric_focus" for a in actions): actions.append(UIAction(type="set_metric_focus", metric=metric))
        if re.search(r"\b(?:show|open|display|give|see)\b", value) and "analytics" in value and not any(a.type == "show_widget" and a.target == "analytics" for a in actions): actions.append(UIAction(type="show_widget", target="analytics"))

    if re.search(r"\b(?:summary|summarize|summarise)\b", value):
        summary_metric = metric or "engagement"
        analytics.append(AnalyticsRequest(operation="summarize", metric=summary_metric))
        if not any(a.type == "set_metric_focus" for a in actions): actions.append(UIAction(type="set_metric_focus", metric=summary_metric))

    if re.search(r"\b(?:performance dashboard|system performance)\b", value):
        if not any(a.type == "show_widget" and a.target == "performance" for a in actions): actions.append(UIAction(type="show_widget", target="performance"))

    if re.search(r"\bmodel comparison\b|\bcompare (?:the )?models?\b", value):
        if not any(a.type == "show_widget" and a.target == "model-comparison" for a in actions): actions.append(UIAction(type="show_widget", target="model-comparison"))

    if "comic sans" in value and actions: message = "I can do that. I won't respect you for it, but the font is changing."
    elif any(a.type == "set_model" for a in actions):
        chosen = next(a.model for a in reversed(actions) if a.type == "set_model" and a.model)
        message = f"{ 'NEXUS Deep' if chosen == 'deep' else 'NEXUS' } is now the active model."
    elif any(a.type == "show_widget" and a.target == "analytics" for a in actions): message = "Analytics panel opened."
    elif any(a.type == "hide_widget" and a.target == "analytics" for a in actions): message = "Analytics hidden."
    elif any(a.type == "show_widget" for a in actions):
        target = next(a.target for a in reversed(actions) if a.type == "show_widget" and a.target)
        labels = {"model-usage":"Model usage is now visible.", "response-time":"Response-time chart added.", "active-users":"Active users are now visible.", "activity":"Today's activity is now visible.", "performance":"Performance view opened.", "overview":"Widget overview opened.", "model-comparison":"Model comparison opened.", "system-status":"System status is now visible.", "session-information":"Session information is now visible.", "telemetry":"Telemetry is now visible.", "usage-trends":"Usage trends are now visible.", "messages":"Messages metric is now visible.", "revenue":"Revenue is now visible."}
        message = labels.get(target, "The requested widget is now visible.")
    elif any(a.type == "hide_widget" for a in actions): message = "The requested widget is hidden."
    elif any(a.type == "set_accent_color" for a in actions):
        chosen = next((a.accent for a in reversed(actions) if a.type == "set_accent_color"), "violet")
        message = f"{chosen.capitalize()} accent applied. The background stays dark."
    elif any(a.type == "set_analytics_range" for a in actions): message = "Analytics window updated."
    elif any(a.type == "set_analytics_filter" for a in actions): message = "Analytics model filter updated."
    elif analytics: message = f"I pulled the requested {analytics[-1].metric} data."
    elif any(a.type == "set_text_size" for a in actions): message = "Text size is up. Your eyes can stop filing complaints."
    elif any(a.type == "reset_dashboard" for a in actions): message = "Back to default."
    elif actions: message = "The requested dashboard change is done."
    else: message = "I understood the request, but there was no safe dashboard operation to execute."

    return AgentPlan(intent=intent, message=message, actions=actions, analytics=analytics)
