const PHONE_PATTERN = /^[+]?[\d\s().-]{7,20}$/;

export function normalizePhone(raw: string): string {
  return raw.trim();
}

export function isValidPhone(raw: string): boolean {
  const phone = normalizePhone(raw);
  if (!phone) return false;
  const digits = phone.replace(/\D/g, "");
  return digits.length >= 7 && digits.length <= 15 && PHONE_PATTERN.test(phone);
}
