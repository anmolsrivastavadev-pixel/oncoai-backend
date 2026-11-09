import clsx from 'clsx';
import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';
import { Disclaimer } from '@/components/Disclaimer';
import { Card, ConcernBadge, ErrorState, PageHeader, Skeleton, Tabs } from '@/components/ui';
import { ScanImage } from '@/features/scan/ScanResultView';
import { useAsync } from '@/hooks/useAsync';
import { useAuthedImage } from '@/hooks/useAuthedImage';
import { api } from '@/lib/api';
import { formatDate } from '@/lib/format';
import type { ScanDeltas } from '@/types/api';

const DELTA_LABELS: Record<keyof ScanDeltas, string> = {
  concern_score: 'Concern score',
  asymmetry: 'Asymmetry',
  border_irregularity: 'Border irregularity',
  color_variation: 'Colour variation',
  diameter_relative: 'Relative size',
};

export function deltaDirection(v: number, threshold = 1): 'up' | 'down' | 'flat' {
  if (v >= threshold) return 'up';
  if (v <= -threshold) return 'down';
  return 'flat';
}

export function DeltaRow({ label, value }: { label: string; value: number }) {
  const dir = deltaDirection(value);
  const Icon = dir === 'up' ? ArrowUpRight : dir === 'down' ? ArrowDownRight : Minus;
  const rounded = Math.round(value * 10) / 10;
  return (
    <li className="flex items-center justify-between gap-3 py-2.5">
      <span className="text-sm text-ink">{label}</span>
      <span
        className={clsx('inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-sm font-semibold', dir === 'up' ? 'bg-amber-400/10 text-amber-200' : dir === 'down' ? 'bg-emerald-400/10 text-emerald-200' : 'bg-white/5 text-ink-muted')}
        aria-label={`${label} ${dir === 'flat' ? 'unchanged' : dir === 'up' ? `increased by ${Math.abs(rounded)}` : `decreased by ${Math.abs(rounded)}`}`}
      >
        <Icon className="h-4 w-4" aria-hidden />
        {rounded > 0 ? '+' : ''}
        {rounded}
      </span>
    </li>
  );
}

function SliderCompare({ aUrl, bUrl }: { aUrl: string; bUrl: string }) {
  const a = useAuthedImage(aUrl);
  const b = useAuthedImage(bUrl);
  const [pos, setPos] = useState(50);
  if (!a.src || !b.src) return <Skeleton className="aspect-square w-full" />;
  return (
    <div className="space-y-3">
      <div className="relative aspect-square w-full select-none overflow-hidden rounded-2xl border border-white/10 bg-black/40">
        <img src={b.src} alt="Newer scan" className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 overflow-hidden" style={{ clipPath: `inset(0 ${100 - pos}% 0 0)` }}>
          <img src={a.src} alt="Earlier scan" className="absolute inset-0 h-full w-full object-cover" />
        </div>
        <div className="pointer-events-none absolute inset-y-0 w-0.5 bg-accent-cyan shadow-glow" style={{ left: `${pos}%` }} aria-hidden>
          <span className="absolute left-1/2 top-1/2 h-8 w-8 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-accent-cyan bg-navy-950/80" />
        </div>
        <span className="absolute left-2 top-2 rounded-full bg-navy-950/80 px-2 py-0.5 text-xs text-white">Earlier</span>
        <span className="absolute right-2 top-2 rounded-full bg-navy-950/80 px-2 py-0.5 text-xs text-white">Newer</span>
      </div>
      <input type="range" min={0} max={100} value={pos} onChange={(e) => setPos(Number(e.target.value))} aria-label="Comparison slider position" className="h-11 w-full accent-cyan-400" />
    </div>
  );
}

export default function ComparePage() {
  const [p] = useSearchParams();
  const a = Number(p.get('a'));
  const b = Number(p.get('b'));
  const valid = Number.isFinite(a) && Number.isFinite(b) && a > 0 && b > 0 && a !== b;
  const q = useAsync(() => api.tracking.compare(a, b), [a, b], valid);
  const [mode, setMode] = useState<'side' | 'slider'>('side');
  const c = q.data;

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <PageHeader back eyebrow="Compare" title="Scan comparison" subtitle="See how the visual features of a spot changed between two scans." />
      <Disclaimer variant="inline" />
      {!valid ? (
        <ErrorState message="Choose two different scans from a spot's timeline to compare." />
      ) : q.error ? (
        <ErrorState message={q.error.message} onRetry={q.reload} />
      ) : !c ? (
        <div className="grid grid-cols-2 gap-3" role="status" aria-label="Loading comparison">
          <Skeleton className="aspect-square" />
          <Skeleton className="aspect-square" />
        </div>
      ) : (
        <>
          <Tabs ariaLabel="Comparison view" value={mode} onChange={setMode} items={[{ value: 'side', label: 'Side by side' }, { value: 'slider', label: 'Slider overlay' }]} />
          {mode === 'side' ? (
            <div className="grid grid-cols-2 gap-3">
              {[c.a, c.b].map((s, i) => (
                <Card key={s.id} padded={false} className="overflow-hidden">
                  <ScanImage url={s.image_url} alt={i === 0 ? 'Earlier scan' : 'Newer scan'} className="aspect-square w-full" />
                  <div className="space-y-1.5 p-3">
                    <p className="text-xs text-ink-faint">{i === 0 ? 'Earlier' : 'Newer'} · {formatDate(s.created_at)}</p>
                    <ConcernBadge level={s.concern_level} size="sm" />
                    <p className="text-xs text-ink-muted">Score {Math.round(s.concern_score)}</p>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <SliderCompare aUrl={c.a.image_url} bUrl={c.b.image_url} />
          )}
          <Card>
            <h2 className="mb-1 text-base font-semibold">What changed</h2>
            <p className="mb-2 text-xs text-ink-faint">Differences in visual scores (newer minus earlier). Arrows show direction, not significance.</p>
            <ul className="divide-y divide-white/5">
              {(Object.keys(DELTA_LABELS) as (keyof ScanDeltas)[]).map((k) => (
                <DeltaRow key={k} label={DELTA_LABELS[k]} value={c.deltas[k] ?? 0} />
              ))}
            </ul>
          </Card>
          <Card>
            <h2 className="mb-1 text-base font-semibold">Summary</h2>
            <p className="text-sm leading-relaxed text-ink">{c.summary}</p>
          </Card>
          <Disclaimer variant="compact" />
        </>
      )}
    </div>
  );
}
