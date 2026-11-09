import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus } from 'lucide-react';
import { Button, Input } from '@/components/ui';
import { ApiError } from '@/lib/api';
import { validateEmail, validateFullName, validatePassword } from '@/lib/validation';
import { useAuth } from './AuthContext';
import { AuthLayout } from './AuthLayout';
import { PasswordInput } from './PasswordInput';
import { PasswordStrengthMeter } from './PasswordStrength';

type Errors = Partial<Record<'full_name' | 'email' | 'password' | 'confirm' | 'consent', string | null>>;

export function validateSignup(v: { full_name: string; email: string; password: string; confirm: string; consent: boolean }): Errors {
  return {
    full_name: validateFullName(v.full_name),
    email: validateEmail(v.email),
    password: validatePassword(v.password),
    confirm: v.confirm !== v.password ? 'Passwords do not match.' : null,
    consent: v.consent ? null : 'Please confirm you understand OncoAI is educational only.',
  };
}

export default function SignupPage() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [v, setV] = useState({ full_name: '', email: '', password: '', confirm: '', consent: false });
  const [errors, setErrors] = useState<Errors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof v) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setV((s) => ({ ...s, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const errs = validateSignup(v);
    setErrors(errs);
    setFormError(null);
    if (Object.values(errs).some(Boolean)) return;
    setBusy(true);
    try {
      await register({ full_name: v.full_name.trim(), email: v.email.trim().toLowerCase(), password: v.password });
      nav('/dashboard', { replace: true });
    } catch (err) {
      const e2 = err as ApiError;
      if (Object.keys(e2.fieldErrors ?? {}).length) setErrors((s) => ({ ...s, ...e2.fieldErrors }));
      setFormError(e2.status === 409 || /exist|registered/i.test(e2.message) ? 'An account with this email already exists.' : e2.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Start a private, educational record of your skin spots."
      footer={
        <>
          Already have an account?{' '}
          <Link to="/login" className="font-semibold text-accent-cyan hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={submit} noValidate className="space-y-4">
        {formError && (
          <div role="alert" className="rounded-xl border border-rose-300/30 bg-rose-400/10 px-3.5 py-2.5 text-sm text-rose-100">
            {formError}
          </div>
        )}
        <Input label="Full name" autoComplete="name" value={v.full_name} onChange={set('full_name')} error={errors.full_name} />
        <Input label="Email" type="email" inputMode="email" autoComplete="email" value={v.email} onChange={set('email')} error={errors.email} />
        <div className="space-y-2">
          <PasswordInput
            label="Password"
            autoComplete="new-password"
            value={v.password}
            onChange={set('password')}
            error={errors.password}
            hint="At least 8 characters, including a letter and a number."
          />
          <PasswordStrengthMeter password={v.password} />
        </div>
        <PasswordInput label="Confirm password" autoComplete="new-password" value={v.confirm} onChange={set('confirm')} error={errors.confirm} />
        <div>
          <label className="flex min-h-[44px] cursor-pointer items-start gap-3 text-sm text-ink-muted">
            <input type="checkbox" checked={v.consent} onChange={set('consent')} className="mt-0.5 h-5 w-5 shrink-0 accent-cyan-400" />
            <span>I understand OncoAI is for education and awareness only and does not replace a healthcare professional.</span>
          </label>
          {errors.consent && (
            <p role="alert" className="mt-1 text-xs font-medium text-rose-300">
              {errors.consent}
            </p>
          )}
        </div>
        <Button type="submit" block size="lg" loading={busy} leftIcon={<UserPlus className="h-5 w-5" aria-hidden />}>
          Create account
        </Button>
      </form>
    </AuthLayout>
  );
}
