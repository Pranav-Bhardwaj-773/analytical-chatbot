const GENERIC_SERVER_ERROR = "Something went wrong. Please try again later.";
const GENERIC_CLIENT_ERROR = "Something went wrong. Please try again.";
const EMAIL_UNAVAILABLE =
  "We can't send email right now. Please try again later.";
const CHAT_ERROR =
  "We couldn't answer that question. Try rephrasing it or ask something simpler.";
const SIGN_IN_REQUIRED = "Please sign in to continue.";

/** API messages that are already plain English and safe to show. */
const ALLOWED_API_ERRORS = new Set([
  "Email is required.",
  "Enter a valid email address.",
  "Name is required (at least 2 characters).",
  "A valid phone number is required.",
  "Password and confirm password do not match.",
  "An account with this email already exists.",
  "This email is already verified. You can sign in.",
  "This account uses Google sign-in. Sign in with Google instead.",
  "Could not send verification email.",
  "Could not send reset email.",
  "Reset token is required.",
  "Reset link expired. Request a new one.",
  "Invalid reset link.",
  "Passwords do not match.",
  "Email and password are required.",
  "Something went wrong. Please try again.",
  EMAIL_UNAVAILABLE,
]);

function looksLikeInternalError(message: string): boolean {
  return (
    /is not a function/i.test(message) ||
    /TURBOPACK/i.test(message) ||
    /__TURBOPACK/i.test(message) ||
    /\$5bproject\$5d/i.test(message) ||
    /node_modules/i.test(message) ||
    /^TypeError:/i.test(message) ||
    /^ReferenceError:/i.test(message) ||
    /^\(0\s*,/.test(message) ||
    /Traceback/i.test(message) ||
    /\.py"/i.test(message)
  );
}

function looksLikeTechnicalSetup(message: string): boolean {
  return (
    /RESEND_API_KEY|SMTP_|EMAIL_FROM|\.env\.local/i.test(message) ||
    /Email is not configured/i.test(message) ||
    /SMTP_PASS is missing/i.test(message) ||
    /Failed to send email\s*\(\d+\)/i.test(message) ||
    /Failed to send verification email/i.test(message)
  );
}

function looksLikeChatBackendError(message: string): boolean {
  return (
    /Query failed/i.test(message) ||
    /Model request failed/i.test(message) ||
    /did not return SQL/i.test(message) ||
    /Fixed SQL invalid/i.test(message) ||
    /retry could not reach/i.test(message)
  );
}

/**
 * Turn any raw error string into plain English, or return undefined to use a caller fallback.
 */
export function plainEnglishMessage(message: string): string | undefined {
  const trimmed = message.trim();
  if (!trimmed) return undefined;

  if (looksLikeInternalError(trimmed)) {
    return GENERIC_SERVER_ERROR;
  }

  if (looksLikeTechnicalSetup(trimmed)) {
    return EMAIL_UNAVAILABLE;
  }

  if (/^Unauthorized$/i.test(trimmed) || /^Not authenticated$/i.test(trimmed)) {
    return SIGN_IN_REQUIRED;
  }

  if (trimmed === "Invalid JSON body") {
    return GENERIC_CLIENT_ERROR;
  }

  if (looksLikeChatBackendError(trimmed)) {
    return CHAT_ERROR;
  }

  if (/^Password must be at least \d+ characters\.$/.test(trimmed)) {
    return trimmed;
  }

  if (ALLOWED_API_ERRORS.has(trimmed)) {
    return trimmed;
  }

  if (/^[A-Z][A-Z0-9_]{2,}$/.test(trimmed)) {
    return undefined;
  }

  if (trimmed.length > 160) {
    return undefined;
  }

  return undefined;
}

/**
 * Map API error payloads to user-safe copy. Never surface stack traces, env vars, or SQL.
 */
export function userFacingApiError(
  status: number,
  bodyError: unknown,
  fallback: string,
): string {
  if (typeof bodyError !== "string" || !bodyError.trim()) {
    return status >= 500 ? GENERIC_SERVER_ERROR : fallback;
  }

  const mapped = plainEnglishMessage(bodyError);
  if (mapped) {
    return mapped;
  }

  if (status >= 500) {
    return GENERIC_SERVER_ERROR;
  }

  return fallback;
}

/** Use in catch blocks when displaying Error.message in the UI. */
export function userFacingError(err: unknown, fallback: string): string {
  if (err instanceof Error && err.message.trim()) {
    const mapped = plainEnglishMessage(err.message);
    if (mapped) return mapped;
  }
  return fallback;
}

export function logApiError(scope: string, err: unknown): void {
  console.error(`[${scope}]`, err);
}

export function internalServerErrorResponse() {
  return { error: GENERIC_SERVER_ERROR };
}

export const userMessages = {
  emailUnavailable: EMAIL_UNAVAILABLE,
  genericServer: GENERIC_SERVER_ERROR,
  genericClient: GENERIC_CLIENT_ERROR,
  chat: CHAT_ERROR,
  signInRequired: SIGN_IN_REQUIRED,
} as const;
