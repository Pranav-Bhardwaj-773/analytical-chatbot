"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { showApiErrorToast, showErrorToast, showSuccessToast } from "@/lib/toast-notify";

const MIN_PASSWORD_LENGTH = 8;

export function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token")?.trim() ?? "";

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [tokenStatus, setTokenStatus] = useState<"checking" | "ok" | "invalid" | "expired">(
    token ? "checking" : "invalid",
  );

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    async function check() {
      try {
        const res = await fetch(
          `/api/auth/reset-password?token=${encodeURIComponent(token)}`,
        );
        const data = await res.json().catch(() => ({}));
        if (cancelled) return;
        if (data.valid === true) {
          setTokenStatus("ok");
        } else if (data.reason === "expired") {
          setTokenStatus("expired");
        } else {
          setTokenStatus("invalid");
        }
      } catch {
        if (!cancelled) setTokenStatus("invalid");
      }
    }
    void check();
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password.length < MIN_PASSWORD_LENGTH) {
      showErrorToast({
        description: `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`,
      });
      return;
    }
    if (password !== confirmPassword) {
      showErrorToast({ description: "Passwords do not match." });
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password, confirmPassword }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        showApiErrorToast(res.status, data.error, "Could not reset password.");
        return;
      }
      showSuccessToast({ description: "Password updated. You can sign in now." });
      router.replace("/login?reset=1");
    } catch {
      showErrorToast({ description: "Could not reset password." });
    } finally {
      setLoading(false);
    }
  }

  if (!token || tokenStatus === "invalid") {
    return (
      <div className="space-y-4 text-sm">
        <p className="text-muted-foreground">This password reset link is invalid or incomplete.</p>
        <Link href="/forgot-password" className="font-medium underline-offset-4 hover:underline">
          Request a new reset link
        </Link>
      </div>
    );
  }

  if (tokenStatus === "checking") {
    return <p className="text-sm text-muted-foreground">Checking reset link…</p>;
  }

  if (tokenStatus === "expired") {
    return (
      <div className="space-y-4 text-sm">
        <p className="text-muted-foreground">This reset link has expired.</p>
        <Link href="/forgot-password" className="font-medium underline-offset-4 hover:underline">
          Request a new reset link
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="space-y-2">
        <label htmlFor="password" className="text-sm font-medium">
          New password
        </label>
        <Input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
          minLength={MIN_PASSWORD_LENGTH}
          required
          disabled={loading}
        />
        <p className="text-xs text-muted-foreground">At least {MIN_PASSWORD_LENGTH} characters.</p>
      </div>
      <div className="space-y-2">
        <label htmlFor="confirmPassword" className="text-sm font-medium">
          Confirm new password
        </label>
        <Input
          id="confirmPassword"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          autoComplete="new-password"
          minLength={MIN_PASSWORD_LENGTH}
          required
          disabled={loading}
        />
      </div>
      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? "Updating…" : "Update password"}
      </Button>
    </form>
  );
}
