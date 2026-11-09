import clsx from 'clsx';
import { BODY_LOCATION_GROUPS, BODY_LOCATION_LABEL } from '@/lib/format';
import type { BodyLocation } from '@/types/api';

export function BodyLocationPicker({ value, onChange }: { value: BodyLocation | null; onChange: (v: BodyLocation) => void }) {
  return (
    <fieldset className="space-y-3">
      <legend className="mb-1 text-sm font-medium text-ink">Where on the body?</legend>
      {BODY_LOCATION_GROUPS.map((g) => (
        <div key={g.title}>
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-ink-faint">{g.title}</p>
          <div role="radiogroup" aria-label={g.title} className="flex flex-wrap gap-2">
            {g.items.map((loc) => {
              const active = value === loc;
              return (
                <button key={loc} type="button" role="radio" aria-checked={active} onClick={() => onChange(loc)} className={clsx('chip min-h-[44px]', active && 'chip-active')}>
                  {BODY_LOCATION_LABEL[loc]}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </fieldset>
  );
}
