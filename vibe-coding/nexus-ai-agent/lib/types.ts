export type AgentStatus = "idle" | "thinking" | "executing" | "error";

export type NexusModel = "nexus" | "deep";
export type AnalyticsRange = "7D" | "30D" | "90D";
export type AnalyticsFilter = "ALL" | "NEXUS" | "DEEP";

export type WidgetTarget =
  | "analytics"
  | "overview"
  | "revenue"
  | "engagement-chart"
  | "metrics"
  | "activity"
  | "active-users"
  | "messages"
  | "model-usage"
  | "response-time"
  | "system-status"
  | "session-information"
  | "telemetry"
  | "model-comparison"
  | "performance"
  | "usage-trends"
  | "chat";

export type ActionType =
  | "set_theme"
  | "set_accent_color"
  | "set_model"
  | "show_widget"
  | "hide_widget"
  | "highlight_element"
  | "set_text_size"
  | "set_metric_focus"
  | "set_analytics_range"
  | "set_analytics_filter"
  | "set_font"
  | "set_dashboard_view"
  | "open_panel"
  | "close_panel"
  | "maximize_panel"
  | "minimize_panel"
  | "reset_dashboard"
  | "create_dashboard"
  | "compose_widgets"
  | "remove_generated_section"
  | "show_metric"
  | "show_chart";

export type AccentName = "lime" | "blue" | "violet" | "cyan" | "red" | "orange" | "yellow" | "pink";

export type AgentAction = {
  type: ActionType;
  target?: WidgetTarget;
  accent?: AccentName;
  model?: NexusModel;
  theme?: "dark" | "midnight" | "violet" | "cyberpunk";
  metric?: "engagement" | "sessions" | "conversion" | "sales";
  range?: AnalyticsRange;
  filter?: AnalyticsFilter;
  size?: "sm" | "md" | "lg";
  font?: "system" | "comic";
  view?: "default" | "revenue_only";
  widgets?: WidgetTarget[];
  title?: string;
  dashboardId?: string;
};

export type AnalyticsActionType = "fetch_analytics" | "summarize_analytics";

export type AnalyticsLogAction = {
  type: AnalyticsActionType;
  metric: "engagement" | "sessions" | "conversion" | "sales";
};

export type ActivityEvent = {
  id: string;
  label: string;
  detail?: string;
  status: "active" | "done" | "error";
  kind: "system" | "action" | "analytics";
};

export type AgentActionLog = AgentAction & {
  id: string;
  status: "queued" | "running" | "done" | "rejected";
  label: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "agent";
  content: string;
  actions?: AgentAction[];
};

export type AnalyticsPoint = {
  day: string;
  engagement: number;
  sessions: number;
  conversion: number;
  sales: number;
};

export type AnalyticsResult = {
  metric: "engagement" | "sessions" | "conversion" | "sales";
  period: string;
  values: number[];
  labels: string[];
  summary: string;
};

export type GeneratedSection = {
  id: string;
  title: string;
  widgets: WidgetTarget[];
};

export type AgentErrorType =
  | "RATE_LIMITED"
  | "AUTHENTICATION_ERROR"
  | "MODEL_UNAVAILABLE"
  | "INVALID_REQUEST"
  | "NETWORK_ERROR"
  | "PROVIDER_ERROR"
  | "DUPLICATE_REQUEST";

export type AgentResponse = {
  success: true;
  message: string;
  actions: AgentAction[];
  analytics: AnalyticsResult[];
  agent: "nexus";
  source: "gemini" | "ollama" | "nvidia" | "fallback";
  recovered: boolean;
  warnings: string[];
};
