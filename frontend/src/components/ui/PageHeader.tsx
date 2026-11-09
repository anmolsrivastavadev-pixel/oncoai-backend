import type { ReactNode } from 'react';
import { ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function PageHeader({
  title,
  subtitle,
  actions,
  back,
  eyebrow,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  back?: string | boolean;
  eyebrow?: ReactNode;
}) {
  const nav = useNavigate();
  return (
    <header className="mb-5 flex flex-wrap items-start justify-between gap-3">
      <div className="flex min-w-0 items-start gap-2">
        {back && (
          <button
            type="button"
            onClick={() => (typeof back === 'string' ? nav(back) : nav(-1))}
            className="-ml-2 grid h-11 w-11 shrink-0 place-items-center rounded-xl text-ink-muted hover:bg-white/5 hover:text-white"
            aria-label="Go back"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
        )}
        <div className="min-w-0">
          {eyebrow && <p className="mb-1 text-xs font-semibold uppercase tracking-[0.16em] text-accent-cyan">{eyebrow}</p>}
          <h1 className="text-2xl font-bold sm:text-3xl">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-ink-muted sm:text-[15px]">{subtitle}</p>}
        </div>
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </header>
  );
}
