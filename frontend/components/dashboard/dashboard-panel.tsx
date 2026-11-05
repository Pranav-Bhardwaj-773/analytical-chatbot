"use client";

import { BarChart3 } from "lucide-react";

import type { Dashboard } from "@/lib/types";
import { KpiCards } from "./kpi-cards";
import { ResultChart } from "./result-chart";
import { ResultTable } from "./result-table";

export function DashboardPanel({ dashboard }: { dashboard: Dashboard | null | undefined }) {
  if (!dashboard) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="mb-4 flex size-14 items-center justify-center rounded-xl border border-border bg-card text-primary">
          <BarChart3 className="size-7" aria-hidden />
        </div>
        <p className="text-sm font-medium">Your charts will show here</p>
        <p className="mt-2 max-w-[220px] text-xs leading-relaxed text-muted-foreground">
          Pick a suggested question or type your own to see colorful KPIs and graphs.
        </p>
        <div className="mt-5 flex flex-wrap justify-center gap-2">
          {["Bar", "Line", "Pie"].map((type) => (
            <span
              key={type}
              className="rounded-full border border-border/60 bg-muted/30 px-2.5 py-1 text-[10px] font-medium uppercase tracking-wide text-muted-foreground"
            >
              {type}
            </span>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-base font-semibold tracking-tight">{dashboard.title}</h2>
      <KpiCards kpis={dashboard.kpis} />
      <ResultChart chart={dashboard.chart} />
      <ResultTable table={dashboard.table} />
    </div>
  );
}
