import clsx from 'clsx';
import { ShieldAlert, Info } from 'lucide-react';
import { DISCLAIMER } from '@/lib/constants';

export interface DisclaimerProps {
  variant?: 'banner' | 'inline' | 'compact';
  className?: string;
}

/** The single source of the product disclaimer. Always renders the exact constant text. */
export function Disclaimer({ variant = 'inline', className }: DisclaimerProps) {
  if (variant === 'banner') {
    return (
      <aside
        role="note"
        aria-label="Medical disclaimer"
        data-testid="disclaimer"
        className={clsx(
          'flex items-start gap-3 rounded-2xl border border-amber-300/25 bg-amber-300/[0.07] px-4 py-3.5 text-sm leading-relaxed text-amber-50',
          className,
        )}
      >
        <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-amber-300" aria-hidden />
        <p>
          <span className="font-semibold text-amber-200">Important: </span>
          {DISCLAIMER}
        </p>
      </aside>
    );
  }
  if (variant === 'compact') {
    return (
      <p role="note" data-testid="disclaimer" className={clsx('text-xs leading-relaxed text-ink-faint', className)}>
        {DISCLAIMER}
      </p>
    );
  }
  return (
    <div
      role="note"
      data-testid="disclaimer"
      className={clsx('flex items-start gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2.5 text-xs leading-relaxed text-ink-muted', className)}
    >
      <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent-cyan" aria-hidden />
      <p>{DISCLAIMER}</p>
    </div>
  );
}
