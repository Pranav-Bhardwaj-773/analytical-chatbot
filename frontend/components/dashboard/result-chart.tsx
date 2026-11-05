"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DashboardChart } from "@/lib/types";
import { chartColor } from "@/lib/chart-colors";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const GRID = "oklch(0.68 0.02 264 / 18%)";
const TICK = "oklch(0.68 0.02 264)";

const TOOLTIP_STYLE = {
  borderRadius: "8px",
  border: "1px solid oklch(0.68 0.02 264 / 25%)",
  backgroundColor: "oklch(0.15 0.01 264)",
  color: "oklch(0.92 0.01 264)",
  fontSize: "12px",
};

export function ResultChart({ chart }: { chart: DashboardChart | null }) {
  if (!chart?.points?.length) return null;

  const data = chart.points.map((p) => ({ name: p.x, value: p.y }));
  const chartType = chart.type ?? "bar";

  return (
    <Card className="border-border bg-background">
      <CardHeader className="border-b border-border pb-2">
        <CardTitle className="text-sm font-semibold">{chart.title}</CardTitle>
      </CardHeader>
      <CardContent className="h-64 pt-4">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === "line" ? (
            <LineChart data={data}>
              <CartesianGrid stroke={GRID} strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: TICK }} />
              <YAxis tick={{ fontSize: 10, fill: TICK }} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Line
                type="monotone"
                dataKey="value"
                stroke="var(--cobalt)"
                strokeWidth={2.5}
                connectNulls
                dot={{ r: 4, fill: "var(--cobalt)", stroke: "var(--card)", strokeWidth: 2 }}
                activeDot={{ r: 5, fill: "var(--chart-3)" }}
              />
            </LineChart>
          ) : chartType === "pie" ? (
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={78}
                paddingAngle={2}
                label={({ name, value }) => `${name}: ${value}`}
              >
                {data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={chartColor(index)} stroke="var(--card)" />
                ))}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ fontSize: "11px", color: TICK }} />
            </PieChart>
          ) : (
            <BarChart data={data} barCategoryGap="18%">
              <CartesianGrid stroke={GRID} strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: TICK }} />
              <YAxis tick={{ fontSize: 10, fill: TICK }} />
              <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "oklch(0.68 0.02 264 / 8%)" }} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={48}>
                {data.map((_, index) => (
                  <Cell key={`bar-${index}`} fill={chartColor(index)} />
                ))}
              </Bar>
            </BarChart>
          )}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
