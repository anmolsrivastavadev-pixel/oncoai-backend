import { useState } from 'react';
import { ClipboardList, Plus } from 'lucide-react';
import { Button, Card, EmptyState, ErrorState, ListSkeleton, Modal, Select, useToast } from '@/components/ui';
import { EMPTY_SYMPTOMS, SYMPTOM_KEYS, SYMPTOM_LABELS, SymptomsChecklist, hasAnySymptom } from '@/features/scan/SymptomsChecklist';
import { useAsync } from '@/hooks/useAsync';
import { api, type ApiError } from '@/lib/api';
import { formatDateTime } from '@/lib/format';
import type { Lesion, Symptoms } from '@/types/api';

export function SymptomsPanel({ lesionId, lesions }: { lesionId?: number; lesions?: Lesion[] }) {
  const toast = useToast();
  const q = useAsync(() => api.tracking.symptoms(), []);
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState<Symptoms>(EMPTY_SYMPTOMS);
  const [forLesion, setForLesion] = useState<string>(lesionId ? String(lesionId) : '');
  const [busy, setBusy] = useState(false);

  const items = (q.data?.items ?? []).filter((s) => (lesionId ? s.lesion_id === lesionId : true));
  const labelFor = (id: number | null) => (id ? (lesions?.find((l) => l.id === id)?.label ?? `Spot #${id}`) : 'General');

  const save = async () => {
    if (!hasAnySymptom(value)) {
      toast.error('Select at least one symptom or add a note.');
      return;
    }
    setBusy(true);
    try {
      const log = await api.tracking.logSymptoms({ ...value, notes: value.notes?.trim() || undefined, lesion_id: forLesion ? Number(forLesion) : undefined });
      q.setData((d) => ({ items: [log, ...(d?.items ?? [])] }));
      setOpen(false);
      setValue(EMPTY_SYMPTOMS);
      toast.success('Symptoms logged.');
    } catch (e) {
      toast.error((e as ApiError).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section aria-labelledby="symptoms-h" className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 id="symptoms-h" className="text-lg font-semibold">
          Symptom log
        </h2>
        <Button size="sm" variant="glass" onClick={() => setOpen(true)} leftIcon={<Plus className="h-4 w-4" aria-hidden />}>
          Log symptoms
        </Button>
      </div>
      {q.loading ? (
        <ListSkeleton rows={2} />
      ) : q.error ? (
        <ErrorState message={q.error.message} onRetry={q.reload} />
      ) : items.length === 0 ? (
        <EmptyState icon={ClipboardList} title="No symptoms logged" description="Note itching, bleeding or changes you notice so you can share them with a professional." />
      ) : (
        <ul className="space-y-2">
          {items.map((s) => {
            const on = SYMPTOM_KEYS.filter((k) => s[k]);
            return (
              <Card key={s.id} className="py-3">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <p className="text-sm font-semibold text-white">{labelFor(s.lesion_id)}</p>
                  <p className="text-xs text-ink-faint">{formatDateTime(s.created_at)}</p>
                </div>
                {on.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {on.map((k) => (
                      <span key={k} className="rounded-full bg-white/[0.06] px-2.5 py-0.5 text-xs text-ink-muted">
                        {SYMPTOM_LABELS[k]}
                      </span>
                    ))}
                  </div>
                )}
                {s.notes && <p className="mt-2 text-sm text-ink-muted">{s.notes}</p>}
              </Card>
            );
          })}
        </ul>
      )}

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Log symptoms"
        description="Record what you've noticed today."
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={save} loading={busy}>
              Save
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          {!lesionId && lesions && lesions.length > 0 && (
            <Select label="Related spot" value={forLesion} onChange={(e) => setForLesion(e.target.value)} placeholder="General (no specific spot)" options={lesions.map((l) => ({ value: String(l.id), label: l.label }))} />
          )}
          <SymptomsChecklist value={value} onChange={setValue} />
        </div>
      </Modal>
    </section>
  );
}
