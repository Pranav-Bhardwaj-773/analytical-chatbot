"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { userFacingApiError } from "@/lib/api-errors";
import { showApiErrorToast, showErrorToast, showSuccessToast } from "@/lib/toast-notify";

type VerifyState = "idle" | "working" | "ok" | "expired" | "invalid";

export function VerifyEmailPanel() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialEmail = searchParams.get("email") ?? "";
  const tokenFromUrl = searchParams.get("token")?.trim() ?? "";

  const [email, setEmail] = useState(initialEmail);
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [verifyState, setVerifyState] = useState<VerifyState>("idle");
  const [devVerifyUrl, setDevVerifyUrl] = useState<string | null>(null);
  const tokenAttempted = useRef<string | null>(null);

  useEffect(() => {
    const stored = sessionStorage.getItem("devVerifyUrl");
    if (stored) {
      setDevVerifyUrl(stored);
      sessionStorage.removeItem("devVerifyUrl");
    }
  }, []);

  useEffect(() => {
    if (!tokenFromUrl || tokenAttempted.current === tokenFromUrl) return;
    tokenAttempted.current = tokenFromUrl;

    async function confirmToken() {
      setVerifyState("working");
      try {
        const res = await fetch("/api/auth/verify-email", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token: tokenFromUrl }),
        });
        const data = await res.json().catch(() => ({}));
        const result = data.result as VerifyState | undefined;

        if (result === "ok") {
          setVerifyState("ok");
          showSuccessToast({ description: "Email verified. You can sign in now." });
          router.replace("/login?verified=1");
          return;
        }
        if (result === "expired") {
          setVerifyState("expired");
          showErrorToast({ description: "Verification link expired. Request a new one below." });
          return;
        }
        setVerifyState("invalid");
        showErrorToast({ description: "Invalid verification link. Request a new one below." });
      } catch {
        setVerifyState("invalid");
        showErrorToast({ description: "Could not verify email. Try again or request a new link." });
      }
    }

    void confirmToken();
  }, [tokenFromUrl, router]);

  async function onResend(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setStatus(null);
    setDevVerifyUrl(null);
    try {
      const res = await fetch("/api/auth/resend-verification", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim().toLowerCase() }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = userFacingApiError(res.status, data.error, "Could not send email.");
        setStatus(msg);
        showApiErrorToast(res.status, data.error, "Could not send email.");
        return;
      }

      if (data.emailSent === true) {
        setStatus("Verification email sent. Check your inbox and spam folder.");
        showSuccessToast({ description: "Verification email sent." });
        return;
      }

      if (typeof data.devVerifyUrl === "string") {
        setDevVerifyUrl(data.devVerifyUrl);
        setStatus(
          "No real email is sent in development until RESEND_API_KEY is set in .env.local. Use the link below.",
        );
        showSuccessToast({ description: "Verification link ready — open it below." });
        return;
      }

      setStatus("If an unverified account exists for this email, a new link was created.");
    } catch {
      setStatus("Could not send email.");
      showErrorToast({ description: "Could not send email." });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      {verifyState === "working" && (
        <p className="text-sm text-muted-foreground">Verifying your email…</p>
      )}

      {devVerifyUrl && (
        <div className="rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
          <p className="font-medium">Your verification link (development)</p>
          <p className="mt-1 text-muted-foreground">
            Gmail will not receive a message until you add{" "}
            <code className="text-xs">RESEND_API_KEY</code> to{" "}
            <code className="text-xs">frontend/.env.local</code> and restart{" "}
            <code className="text-xs">npm run dev</code>. For now, click:
          </p>
          <Button asChild className="mt-3 w-full sm:w-auto" size="sm">
            <a href={devVerifyUrl}>Verify my email</a>
          </Button>
          <p className="mt-2 break-all text-xs text-muted-foreground">{devVerifyUrl}</p>
        </div>
      )}

      {!devVerifyUrl && (
        <p className="text-sm text-muted-foreground">
          After you click resend, either check your inbox (when Resend is configured) or use the
          development link shown on this page.
        </p>
      )}

      <form onSubmit={onResend} className="space-y-3">
        <div className="space-y-2">
          <label htmlFor="email" className="text-sm font-medium">
            Email
          </label>
          <Input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
          />
        </div>
        <Button type="submit" variant="secondary" disabled={loading}>
          {loading ? "Sending…" : "Resend verification email"}
        </Button>
      </form>
      {status && <p className="text-sm text-muted-foreground">{status}</p>}
      <p className="text-sm">
        <Link href="/login" className="font-medium underline-offset-4 hover:underline">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
