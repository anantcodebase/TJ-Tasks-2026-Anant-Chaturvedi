"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { AgentAction, AccentName, AnalyticsFilter, AnalyticsRange, NexusModel, WidgetTarget, GeneratedSection } from "./types";
import { isRegisteredAction } from "./action-registry";

export type AccentConfig = { label: string; hex: string };

export const ACCENT_CONFIG: Record<AccentName, AccentConfig> = {
  lime: { label: "Lime", hex: "#CCFF00" },
  blue: { label: "Blue", hex: "#3B82F6" },
  violet: { label: "Violet", hex: "#A855F7" },
  cyan: { label: "Cyan", hex: "#00F0FF" },
  red: { label: "Red", hex: "#F43F5E" },
  orange: { label: "Orange", hex: "#F97316" },
  yellow: { label: "Yellow", hex: "#FACC15" },
  pink: { label: "Pink", hex: "#EC4899" },
};

export const DEFAULT_VISIBLE_WIDGETS: Record<WidgetTarget, boolean> = {
  analytics: true,
  overview: false,
  revenue: false,
  "engagement-chart": false,
  metrics: false,
  activity: false,
  "active-users": false,
  messages: false,
  "model-usage": false,
  "response-time": false,
  "system-status": false,
  "session-information": false,
  telemetry: false,
  "model-comparison": false,
  performance: false,
  "usage-trends": false,
  chat: false,
};

const STORAGE_KEY = "nexus-ui-state";

function hexToRgb(hex: string) {
  const value = hex.replace("#", "");
  const number = Number.parseInt(value, 16);
  return `${(number >> 16) & 255}, ${(number >> 8) & 255}, ${number & 255}`;
}

function applyAccentVariables(accent: AccentName) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  const hex = ACCENT_CONFIG[accent].hex;
  root.style.setProperty("--accent", hex);
  root.style.setProperty("--accent-rgb", hexToRgb(hex));
  root.style.setProperty("--lime", hex);
}

type NexusUIContextValue = {
  accent: AccentName;
  model: NexusModel;
  analyticsRange: AnalyticsRange;
  analyticsFilter: AnalyticsFilter;
  metricFocus: "engagement" | "sessions" | "conversion" | "sales" | null;
  visibleWidgets: Record<WidgetTarget, boolean>;
  generatedSection: GeneratedSection | null;
  setAccent: (accent: AccentName) => void;
  setModel: (model: NexusModel) => void;
  setAnalyticsRange: (range: AnalyticsRange) => void;
  setAnalyticsFilter: (filter: AnalyticsFilter) => void;
  setMetricFocus: (metric: "engagement" | "sessions" | "conversion" | "sales" | null) => void;
  showWidget: (target: WidgetTarget) => void;
  hideWidget: (target: WidgetTarget) => void;
  /** Resolves only after React has committed and verified the shared UI state. */
  applyActions: (actions: AgentAction[]) => Promise<AgentAction[]>;
};

const NexusUIContext = createContext<NexusUIContextValue | null>(null);

type UIState = {
  accent: AccentName;
  model: NexusModel;
  analyticsRange: AnalyticsRange;
  analyticsFilter: AnalyticsFilter;
  metricFocus: "engagement" | "sessions" | "conversion" | "sales" | null;
  visibleWidgets: Record<WidgetTarget, boolean>;
  generatedSection: GeneratedSection | null;
};

type PendingExecution = {
  actions: AgentAction[];
  resolve: (actions: AgentAction[]) => void;
};

function defaultState(): UIState {
  return {
    accent: "lime",
    model: "nexus",
    analyticsRange: "7D",
    analyticsFilter: "ALL",
    metricFocus: null,
    visibleWidgets: { ...DEFAULT_VISIBLE_WIDGETS },
    generatedSection: null,
  };
}

function collectionVisibility(visible: boolean): Record<WidgetTarget, boolean> {
  const widgets = { ...DEFAULT_VISIBLE_WIDGETS };
  if (visible) {
    widgets.analytics = true;
    widgets.overview = true;
  }
  return widgets;
}

function updateWidget(state: UIState, target: WidgetTarget, visible: boolean): UIState {
  // "Widget overview" is the registered collection control. It must control
  // every renderer fed by shared widget state, rather than leaving Analytics
  // or an old generated section visible beneath an optimistic chat reply.
  if (target === "overview") {
    return {
      ...state,
      visibleWidgets: collectionVisibility(visible),
      generatedSection: visible ? state.generatedSection : null,
    };
  }
  return { ...state, visibleWidgets: { ...state.visibleWidgets, [target]: visible } };
}

function applyActionToState(state: UIState, action: AgentAction): UIState | null {
  switch (action.type) {
    case "set_accent_color":
      return action.accent ? { ...state, accent: action.accent } : null;
    case "set_model":
      return action.model ? { ...state, model: action.model } : null;
    case "show_widget":
    case "open_panel":
    case "show_metric":
    case "show_chart":
      return action.target ? updateWidget(state, action.target, true) : null;
    case "hide_widget":
    case "close_panel":
      return action.target ? updateWidget(state, action.target, false) : null;
    case "set_metric_focus":
      return action.metric ? { ...state, metricFocus: action.metric } : null;
    case "set_analytics_range":
      return action.range ? { ...state, analyticsRange: action.range, visibleWidgets: { ...state.visibleWidgets, analytics: true } } : null;
    case "set_analytics_filter":
      return action.filter ? { ...state, analyticsFilter: action.filter, visibleWidgets: { ...state.visibleWidgets, analytics: true } } : null;
    case "reset_dashboard":
      return defaultState();
    case "create_dashboard":
    case "compose_widgets":
      if (!action.widgets?.length || !action.dashboardId) return null;
      return {
        ...state,
        generatedSection: { id: action.dashboardId, title: action.title ?? "NEXUS dashboard", widgets: action.widgets },
      };
    case "remove_generated_section":
      return { ...state, generatedSection: null };
    default:
      return null;
  }
}

function actionMatchesState(action: AgentAction, state: UIState): boolean {
  switch (action.type) {
    case "set_accent_color": return state.accent === action.accent;
    case "set_model": return state.model === action.model;
    case "set_metric_focus": return state.metricFocus === action.metric;
    case "set_analytics_range": return state.analyticsRange === action.range && state.visibleWidgets.analytics;
    case "set_analytics_filter": return state.analyticsFilter === action.filter && state.visibleWidgets.analytics;
    case "show_widget":
    case "open_panel":
    case "show_metric":
    case "show_chart":
      return action.target === "overview"
        ? state.visibleWidgets.analytics && state.visibleWidgets.overview
        : Boolean(action.target && state.visibleWidgets[action.target]);
    case "hide_widget":
    case "close_panel":
      return action.target === "overview"
        ? !Object.values(state.visibleWidgets).some(Boolean) && state.generatedSection === null
        : Boolean(action.target && !state.visibleWidgets[action.target]);
    case "reset_dashboard":
      return state.accent === "lime" && state.model === "nexus" && state.analyticsRange === "7D" && state.analyticsFilter === "ALL" && state.metricFocus === null && state.visibleWidgets.analytics && !state.visibleWidgets.overview && state.generatedSection === null;
    case "create_dashboard":
    case "compose_widgets":
      return Boolean(state.generatedSection && action.dashboardId === state.generatedSection.id && action.widgets?.every((widget) => state.generatedSection?.widgets.includes(widget)));
    case "remove_generated_section": return state.generatedSection === null;
    default: return false;
  }
}

export function NexusUIProvider({ children }: { children: React.ReactNode }) {
  const stateRef = useRef<UIState>(defaultState());
  const [uiState, setUIState] = useState<UIState>(stateRef.current);
  const pendingExecutions = useRef<PendingExecution[]>([]);

  const commitState = useCallback((next: UIState) => {
    stateRef.current = next;
    setUIState(next);
  }, []);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (!stored) return;
      const parsed = JSON.parse(stored) as Partial<{
        accent: AccentName;
        model: NexusModel;
        analyticsRange: AnalyticsRange;
        analyticsFilter: AnalyticsFilter;
        metricFocus: "engagement" | "sessions" | "conversion" | "sales" | null;
        visibleWidgets: Partial<Record<WidgetTarget, boolean>>;
        generatedSection: GeneratedSection | null;
      }>;
      const current = stateRef.current;
      const next: UIState = {
        ...current,
        accent: parsed.accent && parsed.accent in ACCENT_CONFIG ? parsed.accent : current.accent,
        model: parsed.model === "nexus" || parsed.model === "deep" ? parsed.model : current.model,
        analyticsRange: parsed.analyticsRange === "7D" || parsed.analyticsRange === "30D" || parsed.analyticsRange === "90D" ? parsed.analyticsRange : current.analyticsRange,
        analyticsFilter: parsed.analyticsFilter === "ALL" || parsed.analyticsFilter === "NEXUS" || parsed.analyticsFilter === "DEEP" ? parsed.analyticsFilter : current.analyticsFilter,
        metricFocus: parsed.metricFocus === null || parsed.metricFocus === "engagement" || parsed.metricFocus === "sessions" || parsed.metricFocus === "conversion" || parsed.metricFocus === "sales" ? parsed.metricFocus : current.metricFocus,
        visibleWidgets: { ...current.visibleWidgets, ...(parsed.visibleWidgets ?? {}) },
        generatedSection: parsed.generatedSection && typeof parsed.generatedSection.id === "string" && Array.isArray(parsed.generatedSection.widgets) ? parsed.generatedSection : current.generatedSection,
      };
      commitState(next);
    } catch {
      // Ignore malformed local state and keep safe defaults.
    }
  }, [commitState]);

  useEffect(() => {
    applyAccentVariables(uiState.accent);
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(uiState));
    } catch {
      // Local persistence is an enhancement, not a requirement for the UI to work.
    }
  }, [uiState]);

  useEffect(() => {
    const pending = pendingExecutions.current.splice(0);
    if (!pending.length) return;
    const settle = () => {
      for (const execution of pending) {
        execution.resolve(execution.actions.filter((action) => actionMatchesState(action, uiState)));
      }
    };
    if (typeof window !== "undefined" && typeof window.requestAnimationFrame === "function") {
      window.requestAnimationFrame(settle);
    } else {
      settle();
    }
  }, [uiState]);

  const setAccent = useCallback((next: AccentName) => {
    if (!(next in ACCENT_CONFIG)) return;
    commitState({ ...stateRef.current, accent: next });
  }, [commitState]);

  const setModel = useCallback((next: NexusModel) => commitState({ ...stateRef.current, model: next }), [commitState]);
  const setAnalyticsRange = useCallback((next: AnalyticsRange) => commitState({ ...stateRef.current, analyticsRange: next }), [commitState]);
  const setAnalyticsFilter = useCallback((next: AnalyticsFilter) => commitState({ ...stateRef.current, analyticsFilter: next }), [commitState]);
  const setMetricFocus = useCallback((next: "engagement" | "sessions" | "conversion" | "sales" | null) => commitState({ ...stateRef.current, metricFocus: next }), [commitState]);
  const showWidget = useCallback((target: WidgetTarget) => commitState(updateWidget(stateRef.current, target, true)), [commitState]);
  const hideWidget = useCallback((target: WidgetTarget) => commitState(updateWidget(stateRef.current, target, false)), [commitState]);

  const applyActions = useCallback((actions: AgentAction[]): Promise<AgentAction[]> => {
    let next = stateRef.current;
    const proposed: AgentAction[] = [];
    for (const original of actions) {
      if (!isRegisteredAction(original)) continue;
      const action = (original.type === "create_dashboard" || original.type === "compose_widgets") && original.widgets?.length
        ? { ...original, widgets: original.widgets.filter((target) => target in DEFAULT_VISIBLE_WIDGETS), dashboardId: original.dashboardId ?? `agent-${Date.now()}` }
        : original;
      if ((action.type === "create_dashboard" || action.type === "compose_widgets") && !action.widgets?.length) continue;
      const updated = applyActionToState(next, action);
      if (!updated) continue;
      next = updated;
      proposed.push(action);
    }
    if (!proposed.length) return Promise.resolve([]);
    return new Promise((resolve) => {
      pendingExecutions.current.push({ actions: proposed, resolve });
      commitState(next);
    });
  }, [commitState]);

  const value = useMemo(() => ({
    accent: uiState.accent, model: uiState.model, analyticsRange: uiState.analyticsRange,
    analyticsFilter: uiState.analyticsFilter, metricFocus: uiState.metricFocus,
    visibleWidgets: uiState.visibleWidgets, generatedSection: uiState.generatedSection,
    setAccent, setModel, setAnalyticsRange, setAnalyticsFilter, setMetricFocus,
    showWidget, hideWidget, applyActions,
  }), [uiState, setAccent, setModel, setAnalyticsRange, setAnalyticsFilter, setMetricFocus, showWidget, hideWidget, applyActions]);
  return <NexusUIContext.Provider value={value}>{children}</NexusUIContext.Provider>;
}

export function useNexusUI() {
  const context = useContext(NexusUIContext);
  if (!context) throw new Error("useNexusUI must be used inside NexusUIProvider");
  return context;
}
