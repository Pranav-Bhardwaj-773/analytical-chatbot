import { NextResponse } from "next/server";

import { internalServerErrorResponse, logApiError } from "@/lib/api-errors";
import { getEmailSetupHint, isEmailDeliveryConfigured } from "@/lib/email";
import { prisma } from "@/lib/prisma";
import { issueEmailVerification } from "@/lib/verification";

export async function POST(req: Request) {
  let body: { email?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const email = body.email?.trim().toLowerCase();
  if (!email) {
    return NextResponse.json({ error: "Email is required." }, { status: 400 });
  }

  const user = await prisma.user.findUnique({ where: { email } });
  if (!user) {
    return NextResponse.json({ ok: true, emailSent: false });
  }
  if (user.emailVerified) {
    return NextResponse.json({ error: "This email is already verified. You can sign in." }, { status: 400 });
  }
  if (!user.passwordHash) {
    return NextResponse.json(
      { error: "This account uses Google sign-in. Sign in with Google instead." },
      { status: 400 },
    );
  }

  const setupHint = getEmailSetupHint();
  if (setupHint && !isEmailDeliveryConfigured()) {
    return NextResponse.json({ error: setupHint }, { status: 503 });
  }

  try {
    const issued = await issueEmailVerification(email, req);
    const payload: { ok: true; emailSent: boolean; devVerifyUrl?: string } = {
      ok: true,
      emailSent: issued.emailSent,
    };
    if (!issued.emailSent && process.env.NODE_ENV === "development") {
      payload.devVerifyUrl = issued.verifyUrl;
    }
    return NextResponse.json(payload);
  } catch (err) {
    logApiError("resend-verification", err);
    return NextResponse.json(internalServerErrorResponse(), { status: 503 });
  }
}
