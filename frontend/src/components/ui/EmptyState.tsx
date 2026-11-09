import clsx from 'clsx';
import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon?: LucideIcon;
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={clsx('glass flex flex-col items-center px-6 py-10 text-center', className)}>
      {Icon && (
        <div className="mb-4 grid h-14 w-14 place-items-center rounded-2xl border border-accent-cyan/20 bg-accent-cyan/10 text-accent-cyan">
          <Icon className="h-7 w-7" aria-hidden />
        </div>
      )}
      <h3 className="text-lg font-semibold">{title}</h3>
      {description && <p className="mt-1.5 max-w-sm text-sm text-ink-muted">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function ErrorState({ message, onRetry, className }: { message?: string; onRetry?: () => void; className?: string }) {
  return (
    <div role="alert" className={clsx('glass flex flex-col items-center px-6 py-8 text-center', className)}>
      <AlertCircle className="mb-3 h-8 w-8 text-rose-300" aria-hidden />
      <p className="font-medium text-white">We couldn't load this</p>
      <p className="mt-1 max-w-sm text-sm text-ink-muted">{message || 'Something went wrong. Please try again.'}</p>
      {onRetry && (
        <Button variant="glass" size="sm" className="mt-4" onClick={onRetry} leftIcon={<RefreshCw className="h-4 w-4" aria-hidden />}>
          Try again
        </Button>
      )}
    </div>
  );
}
