import clsx from 'clsx';
import { motion } from 'framer-motion';
import { useId, useRef, type KeyboardEvent } from 'react';

export interface TabItem<V extends string> {
  value: V;
  label: string;
  count?: number;
}

export function Tabs<V extends string>({
  items,
  value,
  onChange,
  className,
  ariaLabel,
}: {
  items: TabItem<V>[];
  value: V;
  onChange: (v: V) => void;
  className?: string;
  ariaLabel: string;
}) {
  const id = useId();
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const onKey = (e: KeyboardEvent, i: number) => {
    const dir = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
    if (!dir) return;
    e.preventDefault();
    const n = (i + dir + items.length) % items.length;
    refs.current[n]?.focus();
    onChange(items[n]!.value);
  };
  return (
    <div role="tablist" aria-label={ariaLabel} className={clsx('glass flex gap-1 overflow-x-auto p-1 no-scrollbar', className)}>
      {items.map((it, i) => {
        const active = it.value === value;
        return (
          <button
            key={it.value}
            ref={(el) => (refs.current[i] = el)}
            role="tab"
            type="button"
            aria-selected={active}
            tabIndex={active ? 0 : -1}
            onKeyDown={(e) => onKey(e, i)}
            onClick={() => onChange(it.value)}
            className={clsx('relative min-h-[40px] flex-1 whitespace-nowrap rounded-xl px-3 text-sm font-medium transition', active ? 'text-white' : 'text-ink-muted hover:text-white')}
          >
            {active && <motion.span layoutId={`tab-${id}`} className="absolute inset-0 rounded-xl border border-accent-cyan/30 bg-accent-cyan/15" transition={{ type: 'spring', damping: 30, stiffness: 380 }} />}
            <span className="relative">
              {it.label}
              {it.count !== undefined && <span className="ml-1.5 text-xs text-ink-faint">{it.count}</span>}
            </span>
          </button>
        );
      })}
    </div>
  );
}
