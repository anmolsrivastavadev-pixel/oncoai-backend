import clsx from 'clsx';
import { useEffect, useRef, useState } from 'react';
import { Skeleton } from '@/components/ui';
import { useAsync } from '@/hooks/useAsync';
import { api } from '@/lib/api';
import { nextDays, toYMD } from '@/lib/format';

export interface SlotValue {
  date: string | null;
  time: string | null;
}

export function SlotPicker({ dermatologistId, value, onChange }: { dermatologistId: number; value: SlotValue; onChange: (v: SlotValue) => void }) {
  const [days] = useState(() => nextDays(30));
  const date = value.date ?? toYMD(days[0]!);
  const q = useAsync(() => api.dermatologists.availability(dermatologistId, date), [dermatologistId, date]);
  const stripRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!value.date) onChange({ date, time: null });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-3">
      <div>
        <p className="mb-2 text-sm font-medium text-ink">Choose a date</p>
        <div ref={stripRef} role="radiogroup" aria-label="Date" className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1 no-scrollbar">
          {days.map((d) => {
            const ymd = toYMD(d);
            const active = ymd === date;
            const weekend = d.getDay() === 0 || d.getDay() === 6;
            return (
              <button
                key={ymd}
                type="button"
                role="radio"
                aria-checked={active}
                aria-label={d.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}
                onClick={() => onChange({ date: ymd, time: null })}
                className={clsx(
                  'flex min-h-[64px] w-14 shrink-0 flex-col items-center justify-center rounded-xl border text-center transition',
                  active ? 'border-accent-cyan bg-accent-cyan/15 text-white shadow-glow-sm' : 'border-white/10 bg-white/[0.03] text-ink-muted hover:border-white/20',
                  weekend && !active && 'opacity-60',
                )}
              >
                <span className="text-[11px] uppercase">{d.toLocaleDateString(undefined, { weekday: 'short' })}</span>
                <span className="font-display text-lg font-semibold">{d.getDate()}</span>
                <span className="text-[10px]">{d.toLocaleDateString(undefined, { month: 'short' })}</span>
              </button>
            );
          })}
        </div>
      </div>
      <div>
        <p className="mb-2 text-sm font-medium text-ink">Available times</p>
        {q.loading ? (
          <div className="grid grid-cols-4 gap-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-11" />
            ))}
          </div>
        ) : q.error ? (
          <p className="text-sm text-rose-200">{q.error.message}</p>
        ) : !q.data?.slots.length ? (
          <p className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-4 text-center text-sm text-ink-muted">No times available on this day. Try another date.</p>
        ) : (
          <div role="radiogroup" aria-label="Time" className="grid grid-cols-4 gap-2 sm:grid-cols-6">
            {q.data.slots.map((t) => {
              const active = value.time === t && value.date === date;
              return (
                <button
                  key={t}
                  type="button"
                  role="radio"
                  aria-checked={active}
                  onClick={() => onChange({ date, time: t })}
                  className={clsx('min-h-[44px] rounded-xl border text-sm font-medium transition', active ? 'border-accent-cyan bg-accent-cyan text-navy-950' : 'border-white/10 bg-white/[0.03] text-ink hover:border-accent-cyan/40')}
                >
                  {t}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
