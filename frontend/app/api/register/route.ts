import bcrypt from "bcryptjs";
import { NextResponse } from "next/server";

import { internalServerErrorResponse, logApiError } from "@/lib/api-errors";
import { getEmailSetupHint } from "@/lib/email";
import { isValidPhone, normalizePhone } from "@/lib/phone";
import { prisma } from "@/lib/prisma";
import { issueEmailVerification } from "@/lib/verification";

const MIN_PASSWORD_LENGTH = 8;
const MIN_NAME_LENGTH = 2;

export async function POST(req: Request) {
  let body: { email?: string; password?: string; confirmPassword?: string; name?: string; phone?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const email = body.email?.trim().toLowerCase();
  const password = body.password ?? "";
  const name = body.name?.trim() ?? "";
  const phone = normalizePhone(body.phone ?? "");

  if (!name || name.length < MIN_NAME_LENGTH) {
    return NextResponse.json({ error: "Name is required (at least 2 characters)." }, { status: 400 });
  }
  if (!isValidPhone(phone)) {
    return NextResponse.json({ error: "A valid phone number is required." }, { status: 400 });
  }
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return NextResponse.json({ error: "Enter a valid email address." }, { status: 400 });
  }
  if (password.length < MIN_PASSWORD_LENGTH) {
    return NextResponse.json(
      { error: `Password must be at least ${MIN_PASSWORD_LENGTH} characters.` },
      { status: 400 },
    );
  }

  const confirmPassword = body.confirmPassword ?? "";
  if (password !== confirmPassword) {
    return NextResponse.json(
      { error: "Password and confirm password do not match." },
      { status: 400 },
    );
  }

  const existing = await prisma.user.findUnique({ where: { email } });
  if (existing) {
    return NextResponse.json({ error: "An account with this email already exists." }, { status: 409 });
  }

  const passwordHash = await bcrypt.hash(password, 12);

  const setupHint = getEmailSetupHint();
  if (setupHint) {
    return NextResponse.json({ error: setupHint }, { status: 503 });
  }

  await prisma.user.create({
    data: {
      email,
      name,
      phone,
      passwordHash,
    },
  });

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
    await prisma.user.delete({ where: { email } }).catch(() => undefined);
    logApiError("register", err);
    return NextResponse.json(internalServerErrorResponse(), { status: 503 });
  }
}
