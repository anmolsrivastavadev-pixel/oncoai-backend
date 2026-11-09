import clsx from 'clsx';
import type { HTMLAttributes } from 'react';
import { AlertTriangle, CheckCircle2, CircleAlert } from 'lucide-react';
import type { ConcernLevel } from '@/types/api';
import { CONCERN_LABEL } from '@/lib/format';

export type BadgeTone = 'neutral' | 'cyan' | 'teal' | 'amber' | 'rose' | 'green' | 'violet';

const tones: Record<BadgeTone, string> = {
  neutral: 'bg-white/[0.07] text-ink-muted border-white/10',
  cyan: 'bg-accent-cyan/10 text-cyan-200 border-accent-cyan/30',
  teal: 'bg-accent-teal/10 text-teal-200 border-accent-teal/30',
  amber: 'bg-amber-400/10 text-amber-200 border-amber-300/30',
  rose: 'bg-rose-400/10 text-rose-200 border-rose-300/30',
  green: 'bg-emerald-400/10 text-emerald-200 border-emerald-300/30',
  violet: 'bg-violet-400/10 text-violet-200 border-violet-300/30',
};

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
}

export function Badge({ tone = 'neutral', className, ...rest }: BadgeProps) {
  return (
    <span
      className={clsx('inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-medium', tones[tone], className)}
      {...rest}
    />
  );
}

const concernTone: Record<ConcernLevel, BadgeTone> = { low: 'green', moderate: 'amber', higher: 'rose' };
const concernIcon = { low: CheckCircle2, moderate: CircleAlert, higher: AlertTriangle } as const;

export const CONCERN_COLOR: Record<ConcernLevel, string> = {
  low: '#34D399',
  moderate: '#FBBF24',
  higher: '#FB7185',
};

export function ConcernBadge({ level, size = 'md', className }: { level: ConcernLevel | null | undefined; size?: 'sm' | 'md' | 'lg'; className?: string }) {
  if (!level) {
    return (
      <Badge tone="neutral" className={className}>
        Not scanned yet
      </Badge>
    );
  }
  const Icon = concernIcon[level];
  return (
    <Badge
      tone={concernTone[level]}
      data-level={level}
      className={clsx(size === 'lg' && 'px-3.5 py-1.5 text-sm', size === 'sm' && 'px-2 text-[11px]', className)}
    >
      <Icon className={size === 'lg' ? 'h-4 w-4' : 'h-3.5 w-3.5'} aria-hidden />
      {CONCERN_LABEL[level]}
    </Badge>
  );
}
