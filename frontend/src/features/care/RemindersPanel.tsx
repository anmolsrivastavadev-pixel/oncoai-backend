import clsx from 'clsx';
import { useEffect, useState } from 'react';
import { Bell, BellRing, Check, Plus, Repeat, Trash2 } from 'lucide-react';
import { Badge, Button, Card, EmptyState, ErrorState, Input, ListSkeleton, Modal, Select, useToast } from '@/components/ui';
import { useAsync } from '@/hooks/useAsync';
import { api, type ApiError } from '@/lib/api';
import { formatDateTime, relativeTime } from '@/lib/format';
import { cancelReminderNotification, ensureNotificationPermission, scheduleReminderNotifications } from '@/lib/native';
import { isNative } from '@/lib/platform';
import type { Reminder, ReminderKind } from '@/types/api';

const KIND_LABEL: Record<ReminderKind, string> = { rescan: 'Re-scan', appointment: 'Appointment', self_check: 'Self-check', custom: 'Custom' };

function defaultDue() {
  const d = new Date(Date.now() + 7 * 86400000);
  d.setHours(9, 0, 0, 0);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function RemindersPanel({ refreshKey }: { refreshKey: number }) {
  const toast = useToast();
  const q = useAsync(() => api.reminders.list(), [refreshKey]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ title: '', kind: 'self_check' as ReminderKind, due: defaultDue(), repeat: '' });
  const [busy, setBusy] = useState(false);
  const lesions = useAsync(() => api.lesions.list(), [], open);
  const [lesionId, setLesionId] = useState('');

  // Keep device notifications in sync with the server list (native only).
  useEffect(() => {
    if (q.data) void scheduleReminderNotifications(q.data.items);
  }, [q.data]);

  const items = [...(q.data?.items ?? [])].sort((a, b) => Number(a.done) - Number(b.done) || a.due_at.localeCompare(b.due_at));

  const create = async () => {
    if (!form.title.trim()) return toast.error('Add a title for the reminder.');
    const due = new Date(form.due);
    if (Number.isNaN(due.getTime())) return toast.error('Choose a valid date and time.');
    setBusy(true);
    try {
      const r = await api.reminders.create({
        title: form.title.trim(),
        kind: form.kind,
        due_at: due.toISOString(),
        repeat_days: form.repeat ? Number(form.repeat) : undefined,
        lesion_id: lesionId ? Number(lesionId) : undefined,
      });
      q.setData((d) => ({ items: [...(d?.items ?? []), r] }));
      setOpen(false);
      setForm({ title: '', kind: 'self_check', due: defaultDue(), repeat: '' });
      if (isNative()) {
        const ok = await ensureNotificationPermission();
        toast.success(ok ? 'Reminder set. You will get a notification on this device.' : 'Reminder saved. Enable notifications in Settings to be alerted.');
      } else toast.success('Reminder saved.');
    } catch (e) {
      toast.error((e as ApiError).message);
    } finally {
      setBusy(false);
    }
  };

  const toggleDone = async (r: Reminder) => {
    q.setData((d) => (d ? { items: d.items.map((x) => (x.id === r.id ? { ...x, done: !r.done } : x)) } : d));
    try {
      const u = await api.reminders.update(r.id, { done: !r.done });
      q.setData((d) => (d ? { items: d.items.map((x) => (x.id === r.id ? u : x)) } : d));
      if (u.done) void cancelReminderNotification(r.id);
    } catch (e) {
      q.setData((d) => (d ? { items: d.items.map((x) => (x.id === r.id ? r : x)) } : d));
      toast.error((e as ApiError).message);
    }
  };

  const remove = async (r: Reminder) => {
    const prev = q.data;
    q.setData((d) => (d ? { items: d.items.filter((x) => x.id !== r.id) } : d));
    try {
      await api.reminders.remove(r.id);
      void cancelReminderNotification(r.id);
    } catch (e) {
      q.setData(prev);
      toast.error((e as ApiError).message);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm text-ink-muted">{isNative() ? 'Reminders also appear as notifications on this device.' : 'Install the Android app to get reminder notifications.'}</p>
        <Button size="sm" onClick={() => setOpen(true)} leftIcon={<Plus className="h-4 w-4" aria-hidden />}>
          New
        </Button>
      </div>
      {q.loading ? (
        <ListSkeleton rows={3} />
      ) : q.error ? (
        <ErrorState message={q.error.message} onRetry={q.reload} />
      ) : !items.length ? (
        <EmptyState icon={Bell} title="No reminders" description="Set a reminder to re-scan a spot or do a monthly skin self-check." />
      ) : (
        <ul className="space-y-2">
          {items.map((r) => {
            const overdue = !r.done && new Date(r.due_at) < new Date();
            return (
              <li key={r.id}>
                <Card className={clsx('flex items-center gap-3 py-3', r.done && 'opacity-60')}>
                  <button
                    type="button"
                    onClick={() => toggleDone(r)}
                    aria-pressed={r.done}
                    aria-label={r.done ? `Mark "${r.title}" as not done` : `Mark "${r.title}" as done`}
                    className={clsx('grid h-11 w-11 shrink-0 place-items-center rounded-xl border transition', r.done ? 'border-emerald-300 bg-emerald-400/20 text-emerald-200' : 'border-white/15 text-ink-faint hover:text-white')}
                  >
                    {r.done ? <Check className="h-5 w-5" /> : <BellRing className="h-5 w-5" />}
                  </button>
                  <div className="min-w-0 flex-1">
                    <p className={clsx('truncate font-medium text-white', r.done && 'line-through')}>{r.title}</p>
                    <div className="mt-0.5 flex flex-wrap items-center gap-2 text-xs">
                      <span className={overdue ? 'text-amber-300' : 'text-ink-faint'}>
                        {formatDateTime(r.due_at)} · {relativeTime(r.due_at)}
                      </span>
                      <Badge>{KIND_LABEL[r.kind]}</Badge>
                      {r.repeat_days ? (
                        <span className="inline-flex items-center gap-0.5 text-ink-faint">
                          <Repeat className="h-3 w-3" aria-hidden /> every {r.repeat_days} d
                        </span>
                      ) : null}
                    </div>
                  </div>
                  <Button size="icon" variant="ghost" onClick={() => remove(r)} aria-label={`Delete reminder "${r.title}"`}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </Card>
              </li>
            );
          })}
        </ul>
      )}

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="New reminder"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={create} loading={busy}>
              Save reminder
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Input label="Title" maxLength={120} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Monthly skin self-check" />
          <Select label="Type" value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value as ReminderKind })} options={(Object.keys(KIND_LABEL) as ReminderKind[]).map((k) => ({ value: k, label: KIND_LABEL[k] }))} />
          <Input label="When" type="datetime-local" value={form.due} onChange={(e) => setForm({ ...form, due: e.target.value })} />
          <Select
            label="Repeat"
            value={form.repeat}
            onChange={(e) => setForm({ ...form, repeat: e.target.value })}
            placeholder="Does not repeat"
            options={[
              { value: '7', label: 'Every week' },
              { value: '30', label: 'Every 30 days' },
              { value: '90', label: 'Every 90 days' },
            ]}
          />
          {(lesions.data?.items.length ?? 0) > 0 && (
            <Select label="Related spot (optional)" value={lesionId} onChange={(e) => setLesionId(e.target.value)} placeholder="None" options={lesions.data!.items.map((l) => ({ value: String(l.id), label: l.label }))} />
          )}
        </div>
      </Modal>
    </div>
  );
}
