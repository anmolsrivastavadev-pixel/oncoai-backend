import clsx from 'clsx';
import { passwordStrength } from '@/lib/validation';

const colors = ['bg-rose-400', 'bg-rose-400', 'bg-amber-300', 'bg-teal-300', 'bg-emerald-300'];

export function PasswordStrengthMeter({ password }: { password: string }) {
  const { score, label } = passwordStrength(password);
  if (!password) return null;
  return (
    <div className="space-y-1" aria-live="polite">
      <div className="flex gap-1" aria-hidden>
        {[1, 2, 3, 4].map((i) => (
          <span key={i} className={clsx('h-1.5 flex-1 rounded-full transition-colors', i <= Math.max(score, 1) ? colors[score] : 'bg-white/10')} />
        ))}
      </div>
      <p className="text-xs text-ink-muted">
        Password strength: <span className="font-medium text-ink" data-testid="pw-strength">{label}</span>
      </p>
    </div>
  );
}
