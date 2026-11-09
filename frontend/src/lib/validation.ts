export const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function validateEmail(email: string): string | null {
  if (!email.trim()) return 'Email is required.';
  if (!EMAIL_RE.test(email.trim())) return 'Enter a valid email address.';
  return null;
}

/** Contract: min 8 chars, at least one letter and one digit. */
export function validatePassword(pw: string): string | null {
  if (!pw) return 'Password is required.';
  if (pw.length < 8) return 'Password must be at least 8 characters.';
  if (!/[A-Za-z]/.test(pw)) return 'Password must include at least one letter.';
  if (!/\d/.test(pw)) return 'Password must include at least one number.';
  return null;
}

export function validateFullName(name: string): string | null {
  const n = name.trim();
  if (!n) return 'Full name is required.';
  if (n.length < 2) return 'Name is too short.';
  if (n.length > 120) return 'Name is too long.';
  return null;
}

export type StrengthLevel = 0 | 1 | 2 | 3 | 4;

export interface PasswordStrength {
  score: StrengthLevel;
  label: 'Too weak' | 'Weak' | 'Fair' | 'Good' | 'Strong';
}

export function passwordStrength(pw: string): PasswordStrength {
  if (!pw) return { score: 0, label: 'Too weak' };
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score++;
  if (/\d/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  // Must satisfy contract rules to be anything above "Weak".
  if (validatePassword(pw)) score = Math.min(score, 1);
  const s = Math.min(4, score) as StrengthLevel;
  const labels = ['Too weak', 'Weak', 'Fair', 'Good', 'Strong'] as const;
  return { score: s, label: labels[s] };
}

export function validateLength(value: string, min: number, max: number, field: string): string | null {
  const v = value.trim();
  if (v.length < min) return min <= 1 ? `${field} is required.` : `${field} must be at least ${min} characters.`;
  if (v.length > max) return `${field} must be at most ${max} characters.`;
  return null;
}

/** Client-side mirror of the server privacy filter (server is authoritative). */
export function containsContactInfo(text: string): boolean {
  const email = /[^\s@]+@[^\s@]+\.[a-z]{2,}/i;
  const phone = /(\+?\d[\d\s().-]{7,}\d)/;
  return email.test(text) || phone.test(text);
}
