/** Public origin for auth links (verification, callbacks). */
export function resolveAuthBaseUrl(request?: Request): string {
  const configured = (process.env.AUTH_URL ?? process.env.NEXTAUTH_URL)?.replace(/\/$/, "");

  if (process.env.VERCEL_URL) {
    const vercelBase = `https://${process.env.VERCEL_URL.replace(/\/$/, "")}`;
    if (!configured || configured.includes("localhost")) {
      return vercelBase;
    }
  }

  if (configured) {
    return configured;
  }

  if (request) {
    const forwardedHost = request.headers.get("x-forwarded-host");
    const host = forwardedHost ?? request.headers.get("host");
    if (host) {
      const proto =
        request.headers.get("x-forwarded-proto") ??
        (host.includes("localhost") ? "http" : "https");
      return `${proto}://${host}`;
    }
    return new URL(request.url).origin;
  }

  return "http://localhost:3000";
}
