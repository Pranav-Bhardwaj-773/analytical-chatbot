import { toast } from "@/components/ui/toast";

import { userFacingApiError } from "@/lib/api-errors";

type ToastOptions = {
  title?: string;
  description: string;
};

export function showErrorToast({ title = "Error", description }: ToastOptions) {
  toast.add({ type: "error", title, description });
}

export function showSuccessToast({ title = "Success", description }: ToastOptions) {
  toast.add({ type: "success", title, description });
}

export function showApiErrorToast(
  status: number,
  bodyError: unknown,
  fallback: string,
  title = "Error",
) {
  showErrorToast({
    title,
    description: userFacingApiError(status, bodyError, fallback),
  });
}

export function apiErrorMessage(
  status: number,
  bodyError: unknown,
  fallback: string,
): string {
  return userFacingApiError(status, bodyError, fallback);
}

export const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function isValidEmail(email: string): boolean {
  return EMAIL_PATTERN.test(email.trim());
}
