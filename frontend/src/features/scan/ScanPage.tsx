import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Check, MapPin, Plus, ScanLine } from 'lucide-react';
import { Disclaimer } from '@/components/Disclaimer';
import { Button, Card, ConcernBadge, ErrorState, Input, ListSkeleton, PageHeader, Tabs, useToast } from '@/components/ui';
import { useAsync } from '@/hooks/useAsync';
import { api, type ApiError } from '@/lib/api';
import { BODY_LOCATION_LABEL, formatDate } from '@/lib/format';
import type { CapturedPhoto } from '@/lib/native';
import type { BodyLocation, Lesion, Symptoms } from '@/types/api';
import { AnalyzingState } from './AnalyzingState';
import { BodyLocationPicker } from './BodyLocationPicker';
import { PhotoCapture, PhotoTips } from './PhotoCapture';
import { EMPTY_SYMPTOMS, SymptomsChecklist, hasAnySymptom } from './SymptomsChecklist';
import { ScanImage } from './ScanResultView';

type Step = 0 | 1 | 2 | 3;
const STEP_LABELS = ['Spot', 'Photo', 'Symptoms'];

function Stepper({ step }: { step: Step }) {
  return (
    <ol className="mb-5 flex items-center gap-2" aria-label="Scan progress">
      {STEP_LABELS.map((l, i) => {
        const done = step > i;
        const active = step === i;
        return (
          <li key={l} className="flex flex-1 items-center gap-2" aria-current={active ? 'step' : undefined}>
            <span
              className={clsx(
                'grid h-8 w-8 shrink-0 place-items-center rounded-full border text-sm font-semibold transition',
                done ? 'border-accent-teal bg-accent-teal text-navy-950' : active ? 'border-accent-cyan bg-accent-cyan/15 text-white shadow-glow-sm' : 'border-white/15 text-ink-faint',
              )}
            >
              {done ? <Check className="h-4 w-4" aria-hidden /> : i + 1}
            </span>
            <span className={clsx('text-sm font-medium', active ? 'text-white' : 'text-ink-faint')}>{l}</span>
            {i < STEP_LABELS.length - 1 && <span className={clsx('h-px flex-1', done ? 'bg-accent-teal/60' : 'bg-white/10')} aria-hidden />}
          </li>
        );
      })}
    </ol>
  );
}

function LesionOption({ lesion, selected, onSelect }: { lesion: Lesion; selected: boolean; onSelect: () => void }) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      onClick={onSelect}
      className={clsx(
        'flex w-full items-center gap-3 rounded-2xl border p-3 text-left transition',
        selected ? 'border-accent-cyan/70 bg-accent-cyan/10 shadow-glow-sm' : 'border-white/10 bg-white/[0.03] hover:border-white/20',
      )}
    >
      <div className="h-14 w-14 shrink-0 overflow-hidden rounded-xl border border-white/10">
        {lesion.thumbnail_url ? <ScanImage url={lesion.thumbnail_url} alt="" className="h-14 w-14" /> : <div className="grid h-full w-full place-items-center bg-white/5"><ScanLine className="h-5 w-5 text-ink-faint" aria-hidden /></div>}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate font-semibold text-white">{lesion.label}</p>
        <p className="flex items-center gap-1 text-xs text-ink-muted">
          <MapPin className="h-3 w-3" aria-hidden /> {BODY_LOCATION_LABEL[lesion.body_location] ?? lesion.body_location} · {lesion.scan_count} scan{lesion.scan_count === 1 ? '' : 's'}
        </p>
        {lesion.latest_scan_at && <p className="text-xs text-ink-faint">Last scanned {formatDate(lesion.latest_scan_at)}</p>}
      </div>
      <ConcernBadge level={lesion.latest_concern} size="sm" className="hidden sm:inline-flex" />
    </button>
  );
}

export default function ScanPage() {
  const nav = useNavigate();
  const toast = useToast();
  const [params] = useSearchParams();
  const preLesion = Number(params.get('lesion')) || null;

  const lesions = useAsync(() => api.lesions.list(), []);
  const [step, setStep] = useState<Step>(0);
  const [mode, setMode] = useState<'existing' | 'new'>('existing');
  const [lesionId, setLesionId] = useState<number | null>(preLesion);
  const [newLabel, setNewLabel] = useState('');
  const [newLocation, setNewLocation] = useState<BodyLocation | null>(null);
  const [labelError, setLabelError] = useState<string | null>(null);
  const [photo, setPhoto] = useState<CapturedPhoto | null>(null);
  const [symptoms, setSymptoms] = useState<Symptoms>(EMPTY_SYMPTOMS);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (lesions.data && lesions.data.items.length === 0 && !preLesion) setMode('new');
  }, [lesions.data, preLesion]);

  useEffect(() => () => {
    if (photo) URL.revokeObjectURL(photo.previewUrl);
  }, [photo]);

  const spotValid = mode === 'existing' ? lesionId !== null : newLabel.trim().length > 0 && newLocation !== null;

  const nextFromSpot = () => {
    if (mode === 'new') {
      if (!newLabel.trim()) return setLabelError('Give this spot a name, e.g. "Left shoulder mole".');
      if (!newLocation) {
        setLabelError(null);
        toast.error('Choose where on the body the spot is.');
        return;
      }
    }
    setLabelError(null);
    setStep(1);
  };

  const analyse = async () => {
    if (!photo) return;
    setStep(3);
    setError(null);
    setProgress(0);
    try {
      let id = lesionId;
      if (mode === 'new') {
        const created = await api.lesions.create({ label: newLabel.trim(), body_location: newLocation ?? 'other' });
        id = created.id;
        setLesionId(created.id);
        setMode('existing');
        lesions.reload();
      }
      const scan = await api.scans.create(
        {
          image: photo.blob,
          lesion_id: id ?? undefined,
          symptoms: hasAnySymptom(symptoms) ? { ...symptoms, notes: symptoms.notes?.trim() || undefined } : undefined,
        },
        (p) => setProgress(p.percent),
      );
      setProgress(100);
      nav(`/scan/${scan.id}`, { replace: false, state: { scan } });
    } catch (e) {
      setError((e as ApiError).message);
      setStep(2);
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader eyebrow="AI skin scan" title="New scan" subtitle="Photograph a spot to get an educational summary of its visual features." />
      {step < 3 && <Stepper step={step} />}

      <AnimatePresence mode="wait">
        <motion.div key={step} initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }} transition={{ duration: 0.2 }}>
          {step === 0 && (
            <div className="space-y-4">
              <Tabs
                ariaLabel="Choose spot"
                value={mode}
                onChange={setMode}
                items={[
                  { value: 'existing', label: 'Tracked spot', count: lesions.data?.total },
                  { value: 'new', label: 'New spot' },
                ]}
              />
              {mode === 'existing' ? (
                lesions.loading ? (
                  <ListSkeleton rows={3} />
                ) : lesions.error ? (
                  <ErrorState message={lesions.error.message} onRetry={lesions.reload} />
                ) : lesions.data?.items.length ? (
                  <div role="radiogroup" aria-label="Tracked spots" className="space-y-2">
                    {lesions.data.items.map((l) => (
                      <LesionOption key={l.id} lesion={l} selected={lesionId === l.id} onSelect={() => setLesionId(l.id)} />
                    ))}
                  </div>
                ) : (
                  <Card className="text-center">
                    <p className="text-sm text-ink-muted">You aren't tracking any spots yet.</p>
                    <Button className="mt-3" variant="glass" onClick={() => setMode('new')} leftIcon={<Plus className="h-4 w-4" aria-hidden />}>
                      Add a new spot
                    </Button>
                  </Card>
                )
              ) : (
                <Card className="space-y-5">
                  <Input label="Spot name" placeholder='e.g. "Mole on left shoulder"' maxLength={80} value={newLabel} onChange={(e) => setNewLabel(e.target.value)} error={labelError} />
                  <BodyLocationPicker value={newLocation} onChange={setNewLocation} />
                </Card>
              )}
              <Button block size="lg" disabled={!spotValid} onClick={nextFromSpot} rightIcon={<ArrowRight className="h-5 w-5" aria-hidden />}>
                Continue
              </Button>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <PhotoTips />
              <PhotoCapture photo={photo} onPhoto={setPhoto} />
              <div className="flex gap-2">
                <Button variant="ghost" size="lg" onClick={() => setStep(0)} leftIcon={<ArrowLeft className="h-5 w-5" aria-hidden />}>
                  Back
                </Button>
                <Button block size="lg" disabled={!photo} onClick={() => setStep(2)} rightIcon={<ArrowRight className="h-5 w-5" aria-hidden />}>
                  Continue
                </Button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <Card>
                <h2 className="text-lg font-semibold">Anything you've noticed?</h2>
                <p className="mb-4 mt-1 text-sm text-ink-muted">Optional. Logging symptoms helps you describe changes to a professional.</p>
                <SymptomsChecklist value={symptoms} onChange={setSymptoms} />
              </Card>
              {error && (
                <p role="alert" className="rounded-xl border border-rose-300/30 bg-rose-400/10 px-3 py-2 text-sm text-rose-100">
                  {error}
                </p>
              )}
              <div className="flex gap-2">
                <Button variant="ghost" size="lg" onClick={() => setStep(1)} leftIcon={<ArrowLeft className="h-5 w-5" aria-hidden />}>
                  Back
                </Button>
                <Button block size="lg" onClick={analyse} leftIcon={<ScanLine className="h-5 w-5" aria-hidden />}>
                  Analyse photo
                </Button>
              </div>
            </div>
          )}

          {step === 3 && <AnalyzingState progress={progress} previewUrl={photo?.previewUrl} />}
        </motion.div>
      </AnimatePresence>
      <Disclaimer variant="inline" className="mt-6" />
    </div>
  );
}
