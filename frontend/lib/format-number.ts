/** Match backend MAX_DISPLAY_DECIMALS (2) for display-only formatting. */
const MAX_DECIMALS = 2;

export function formatDisplayNumber(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "boolean") return String(value);
  const n = Number(value);
  if (!Number.isFinite(n)) return String(value);
  if (Math.abs(n - Math.round(n)) < 1e-9) return String(Math.round(n));
  const rounded = Math.round(n * 10 ** MAX_DECIMALS) / 10 ** MAX_DECIMALS;
  return String(rounded)
    .replace(/(\.\d*?[1-9])0+$/u, "$1")
    .replace(/\.0+$/u, "");
}
