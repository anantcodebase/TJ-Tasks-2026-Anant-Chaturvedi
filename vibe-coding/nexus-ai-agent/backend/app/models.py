from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


UIActionType = Literal[
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
    "show_chart",
]

RequestIntent = Literal[
    "action",
    "analytics",
    "conversation",
    "unsupported",
    "mixed",
]

AnalyticsOperation = Literal["fetch", "summarize"]
AnalyticsMetric = Literal["engagement", "sessions", "conversion", "sales"]
ThemeName = Literal["dark", "midnight", "violet", "cyberpunk"]
AccentName = Literal["lime", "blue", "violet", "cyan", "red", "orange", "yellow", "pink"]
NexusModel = Literal["nexus", "deep"]
AnalyticsRange = Literal["7D", "30D", "90D"]
AnalyticsFilter = Literal["ALL", "NEXUS", "DEEP"]
TextSize = Literal["sm", "md", "lg"]
FontName = Literal["system", "comic"]
DashboardView = Literal["default", "revenue_only"]
WidgetTarget = Literal[
    "analytics",
    "overview",
    "revenue",
    "engagement-chart",
    "metrics",
    "activity",
    "active-users",
    "messages",
    "model-usage",
    "response-time",
    "system-status",
    "session-information",
    "telemetry",
    "model-comparison",
    "performance",
    "usage-trends",
    "chat",
]
MetricFocus = Literal["engagement", "sessions", "conversion", "sales"]


class UIAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: UIActionType
    target: WidgetTarget | None = None
    accent: AccentName | None = None
    model: NexusModel | None = None
    theme: ThemeName | None = None
    metric: MetricFocus | None = None
    range: AnalyticsRange | None = None
    filter: AnalyticsFilter | None = None
    size: TextSize | None = None
    font: FontName | None = None
    view: DashboardView | None = None
    widgets: list[WidgetTarget] | None = Field(default=None, max_length=12)
    title: str | None = Field(default=None, max_length=120)
    dashboardId: str | None = Field(default=None, max_length=80)


class AnalyticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: AnalyticsOperation
    metric: AnalyticsMetric
    period: Literal["7d"] = "7d"


class AgentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: RequestIntent = "conversation"
    message: str = Field(default="", max_length=1000)
    actions: list[UIAction] = Field(default_factory=list, max_length=12)
    analytics: list[AnalyticsRequest] = Field(default_factory=list, max_length=4)


class ConversationMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class GeneratedSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=120)
    widgets: list[WidgetTarget] = Field(default_factory=list, max_length=12)


class ChatUIContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: NexusModel = "nexus"
    accent: AccentName = "lime"
    visible_widgets: dict[WidgetTarget, bool] = Field(default_factory=dict, max_length=20)
    analytics_range: AnalyticsRange = "7D"
    analytics_filter: AnalyticsFilter = "ALL"
    generated_section: GeneratedSection | None = None


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000)
    history: list[ConversationMessage] = Field(default_factory=list, max_length=24)
    ui_context: ChatUIContext | None = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be empty.")
        return value


class AnalyticsPoint(BaseModel):
    day: str
    engagement: float
    sessions: int
    conversion: float
    sales: float


class AnalyticsResult(BaseModel):
    metric: AnalyticsMetric
    period: str
    values: list[float]
    labels: list[str]
    summary: str


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    message: str
    actions: list[UIAction]
    analytics: list[AnalyticsResult]
    agent: Literal["nexus"] = "nexus"
    source: Literal["gemini", "ollama", "nvidia", "fallback"]
    recovered: bool = False
    warnings: list[str] = Field(default_factory=list)
