"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { DashboardTable } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ResultTable({ table }: { table: DashboardTable }) {
  if (!table.columns?.length) return null;

  return (
    <Card className="border-border bg-background">
      <CardHeader className="border-b border-border pb-2">
        <CardTitle className="text-sm font-semibold">Detail table</CardTitle>
      </CardHeader>
      <CardContent className="max-h-56 overflow-auto p-0">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              {table.columns.map((col) => (
                <TableHead
                  key={col}
                  className="text-[10px] font-semibold uppercase tracking-wide text-primary"
                >
                  {col}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {table.rows.map((row, i) => (
              <TableRow key={i} className={i % 2 === 1 ? "bg-muted/20" : undefined}>
                {table.columns.map((col) => (
                  <TableCell key={col} className="text-xs tabular-nums">
                    {String(row[col] ?? "")}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
