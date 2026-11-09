"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowUp,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  PanelRightOpen,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { sendChatMessage } from "@/lib/api";
import { userFacingError, userMessages } from "@/lib/api-errors";
import {
  loadChatSession,
  saveChatSession,
} from "@/lib/chat-session-storage";
import type { ChatMessage, Dashboard } from "@/lib/types";
import { ChatTypingIndicator } from "@/components/dashboard/chat-typing-indicator";
import { DashboardLoading } from "@/components/dashboard/dashboard-loading";
import { DashboardPanel } from "@/components/dashboard/dashboard-panel";
import { SuggestedQuestions } from "@/components/dashboard/suggested-questions";
import { cn } from "@/lib/utils";

function newId() {
  return crypto.randomUUID();
}

type DashboardSnapshot = {
  messageId: string;
  dashboard: Dashboard;
};

function buildDashboardSnapshots(messages: ChatMessage[]): DashboardSnapshot[] {
  return messages
    .filter(
      (m) => m.role === "assistant" && m.response?.dashboard != null,
    )
    .map((m) => ({
      messageId: m.id,
      dashboard: m.response!.dashboard!,
    }));
}

function lastExecutedSql(messages: ChatMessage[]): string | null | undefined {
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];
    if (msg.role === "assistant" && msg.response?.sql) {
      return msg.response.sql;
    }
  }
  return undefined;
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
  const [selectedDashboardIndex, setSelectedDashboardIndex] = useState(0);
  const [hydrated, setHydrated] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const prevSnapshotCount = useRef(0);

  const dashboardSnapshots = useMemo(
    () => buildDashboardSnapshots(messages),
    [messages],
  );

  const currentDashboard =
    dashboardSnapshots[selectedDashboardIndex]?.dashboard ?? null;

  const hasConversation = messages.length > 0 || loading;

  useEffect(() => {
    const stored = loadChatSession();
    if (stored?.messages.length) {
      setMessages(stored.messages);
      const snaps = buildDashboardSnapshots(stored.messages);
      const idx = Math.min(
        Math.max(0, stored.selectedDashboardIndex),
        Math.max(0, snaps.length - 1),
      );
      setSelectedDashboardIndex(idx);
      setShowInsightsMobile(snaps.length > 0);
      prevSnapshotCount.current = snaps.length;
    }
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    saveChatSession({ messages, selectedDashboardIndex });
  }, [messages, selectedDashboardIndex, hydrated]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  useEffect(() => {
    const count = dashboardSnapshots.length;
    if (count > prevSnapshotCount.current) {
      setSelectedDashboardIndex(count - 1);
    } else if (count > 0 && selectedDashboardIndex >= count) {
      setSelectedDashboardIndex(count - 1);
    }
    prevSnapshotCount.current = count;
  }, [dashboardSnapshots.length, selectedDashboardIndex]);

  function selectDashboardByMessageId(messageId: string) {
    const idx = dashboardSnapshots.findIndex((s) => s.messageId === messageId);
    if (idx >= 0) {
      setSelectedDashboardIndex(idx);
      setShowInsightsMobile(true);
    }
  }

  async function submitMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setError(null);
    setInput("");
    setShowInsightsMobile(true);

    const history = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));
    const last_sql = lastExecutedSql(messages);

    setMessages((m) => [
      ...m,
      { id: newId(), role: "user", content: trimmed },
    ]);
    setLoading(true);

    try {
      const res = await sendChatMessage(trimmed, { history, last_sql });
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

  const canGoPrev = selectedDashboardIndex > 0;
  const canGoNext = selectedDashboardIndex < dashboardSnapshots.length - 1;
  const dashboardPositionLabel =
    dashboardSnapshots.length > 0
      ? `${selectedDashboardIndex + 1} / ${dashboardSnapshots.length}`
      : null;

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
              {messages.map((msg) => {
                const hasDashboard =
                  msg.role === "assistant" && msg.response?.dashboard != null;
                const isActiveDashboard =
                  hasDashboard &&
                  dashboardSnapshots[selectedDashboardIndex]?.messageId ===
                    msg.id;

                return (
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
                    {msg.role === "user" ? (
                      <div className="max-w-[85%] rounded-xl bg-primary px-4 py-3 text-sm leading-relaxed text-primary-foreground">
                        {msg.content}
                      </div>
                    ) : (
                      <button
                        type="button"
                        disabled={!hasDashboard}
                        onClick={() =>
                          hasDashboard && selectDashboardByMessageId(msg.id)
                        }
                        className={cn(
                          "max-w-[85%] rounded-xl border border-border bg-card px-4 py-3 text-left text-sm leading-relaxed",
                          hasDashboard &&
                            "cursor-pointer transition-colors hover:bg-muted/50",
                          isActiveDashboard &&
                            "ring-2 ring-primary/40 ring-offset-2 ring-offset-background",
                        )}
                      >
                        {msg.content}
                        {hasDashboard && (
                          <span className="mt-2 block text-xs text-muted-foreground">
                            View chart in insights
                          </span>
                        )}
                      </button>
                    )}
                  </div>
                );
              })}
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
              aria-expanded={showInsightsMobile}
              aria-controls="insights-panel"
            >
              <PanelRightOpen className="size-4" />
              {showInsightsMobile ? "Hide insights" : "Show charts & KPIs"}
            </Button>
          </div>
        </div>
      </section>

      <aside
        id="insights-panel"
        className={cn(
          "insights-panel flex min-h-0 flex-col overflow-hidden border-t transition-[max-height,opacity] duration-300 ease-in-out motion-reduce:transition-none lg:overflow-visible lg:opacity-100 lg:transition-none",
          showInsightsMobile
            ? "max-h-[45vh] opacity-100 lg:max-h-none"
            : "pointer-events-none max-h-0 opacity-0 lg:pointer-events-auto lg:max-h-none",
        )}
      >
        <div className="flex shrink-0 items-center gap-2 border-b border-border px-4 py-3">
          <span className="size-2 rounded-full bg-primary" aria-hidden />
          <span className="text-sm font-medium text-foreground">Insights</span>
          <span className="text-xs text-muted-foreground">Charts & KPIs</span>
          {dashboardSnapshots.length > 1 && (
            <div className="ml-auto flex items-center gap-1">
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="size-8"
                disabled={!canGoPrev}
                onClick={() =>
                  setSelectedDashboardIndex((i) => Math.max(0, i - 1))
                }
                aria-label="Previous dashboard"
              >
                <ChevronLeft className="size-4" />
              </Button>
              <span className="min-w-[3.25rem] text-center text-xs tabular-nums text-muted-foreground">
                {dashboardPositionLabel}
              </span>
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="size-8"
                disabled={!canGoNext}
                onClick={() =>
                  setSelectedDashboardIndex((i) =>
                    Math.min(dashboardSnapshots.length - 1, i + 1),
                  )
                }
                aria-label="Next dashboard"
              >
                <ChevronRight className="size-4" />
              </Button>
            </div>
          )}
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto p-4">
          {loading && !currentDashboard ? (
            <DashboardLoading />
          ) : (
            <DashboardPanel dashboard={currentDashboard} />
          )}
        </div>
      </aside>
    </div>
  );
}
