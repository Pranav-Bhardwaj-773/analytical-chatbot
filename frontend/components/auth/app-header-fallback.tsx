export function AppHeaderFallback() {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border/50 px-4 sm:px-6">
      <div className="h-9 w-40 animate-pulse rounded-full bg-muted/60" />
      <div className="h-8 w-16 animate-pulse rounded-lg bg-muted/60" />
    </header>
  );
}
