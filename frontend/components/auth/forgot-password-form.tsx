"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { userFacingApiError } from "@/lib/api-errors";
import { isValidEmail, showApiErrorToast, showErrorToast, showSuccessToast } from "@/lib/toast-notify";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [devResetUrl, setDevResetUrl] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = email.trim().toLowerCase();
    if (!isValidEmail(trimmed)) {
      showErrorToast({ description: "Enter a valid email address." });
      return;
    }

    setLoading(true);
    setStatus(null);
    setDevResetUrl(null);
    try {
      const res = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: trimmed }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = userFacingApiError(res.status, data.error, "Could not send reset email.");
        setStatus(msg);
        showApiErrorToast(res.status, data.error, "Could not send reset email.");
        return;
      }

      if (data.emailSent === true) {
        setStatus("If an account exists for this email, we sent a password reset link.");
        showSuccessToast({ description: "Check your inbox for the reset link." });
        return;
      }

      if (typeof data.devResetUrl === "string") {
        setDevResetUrl(data.devResetUrl);
        setStatus("Development mode: use the reset link below (email was not sent).");
        return;
      }

      setStatus("If an account exists for this email, we sent a password reset link.");
    } catch {
      setStatus("Could not send reset email.");
      showErrorToast({ description: "Could not send reset email." });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Enter the email for your account. We will send a link to reset your password. Google-only
        accounts cannot reset a password here — use Google sign-in instead.
      </p>

      {devResetUrl && (
        <div className="rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
          <p className="font-medium">Development reset link</p>
          <Button
            render={<a href={devResetUrl} />}
            className="mt-2 w-full sm:w-auto"
            size="sm"
          >
            Open reset password page
          </Button>
          <p className="mt-2 break-all text-xs text-muted-foreground">{devResetUrl}</p>
        </div>
      )}

      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="email" className="text-sm font-medium">
            Email
          </label>
          <Input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
            disabled={loading}
          />
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Sending…" : "Send reset link"}
        </Button>
      </form>

      {status && <p className="text-sm text-muted-foreground">{status}</p>}

      <p className="text-center text-sm">
        <Link href="/login" className="font-medium underline-offset-4 hover:underline">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
