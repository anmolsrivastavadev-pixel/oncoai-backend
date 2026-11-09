import clsx from 'clsx';

export function Spinner({ className, label = 'Loading' }: { className?: string; label?: string }) {
  return (
    <span role="status" aria-label={label} className={clsx('inline-block h-5 w-5 animate-spin rounded-full border-2 border-white/20 border-t-accent-cyan', className)} />
  );
}
