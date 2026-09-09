import type { WidgetTarget } from "./types";

export type WidgetDefinition = {
  id: WidgetTarget;
  label: string;
  aliases: string[];
  description: string;
  kind: "panel" | "metric" | "chart" | "composite" | "surface";
  dataSource: "existing-ui";
};

export const WIDGET_REGISTRY: Record<WidgetTarget, WidgetDefinition> = {
  analytics: { id: "analytics", label: "Analytics", aliases: ["analytics", "dashboard stats", "usage data"], description: "Full analytics panel with range and model filters.", kind: "surface", dataSource: "existing-ui" },
  overview: { id: "overview", label: "Widget overview", aliases: ["widgets", "widget overview", "dashboard overview", "overview"], description: "Composed overview using existing NEXUS metric widgets.", kind: "composite", dataSource: "existing-ui" },
  revenue: { id: "revenue", label: "Revenue", aliases: ["revenue", "sales"], description: "Revenue widget when the existing dashboard exposes it.", kind: "metric", dataSource: "existing-ui" },
  "engagement-chart": { id: "engagement-chart", label: "Engagement chart", aliases: ["engagement chart", "engagement"], description: "Existing engagement visualization.", kind: "chart", dataSource: "existing-ui" },
  metrics: { id: "metrics", label: "Metrics", aliases: ["metrics", "metric"], description: "Existing dashboard metrics.", kind: "metric", dataSource: "existing-ui" },
  activity: { id: "activity", label: "Activity", aliases: ["activity", "today's activity", "todays activity", "activity overview"], description: "Current activity summary built from existing interface telemetry.", kind: "chart", dataSource: "existing-ui" },
  "active-users": { id: "active-users", label: "Active users", aliases: ["active users", "active-user", "users online"], description: "Active-user metric already present in the analytics surface.", kind: "metric", dataSource: "existing-ui" },
  messages: { id: "messages", label: "Messages", aliases: ["messages", "messages today"], description: "Messages-today metric already present in telemetry.", kind: "metric", dataSource: "existing-ui" },
  "model-usage": { id: "model-usage", label: "Model usage", aliases: ["model usage", "model mix", "usage distribution", "model distribution", "deep usage"], description: "Existing model-share visualization.", kind: "chart", dataSource: "existing-ui" },
  "response-time": { id: "response-time", label: "Response time", aliases: ["response time", "response-time", "latency"], description: "Existing response-time metric from analytics telemetry.", kind: "metric", dataSource: "existing-ui" },
  "system-status": { id: "system-status", label: "System status", aliases: ["system status", "status"], description: "Current local runtime and uptime status.", kind: "metric", dataSource: "existing-ui" },
  "session-information": { id: "session-information", label: "Session information", aliases: ["session information", "session info"], description: "Current model and local session state.", kind: "metric", dataSource: "existing-ui" },
  telemetry: { id: "telemetry", label: "Telemetry", aliases: ["telemetry", "system telemetry"], description: "Existing telemetry summary.", kind: "metric", dataSource: "existing-ui" },
  "model-comparison": { id: "model-comparison", label: "Model comparison", aliases: ["model comparison", "compare models"], description: "Composed comparison of the two NEXUS modes using existing model-share and response signals.", kind: "composite", dataSource: "existing-ui" },
  performance: { id: "performance", label: "Performance", aliases: ["performance", "performance dashboard", "system performance"], description: "Composed performance view using existing response, user, and status metrics.", kind: "composite", dataSource: "existing-ui" },
  "usage-trends": { id: "usage-trends", label: "Usage trends", aliases: ["usage trends", "trend"], description: "Existing analytics trend visualization.", kind: "chart", dataSource: "existing-ui" },
  chat: { id: "chat", label: "Chat", aliases: ["chat", "conversation"], description: "NEXUS chat surface.", kind: "surface", dataSource: "existing-ui" },
};

export const REGISTERED_WIDGET_IDS = Object.keys(WIDGET_REGISTRY) as WidgetTarget[];
export const REGISTERED_WIDGET_SET = new Set<WidgetTarget>(REGISTERED_WIDGET_IDS);

export const WIDGET_COMPOSITIONS: Record<string, { title: string; widgets: WidgetTarget[] }> = {
  model_comparison: { title: "Model comparison", widgets: ["model-comparison", "model-usage", "response-time", "system-status"] },
  activity_dashboard: { title: "Today's activity", widgets: ["activity", "messages", "active-users", "model-usage"] },
  performance_dashboard: { title: "Performance dashboard", widgets: ["response-time", "active-users", "system-status", "telemetry"] },
  analytics_overview: { title: "Analytics overview", widgets: ["analytics", "model-usage", "response-time", "active-users"] },
};
