"use client";

export function ChatTypingIndicator() {
  return (
    <div
      className="flex items-center rounded-xl border border-border bg-card px-4 py-3"
      role="status"
      aria-live="polite"
      aria-label="Assistant is typing"
    >
      <span className="chat-typing-dots flex items-center gap-1.5" aria-hidden>
        <span className="chat-typing-dot" />
        <span className="chat-typing-dot" />
        <span className="chat-typing-dot" />
      </span>
    </div>
  );
}
