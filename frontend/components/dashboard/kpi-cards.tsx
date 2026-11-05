"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DashboardKpi } from "@/lib/types";
import { cn } from "@/lib/utils";

const KPI_VALUE_COLORS = [
  "text-chart-1",
  "text-chart-2",
  "text-chart-3",
  "text-chart-4",
  "text-chart-5",
  "text-chart-6",
] as const;

export function KpiCards({ kpis }: { kpis: DashboardKpi[] }) {
  if (!kpis.length) return null;

  return (
    <div className="grid grid-cols-2 gap-2.5">
      {kpis.map((kpi, index) => {
        const valueColor = KPI_VALUE_COLORS[index % KPI_VALUE_COLORS.length];
        return (
          <Card
            key={kpi.id ?? `${index}-${kpi.label}`}
            className="border-border bg-background"
          >
            <CardHeader className="pb-0">
              <CardTitle className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                {kpi.label}
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-1">
              <p className={cn("text-xl font-bold tabular-nums", valueColor)}>{kpi.value}</p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
