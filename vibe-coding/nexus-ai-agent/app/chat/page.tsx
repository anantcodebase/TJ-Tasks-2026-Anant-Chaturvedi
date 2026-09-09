"use client";
import { FormEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight, Bot, Send } from "lucide-react";
import { Shell } from "../../components/marketing/Shell";
import { sendChatMessage } from "../../lib/api";
import { useNexusUI } from "../../lib/nexus-ui";
import { NexusWidgetSurface } from "../../components/agent/NexusWidgetSurface";
import { loadConversation, saveConversation, trimConversation } from "../../lib/chat-context";
import type { ChatMessage } from "../../lib/types";

type Message = { id: string; role: "user" | "agent"; content: string };

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const messagesRef = useRef<HTMLDivElement>(null);
  const stickToBottom = useRef(true);
  const conversationHydrated = useRef(false);
  const submitting = useRef(false);
  const { model, accent, visibleWidgets, analyticsRange, analyticsFilter, generatedSection, applyActions } = useNexusUI();

  const scrollToLatest = () => {
    const el = messagesRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  };

  useEffect(() => {
    setMessages(loadConversation());
    conversationHydrated.current = true;
  }, []);

  useEffect(() => {
    if (stickToBottom.current) scrollToLatest();
  }, [messages, busy]);

  useEffect(() => {
    if (conversationHydrated.current) saveConversation(messages);
  }, [messages]);

  function onScroll() {
    const el = messagesRef.current;
    if (!el) return;
    stickToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 120;
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    const q = input.trim();
    if (!q || busy || submitting.current) return;
    submitting.current = true;
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setInput("");
    stickToBottom.current = true;
    const userMessage: ChatMessage = { id, role: "user", content: q };
    const nextConversation = trimConversation([...messages, userMessage]);
    setMessages(nextConversation);
    setBusy(true);
    try {
      // `messages` intentionally excludes the new user turn; the backend/provider appends `q` after prior history.
      const r = await sendChatMessage(q, messages, {
        model,
        accent,
        visibleWidgets,
        analyticsRange,
        analyticsFilter,
        generatedSection,
      });
      const actionStarted = typeof performance !== "undefined" ? performance.now() : Date.now();
      const executed = await applyActions(r.actions);
      if (typeof console !== "undefined") {
        const actionDuration = (typeof performance !== "undefined" ? performance.now() : Date.now()) - actionStarted;
        console.debug(`[CHAT PERF FRONTEND] actions=${r.actions.length} state_commit_and_render=${actionDuration.toFixed(3)}ms`);
      }
      const actionMessage = describeExecutedActions(executed);
      const safeMessage = r.actions.length > executed.length
        ? actionMessage ? `${actionMessage} Some requested UI changes could not be verified.` : "I couldn't execute that UI action."
        : actionMessage ?? r.message;
      setMessages((v) => trimConversation([...v, { id: `${id}-reply`, role: "agent", content: r.recovered ? `Local recovery mode: ${safeMessage}` : safeMessage }]));
    } catch (error) {
      const message = error instanceof Error ? error.message : "The agent could not complete this request.";
      setMessages((v) => trimConversation([...v, { id: `${id}-reply`, role: "agent", content: message }]));
    } finally {
      setBusy(false);
      submitting.current = false;
    }
  }

  return <Shell><div className="chat-page"><div className="chat-page-head"><div><span className="section-label">// NEXUS.EXE / CHAT</span><h1>Good ideas start ugly.</h1><div className="chat-model-state"><span className="model-identity-dot"/> ACTIVE: <strong>{model === "deep" ? "NEXUS DEEP" : "NEXUS"}</strong></div></div><Link href="/" className="ghost-button"><ArrowLeft size={15}/> HOME</Link></div><section className="chat-terminal glass-card"><div className="terminal-header"><span>/ NEXUS.EXE</span><span>LOCAL / READY</span></div><div className="chat-messages" ref={messagesRef} onScroll={onScroll} aria-live="polite">{messages.length===0&&<div className="empty-chat"><Bot size={28}/><strong>What are you thinking about?</strong><span>Ask for a plan, a bug fix, a summary, or something random.</span></div>}{messages.map((m)=><div key={m.id} className={`chat-msg ${m.role}`}><span>{m.role === "user" ? "> YOU" : "> NEXUS"}</span><p>{m.content}</p></div>)}{busy&&<div className="chat-msg agent"><span>&gt; NEXUS</span><p className="typing">processing…</p></div>}</div><form className="chat-input" onSubmit={submit}><span>&gt;</span><input value={input} onChange={e=>setInput(e.target.value)} placeholder="Type a thought…"/><button type="submit" disabled={busy || !input.trim()} aria-label="Send"><Send size={15}/></button></form></section><NexusWidgetSurface /><div className="chat-footnote"><span>OPEN MODELS / LOW FRICTION / HUMAN QUESTIONS</span><Link href="/models" className="text-link">SWITCH MODEL <ArrowRight size={14}/></Link></div></div></Shell>;
}

function describeExecutedActions(actions: import("../../lib/types").AgentAction[]) {
  if (!actions.length) return null;
  const confirmations: string[] = [];
  for (const action of actions) {
    if (action.type === "set_model") confirmations.push(action.model === "deep" ? "NEXUS Deep is now active." : "NEXUS is now active.");
    if (action.type === "set_accent_color" && action.accent) confirmations.push(`Accent changed to ${action.accent}.`);
    if (action.type === "show_widget" && action.target) confirmations.push(action.target === "analytics" ? "Analytics panel opened." : action.target === "overview" ? "Widgets are now visible." : `${labelForTarget(action.target)} is now visible.`);
    if (action.type === "hide_widget" && action.target) confirmations.push(action.target === "analytics" ? "Analytics hidden." : action.target === "overview" ? "Widgets hidden." : `${labelForTarget(action.target)} hidden.`);
    if (action.type === "set_analytics_range" && action.range) confirmations.push(`Analytics range set to ${action.range}.`);
    if (action.type === "set_analytics_filter" && action.filter) confirmations.push(`Analytics filter set to ${action.filter}.`);
    if (action.type === "set_metric_focus" && action.metric) confirmations.push(`${capitalize(action.metric)} is now the analytics focus.`);
    if (action.type === "open_panel" && action.target) confirmations.push(action.target === "analytics" ? "Analytics panel opened." : `${labelForTarget(action.target)} opened.`);
    if (action.type === "close_panel" && action.target) confirmations.push(action.target === "analytics" ? "Analytics hidden." : `${labelForTarget(action.target)} closed.`);
    if (action.type === "reset_dashboard") confirmations.push("Dashboard reset to default.");
    if ((action.type === "create_dashboard" || action.type === "compose_widgets") && action.widgets?.length) confirmations.push(`${action.title ?? "Temporary dashboard"} composed from ${action.widgets.length} registered widgets.`);
    if (action.type === "remove_generated_section") confirmations.push("Temporary dashboard removed.");
  }
  return confirmations.length ? confirmations.join(" ") : null;
}

function labelForTarget(target: import("../../lib/types").WidgetTarget) {
  const labels: Partial<Record<import("../../lib/types").WidgetTarget, string>> = {
    "model-usage": "Model usage", "response-time": "Response-time chart", "active-users": "Active users",
    activity: "Today's activity", performance: "Performance view", overview: "Widget overview",
    "model-comparison": "Model comparison", "system-status": "System status", "session-information": "Session information",
    telemetry: "Telemetry", "usage-trends": "Usage trends", messages: "Messages", revenue: "Revenue",
  };
  return labels[target] ?? target.replaceAll("-", " ");
}

function capitalize(value: string) { return value.charAt(0).toUpperCase() + value.slice(1); }
