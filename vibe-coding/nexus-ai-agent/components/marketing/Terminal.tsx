"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { Maximize2, Minus, X, RotateCcw, Send, Activity } from "lucide-react";
import { sendChatMessage } from "../../lib/api";
import { useNexusUI } from "../../lib/nexus-ui";
import { loadConversation, saveConversation, trimConversation } from "../../lib/chat-context";
import type { ChatMessage } from "../../lib/types";

export function Terminal() {
  const [input, setInput] = useState("");
  const [lines, setLines] = useState<string[]>([
    "> Hello! I'm Nexus.",
    "> Ask me anything - ideas, code, notes, or just random thoughts.",
  ]);
  const [conversation, setConversation] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const [maximized, setMaximized] = useState(false);
  const [closed, setClosed] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const stickToBottom = useRef(true);
  const conversationHydrated = useRef(false);
  const submitting = useRef(false);
  const { model, accent, visibleWidgets, analyticsRange, analyticsFilter, generatedSection, applyActions } = useNexusUI();

  useEffect(() => {
    setConversation(loadConversation());
    conversationHydrated.current = true;
  }, []);

  useEffect(() => {
    if (conversationHydrated.current) saveConversation(conversation);
  }, [conversation]);

  useEffect(() => {
    if (!scrollRef.current || !stickToBottom.current) return;
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [lines, busy]);

  function onScroll() {
    const el = scrollRef.current;
    if (!el) return;
    stickToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    const q = input.trim();
    if (!q || busy || submitting.current) return;
    submitting.current = true;
    setInput("");
    stickToBottom.current = true;
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const userMessage: ChatMessage = { id, role: "user", content: q };
    const nextConversation = trimConversation([...conversation, userMessage]);
    setConversation(nextConversation);
    setLines((v) => [...v, `> ${q}`]);
    setBusy(true);
    try {
      // `conversation` intentionally excludes the new user turn; the backend/provider appends `q` after prior history.
      const responseStarted = typeof performance !== "undefined" ? performance.now() : Date.now();
      const res = await sendChatMessage(q, conversation, {
        model,
        accent,
        visibleWidgets,
        analyticsRange,
        analyticsFilter,
        generatedSection,
      });
      const backendToAction = (typeof performance !== "undefined" ? performance.now() : Date.now()) - responseStarted;
      const actionStarted = typeof performance !== "undefined" ? performance.now() : Date.now();
      const executed = await applyActions(res.actions);
      if (typeof console !== "undefined") {
        const actionDuration = (typeof performance !== "undefined" ? performance.now() : Date.now()) - actionStarted;
        console.debug(`[CHAT PERF FRONTEND] actions=${res.actions.length} state_commit_and_render=${actionDuration.toFixed(3)}ms backend_to_action=${backendToAction.toFixed(3)}ms`);
      }
      const actionMessage = executed.length ? executed.map((action) => {
        if (action.type === "set_model") return action.model === "deep" ? "NEXUS Deep is now active." : "NEXUS is now active.";
        if (action.type === "set_accent_color" && action.accent) return `Accent changed to ${action.accent}.`;
        if (action.type === "show_widget" && action.target) return action.target === "analytics" ? "Analytics panel opened." : action.target === "overview" ? "Widgets are now visible." : `${action.target.replaceAll("-", " ")} is now visible.`;
        if (action.type === "hide_widget" && action.target) return action.target === "analytics" ? "Analytics hidden." : action.target === "overview" ? "Widgets hidden." : `${action.target.replaceAll("-", " ")} hidden.`;
        if (action.type === "set_analytics_range" && action.range) return `Analytics range set to ${action.range}.`;
        if (action.type === "set_analytics_filter" && action.filter) return `Analytics filter set to ${action.filter}.`;
        return action.type.replaceAll("_", " ");
      }).join(" ") : null;
      const actionFailure = res.actions.length > executed.length;
      const coreMessage = actionFailure
        ? actionMessage ? `${actionMessage} Some requested UI changes could not be verified.` : "I couldn't execute that UI action."
        : actionMessage ?? res.message;
      const responseMessage = res.recovered ? `Local recovery mode: ${coreMessage}` : coreMessage;
      const assistantMessage: ChatMessage = { id: `${id}-reply`, role: "agent", content: responseMessage };
      setConversation((v) => trimConversation([...v, assistantMessage]));
      setLines((v) => [...v, `> ${responseMessage}`]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "The agent could not complete this request.";
      const assistantMessage: ChatMessage = { id: `${id}-reply`, role: "agent", content: message };
      setConversation((v) => trimConversation([...v, assistantMessage]));
      setLines((v) => [...v, `> ${message}`]);
    } finally {
      setBusy(false);
      submitting.current = false;
    }
  }

  if (closed) return <section className="terminal-wrap"><button className="ghost-button terminal-reopen" onClick={() => { setClosed(false); setMinimized(false); setMaximized(false); }}><RotateCcw size={14}/> REOPEN NEXUS.EXE</button><div className="terminal-easter"><span className="mascot">◒</span><span>CURIOSITY LOOKS GOOD ON YOU.</span></div></section>;

  return <section className={`terminal-wrap ${maximized ? "terminal-wrap-maximized" : ""}`}>
    <div className={`terminal glass-card ${minimized ? "terminal-minimized" : ""} ${maximized ? "terminal-maximized" : ""}`}>
      <div className="terminal-header">
        <span>/ NEXUS.EXE</span>
        <div className="terminal-window-controls">
          <button aria-label={minimized ? "Restore terminal" : "Minimize terminal"} onClick={() => setMinimized((v) => !v)}>{minimized ? <RotateCcw size={13}/> : <Minus size={13}/>}</button>
          <button aria-label={maximized ? "Restore size" : "Maximize terminal"} onClick={() => { setMaximized((v) => !v); setMinimized(false); }}><Maximize2 size={13}/></button>
          <button aria-label="Close terminal" onClick={() => { setClosed(true); setMaximized(false); setMinimized(false); }}><X size={13}/></button>
        </div>
      </div>
      {!minimized && <>
        <div className="terminal-telemetry" aria-label="Terminal telemetry">
          <span><Activity size={12}/> MODEL <b>{model === "deep" ? "NEXUS DEEP" : "NEXUS"}</b></span>
          <span>LATENCY <b>{busy ? "…" : "1.2s"}</b></span>
          <span>MESSAGES <b>{Math.max(0, lines.length - 2).toString().padStart(2, "0")}</b></span>
          <span>STATUS <b>{busy ? "THINKING" : "READY"}</b></span>
        </div>
        <div className="terminal-body terminal-scroll" ref={scrollRef} onScroll={onScroll} aria-live="polite">
          {lines.map((line, i) => <div key={`${line}-${i}`} className="terminal-line">{line}</div>)}
          <form onSubmit={submit} className="terminal-input"><span>&gt;</span><input value={input} onChange={(e) => setInput(e.target.value)} placeholder={busy ? "processing…" : "type a thought"} /><span className="cursor">▌</span><button type="submit" className="terminal-send" disabled={busy || !input.trim()} aria-label="Send message"><Send size={13}/></button></form>
        </div>
      </>}
    </div>
    <div className="terminal-easter"><span className="mascot">◒</span><span>CURIOSITY LOOKS GOOD ON YOU.</span></div>
  </section>;
}
