import { useEffect, useState } from 'react';
import { CalendarCheck, CheckCircle2, MapPin, Phone } from 'lucide-react';
import { Disclaimer } from '@/components/Disclaimer';
import { Button, Modal, Select, Textarea, useToast } from '@/components/ui';
import { useAsync } from '@/hooks/useAsync';
import { api, type ApiError } from '@/lib/api';
import { formatDate, formatDateTime } from '@/lib/format';
import type { Appointment, Dermatologist } from '@/types/api';
import { Rating, SampleBadge } from './DermatologistCard';
import { SlotPicker, type SlotValue } from './SlotPicker';

export function BookingSheet({
  dermatologist,
  onClose,
  prefillScanId,
  onBooked,
}: {
  dermatologist: Dermatologist | null;
  onClose: () => void;
  prefillScanId?: number | null;
  onBooked: (a: Appointment) => void;
}) {
  const toast = useToast();
  const [slot, setSlot] = useState<SlotValue>({ date: null, time: null });
  const [reason, setReason] = useState('');
  const [scanId, setScanId] = useState<string>(prefillScanId ? String(prefillScanId) : '');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [booked, setBooked] = useState<Appointment | null>(null);
  const scans = useAsync(() => api.scans.list({ limit: 20 }), [], !!dermatologist);

  useEffect(() => {
    if (dermatologist) {
      setSlot({ date: null, time: null });
      setReason(prefillScanId ? 'I would like a professional evaluation of a spot I scanned.' : '');
      setScanId(prefillScanId ? String(prefillScanId) : '');
      setBooked(null);
      setError(null);
    }
  }, [dermatologist, prefillScanId]);

  if (!dermatologist) return null;
  const d = dermatologist;

  const book = async () => {
    if (!slot.date || !slot.time) return setError('Choose a date and time.');
    if (!reason.trim()) return setError('Please add a short reason for the visit.');
    setError(null);
    setBusy(true);
    try {
      const a = await api.appointments.create({ dermatologist_id: d.id, date: slot.date, time: slot.time, reason: reason.trim(), scan_id: scanId ? Number(scanId) : undefined });
      setBooked(a);
      onBooked(a);
      toast.success('Appointment booked. A reminder was added 24 h before.');
    } catch (e) {
      const ae = e as ApiError;
      setError(ae.status === 409 ? 'That time was just taken. Please choose another slot.' : ae.message);
      if (ae.status === 409) setSlot((s) => ({ date: s.date, time: null }));
    } finally {
      setBusy(false);
    }
  };

  const scanOptions = (scans.data?.items ?? []).map((s) => ({ value: String(s.id), label: `${formatDate(s.created_at)} · ${s.headline.slice(0, 48)}` }));
  if (prefillScanId && !scanOptions.some((o) => o.value === String(prefillScanId))) scanOptions.unshift({ value: String(prefillScanId), label: `Scan #${prefillScanId}` });

  return (
    <Modal
      open
      onClose={onClose}
      title={booked ? 'Booking confirmed' : d.name}
      description={booked ? undefined : `${d.title} · ${d.specialty}`}
      size="lg"
      footer={
        booked ? (
          <Button block onClick={onClose}>
            Done
          </Button>
        ) : (
          <Button block size="lg" onClick={book} loading={busy} disabled={!slot.time} leftIcon={<CalendarCheck className="h-5 w-5" aria-hidden />}>
            {slot.time && slot.date ? `Book ${formatDate(slot.date + 'T00:00:00', { weekday: 'short', month: 'short', day: 'numeric' })} at ${slot.time}` : 'Select a time'}
          </Button>
        )
      }
    >
      {booked ? (
        <div className="space-y-4 py-2 text-center">
          <CheckCircle2 className="mx-auto h-14 w-14 text-emerald-300" aria-hidden />
          <p className="text-lg font-semibold text-white">{formatDateTime(booked.scheduled_at)}</p>
          <p className="text-sm text-ink-muted">
            with {booked.dermatologist.name} at {booked.dermatologist.clinic_name}
          </p>
          {booked.dermatologist.is_sample && <p className="text-xs text-ink-faint">This is a fictional sample listing for demonstration purposes.</p>}
          <Disclaimer variant="inline" />
        </div>
      ) : (
        <div className="space-y-5">
          <div className="space-y-2 rounded-xl border border-white/10 bg-white/[0.03] p-3">
            <div className="flex flex-wrap items-center gap-2">
              <Rating rating={d.rating} count={d.review_count} />
              {d.is_sample && <SampleBadge />}
            </div>
            <p className="flex items-start gap-1.5 text-sm text-ink-muted">
              <MapPin className="mt-0.5 h-4 w-4 shrink-0" aria-hidden /> {d.clinic_name}, {d.address}, {d.city}
            </p>
            {d.phone && (
              <p className="flex items-center gap-1.5 text-sm text-ink-muted">
                <Phone className="h-4 w-4 shrink-0" aria-hidden /> {d.phone}
              </p>
            )}
            {d.bio && <p className="text-sm text-ink">{d.bio}</p>}
            {d.languages.length > 0 && <p className="text-xs text-ink-faint">Languages: {d.languages.join(', ')}</p>}
          </div>
          <SlotPicker dermatologistId={d.id} value={slot} onChange={setSlot} />
          <Textarea label="Reason for visit" maxLength={500} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. A spot on my back has changed colour." />
          <Select label="Link a scan (optional)" value={scanId} onChange={(e) => setScanId(e.target.value)} placeholder="No scan linked" options={scanOptions} hint="The dermatologist can review your scan photo with you." />
          {error && (
            <p role="alert" className="rounded-xl border border-rose-300/30 bg-rose-400/10 px-3 py-2 text-sm text-rose-100">
              {error}
            </p>
          )}
          <Disclaimer variant="compact" />
        </div>
      )}
    </Modal>
  );
}
