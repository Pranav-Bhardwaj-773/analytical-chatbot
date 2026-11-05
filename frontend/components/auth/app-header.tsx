import { connection } from "next/server";
import { BarChart3 } from "lucide-react";

import { auth, signOut } from "@/auth";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";

export async function AppHeader() {
  await connection();
  const session = await auth();
  if (!session?.user) return null;

  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-border bg-card px-4 sm:px-6">
      <div className="flex min-w-0 items-center gap-2.5">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-lg border border-border bg-background text-primary">
          <BarChart3 className="size-4" aria-hidden />
        </span>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold sm:text-base">School Analytics</p>
          <p className="hidden truncate text-xs text-muted-foreground sm:block">
            Greenwood International School
          </p>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2 sm:gap-3">
        <span className="hidden max-w-[180px] truncate text-xs text-muted-foreground md:inline">
          {session.user.email}
        </span>
        <ThemeToggle />
        <form
          action={async () => {
            "use server";
            await signOut({ redirectTo: "/login" });
          }}
        >
          <Button type="submit" variant="outline" size="sm">
            Sign out
          </Button>
        </form>
      </div>
    </header>
  );
}
