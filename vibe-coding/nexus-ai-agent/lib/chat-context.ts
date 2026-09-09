import type { ChatMessage } from "./types";

export const CHAT_STORAGE_KEY = "nexus-conversation-v1";
export const MAX_CONVERSATION_MESSAGES = 24;
export const MAX_CONVERSATION_CHARS = 16000;

export type ApiConversationMessage = {
  role: "user" | "assistant";
  content: string;
};

function isChatMessage(value: unknown): value is ChatMessage {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.id === "string" &&
    (candidate.role === "user" || candidate.role === "agent") &&
    typeof candidate.content === "string" &&
    candidate.content.trim().length > 0
  );
}

export function trimConversation(messages: ChatMessage[]): ChatMessage[] {
  const valid = messages.filter(isChatMessage);
  const recent = valid.slice(-MAX_CONVERSATION_MESSAGES);
  const bounded: ChatMessage[] = [];
  let chars = 0;
  for (let i = recent.length - 1; i >= 0; i -= 1) {
    const message = recent[i];
    const nextChars = chars + message.content.length;
    if (bounded.length > 0 && nextChars > MAX_CONVERSATION_CHARS) break;
    bounded.unshift(message);
    chars = nextChars;
  }
  return bounded;
}

export function loadConversation(): ChatMessage[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(CHAT_STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return trimConversation(parsed);
  } catch {
    return [];
  }
}

export function saveConversation(messages: ChatMessage[]) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(trimConversation(messages)));
  } catch {
    // Local persistence is best-effort; the active React state remains authoritative.
  }
}

export function toApiConversation(messages: ChatMessage[]): ApiConversationMessage[] {
  return trimConversation(messages).map((message) => ({
    role: message.role === "agent" ? "assistant" : "user",
    content: message.content,
  }));
}
