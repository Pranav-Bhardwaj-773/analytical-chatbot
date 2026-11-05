"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUp, BarChart3, PanelRightOpen } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { sendChatMessage } from "@/lib/api";
import { userFacingError, userMessages } from "@/lib/api-errors";
import type { ChatMessage, ChatResponse } from "@/lib/types";
import { ChatTypingIndicator } from "@/components/dashboard/chat-typing-indicator";
import { DashboardLoading } from "@/components/dashboard/dashboard-loading";
import { DashboardPanel } from "@/components/dashboard/dashboard-panel";
import { SuggestedQuestions } from "@/components/dashboard/suggested-questions";
import { cn } from "@/lib/utils";

function newId() {
  return crypto.randomUUID();
}

type ChatPanelProps = {
  className?: string;
};

export function ChatPanel({ className }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showInsightsMobile, setShowInsightsMobile] = useState(false);
  const [latestDashboard, setLatestDashboard] = useState<
    ChatResponse["dashboard"] | null
  >(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const hasConversation = messages.length > 0 || loading;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  async function submitMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setError(null);
    setInput("");
    setShowInsightsMobile(true);
    setMessages((m) => [
      ...m,
      { id: newId(), role: "user", content: trimmed },
    ]);
    setLoading(true);

    try {
      const res = await sendChatMessage(trimmed);
      setLatestDashboard(res.dashboard ?? null);
      setMessages((m) => [
        ...m,
        {
          id: newId(),
          role: "assistant",
          content: res.answer,
          response: res,
        },
      ]);
    } catch (err) {
      setError(userFacingError(err, userMessages.chat));
    } finally {
      setLoading(false);
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    await submitMessage(input);
  }

  const promptBar = (
    <form onSubmit={onSubmit} className="mx-auto w-full max-w-3xl">
      <div className="flex items-center gap-2 rounded-xl border border-border bg-card px-3 py-2 sm:px-4">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about students, exams, sports…"
          disabled={loading}
          className="h-11 flex-1 border-0 bg-transparent text-base shadow-none focus-visible:ring-0"
        />
        <Button
          type="submit"
          size="icon"
          disabled={loading || !input.trim()}
          className="size-10 shrink-0 rounded-lg"
          aria-label="Send message"
        >
          <ArrowUp className="size-5" />
        </Button>
      </div>
      {error && (
        <p className="mt-2 text-center text-sm text-destructive">{error}</p>
      )}
    </form>
  );

  return (
    <div
      className={cn(
        "flex min-h-0 flex-1 flex-col lg:grid lg:grid-cols-[minmax(0,1fr)_min(420px,38%)]",
        className,
      )}
    >
      <section className="relative flex min-h-0 flex-col bg-background">
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-4 sm:px-6">
          {!hasConversation ? (
            <div className="flex min-h-full flex-col items-center justify-center py-6 sm:py-10">
              <div className="mb-5 flex size-14 items-center justify-center rounded-xl border border-border bg-card text-primary">
                <BarChart3 className="size-7" aria-hidden />
              </div>
              <h1 className="text-center text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
                What would you like to know?
              </h1>
              <p className="mt-3 max-w-md text-center text-sm text-muted-foreground sm:text-base">
                Ask in plain English. KPIs and charts appear in the insights panel.
              </p>
              <div className="mt-10 w-full">
                <SuggestedQuestions
                  onSelect={(prompt) => submitMessage(prompt)}
                  disabled={loading}
                />
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-4 pb-4 pt-2">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={cn(
                    "flex w-full",
                    msg.role === "user" ? "justify-end" : "justify-start",
                  )}
                >
                  {msg.role === "assistant" && (
                    <span className="mr-2 mt-1 flex size-8 shrink-0 items-center justify-center rounded-lg border border-border bg-card text-primary">
                      <BarChart3 className="size-3.5" aria-hidden />
                    </span>
                  )}
                  <div
                    className={
                      msg.role === "user"
                        ? "max-w-[85%] rounded-xl bg-primary px-4 py-3 text-sm leading-relaxed text-primary-foreground"
                        : "max-w-[85%] rounded-xl border border-border bg-card px-4 py-3 text-sm leading-relaxed"
                    }
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start pl-10">
                  <ChatTypingIndicator />
                </div>
              )}
              <div ref={bottomRef} aria-hidden className="h-px shrink-0" />
            </div>
          )}
        </div>

        <div className="shrink-0 border-t border-border bg-card px-4 py-4 sm:px-6">
          {promptBar}
          <div className="mt-3 flex justify-center lg:hidden">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowInsightsMobile((v) => !v)}
            >
              <PanelRightOpen className="size-4" />
              {showInsightsMobile ? "Hide insights" : "Show charts & KPIs"}
            </Button>
          </div>
        </div>
      </section>

      <aside
        className={cn(
          "insights-panel flex min-h-0 flex-col border-t lg:border-t-0 lg:border-l",
          showInsightsMobile || latestDashboard || loading
            ? "flex max-h-[45vh] lg:max-h-none"
            : "hidden lg:flex",
        )}
      >
        <div className="flex shrink-0 items-center gap-2 border-b border-border px-4 py-3">
          <span className="size-2 rounded-full bg-primary" aria-hidden />
          <span className="text-sm font-medium text-foreground">Insights</span>
          <span className="text-xs text-muted-foreground">Charts & KPIs</span>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto p-4">
          {loading ? (
            <DashboardLoading />
          ) : (
            <DashboardPanel dashboard={latestDashboard} />
          )}
        </div>
      </aside>
    </div>
  );
}
