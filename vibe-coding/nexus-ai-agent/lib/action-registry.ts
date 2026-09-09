import type { ActionType, AgentAction } from "./types";
import { REGISTERED_WIDGET_SET } from "./widget-registry";

export type ActionDefinition = {
  type: ActionType;
  description: string;
  executable: boolean;
  requiresTarget?: boolean;
  requiresValue?: boolean;
};

export const ACTION_REGISTRY: Record<ActionType, ActionDefinition> = {
  show_widget: { type: "show_widget", description: "Reveal a registered widget", executable: true, requiresTarget: true },
  hide_widget: { type: "hide_widget", description: "Hide a registered widget", executable: true, requiresTarget: true },
  set_model: { type: "set_model", description: "Switch the shared NEXUS model", executable: true, requiresValue: true },
  set_accent_color: { type: "set_accent_color", description: "Change the shared accent color", executable: true, requiresValue: true },
  set_analytics_range: { type: "set_analytics_range", description: "Change the analytics time range", executable: true, requiresValue: true },
  set_analytics_filter: { type: "set_analytics_filter", description: "Change the analytics model filter", executable: true, requiresValue: true },
  set_metric_focus: { type: "set_metric_focus", description: "Focus an existing analytics metric", executable: true },
  open_panel: { type: "open_panel", description: "Open a registered panel", executable: true, requiresTarget: true },
  close_panel: { type: "close_panel", description: "Close a registered panel", executable: true, requiresTarget: true },
  maximize_panel: { type: "maximize_panel", description: "Panel sizing is not currently exposed as a shared capability", executable: false, requiresTarget: true },
  minimize_panel: { type: "minimize_panel", description: "Panel sizing is not currently exposed as a shared capability", executable: false, requiresTarget: true },
  highlight_element: { type: "highlight_element", description: "Legacy highlight action; currently not executable", executable: false, requiresTarget: true },
  set_theme: { type: "set_theme", description: "Legacy theme action; currently not executable", executable: false },
  set_text_size: { type: "set_text_size", description: "Legacy text-size action; currently not executable", executable: false },
  set_font: { type: "set_font", description: "Legacy font action; currently not executable", executable: false },
  set_dashboard_view: { type: "set_dashboard_view", description: "Legacy dashboard-view action; currently not executable", executable: false },
  reset_dashboard: { type: "reset_dashboard", description: "Restore the default NEXUS UI state", executable: true },
  create_dashboard: { type: "create_dashboard", description: "Compose a temporary dashboard from registered widgets", executable: true, requiresValue: true },
  compose_widgets: { type: "compose_widgets", description: "Compose registered widgets into a temporary section", executable: true, requiresValue: true },
  remove_generated_section: { type: "remove_generated_section", description: "Remove the current temporary dashboard section", executable: true },
  show_metric: { type: "show_metric", description: "Show a registered metric widget", executable: true, requiresTarget: true },
  show_chart: { type: "show_chart", description: "Show a registered chart widget", executable: true, requiresTarget: true },
};

export const EXECUTABLE_ACTIONS = Object.values(ACTION_REGISTRY)
  .filter((definition) => definition.executable)
  .map((definition) => definition.type);

export function isRegisteredAction(action: AgentAction) {
  const definition = ACTION_REGISTRY[action.type];
  if (!definition || !definition.executable) return false;
  if (definition.requiresTarget && (!action.target || !REGISTERED_WIDGET_SET.has(action.target))) return false;
  if (definition.requiresValue && !action.accent && !action.model && !action.range && !action.filter && !action.widgets?.length && !action.title) return false;
  return true;
}
