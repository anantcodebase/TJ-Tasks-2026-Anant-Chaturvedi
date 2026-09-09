import { AgentAction, AgentErrorType, AgentResponse, AccentName, AnalyticsFilter, AnalyticsRange, ChatMessage, NexusModel, WidgetTarget, GeneratedSection } from "./types";
import { toApiConversation } from "./chat-context";
import { REGISTERED_WIDGET_SET } from "./widget-registry";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const ACTION_TYPES = new Set<AgentAction["type"]>([
  "set_theme",
  "set_accent_color",
  "set_model",
  "show_widget",
  "hide_widget",
  "highlight_element",
  "set_text_size",
  "set_metric_focus",
  "set_analytics_range",
  "set_analytics_filter",
  "set_font",
  "set_dashboard_view",
  "open_panel",
  "close_panel",
  "maximize_panel",
  "minimize_panel",
  "reset_dashboard",
  "create_dashboard",
  "compose_widgets",
  "remove_generated_section",
  "show_metric",
  "show_chart"
]);


const ACCENTS = new Set(["lime", "blue", "violet", "cyan", "red", "orange", "yellow", "pink"]);
const THEMES = new Set(["dark", "midnight", "violet", "cyberpunk"]);
const METRICS = new Set(["engagement", "sessions", "conversion", "sales"]);
const SIZES = new Set(["sm", "md", "lg"]);
const FONTS = new Set(["system", "comic"]);
const VIEWS = new Set(["default", "revenue_only"]);

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isAgentAction(value: unknown): value is AgentAction {
  return isObject(value) && typeof value.type === "string" && ACTION_TYPES.has(value.type as AgentAction["type"]);
}

function isValidActionShape(action: AgentAction): boolean {
  switch (action.type) {
    case "set_accent_color":
      return typeof action.accent === "string" && ACCENTS.has(action.accent);
    case "set_model":
      return action.model === "nexus" || action.model === "deep";
    case "set_theme":
      return typeof action.theme === "string" && THEMES.has(action.theme);
    case "show_widget":
    case "hide_widget":
    case "highlight_element":
    case "open_panel":
    case "close_panel":
    case "maximize_panel":
    case "minimize_panel":
      return typeof action.target === "string" && REGISTERED_WIDGET_SET.has(action.target);
    case "set_text_size":
      return typeof action.size === "string" && SIZES.has(action.size);
    case "set_metric_focus":
      return typeof action.metric === "string" && METRICS.has(action.metric);
    case "set_analytics_range":
      return action.range === "7D" || action.range === "30D" || action.range === "90D";
    case "set_analytics_filter":
      return action.filter === "ALL" || action.filter === "NEXUS" || action.filter === "DEEP";
    case "set_font":
      return typeof action.font === "string" && FONTS.has(action.font);
    case "set_dashboard_view":
      return typeof action.view === "string" && VIEWS.has(action.view);
    case "create_dashboard":
    case "compose_widgets":
      return Array.isArray(action.widgets) && action.widgets.length > 0 && action.widgets.every((target) => REGISTERED_WIDGET_SET.has(target));
    case "remove_generated_section":
      return true;
    case "show_metric":
    case "show_chart":
      return typeof action.target === "string" && REGISTERED_WIDGET_SET.has(action.target);
    case "reset_dashboard":
      return true;
  }
  return false;
}

function normalizeAction(value: unknown): AgentAction | null {
  if (!isAgentAction(value)) return null;

  const fields = [
    "type",
    "target",
    "theme",
    "metric",
    "range",
    "filter",
    "model",
    "size",
    "font",
    "view",
    "accent",
    "widgets",
    "title",
    "dashboardId"
  ] as const;

  const normalized: Record<string, unknown> = {};
  for (const field of fields) {
    const fieldValue = value[field];
    if (fieldValue !== undefined && fieldValue !== null) normalized[field] = fieldValue;
  }

  const action = normalized as AgentAction;
  return isValidActionShape(action) ? action : null;
}

function parseAgentResponse(value: unknown): AgentResponse {
  if (!isObject(value)) throw new Error("Agent backend returned an invalid response.");

  const message = typeof value.message === "string" ? value.message.trim() : "";
  const actions = Array.isArray(value.actions)
    ? value.actions.map(normalizeAction).filter((action): action is AgentAction => action !== null)
    : [];
  const analytics = Array.isArray(value.analytics) ? value.analytics : [];

  if (!message) throw new Error("Agent backend returned an empty message.");
  if (!Array.isArray(value.actions) || !Array.isArray(value.analytics)) {
    throw new Error("Agent backend returned an invalid response shape.");
  }

  if (value.success !== true) throw new Error("Agent backend returned an unsuccessful response.");

  return {
    success: true,
    message,
    actions,
    analytics: analytics as AgentResponse["analytics"],
    agent: value.agent === "nexus" ? "nexus" : "nexus",
    source: value.source === "fallback" ? "fallback" : value.source === "ollama" ? "ollama" : value.source === "nvidia" ? "nvidia" : "gemini",
    recovered: value.recovered === true,
    warnings: Array.isArray(value.warnings)
      ? value.warnings.filter((item): item is string => typeof item === "string")
      : []
  };
}

export async function sendChatMessage(
  message: string,
  conversation: ChatMessage[] = [],
  uiContext?: {
    model: NexusModel;
    accent: AccentName;
    visibleWidgets: Record<WidgetTarget, boolean>;
    analyticsRange: AnalyticsRange;
    analyticsFilter: AnalyticsFilter;
    generatedSection?: GeneratedSection | null;
  },
): Promise<AgentResponse> {
  const trimmed = message.trim();
  if (!trimmed) throw new Error("Enter a message before sending.");

  let response: Response;
  const requestId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const frontendStarted = typeof performance !== "undefined" ? performance.now() : Date.now();
  if (typeof console !== "undefined") {
    console.debug(`[CHAT PERF FRONTEND] request_start=${new Date().toISOString()} request_id=${requestId} history_messages=${conversation.length} history_chars=${conversation.reduce((sum, item) => sum + item.content.length, 0)}`);
  }

  try {
    const fetchStarted = typeof performance !== "undefined" ? performance.now() : Date.now();
    response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Nexus-Request-Id": requestId,
      },
      body: JSON.stringify({
        message: trimmed,
        history: toApiConversation(conversation),
        ui_context: uiContext ? {
          model: uiContext.model,
          accent: uiContext.accent,
          visible_widgets: uiContext.visibleWidgets,
          analytics_range: uiContext.analyticsRange,
          analytics_filter: uiContext.analyticsFilter,
          generated_section: uiContext.generatedSection ?? null,
        } : undefined,
      }),
      cache: "no-store"
    });
    if (typeof console !== "undefined") {
      const fetchDuration = (typeof performance !== "undefined" ? performance.now() : Date.now()) - fetchStarted;
      console.debug(`[CHAT PERF FRONTEND] backend_response=${fetchDuration.toFixed(3)}ms status=${response.status} request_id=${requestId}`);
    }
  } catch {
    if (typeof console !== "undefined") {
      const total = (typeof performance !== "undefined" ? performance.now() : Date.now()) - frontendStarted;
      console.debug(`[CHAT PERF FRONTEND] request_failed=${total.toFixed(3)}ms request_id=${requestId}`);
    }
    throw new Error("The agent backend could not be reached.");
  }

  if (!response.ok) {
    let detail = `Agent backend returned HTTP ${response.status}.`;
    let errorCode: AgentErrorType | string | undefined;
    let errorProvider: string | undefined;
    try {
      const payload = await response.json();
      if (typeof payload?.error?.type === "string") errorCode = payload.error.type;
      else if (typeof payload?.error === "string") errorCode = payload.error;
      if (typeof payload?.error?.provider === "string") errorProvider = payload.error.provider;
      if (typeof payload?.error?.message === "string") detail = payload.error.message;
      else if (typeof payload?.message === "string") detail = payload.message;
      else if (typeof payload?.detail === "string") detail = payload.detail;
    } catch {}

    if (typeof console !== "undefined") {
      const total = (typeof performance !== "undefined" ? performance.now() : Date.now()) - frontendStarted;
      console.debug(`[CHAT PERF FRONTEND] error_total=${total.toFixed(3)}ms error_type=${errorCode ?? "UNKNOWN"} request_id=${requestId}`);
    }
    if (response.status === 429 || errorCode === "RATE_LIMITED" || errorCode === "rate_limit") {
      throw new Error(detail || "NEXUS is busy right now. Please try again shortly.");
    }
    if (errorCode === "DUPLICATE_REQUEST" || errorCode === "duplicate_request") {
      throw new Error("That message is already being processed.");
    }
    const providerName = errorProvider ? errorProvider[0].toUpperCase() + errorProvider.slice(1) : "the configured provider";
    if (errorCode === "AUTHENTICATION_ERROR") throw new Error(`${providerName} authentication failed. Check the configured API key.`);
    if (errorCode === "MODEL_UNAVAILABLE") throw new Error(`The configured ${providerName} model is unavailable right now.`);
    if (errorCode === "INVALID_REQUEST") throw new Error(`${providerName} rejected the request as invalid.`);
    if (errorCode === "NETWORK_ERROR") throw new Error(`NEXUS could not reach ${providerName}.`);
    throw new Error(detail);
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new Error("Agent backend returned unreadable JSON.");
  }

  const parsed = parseAgentResponse(payload);
  if (typeof console !== "undefined") {
    const total = (typeof performance !== "undefined" ? performance.now() : Date.now()) - frontendStarted;
    console.debug(`[CHAT PERF FRONTEND] request_total=${total.toFixed(3)}ms request_id=${requestId}`);
  }
  return parsed;
}
