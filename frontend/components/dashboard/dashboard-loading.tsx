"use client";

import { Loader2 } from "lucide-react";

export function DashboardLoading() {
  return (
    <div
      className="flex flex-col items-center justify-center gap-3 py-16"
      role="status"
      aria-live="polite"
      aria-label="Loading dashboard"
    >
      <Loader2 className="size-8 animate-spin text-primary" />
      <p className="text-xs text-muted-foreground">Building your charts…</p>
    </div>
  );
}
