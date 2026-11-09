import clsx from 'clsx';
import { motion, useReducedMotion } from 'framer-motion';
import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Check, GitCompareArrows, MapPin, Pencil, ScanLine, Trash2 } from 'lucide-react';
import { Disclaimer } from '@/components/Disclaimer';
import { Button, Card, ConcernBadge, EmptyState, ErrorState, Input, Modal, PageHeader, Skeleton, buttonClasses, useToast } from '@/components/ui';
import { BodyLocationPicker } from '@/features/scan/BodyLocationPicker';
import { ScanImage } from '@/features/scan/ScanResultView';
import { useAsync } from '@/hooks/useAsync';
import { api, type ApiError } from '@/lib/api';
import { BODY_LOCATION_LABEL, formatDate, formatDateTime } from '@/lib/format';
import type { BodyLocation, ScanSummary } from '@/types/api';
import { SymptomsPanel } from './SymptomsPanel';

/** Toggle selection keeping at most two ids (oldest selection dropped). */
export function toggleCompare(sel: number[], id: number): number[] {
  if (sel.includes(id)) return sel.filter((x) => x !== id);
  return [...sel, id].slice(-2);
}

function Timeline({ scans, selected, onToggle }: { scans: ScanSummary[]; selected: number[]; onToggle: (id: number) => void }) {
  const reduce = useReducedMotion();
  return (
    <ol className="relative ml-3 border-l border-white/10 pl-6">
      {scans.map((s, i) => {
        const sel = selected.includes(s.id);
        return (
          <motion.li
            key={s.id}
            initial={reduce ? false : { opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="relative mb-4 last:mb-0"
          >
            <span
              className={clsx('absolute -left-[33px] top-5 h-4 w-4 rounded-full border-2 border-navy-950', i === 0 ? 'bg-accent-cyan shadow-glow-sm' : 'bg-white/30')}
              aria-hidden
            />
            <div className={clsx('glass flex items-center gap-3 p-3 transition', sel && 'border-accent-cyan/60 bg-accent-cyan/[0.08]')}>
              <Link to={`/scan/${s.id}`} className="flex min-w-0 flex-1 items-center gap-3">
                <ScanImage url={s.thumbnail_url} alt={`Scan from ${formatDate(s.created_at)}`} className="h-16 w-16 shrink-0 rounded-xl" />
                <div className="min-w-0">
                  <p className="text-xs text-ink-faint">{formatDateTime(s.created_at)}</p>
                  <p className="line-clamp-2 text-sm font-medium text-white">{s.headline}</p>
                  <div className="mt-1 flex items-center gap-2">
                    <ConcernBadge level={s.concern_level} size="sm" />
                    <span className="text-[11px] text-ink-faint">score {Math.round(s.concern_score)}</span>
                  </div>
                </div>
              </Link>
              <button
                type="button"
                onClick={() => onToggle(s.id)}
                aria-pressed={sel}
                aria-label={sel ? 'Remove from comparison' : 'Select for comparison'}
                className={clsx('grid h-11 w-11 shrink-0 place-items-center rounded-xl border transition', sel ? 'border-accent-cyan bg-accent-cyan text-navy-950' : 'border-white/15 text-ink-faint hover:text-white')}
              >
                {sel ? <Check className="h-5 w-5" /> : <GitCompareArrows className="h-5 w-5" />}
              </button>
            </div>
          </motion.li>
        );
      })}
    </ol>
  );
}

export default function LesionDetailPage() {
  const { id } = useParams();
  const lesionId = Number(id);
  const nav = useNavigate();
  const toast = useToast();
  const q = useAsync(() => api.lesions.get(lesionId), [lesionId]);
  const [selected, setSelected] = useState<number[]>([]);
  const [editOpen, setEditOpen] = useState(false);
  const [edit, setEdit] = useState<{ label: string; body_location: BodyLocation; notes: string }>({ label: '', body_location: 'other', notes: '' });
  const [delOpen, setDelOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  const l = q.data;

  const openEdit = () => {
    if (!l) return;
    setEdit({ label: l.label, body_location: l.body_location, notes: l.notes ?? '' });
    setEditOpen(true);
  };

  const saveEdit = async () => {
    if (!edit.label.trim()) return toast.error('Name is required.');
    setBusy(true);
    try {
      const u = await api.lesions.update(lesionId, { label: edit.label.trim(), body_location: edit.body_location, notes: edit.notes.trim() || undefined });
      q.setData((d) => (d ? { ...d, ...u, scans: d.scans } : d));
      setEditOpen(false);
      toast.success('Spot updated.');
    } catch (e) {
      toast.error((e as ApiError).message);
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    setBusy(true);
    try {
      await api.lesions.remove(lesionId);
      toast.success('Spot and its scans deleted.');
      nav('/track', { replace: true });
    } catch (e) {
      toast.error((e as ApiError).message);
      setBusy(false);
    }
  };

  if (q.error) return <ErrorState message={q.error.message} onRetry={q.reload} className="mx-auto max-w-xl" />;
  if (!l)
    return (
      <div className="mx-auto max-w-3xl space-y-3" role="status" aria-label="Loading spot">
        <Skeleton className="h-10 w-1/2" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
    );

  const [a, b] = [...selected].sort((x, y) => {
    const tx = new Date(l.scans.find((s) => s.id === x)?.created_at ?? 0).getTime();
    const ty = new Date(l.scans.find((s) => s.id === y)?.created_at ?? 0).getTime();
    return tx - ty;
  });

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <PageHeader
        back="/track"
        eyebrow="Tracked spot"
        title={l.label}
        subtitle={
          <span className="inline-flex items-center gap-1">
            <MapPin className="h-3.5 w-3.5" aria-hidden /> {BODY_LOCATION_LABEL[l.body_location] ?? l.body_location} · since {formatDate(l.created_at)}
          </span>
        }
        actions={
          <>
            <Button size="icon" variant="glass" onClick={openEdit} aria-label="Edit spot">
              <Pencil className="h-4 w-4" />
            </Button>
            <Button size="icon" variant="danger" onClick={() => setDelOpen(true)} aria-label="Delete spot">
              <Trash2 className="h-4 w-4" />
            </Button>
          </>
        }
      />
      {l.notes && <p className="-mt-2 text-sm text-ink-muted">{l.notes}</p>}

      <Card className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <ConcernBadge level={l.latest_concern} />
          <span className="text-sm text-ink-muted">{l.scan_count} scan{l.scan_count === 1 ? '' : 's'}</span>
        </div>
        <Link to={`/scan?lesion=${l.id}`} className={buttonClasses('primary', 'sm')}>
          <ScanLine className="h-4 w-4" aria-hidden /> Re-scan this spot
        </Link>
      </Card>

      <section aria-labelledby="timeline-h">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 id="timeline-h" className="text-lg font-semibold">
            Scan timeline
          </h2>
          {l.scans.length >= 2 && <p className="text-xs text-ink-faint">Select two scans to compare</p>}
        </div>
        {l.scans.length ? (
          <Timeline scans={l.scans} selected={selected} onToggle={(sid) => setSelected((s) => toggleCompare(s, sid))} />
        ) : (
          <EmptyState icon={ScanLine} title="No scans yet" description="Scan this spot to start its timeline." />
        )}
      </section>

      {selected.length === 2 && a && b && (
        <div className="sticky z-20" style={{ bottom: 'calc(var(--bottom-nav-h) + var(--safe-bottom) + 12px)' }}>
          <Link to={`/tracking/compare?a=${a}&b=${b}`} className={buttonClasses('primary', 'lg', true)}>
            <GitCompareArrows className="h-5 w-5" aria-hidden /> Compare selected scans
          </Link>
        </div>
      )}

      <SymptomsPanel lesionId={l.id} />
      <Disclaimer variant="inline" />

      <Modal
        open={editOpen}
        onClose={() => setEditOpen(false)}
        title="Edit spot"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setEditOpen(false)}>
              Cancel
            </Button>
            <Button loading={busy} onClick={saveEdit}>
              Save
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Input label="Name" value={edit.label} maxLength={80} onChange={(e) => setEdit({ ...edit, label: e.target.value })} />
          <BodyLocationPicker value={edit.body_location} onChange={(v) => setEdit({ ...edit, body_location: v })} />
          <Input label="Notes" value={edit.notes} onChange={(e) => setEdit({ ...edit, notes: e.target.value })} />
        </div>
      </Modal>
      <Modal
        open={delOpen}
        onClose={() => setDelOpen(false)}
        size="sm"
        title="Delete this spot?"
        description="All scans and images for this spot will be permanently deleted."
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setDelOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" loading={busy} onClick={remove}>
              Delete
            </Button>
          </div>
        }
      >
        <p className="text-sm text-ink-muted">This cannot be undone.</p>
      </Modal>
    </div>
  );
}
