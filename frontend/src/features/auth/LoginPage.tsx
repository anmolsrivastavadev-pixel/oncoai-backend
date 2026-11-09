import { useState, type FormEvent } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LogIn } from 'lucide-react';
import { Button, Input } from '@/components/ui';
import { ApiError } from '@/lib/api';
import { validateEmail } from '@/lib/validation';
import { useAuth } from './AuthContext';
import { AuthLayout } from './AuthLayout';
import { PasswordInput } from './PasswordInput';

export default function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const from = (loc.state as { from?: string } | null)?.from ?? '/dashboard';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ email?: string | null; password?: string | null }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const errs = { email: validateEmail(email), password: password ? null : 'Password is required.' };
    setErrors(errs);
    setFormError(null);
    if (errs.email || errs.password) return;
    setBusy(true);
    try {
      await login({ email: email.trim().toLowerCase(), password });
      nav(from.startsWith('/') ? from : '/dashboard', { replace: true });
    } catch (err) {
      const e2 = err as ApiError;
      setFormError(
        e2.status === 401
          ? 'Incorrect email or password.'
          : e2.status === 429
            ? 'Too many sign-in attempts. Please wait a minute and try again.'
            : e2.message,
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to continue tracking your skin health."
      footer={
        <>
          New to OncoAI?{' '}
          <Link to="/signup" className="font-semibold text-accent-cyan hover:underline">
            Create an account
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
        <Input label="Email" type="email" autoComplete="email" inputMode="email" value={email} onChange={(e) => setEmail(e.target.value)} error={errors.email} />
        <PasswordInput label="Password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} error={errors.password} />
        <Button type="submit" block size="lg" loading={busy} leftIcon={<LogIn className="h-5 w-5" aria-hidden />}>
          Sign in
        </Button>
      </form>
    </AuthLayout>
  );
}
