import crypto from "crypto";

import { resolveAuthBaseUrl } from "@/lib/auth-base-url";
import { deliverVerificationEmailMessage } from "@/lib/email";
import { prisma } from "@/lib/prisma";

const TOKEN_BYTES = 32;
const TOKEN_TTL_MS = 24 * 60 * 60 * 1000;

export function buildVerifyUrl(token: string, request?: Request): string {
  const base = resolveAuthBaseUrl(request);
  return `${base}/verify-email?token=${encodeURIComponent(token)}`;
}

export type IssueEmailVerificationResult = {
  verifyUrl: string;
  emailSent: boolean;
};

/** Creates a token, sends (or logs) the verification link, and returns the URL. */
export async function issueEmailVerification(
  email: string,
  request?: Request,
): Promise<IssueEmailVerificationResult> {
  const token = crypto.randomBytes(TOKEN_BYTES).toString("hex");
  const expires = new Date(Date.now() + TOKEN_TTL_MS);

  await prisma.verificationToken.deleteMany({ where: { identifier: email } });
  await prisma.verificationToken.create({
    data: { identifier: email, token, expires },
  });

  const verifyUrl = buildVerifyUrl(token, request);
  const delivery = await deliverVerificationEmailMessage(email, verifyUrl);
  return { verifyUrl, emailSent: delivery.delivered };
}

/** @deprecated Use issueEmailVerification */
export async function createAndSendVerificationEmail(
  email: string,
  request?: Request,
): Promise<IssueEmailVerificationResult> {
  return issueEmailVerification(email, request);
}

export async function verifyEmailToken(token: string): Promise<"ok" | "invalid" | "expired"> {
  const normalized = token.trim();
  if (!normalized) return "invalid";

  const record = await prisma.verificationToken.findUnique({ where: { token: normalized } });
  if (!record) return "invalid";
  if (record.expires < new Date()) {
    await prisma.verificationToken.delete({ where: { token: normalized } });
    return "expired";
  }

  await prisma.user.updateMany({
    where: { email: record.identifier },
    data: { emailVerified: new Date() },
  });
  await prisma.verificationToken.delete({ where: { token: normalized } });
  return "ok";
}
