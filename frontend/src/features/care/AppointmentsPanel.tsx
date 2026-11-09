import { useState } from 'react';
import { CalendarClock, CalendarX2, Link2, MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Badge, Button, Card, EmptyState, ErrorState, ListSkeleton, Modal, Tabs, useToast } from '@/components/ui';
import { useAsync } from '@/hooks/useAsync';
import { api, type ApiError } from '@/lib/api';
import { formatDateTime } from '@/lib/format';
import type { Appointment } from '@/types/api';
import { SampleBadge } from './DermatologistCard';
import { SlotPicker, type SlotValue } from './SlotPicker';

const statusTone = { booked: 'cyan', cancelled: 'rose', completed: 'green' } as const;

export function AppointmentCard({ a, onReschedule, onCancel }: { a: Appointment; onReschedule?: () => void; onCancel?: () => void }) {
  const d = new Date(a.scheduled_at);
  return (
    <Card className="flex gap-4">
      <div className="flex w-14 shrink-0 flex-col items-center justify-center rounded-xl border border-accent-cyan/25 bg-accent-cyan/10 py-2 text-center">
        <span className="text-[11px] uppercase text-cyan-100">{d.toLocaleDateString(undefined, { month: 'short' })}</span>
        <span className="font-display text-xl font-bold text-white">{d.getDate()}</span>
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-semibold text-white">{a.dermatologist.name}</p>
          <Badge tone={statusTone[a.status]}>{a.status}</Badge>
          {a.dermatologist.is_sample && <SampleBadge />}
        </div>
        <p className="mt-0.5 flex items-center gap-1 text-sm text-ink-muted">
          <CalendarClock className="h-3.5 w-3.5" aria-hidden /> {formatDateTime(a.scheduled_at)}
        </p>
        <p className="flex items-center gap-1 text-xs text-ink-faint">
          <MapPin className="h-3 w-3" aria-hidden /> {a.dermatologist.clinic_name}, {a.dermatologist.city}
        </p>
        {a.reason && <p className="mt-1.5 line-clamp-2 text-sm text-ink">{a.reason}</p>}
        {a.scan_id && (
          <Link to={`/scan/${a.scan_id}`} className="mt-1 inline-flex min-h-[32px] items-center gap-1 text-xs font-medium text-accent-cyan hover:underline">
            <Link2 className="h-3.5 w-3.5" aria-hidden /> Linked scan
          </Link>
        )}
        {(onReschedule || onCancel) && a.status === 'booked' && (
          <div className="mt-3 flex gap-2">
            {onReschedule && (
              <Button size="sm" variant="glass" onClick={onReschedule}>
                Reschedule
              </Button>
            )}
            {onCancel && (
              <Button size="sm" variant="danger" onClick={onCancel}>
                Cancel
              </Button>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}

export function AppointmentsPanel({ refreshKey }: { refreshKey: number }) {
  const toast = useToast();
  const [status, setStatus] = useState<'upcoming' | 'past'>('upcoming');
  const q = useAsync(() => api.appointments.list(status), [status, refreshKey]);
  const [resched, setResched] = useState<Appointment | null>(null);
  const [slot, setSlot] = useState<SlotValue>({ date: null, time: null });
  const [cancelling, setCancelling] = useState<Appointment | null>(null);
  const [busy, setBusy] = useState(false);

  const replace = (a: Appointment) => q.setData((d) => (d ? { ...d, items: d.items.map((x) => (x.id === a.id ? a : x)) } : d));

  const doReschedule = async () => {
    if (!resched || !slot.date || !slot.time) return;
    setBusy(true);
    try {
      const a = await api.appointments.update(resched.id, { date: slot.date, time: slot.time });
      replace(a);
      setResched(null);
      toast.success('Appointment rescheduled.');
    } catch (e) {
      const ae = e as ApiError;
      toast.error(ae.status === 409 ? 'That time is no longer available.' : ae.message);
    } finally {
      setBusy(false);
    }
  };

  const doCancel = async () => {
    if (!cancelling) return;
    setBusy(true);
    try {
      const a = await api.appointments.cancel(cancelling.id);
      replace(a);
      setCancelling(null);
      toast.success('Appointment cancelled.');
    } catch (e) {
      toast.error((e as ApiError).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3">
      <Tabs ariaLabel="Appointment filter" value={status} onChange={setStatus} items={[{ value: 'upcoming', label: 'Upcoming' }, { value: 'past', label: 'Past' }]} className="max-w-xs" />
      {q.loading ? (
        <ListSkeleton rows={2} />
      ) : q.error ? (
        <ErrorState message={q.error.message} onRetry={q.reload} />
      ) : !q.data?.items.length ? (
        <EmptyState icon={CalendarX2} title={status === 'upcoming' ? 'No upcoming appointments' : 'No past appointments'} description="Find a dermatologist to book a visit." />
      ) : (
        <ul className="space-y-3">
          {q.data.items.map((a) => (
            <li key={a.id}>
              <AppointmentCard
                a={a}
                onReschedule={
                  status === 'upcoming'
                    ? () => {
                        setSlot({ date: null, time: null });
                        setResched(a);
                      }
                    : undefined
                }
                onCancel={status === 'upcoming' ? () => setCancelling(a) : undefined}
              />
            </li>
          ))}
        </ul>
      )}

      <Modal
        open={!!resched}
        onClose={() => setResched(null)}
        title="Reschedule"
        description={resched ? `Currently ${formatDateTime(resched.scheduled_at)} with ${resched.dermatologist.name}` : undefined}
        footer={
          <Button block onClick={doReschedule} loading={busy} disabled={!slot.time}>
            Confirm new time
          </Button>
        }
      >
        {resched && <SlotPicker dermatologistId={resched.dermatologist.id} value={slot} onChange={setSlot} />}
      </Modal>
      <Modal
        open={!!cancelling}
        onClose={() => setCancelling(null)}
        size="sm"
        title="Cancel appointment?"
        description={cancelling ? `${formatDateTime(cancelling.scheduled_at)} with ${cancelling.dermatologist.name}` : undefined}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setCancelling(null)}>
              Keep it
            </Button>
            <Button variant="danger" onClick={doCancel} loading={busy}>
              Cancel appointment
            </Button>
          </div>
        }
      >
        <p className="text-sm text-ink-muted">You can book another time whenever you're ready.</p>
      </Modal>
    </div>
  );
}
