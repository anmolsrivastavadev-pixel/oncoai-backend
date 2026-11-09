import { Link } from 'react-router-dom';
import { useState } from 'react';
import { ChevronRight, MapPin, ScanLine, LineChart } from 'lucide-react';
import { Disclaimer } from '@/components/Disclaimer';
import { ConcernBadge, EmptyState, ErrorState, ListSkeleton, PageHeader, Tabs, buttonClasses } from '@/components/ui';
import { ScanImage } from '@/features/scan/ScanResultView';
import { useAsync } from '@/hooks/useAsync';
import { api } from '@/lib/api';
import { BODY_LOCATION_LABEL, formatDate } from '@/lib/format';
import { SymptomsPanel } from './SymptomsPanel';

export default function TrackPage() {
  const q = useAsync(() => api.lesions.list(), []);
  const [tab, setTab] = useState<'spots' | 'symptoms'>('spots');
  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        eyebrow="Tracking"
        title="Your tracked spots"
        subtitle="Follow each spot over time and compare scans."
        actions={
          <Link to="/scan" className={buttonClasses('primary', 'sm')}>
            <ScanLine className="h-4 w-4" aria-hidden /> Scan
          </Link>
        }
      />
      <Tabs ariaLabel="Tracking sections" className="mb-4" value={tab} onChange={setTab} items={[{ value: 'spots', label: 'Spots', count: q.data?.total }, { value: 'symptoms', label: 'Symptoms' }]} />
      {tab === 'spots' ? (
        q.loading ? (
          <ListSkeleton rows={4} />
        ) : q.error ? (
          <ErrorState message={q.error.message} onRetry={q.reload} />
        ) : !q.data?.items.length ? (
          <EmptyState
            icon={LineChart}
            title="No spots tracked yet"
            description="Each time you scan a spot, it's added to its own timeline here."
            action={
              <Link to="/scan" className={buttonClasses('primary')}>
                <ScanLine className="h-5 w-5" aria-hidden /> Scan your first spot
              </Link>
            }
          />
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2">
            {q.data.items.map((l) => (
              <li key={l.id}>
                <Link to={`/track/${l.id}`} className="glass flex items-center gap-3 p-3 transition hover:border-accent-cyan/30">
                  <div className="h-16 w-16 shrink-0 overflow-hidden rounded-xl border border-white/10">
                    {l.thumbnail_url ? <ScanImage url={l.thumbnail_url} alt={`Latest photo of ${l.label}`} className="h-16 w-16" /> : <div className="grid h-full place-items-center bg-white/5"><ScanLine className="h-5 w-5 text-ink-faint" aria-hidden /></div>}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold text-white">{l.label}</p>
                    <p className="flex items-center gap-1 truncate text-xs text-ink-muted">
                      <MapPin className="h-3 w-3 shrink-0" aria-hidden /> {BODY_LOCATION_LABEL[l.body_location] ?? l.body_location}
                    </p>
                    <div className="mt-1.5 flex flex-wrap items-center gap-2">
                      <ConcernBadge level={l.latest_concern} size="sm" />
                      <span className="text-[11px] text-ink-faint">
                        {l.scan_count} scan{l.scan_count === 1 ? '' : 's'}
                        {l.latest_scan_at ? ` · ${formatDate(l.latest_scan_at)}` : ''}
                      </span>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 shrink-0 text-ink-faint" aria-hidden />
                </Link>
              </li>
            ))}
          </ul>
        )
      ) : (
        <SymptomsPanel lesions={q.data?.items} />
      )}
      <Disclaimer variant="inline" className="mt-6" />
    </div>
  );
}
