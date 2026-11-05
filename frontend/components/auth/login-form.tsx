"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useActionState, useEffect, useRef, useState } from "react";

import { loginWithCredentials, type LoginState } from "@/app/login/actions";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { isValidEmail, showApiErrorToast, showErrorToast, showSuccessToast } from "@/lib/toast-notify";
import { cn } from "@/lib/utils";

const initialState: LoginState = {};

type LoginFormProps = {
  googleAuthEnabled?: boolean;
};

function loginErrorMessage(error: string | undefined): string | null {
  if (!error) return null;
  if (error === "email_not_verified") {
    return "Verify your email before signing in. Check your inbox or request a new link below.";
  }
  if (error === "invalid_credentials") {
    return "Invalid email or password.";
  }
  return error;
}

export function LoginForm({ googleAuthEnabled = false }: LoginFormProps) {
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") ?? "/";
  const googleHref = `/api/auth/signin/google?${new URLSearchParams({ callbackUrl }).toString()}`;
  const verified = searchParams.get("verified") === "1";
  const urlError = searchParams.get("error");

  const [state, formAction, pending] = useActionState(loginWithCredentials, initialState);
  const [resendEmail, setResendEmail] = useState("");
  const [resendLoading, setResendLoading] = useState(false);
  const lastLoginError = useRef<string | undefined>(undefined);

  useEffect(() => {
    if (verified) {
      showSuccessToast({ description: "Email verified. You can sign in now." });
    }
  }, [verified]);

  useEffect(() => {
    if (searchParams.get("reset") === "1") {
      showSuccessToast({ description: "Password updated. Sign in with your new password." });
    }
  }, [searchParams]);

  useEffect(() => {
    if (urlError === "TokenExpired") {
      showErrorToast({ description: "Verification link expired. Request a new one below." });
    } else if (urlError === "InvalidToken") {
      showErrorToast({ description: "Invalid verification link." });
    } else if (urlError === "CredentialsSignin" || urlError === "EmailNotVerified") {
      showErrorToast({
        description:
          urlError === "EmailNotVerified"
            ? "Verify your email before signing in."
            : "Invalid email or password.",
      });
    }
  }, [urlError]);

  useEffect(() => {
    if (!state.error || state.error === lastLoginError.current) return;
    lastLoginError.current = state.error;
    const message = loginErrorMessage(state.error);
    if (message) {
      showErrorToast({ description: message });
    }
  }, [state.error]);

  async function onResend(e: React.FormEvent) {
    e.preventDefault();
    setResendLoading(true);
    try {
      const res = await fetch("/api/auth/resend-verification", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: resendEmail.trim().toLowerCase() }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        showApiErrorToast(res.status, data.error, "Could not resend email.");
      } else {
        showSuccessToast({
          description: "If an unverified account exists, a new link was sent.",
        });
      }
    } catch {
      showErrorToast({ description: "Could not resend email." });
    } finally {
      setResendLoading(false);
    }
  }

  const showResend =
    state.error === "email_not_verified" || urlError === "TokenExpired" || urlError === "EmailNotVerified";

  return (
    <div className="space-y-6">
      <form
        action={formAction}
        className="space-y-4"
        onSubmit={(e) => {
          const fd = new FormData(e.currentTarget);
          const email = fd.get("email")?.toString().trim() ?? "";
          const password = fd.get("password")?.toString() ?? "";
          if (!email || !isValidEmail(email)) {
            e.preventDefault();
            showErrorToast({ description: "Enter a valid email address." });
            return;
          }
          if (!password) {
            e.preventDefault();
            showErrorToast({ description: "Password is required." });
          }
        }}
      >
        <input type="hidden" name="callbackUrl" value={callbackUrl} />
        <div className="space-y-2">
          <label htmlFor="email" className="text-sm font-medium">
            Email
          </label>
          <Input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            disabled={pending}
          />
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <label htmlFor="password" className="text-sm font-medium">
              Password
            </label>
            <Link
              href="/forgot-password"
              className="text-xs font-medium text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
            >
              Forgot password?
            </Link>
          </div>
          <Input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            disabled={pending}
          />
        </div>
        <Button type="submit" className="w-full" disabled={pending}>
          {pending ? "Signing in…" : "Sign in"}
        </Button>
      </form>

      {googleAuthEnabled && (
        <>
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-muted-foreground">Or continue with</span>
            </div>
          </div>

          <a
            href={googleHref}
            className={cn(buttonVariants({ variant: "outline" }), "w-full")}
          >
            Sign in with Google
          </a>
        </>
      )}

      <p className="text-center text-sm text-muted-foreground">
        No account?{" "}
        <Link href="/register" className="font-medium text-foreground underline-offset-4 hover:underline">
          Register
        </Link>
      </p>

      {showResend && (
        <div className="space-y-3 rounded-lg border bg-muted/30 p-4">
          <p className="text-sm font-medium">Resend verification email</p>
          <form onSubmit={onResend} className="flex flex-col gap-2 sm:flex-row">
            <Input
              type="email"
              placeholder="you@example.com"
              value={resendEmail}
              onChange={(e) => setResendEmail(e.target.value)}
              required
              disabled={resendLoading}
            />
            <Button type="submit" variant="secondary" disabled={resendLoading}>
              {resendLoading ? "Sending…" : "Resend"}
            </Button>
          </form>
        </div>
      )}
    </div>
  );
}
