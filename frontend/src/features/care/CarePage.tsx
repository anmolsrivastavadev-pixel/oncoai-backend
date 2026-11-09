import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, Stethoscope } from 'lucide-react';
import { Disclaimer } from '@/components/Disclaimer';
import { EmptyState, ErrorState, Input, ListSkeleton, PageHeader, Tabs, Badge } from '@/components/ui';
import { useAsync } from '@/hooks/useAsync';
import { useDebounce } from '@/hooks/useDebounce';
import { api } from '@/lib/api';
import type { Dermatologist } from '@/types/api';
import { AppointmentsPanel } from './AppointmentsPanel';
import { BookingSheet } from './BookingSheet';
import { DermatologistCard } from './DermatologistCard';
import { RemindersPanel } from './RemindersPanel';

type Tab = 'find' | 'appointments' | 'reminders';

function FindPanel({ scanId, onBooked }: { scanId: number | null; onBooked: () => void }) {
  const [q, setQ] = useState('');
  const [city, setCity] = useState('');
  const [specialty, setSpecialty] = useState('');
  const dq = useDebounce(q);
  const dcity = useDebounce(city);
  const dspec = useDebounce(specialty);
  const res = useAsync(() => api.dermatologists.search({ q: dq.trim(), city: dcity.trim(), specialty: dspec.trim(), limit: 30 }), [dq, dcity, dspec]);
  const [open, setOpen] = useState<Dermatologist | null>(null);

  return (
    <div className="space-y-4">
      <div className="glass space-y-3 p-4">
        <Input
          aria-label="Search dermatologists"
          placeholder="Search by name or clinic"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          right={<Search className="mr-3 h-5 w-5 text-ink-faint" aria-hidden />}
          type="search"
        />
        <div className="grid grid-cols-2 gap-3">
          <Input aria-label="City" placeholder="City" value={city} onChange={(e) => setCity(e.target.value)} />
          <Input aria-label="Specialty" placeholder="Specialty" value={specialty} onChange={(e) => setSpecialty(e.target.value)} />
        </div>
      </div>
      {scanId && (
        <Badge tone="cyan" className="py-1">
          Your scan #{scanId} will be linked to the booking
        </Badge>
      )}
      {res.loading ? (
        <ListSkeleton rows={3} />
      ) : res.error ? (
        <ErrorState message={res.error.message} onRetry={res.reload} />
      ) : !res.data?.items.length ? (
        <EmptyState icon={Stethoscope} title="No dermatologists found" description="Try a different name, city or specialty." />
      ) : (
        <>
          <p className="text-xs text-ink-faint">
            {res.data.total} result{res.data.total === 1 ? '' : 's'}
          </p>
          <ul className="grid gap-3 md:grid-cols-2">
            {res.data.items.map((d) => (
              <li key={d.id}>
                <DermatologistCard d={d} onOpen={() => setOpen(d)} />
              </li>
            ))}
          </ul>
        </>
      )}
      <BookingSheet dermatologist={open} onClose={() => setOpen(null)} prefillScanId={scanId} onBooked={onBooked} />
    </div>
  );
}

export default function CarePage() {
  const [params, setParams] = useSearchParams();
  const tab = (['find', 'appointments', 'reminders'].includes(params.get('tab') ?? '') ? params.get('tab') : 'find') as Tab;
  const scanId = Number(params.get('scan_id')) || null;
  const [refreshKey, setRefreshKey] = useState(0);
  const setTab = (t: Tab) => {
    const next = new URLSearchParams(params);
    next.set('tab', t);
    setParams(next, { replace: true });
  };

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader eyebrow="Care" title="Dermatologist care" subtitle="Find a professional, manage visits and stay on top of reminders." />
      <Disclaimer variant="inline" className="mb-4" />
      <Tabs
        ariaLabel="Care sections"
        className="mb-4"
        value={tab}
        onChange={setTab}
        items={[
          { value: 'find', label: 'Find' },
          { value: 'appointments', label: 'Appointments' },
          { value: 'reminders', label: 'Reminders' },
        ]}
      />
      {tab === 'find' && <FindPanel scanId={scanId} onBooked={() => setRefreshKey((k) => k + 1)} />}
      {tab === 'appointments' && <AppointmentsPanel refreshKey={refreshKey} />}
      {tab === 'reminders' && <RemindersPanel refreshKey={refreshKey} />}
    </div>
  );
}
