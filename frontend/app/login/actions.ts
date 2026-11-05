"use server";

import { AuthError, CredentialsSignin } from "next-auth";
import { isRedirectError } from "next/dist/client/components/redirect-error";

import { signIn } from "@/auth";

export type LoginState = { error?: string };

export async function loginWithCredentials(
  _prev: LoginState,
  formData: FormData,
): Promise<LoginState> {
  const email = formData.get("email")?.toString().trim().toLowerCase();
  const password = formData.get("password")?.toString();
  const callbackUrl = formData.get("callbackUrl")?.toString() || "/";

  if (!email || !password) {
    return { error: "Email and password are required." };
  }

  try {
    await signIn("credentials", {
      email,
      password,
      redirectTo: callbackUrl,
    });
    return {};
  } catch (err) {
    if (isRedirectError(err)) {
      throw err;
    }
    if (err instanceof CredentialsSignin) {
      if (err.code === "email_not_verified") {
        return { error: "email_not_verified" };
      }
      return { error: "invalid_credentials" };
    }
    if (err instanceof AuthError) {
      return { error: "Something went wrong. Please try again." };
    }
    return { error: "Something went wrong. Please try again." };
  }
}

export async function loginWithGoogle(callbackUrl?: string) {
  await signIn("google", { redirectTo: callbackUrl || "/" });
}
