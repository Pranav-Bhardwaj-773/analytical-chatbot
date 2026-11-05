import { NextResponse } from "next/server";

import { verifyEmailToken } from "@/lib/verification";

function loginRedirect(req: Request, params: Record<string, string>) {
  const loginBase = new URL("/login", req.url);
  for (const [key, value] of Object.entries(params)) {
    loginBase.searchParams.set(key, value);
  }
  return NextResponse.redirect(loginBase);
}

/** Legacy email links may still hit this URL; forward to the verify page without consuming the token. */
export async function GET(req: Request) {
  const token = new URL(req.url).searchParams.get("token");
  if (!token?.trim()) {
    return loginRedirect(req, { error: "InvalidToken" });
  }

  const verifyPage = new URL("/verify-email", req.url);
  verifyPage.searchParams.set("token", token.trim());
  return NextResponse.redirect(verifyPage);
}

export async function POST(req: Request) {
  let body: { token?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const token = body.token?.trim();
  if (!token) {
    return NextResponse.json({ result: "invalid" as const }, { status: 400 });
  }

  const result = await verifyEmailToken(token);
  return NextResponse.json({ result });
}
