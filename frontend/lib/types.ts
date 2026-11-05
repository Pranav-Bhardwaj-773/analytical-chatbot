export type ChatRequest = {
    message: string;
  };
  
  export type DashboardKpi = {
    id?: string;
    label: string;
    value: number | string;
  };
  
  export type ChartPoint = {
    x: string;
    y: number;
  };
  
  export type DashboardChart = {
    type: "bar" | "line" | "pie";
    title: string;
    points: ChartPoint[];
  };
  
  export type DashboardTable = {
    columns: string[];
    rows: Record<string, unknown>[];
  };
  
  export type Dashboard = {
    title: string;
    kpis: DashboardKpi[];
    chart: DashboardChart | null;
    table: DashboardTable;
  };
  
  export type ChatResponse = {
    answer: string;
    sql?: string | null;
    dashboard?: Dashboard | null;
  };
  
  export type ChatMessage = {
    id: string;
    role: "user" | "assistant";
    content: string;
    response?: ChatResponse;
  };