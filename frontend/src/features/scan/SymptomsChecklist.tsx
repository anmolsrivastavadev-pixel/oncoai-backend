import clsx from 'clsx';
import { Check } from 'lucide-react';
import { Textarea } from '@/components/ui';
import type { Symptoms } from '@/types/api';

export const EMPTY_SYMPTOMS: Symptoms = {
  itching: false,
  bleeding: false,
  pain: false,
  changed_size: false,
  changed_color: false,
  changed_shape: false,
  new_spot: false,
  notes: '',
};

export const SYMPTOM_LABELS: Record<Exclude<keyof Symptoms, 'notes'>, string> = {
  itching: 'Itching',
  bleeding: 'Bleeding',
  pain: 'Pain or tenderness',
  changed_size: 'Changed in size',
  changed_color: 'Changed in colour',
  changed_shape: 'Changed in shape',
  new_spot: 'New spot',
};

export const SYMPTOM_KEYS = Object.keys(SYMPTOM_LABELS) as (keyof typeof SYMPTOM_LABELS)[];

export const hasAnySymptom = (s: Symptoms) => SYMPTOM_KEYS.some((k) => s[k]) || !!s.notes?.trim();

export function SymptomsChecklist({ value, onChange, showNotes = true }: { value: Symptoms; onChange: (s: Symptoms) => void; showNotes?: boolean }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {SYMPTOM_KEYS.map((k) => {
          const on = value[k];
          return (
            <button
              key={k}
              type="button"
              role="checkbox"
              aria-checked={on}
              onClick={() => onChange({ ...value, [k]: !on })}
              className={clsx(
                'flex min-h-[48px] items-center gap-3 rounded-xl border px-3.5 text-left text-sm transition',
                on ? 'border-accent-cyan/60 bg-accent-cyan/10 text-white' : 'border-white/10 bg-white/[0.03] text-ink-muted hover:border-white/20',
              )}
            >
              <span className={clsx('grid h-5 w-5 place-items-center rounded-md border', on ? 'border-accent-cyan bg-accent-cyan text-navy-950' : 'border-white/25')}>
                {on && <Check className="h-3.5 w-3.5" aria-hidden />}
              </span>
              {SYMPTOM_LABELS[k]}
            </button>
          );
        })}
      </div>
      {showNotes && (
        <Textarea label="Notes (optional)" maxLength={1000} placeholder="Anything else you've noticed…" value={value.notes ?? ''} onChange={(e) => onChange({ ...value, notes: e.target.value })} />
      )}
    </div>
  );
}
