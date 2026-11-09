import { Languages, MapPin, Star } from 'lucide-react';
import { Avatar, Badge } from '@/components/ui';
import type { Dermatologist } from '@/types/api';

export function SampleBadge() {
  return (
    <Badge tone="violet" title="Fictional sample listing for demonstration">
      Sample listing
    </Badge>
  );
}

export function Rating({ rating, count }: { rating: number; count: number }) {
  return (
    <span className="inline-flex items-center gap-1 text-sm text-ink" aria-label={`Rated ${rating.toFixed(1)} out of 5 from ${count} reviews`}>
      <Star className="h-4 w-4 fill-amber-300 text-amber-300" aria-hidden />
      <span className="font-semibold">{rating.toFixed(1)}</span>
      <span className="text-xs text-ink-faint">({count})</span>
    </span>
  );
}

export function DermatologistCard({ d, onOpen }: { d: Dermatologist; onOpen: () => void }) {
  return (
    <button type="button" onClick={onOpen} className="glass flex w-full flex-col gap-3 p-4 text-left transition hover:border-accent-cyan/30">
      <div className="flex items-start gap-3">
        <Avatar name={d.name} size={48} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <p className="font-semibold text-white">{d.name}</p>
            {d.is_sample && <SampleBadge />}
          </div>
          <p className="text-sm text-ink-muted">
            {d.title} · {d.specialty}
          </p>
          <p className="mt-0.5 flex items-center gap-1 text-xs text-ink-faint">
            <MapPin className="h-3 w-3 shrink-0" aria-hidden /> {d.clinic_name}, {d.city}
          </p>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <Rating rating={d.rating} count={d.review_count} />
        {d.languages.length > 0 && (
          <span className="inline-flex items-center gap-1 text-xs text-ink-muted">
            <Languages className="h-3.5 w-3.5" aria-hidden /> {d.languages.join(', ')}
          </span>
        )}
        {d.accepts_new_patients ? <Badge tone="green">Accepting new patients</Badge> : <Badge>Not accepting new patients</Badge>}
      </div>
    </button>
  );
}
