import type { ChatRequest, ChatResponse, ChatTurn } from "@/lib/types";
import { userFacingApiError, userMessages } from "@/lib/api-errors";

const MAX_HISTORY_TURNS = 10;
const MAX_TURN_CHARS = 1500;

function trimHistory(history: ChatTurn[]): ChatTurn[] {
  return history.slice(-MAX_HISTORY_TURNS).map((turn) => ({
    role: turn.role,
    content:
      turn.content.length > MAX_TURN_CHARS
        ? `${turn.content.slice(0, MAX_TURN_CHARS)}…`
        : turn.content,
  }));
}

export type SendChatOptions = {
  history?: ChatTurn[];
  last_sql?: string | null;
};

export async function sendChatMessage(
  message: string,
  options?: SendChatOptions,
): Promise<ChatResponse> {
  const body: ChatRequest = { message };
  if (options?.history?.length) {
    body.history = trimHistory(options.history);
  }
  if (options?.last_sql) {
    body.last_sql = options.last_sql;
  }

  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const raw =
      typeof data.detail === "string"
        ? data.detail
        : typeof data.error === "string"
          ? data.error
          : undefined;
    throw new Error(
      userFacingApiError(res.status, raw, userMessages.chat),
    );
  }

  return data as ChatResponse;
}
