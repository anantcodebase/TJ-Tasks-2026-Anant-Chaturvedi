"use client";

import { Activity, BarChart3, Gauge, MessageSquare, Server, Users, Clock3, Cpu, Database, Layers3, LayoutDashboard, type LucideIcon } from "lucide-react";
import { useNexusUI } from "../../lib/nexus-ui";
import type { GeneratedSection, WidgetTarget } from "../../lib/types";
import { WIDGET_REGISTRY } from "../../lib/widget-registry";
import { AnalyticsPanel } from "../analytics/AnalyticsPanel";

const ICONS = {
  activity: Activity,
  "active-users": Users,
  messages: MessageSquare,
  "model-usage": Cpu,
  "response-time": Clock3,
  "system-status": Server,
  "session-information": Database,
  telemetry: Gauge,
  metrics: Layers3,
  "engagement-chart": BarChart3,
  revenue: BarChart3,
  "usage-trends": BarChart3,
  performance: Gauge,
  "model-comparison": Cpu,
  overview: LayoutDashboard,
  analytics: BarChart3,
  chat: MessageSquare,
} satisfies Record<WidgetTarget, LucideIcon>;

const DEFAULT_DETAILS: Partial<Record<WidgetTarget, { value: string; detail: string }>> = {
  activity: { value: "50K+", detail: "Messages today · existing telemetry" },
  "active-users": { value: "10.2K", detail: "Active users in the existing analytics surface" },
  messages: { value: "50K+", detail: "Messages today" },
  "model-usage": { value: "67 / 33", detail: "NEXUS / NEXUS DEEP · existing model-share signal" },
  "response-time": { value: "1.2s", detail: "Current average response signal" },
  "system-status": { value: "99.8%", detail: "Uptime · local interface telemetry" },
  "session-information": { value: "NEXUS", detail: "Shared active model state" },
  telemetry: { value: "READY", detail: "Runtime state and model signal" },
  metrics: { value: "10.2K", detail: "Primary visible metric" },
  "engagement-chart": { value: "LIVE", detail: "Engagement visualization registered" },
  revenue: { value: "AVAILABLE", detail: "Registered revenue widget" },
  "usage-trends": { value: "7D / 30D / 90D", detail: "Existing analytics trend windows" },
};

function MetricCard({ target, model, analyticsRange, analyticsFilter }: { target: WidgetTarget; model: "nexus" | "deep"; analyticsRange: "7D" | "30D" | "90D"; analyticsFilter: "ALL" | "NEXUS" | "DEEP" }) {
  const Icon = ICONS[target];
  const base = DEFAULT_DETAILS[target] ?? { value: "READY", detail: WIDGET_REGISTRY[target].description };
  let value = base.value;
  let detail = base.detail;

  if (target === "model-usage") {
    value = analyticsFilter === "DEEP" ? "100% DEEP" : analyticsFilter === "NEXUS" ? "100% NEXUS" : "67 / 33";
  }
  if (target === "response-time") value = analyticsRange === "7D" ? "1.2s" : "1.0s";
  if (target === "session-information") value = model === "deep" ? "NEXUS DEEP" : "NEXUS";
  if (target === "telemetry") value = model === "deep" ? "DEEP" : "READY";

  return (
    <article className="agent-widget-card glass-card" data-widget={target}>
      <div className="agent-widget-head"><span className="section-label">{WIDGET_REGISTRY[target].label.toUpperCase()}</span><Icon size={15}/></div>
      <strong className="agent-widget-value">{value}</strong>
      <span className="agent-widget-detail">{detail}</span>
    </article>
  );
}

function WidgetGroup({ widgets, model, analyticsRange, analyticsFilter }: { widgets: WidgetTarget[]; model: "nexus" | "deep"; analyticsRange: "7D" | "30D" | "90D"; analyticsFilter: "ALL" | "NEXUS" | "DEEP" }) {
  return (
    <div className="agent-widget-grid">
      {widgets.map((target) => target !== "analytics" && target !== "chat" && (
        <MetricCard key={target} target={target} model={model} analyticsRange={analyticsRange} analyticsFilter={analyticsFilter} />
      ))}
    </div>
  );
}

function GeneratedSectionView({ section, model, analyticsRange, analyticsFilter }: { section: GeneratedSection; model: "nexus" | "deep"; analyticsRange: "7D" | "30D" | "90D"; analyticsFilter: "ALL" | "NEXUS" | "DEEP" }) {
  const safeWidgets = section.widgets.filter((target) => target in WIDGET_REGISTRY);
  const includesAnalytics = safeWidgets.includes("analytics");
  const widgets = safeWidgets.filter((target) => target !== "analytics");
  if (!safeWidgets.length) return null;

  return (
    <section className="agent-widget-block glass-card" data-generated-section={section.id}>
      <div className="section-heading">
        <div><span className="section-label">// GENERATED / CONTROLLED COMPOSITION</span><h2>{section.title}</h2></div>
        <span className="heading-note">{safeWidgets.length} REGISTERED COMPONENTS / SHARED STATE</span>
      </div>
      {includesAnalytics && <AnalyticsPanel />}
      {widgets.length > 0 && <WidgetGroup widgets={widgets} model={model} analyticsRange={analyticsRange} analyticsFilter={analyticsFilter} />}
    </section>
  );
}

export function NexusWidgetSurface() {
  const { visibleWidgets, model, analyticsRange, analyticsFilter, generatedSection } = useNexusUI();
  const extra = (Object.entries(visibleWidgets) as [WidgetTarget, boolean][]).filter(([target, visible]) => visible && target !== "analytics" && target !== "chat").map(([target]) => target);
  const hasOverview = visibleWidgets.overview;
  const hasPerformance = visibleWidgets.performance;
  const hasModelComparison = visibleWidgets["model-comparison"];
  const shouldRenderAnalytics = visibleWidgets.analytics;

  const compositeTargets: WidgetTarget[] = [];
  if (hasOverview) compositeTargets.push("activity", "active-users", "messages", "model-usage", "response-time", "system-status");
  if (hasPerformance) compositeTargets.push("response-time", "active-users", "system-status", "telemetry");
  if (hasModelComparison) compositeTargets.push("model-usage", "response-time", "system-status");
  const targets = [...new Set([...compositeTargets, ...extra])];

  if (!shouldRenderAnalytics && targets.length === 0 && !generatedSection) return null;

  return (
    <section className="agent-widget-surface" aria-label="NEXUS controlled widgets">
      {shouldRenderAnalytics && <AnalyticsPanel />}
      {hasOverview && <div className="agent-widget-block"><div className="section-heading"><div><span className="section-label">// WIDGET REGISTRY / OVERVIEW</span><h2>Relevant signals, composed on demand.</h2></div><span className="heading-note">REGISTERED COMPONENTS / SHARED DATA</span></div></div>}
      {hasPerformance && <div className="agent-widget-block agent-widget-block-heading"><span className="section-label">// PERFORMANCE COMPOSITE</span><span className="heading-note">RESPONSE / USERS / STATUS</span></div>}
      {hasModelComparison && <div className="agent-widget-block agent-widget-block-heading"><span className="section-label">// MODEL COMPARISON</span><span className="heading-note">NEXUS / NEXUS DEEP</span></div>}
      {targets.length > 0 && <WidgetGroup widgets={targets} model={model} analyticsRange={analyticsRange} analyticsFilter={analyticsFilter} />}
      {generatedSection && <GeneratedSectionView section={generatedSection} model={model} analyticsRange={analyticsRange} analyticsFilter={analyticsFilter} />}
      <span className="agent-widget-registry-note">Rendered only from registered NEXUS capabilities. AI selects capabilities; the application controls rendering.</span>
    </section>
  );
}
