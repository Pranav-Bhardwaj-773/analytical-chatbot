import { NextResponse } from "next/server";

import { resetPasswordWithToken, validatePasswordResetToken } from "@/lib/password-reset";

const MIN_PASSWORD_LENGTH = 8;

export async function GET(req: Request) {
  const token = new URL(req.url).searchParams.get("token")?.trim();
  if (!token) {
    return NextResponse.json({ valid: false, reason: "invalid" as const }, { status: 400 });
  }
  const result = await validatePasswordResetToken(token);
  return NextResponse.json({ valid: result === "ok", reason: result });
}

export async function POST(req: Request) {
  let body: { token?: string; password?: string; confirmPassword?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const token = body.token?.trim();
  const password = body.password ?? "";
  const confirmPassword = body.confirmPassword ?? "";

  if (!token) {
    return NextResponse.json({ error: "Reset token is required." }, { status: 400 });
  }
  if (password.length < MIN_PASSWORD_LENGTH) {
    return NextResponse.json(
      { error: `Password must be at least ${MIN_PASSWORD_LENGTH} characters.` },
      { status: 400 },
    );
  }
  if (password !== confirmPassword) {
    return NextResponse.json({ error: "Passwords do not match." }, { status: 400 });
  }

  const result = await resetPasswordWithToken(token, password);
  if (result === "ok") {
    return NextResponse.json({ ok: true });
  }
  if (result === "expired") {
    return NextResponse.json({ error: "Reset link expired. Request a new one." }, { status: 400 });
  }
  return NextResponse.json({ error: "Invalid reset link." }, { status: 400 });
}
