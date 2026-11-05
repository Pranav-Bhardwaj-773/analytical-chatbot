import type { ChatRequest, ChatResponse } from "@/lib/types";
import { userFacingApiError, userMessages } from "@/lib/api-errors";

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message } satisfies ChatRequest),
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
