import crypto from "crypto";

import { resolveAuthBaseUrl } from "@/lib/auth-base-url";
import { deliverPasswordResetEmailMessage } from "@/lib/email";
import { prisma } from "@/lib/prisma";

const TOKEN_BYTES = 32;
const RESET_TOKEN_TTL_MS = 60 * 60 * 1000;

export const PASSWORD_RESET_IDENTIFIER_PREFIX = "password-reset:";

export function passwordResetIdentifier(email: string): string {
  return `${PASSWORD_RESET_IDENTIFIER_PREFIX}${email.trim().toLowerCase()}`;
}

export function buildResetPasswordUrl(token: string, request?: Request): string {
  const base = resolveAuthBaseUrl(request);
  return `${base}/reset-password?token=${encodeURIComponent(token)}`;
}

export type IssuePasswordResetResult = {
  resetUrl: string;
  emailSent: boolean;
};

export async function issuePasswordResetEmail(
  email: string,
  request?: Request,
): Promise<IssuePasswordResetResult | null> {
  const normalized = email.trim().toLowerCase();
  const user = await prisma.user.findUnique({ where: { email: normalized } });
  if (!user?.passwordHash) {
    return null;
  }

  const token = crypto.randomBytes(TOKEN_BYTES).toString("hex");
  const expires = new Date(Date.now() + RESET_TOKEN_TTL_MS);
  const identifier = passwordResetIdentifier(normalized);

  await prisma.verificationToken.deleteMany({ where: { identifier } });
  await prisma.verificationToken.create({
    data: { identifier, token, expires },
  });

  const resetUrl = buildResetPasswordUrl(token, request);
  const delivery = await deliverPasswordResetEmailMessage(normalized, resetUrl);
  return { resetUrl, emailSent: delivery.delivered };
}

export async function resetPasswordWithToken(
  token: string,
  newPassword: string,
): Promise<"ok" | "invalid" | "expired"> {
  const normalized = token.trim();
  if (!normalized) return "invalid";

  const record = await prisma.verificationToken.findUnique({ where: { token: normalized } });
  if (!record || !record.identifier.startsWith(PASSWORD_RESET_IDENTIFIER_PREFIX)) {
    return "invalid";
  }
  if (record.expires < new Date()) {
    await prisma.verificationToken.delete({ where: { token: normalized } });
    return "expired";
  }

  const email = record.identifier.slice(PASSWORD_RESET_IDENTIFIER_PREFIX.length);
  const bcrypt = await import("bcryptjs");
  const passwordHash = await bcrypt.hash(newPassword, 12);

  await prisma.user.updateMany({
    where: { email },
    data: { passwordHash },
  });
  await prisma.verificationToken.delete({ where: { token: normalized } });
  return "ok";
}

export async function validatePasswordResetToken(
  token: string,
): Promise<"ok" | "invalid" | "expired"> {
  const normalized = token.trim();
  if (!normalized) return "invalid";

  const record = await prisma.verificationToken.findUnique({ where: { token: normalized } });
  if (!record || !record.identifier.startsWith(PASSWORD_RESET_IDENTIFIER_PREFIX)) {
    return "invalid";
  }
  if (record.expires < new Date()) {
    await prisma.verificationToken.delete({ where: { token: normalized } });
    return "expired";
  }
  return "ok";
}
