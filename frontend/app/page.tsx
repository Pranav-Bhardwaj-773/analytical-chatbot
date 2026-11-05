import { Suspense } from "react";

import { AppHeader } from "@/components/auth/app-header";
import { AppHeaderFallback } from "@/components/auth/app-header-fallback";
import { ChatPanel } from "@/components/dashboard/chart-panel";

export default function Home() {
  return (
    <div className="app-shell flex h-full min-h-0 flex-col">
      <Suspense fallback={<AppHeaderFallback />}>
        <AppHeader />
      </Suspense>
      <ChatPanel className="min-h-0 flex-1" />
    </div>
  );
}
