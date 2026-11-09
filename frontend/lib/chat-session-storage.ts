import type { ChatMessage } from "@/lib/types";

const STORAGE_KEY = "analytical-chatbot:chat-session";

export type StoredChatSession = {
  messages: ChatMessage[];
  selectedDashboardIndex: number;
};

export function loadChatSession(): StoredChatSession | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as StoredChatSession;
    if (!Array.isArray(parsed.messages)) return null;
    return {
      messages: parsed.messages,
      selectedDashboardIndex:
        typeof parsed.selectedDashboardIndex === "number"
          ? parsed.selectedDashboardIndex
          : 0,
    };
  } catch {
    return null;
  }
}

export function saveChatSession(session: StoredChatSession): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  } catch {
    // ignore quota or private mode
  }
}
