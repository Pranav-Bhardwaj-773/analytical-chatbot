import { NextResponse } from "next/server";

import { internalServerErrorResponse, logApiError } from "@/lib/api-errors";
import { getEmailSetupHint } from "@/lib/email";
import { issuePasswordResetEmail } from "@/lib/password-reset";

export async function POST(req: Request) {
  let body: { email?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const email = body.email?.trim().toLowerCase();
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return NextResponse.json({ error: "Enter a valid email address." }, { status: 400 });
  }

  const setupHint = getEmailSetupHint();
  if (setupHint) {
    return NextResponse.json({ error: setupHint }, { status: 503 });
  }

  try {
    const issued = await issuePasswordResetEmail(email, req);
    const payload: { ok: true; emailSent: boolean; devResetUrl?: string } = {
      ok: true,
      emailSent: issued?.emailSent ?? false,
    };
    if (issued && !issued.emailSent && process.env.NODE_ENV === "development") {
      payload.devResetUrl = issued.resetUrl;
    }
    return NextResponse.json(payload);
  } catch (err) {
    logApiError("forgot-password", err);
    return NextResponse.json(internalServerErrorResponse(), { status: 503 });
  }
}
