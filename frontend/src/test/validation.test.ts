import { describe, expect, it } from 'vitest';
import { containsContactInfo, passwordStrength, validateEmail, validatePassword } from '@/lib/validation';
import { validateSignup } from '@/features/auth/SignupPage';

describe('password validation (contract: ≥8, letter + digit)', () => {
  it.each([
    ['', 'required'],
    ['abc12', 'at least 8'],
    ['12345678', 'letter'],
    ['abcdefgh', 'number'],
  ])('rejects %j', (pw, msg) => {
    expect(validatePassword(pw)).toMatch(new RegExp(msg, 'i'));
  });
  it('accepts a valid password', () => {
    expect(validatePassword('sunny2026')).toBeNull();
  });
  it('strength never exceeds Weak for invalid passwords', () => {
    expect(passwordStrength('!!!!!!!!!!!!AAAA').score).toBeLessThanOrEqual(1);
    expect(passwordStrength('Sunny-Day-2026!').label).toBe('Strong');
  });
});

describe('email & signup', () => {
  it('validates email', () => {
    expect(validateEmail('nope')).toBeTruthy();
    expect(validateEmail('a@b.io')).toBeNull();
  });
  it('flags mismatched confirmation and missing consent', () => {
    const e = validateSignup({ full_name: 'Al', email: 'a@b.io', password: 'abcd1234', confirm: 'abcd12345', consent: false });
    expect(e.confirm).toBeTruthy();
    expect(e.consent).toBeTruthy();
    expect(e.password).toBeNull();
  });
});

describe('privacy hint', () => {
  it('detects phone numbers and emails', () => {
    expect(containsContactInfo('call me at +1 555 123 4567')).toBe(true);
    expect(containsContactInfo('mail me: x@y.com')).toBe(true);
    expect(containsContactInfo('I have 3 spots on my back')).toBe(false);
  });
});
