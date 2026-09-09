"use client";

import { useMemo, useState, type CSSProperties } from "react";
import { Activity, BarChart3, ChevronRight, Filter, Users } from "lucide-react";
import { useNexusUI } from "../../lib/nexus-ui";

type RangeKey = "7D" | "30D" | "90D";
type ModelFilter = "ALL" | "NEXUS" | "DEEP";

type Series = { label: string; engagement: number; sessions: number; response: number };

const DATA: Record<RangeKey, Series[]> = {
  "7D": [
    { label: "M", engagement: 42, sessions: 31, response: 1.4 },
    { label: "T", engagement: 49, sessions: 38, response: 1.3 },
    { label: "W", engagement: 56, sessions: 44, response: 1.1 },
    { label: "T", engagement: 51, sessions: 47, response: 1.2 },
    { label: "F", engagement: 67, sessions: 53, response: 1.0 },
    { label: "S", engagement: 73, sessions: 61, response: 1.1 },
    { label: "S", engagement: 69, sessions: 58, response: 1.2 },
  ],
  "30D": [
    { label: "01", engagement: 36, sessions: 28, response: 1.5 },
    { label: "05", engagement: 41, sessions: 34, response: 1.4 },
    { label: "10", engagement: 48, sessions: 39, response: 1.3 },
    { label: "15", engagement: 54, sessions: 46, response: 1.2 },
    { label: "20", engagement: 63, sessions: 52, response: 1.1 },
    { label: "25", engagement: 71, sessions: 61, response: 1.1 },
    { label: "30", engagement: 75, sessions: 66, response: 1.0 },
  ],
  "90D": [
    { label: "W1", engagement: 28, sessions: 23, response: 1.8 },
    { label: "W3", engagement: 34, sessions: 28, response: 1.6 },
    { label: "W5", engagement: 39, sessions: 31, response: 1.5 },
    { label: "W7", engagement: 47, sessions: 39, response: 1.3 },
    { label: "W9", engagement: 53, sessions: 45, response: 1.2 },
    { label: "W11", engagement: 65, sessions: 54, response: 1.1 },
    { label: "W13", engagement: 76, sessions: 68, response: 1.0 },
  ],
};

const MODEL_SHARE = { ALL: { nexus: 67, deep: 33 }, NEXUS: { nexus: 100, deep: 0 }, DEEP: { nexus: 0, deep: 100 } } as const;

export function AnalyticsPanel() {
  const [hovered, setHovered] = useState<number | null>(null);
  const { model, analyticsRange, analyticsFilter, setAnalyticsRange, setAnalyticsFilter, metricFocus, visibleWidgets } = useNexusUI();
  const range = analyticsRange as RangeKey;
  const filter = analyticsFilter as ModelFilter;
  if (!visibleWidgets.analytics) return null;
  const accentValue = `var(--accent)`;
  const series = useMemo(() => DATA[range], [range]);
  const modelShare = MODEL_SHARE[filter];
  const activeSeries = filter === "DEEP" ? series.map((item) => ({ ...item, engagement: Math.round(item.engagement * .65), sessions: Math.round(item.sessions * .55) })) : filter === "NEXUS" ? series.map((item) => ({ ...item, engagement: Math.round(item.engagement * 1.08), sessions: Math.round(item.sessions * 1.12) })) : series;
  const max = Math.max(...activeSeries.map((point) => point.engagement));
  const points = activeSeries.map((point, index) => {
    const x = 20 + index * (160 / Math.max(activeSeries.length - 1, 1));
    const y = 72 - (point.engagement / max) * 54;
    return `${x},${y}`;
  }).join(" ");

  return <section className="analytics-section" aria-labelledby="analytics-title">
    <div className="section-heading analytics-heading"><div><span className="section-label">// ANALYTICS / SIGNAL</span><h2 id="analytics-title">See the system think in motion.</h2></div><span className="heading-note">SESSION ACTIVITY / MODEL MIX / RESPONSE TREND</span></div>
    <div className="analytics-toolbar glass-card">
      <div className="analytics-tool-group"><span className="tool-label"><Activity size={12}/> WINDOW</span>{(["7D", "30D", "90D"] as RangeKey[]).map((key) => <button key={key} className={range === key ? "tool-button active" : "tool-button"} onClick={() => { setAnalyticsRange(key); setHovered(null); }}>{key}</button>)}</div>
      <div className="analytics-tool-group"><span className="tool-label"><Filter size={12}/> MODEL</span>{(["ALL", "NEXUS", "DEEP"] as ModelFilter[]).map((key) => <button key={key} className={filter === key ? "tool-button active" : "tool-button"} onClick={() => { setAnalyticsFilter(key); setHovered(null); }}>{key}</button>)}</div>
      <div className="analytics-live"><span className="status-dot"/> LIVE SIGNAL <strong>{model === "deep" ? "NEXUS DEEP" : "NEXUS"}</strong></div>
    </div>

    <div className="analytics-grid">
      <article className="analytics-chart glass-card">
        <div className="analytics-card-head"><div><span className="section-label">01 / ENGAGEMENT</span><h3>{metricFocus ? `${metricFocus} trend` : "Messages + sessions"}</h3></div><span className="analytics-current">{activeSeries.at(-1)?.engagement ?? 0} INDEX</span></div>
        <div className="line-chart-wrap">
          <svg viewBox="0 0 180 84" role="img" aria-label="Engagement activity line chart">
            <defs><linearGradient id="nexusArea" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor={accentValue} stopOpacity=".26"/><stop offset="100%" stopColor={accentValue} stopOpacity="0"/></linearGradient></defs>
            {[18,36,54,72].map((y) => <line key={y} x1="20" y1={y} x2="180" y2={y} stroke="rgba(255,255,255,.07)" strokeWidth=".4"/>)}
            <polygon points={`20,72 ${points} 180,72`} fill="url(#nexusArea)"/>
            <polyline points={points} fill="none" stroke={accentValue} strokeWidth="1.4" vectorEffect="non-scaling-stroke"/>
            {activeSeries.map((point, index) => {
              const x = 20 + index * (160 / Math.max(activeSeries.length - 1, 1));
              const y = 72 - (point.engagement / max) * 54;
              return <g key={`${point.label}-${index}`} onMouseEnter={() => setHovered(index)} onMouseLeave={() => setHovered(null)} className="chart-point"><circle cx={x} cy={y} r="2.2" fill={accentValue}/><circle cx={x} cy={y} r="5.5" fill="transparent"/></g>;
            })}
          </svg>
          <div className="chart-axis">{activeSeries.map((point, index) => <span key={`${point.label}-axis-${index}`}>{point.label}</span>)}</div>
          {hovered !== null && activeSeries[hovered] && <div className="chart-tooltip" style={{ left: `${15 + hovered * (70 / Math.max(activeSeries.length - 1, 1))}%` }}><strong>{activeSeries[hovered].engagement} index</strong><span>{activeSeries[hovered].sessions} sessions · {activeSeries[hovered].response}s response</span></div>}
        </div>
      </article>

      <article className="analytics-side glass-card">
        <div className="analytics-card-head"><div><span className="section-label">02 / MODEL USAGE</span><h3>Distribution</h3></div><Users size={16}/></div>
        <div className="usage-ring" style={{ "--deep-share": `${modelShare.deep}%` } as CSSProperties}><div><strong>{modelShare.nexus + modelShare.deep}%</strong><span>tracked</span></div></div>
        <div className="usage-bars"><div><span><i className="usage-dot nexus"/>NEXUS</span><b>{modelShare.nexus}%</b><div className="usage-track"><span style={{ width: `${modelShare.nexus}%` }}/></div></div><div><span><i className="usage-dot deep"/>NEXUS DEEP</span><b>{modelShare.deep}%</b><div className="usage-track"><span className="deep-bar" style={{ width: `${modelShare.deep}%` }}/></div></div></div>
        <div className="analytics-mini-row"><div><span>AVG RESPONSE</span><strong>{(series.reduce((sum, item) => sum + item.response, 0) / series.length).toFixed(1)}s</strong></div><div><span>ACTIVE USERS</span><strong>10.2K</strong></div></div>
      </article>
    </div>
    <div className="analytics-note"><BarChart3 size={13}/><span>Interactive preview data is local to this interface. Hover a point or change the window/model filter.</span><ChevronRight size={13}/></div>
  </section>;
}

