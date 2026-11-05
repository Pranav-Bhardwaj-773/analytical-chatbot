const RESEND_API = "https://api.resend.com/emails";

export function isEmailDeliveryConfigured(): boolean {
  if (process.env.RESEND_API_KEY?.trim()) {
    return true;
  }
  const host = process.env.SMTP_HOST?.trim();
  const user = process.env.SMTP_USER?.trim();
  const pass = process.env.SMTP_PASS?.trim();
  return Boolean(host && user && pass);
}

/** Plain-English hint for API responses when outbound email is not ready. */
export const EMAIL_SETUP_USER_MESSAGE =
  "We can't send email right now. Please try again later.";

/** When SMTP is partially configured, return a message for the client. */
export function getEmailSetupHint(): string | null {
  if (isEmailDeliveryConfigured()) {
    return null;
  }
  if (
    process.env.SMTP_HOST?.trim() &&
    process.env.SMTP_USER?.trim() &&
    !process.env.SMTP_PASS?.trim()
  ) {
    return EMAIL_SETUP_USER_MESSAGE;
  }
  return null;
}

function emailFromAddress(): string {
  return (
    process.env.EMAIL_FROM?.trim() ||
    process.env.SMTP_USER?.trim() ||
    "onboarding@resend.dev"
  );
}

async function sendViaResend(
  to: string,
  subject: string,
  html: string,
  text: string,
): Promise<void> {
  const apiKey = process.env.RESEND_API_KEY?.trim();
  if (!apiKey) {
    throw new Error("RESEND_API_KEY is missing.");
  }

  const res = await fetch(RESEND_API, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: emailFromAddress(),
      to,
      subject,
      html,
      text,
    }),
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Failed to send email (${res.status}): ${body}`);
  }
}

async function sendViaSmtp(
  to: string,
  subject: string,
  html: string,
  text: string,
): Promise<void> {
  const host = process.env.SMTP_HOST?.trim();
  const user = process.env.SMTP_USER?.trim();
  const pass = process.env.SMTP_PASS?.trim();
  if (!host || !user || !pass) {
    throw new Error("SMTP_HOST, SMTP_USER, and SMTP_PASS are required for SMTP email.");
  }

  const port = Number(process.env.SMTP_PORT ?? "587");
  const secure = process.env.SMTP_SECURE === "true" || port === 464;

  const nodemailer = await import("nodemailer");
  const transport = nodemailer.createTransport({
    host,
    port,
    secure,
    auth: { user, pass },
  });

  await transport.sendMail({
    from: emailFromAddress(),
    to,
    subject,
    html,
    text,
  });
}

export type DeliverVerificationResult = {
  delivered: boolean;
};

async function deliverAuthEmail(
  to: string,
  subject: string,
  html: string,
  text: string,
  devLogLabel: string,
  devLogUrl: string,
): Promise<DeliverVerificationResult> {
  if (process.env.RESEND_API_KEY?.trim()) {
    await sendViaResend(to, subject, html, text);
    return { delivered: true };
  }

  if (isEmailDeliveryConfigured()) {
    await sendViaSmtp(to, subject, html, text);
    return { delivered: true };
  }

  if (process.env.NODE_ENV === "development") {
    console.info(`[auth] ${devLogLabel}\n`, devLogUrl);
    return { delivered: false };
  }

  throw new Error("Email delivery is not configured.");
}

export async function deliverVerificationEmailMessage(
  to: string,
  verifyUrl: string,
): Promise<DeliverVerificationResult> {
  const subject = "Verify your email — School Analytics Chat";
  const html = `
    <p>Thanks for signing up. Click the link below to verify your email address:</p>
    <p><a href="${verifyUrl}">Verify email</a></p>
    <p>This link expires in 24 hours. If you did not create an account, you can ignore this message.</p>
  `.trim();
  const text = `Verify your email for School Analytics Chat:\n\n${verifyUrl}\n\nThis link expires in 24 hours.`;

  return deliverAuthEmail(
    to,
    subject,
    html,
    text,
    "Verification email not configured (set RESEND_API_KEY or SMTP_* in .env.local):",
    verifyUrl,
  );
}

export async function deliverPasswordResetEmailMessage(
  to: string,
  resetUrl: string,
): Promise<DeliverVerificationResult> {
  const subject = "Reset your password — School Analytics Chat";
  const html = `
    <p>We received a request to reset your password. Click the link below to choose a new password:</p>
    <p><a href="${resetUrl}">Reset password</a></p>
    <p>This link expires in 1 hour. If you did not request a reset, you can ignore this message.</p>
  `.trim();
  const text = `Reset your password for School Analytics Chat:\n\n${resetUrl}\n\nThis link expires in 1 hour.`;

  return deliverAuthEmail(
    to,
    subject,
    html,
    text,
    "Password reset email not configured (set RESEND_API_KEY or SMTP_* in .env.local):",
    resetUrl,
  );
}
