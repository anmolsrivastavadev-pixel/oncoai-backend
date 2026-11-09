import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { AlertTriangle, Bot, CalendarHeart, Cpu, Eye, ImageOff, LineChart, ListChecks, Sparkles } from 'lucide-react';
import { Disclaimer } from '@/components/Disclaimer';
import { CONCERN_COLOR, Card, ConcernBadge, ProgressRing, Skeleton, buttonClasses } from '@/components/ui';
import { useAuthedImage } from '@/hooks/useAuthedImage';
import { formatDateTime } from '@/lib/format';
import { scrubDiagnosticTerms } from '@/lib/safety';
import type { Scan } from '@/types/api';
import { FeatureBars } from './FeatureBars';
import { SYMPTOM_KEYS, SYMPTOM_LABELS } from './SymptomsChecklist';

const LEVEL_COPY = {
  low: 'The visual features measured in this photo look fairly regular.',
  moderate: 'Some visual features in this photo look less regular than typical.',
  higher: 'Several visual features in this photo look irregular. A professional evaluation is a sensible next step.',
} as const;

export function ScanImage({ url, alt, className }: { url: string | null | undefined; alt: string; className?: string }) {
  const { src, loading, error } = useAuthedImage(url);
  if (loading) return <Skeleton className={className ?? 'aspect-square w-full'} />;
  if (error || !src)
    return (
      <div className={`grid place-items-center bg-white/[0.04] text-ink-faint ${className ?? 'aspect-square w-full'}`}>
        <ImageOff className="h-6 w-6" aria-label="Image unavailable" />
      </div>
    );
  return <img src={src} alt={alt} className={`object-cover ${className ?? 'aspect-square w-full'}`} />;
}

export function ScanResultView({ scan, showImage = true }: { scan: Scan; showImage?: boolean }) {
  const observations = scrubDiagnosticTerms(scan.observations ?? []);
  const recommendations = scrubDiagnosticTerms(scan.recommendations ?? []);
  const qualityIssues = scan.quality?.issues ?? [];
  const symptoms = scan.symptoms ? SYMPTOM_KEYS.filter((k) => scan.symptoms?.[k]) : [];
  const color = CONCERN_COLOR[scan.concern_level];

  return (
    <div className="space-y-4" data-testid="scan-result">
      <Disclaimer variant="banner" />

      <Card className="relative overflow-hidden" glow>
        <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full blur-3xl" style={{ background: `${color}22` }} aria-hidden />
        <div className="relative flex flex-col items-center gap-5 sm:flex-row sm:items-center">
          {showImage && (
            <div className="relative w-40 shrink-0 overflow-hidden rounded-2xl border border-white/10 sm:w-44">
              <ScanImage url={scan.image_url} alt="Photo of the analysed skin spot" className="aspect-square w-full" />
            </div>
          )}
          <div className="flex-1 text-center sm:text-left">
            <ConcernBadge level={scan.concern_level} size="lg" />
            <h2 className="mt-3 text-xl font-semibold leading-snug sm:text-2xl">{scan.headline}</h2>
            <p className="mt-1.5 text-sm text-ink-muted">{LEVEL_COPY[scan.concern_level]}</p>
            <p className="mt-2 text-xs text-ink-faint">Scanned {formatDateTime(scan.created_at)}</p>
          </div>
          <div className="shrink-0 text-center">
            <ProgressRing value={scan.concern_score} color={color} label="Concern score" sublabel="score" size={116} />
            <p className="mt-1 max-w-[9rem] text-[11px] leading-snug text-ink-faint">Visual concern score (0–100). Not a probability.</p>
          </div>
        </div>
      </Card>

      {(!scan.quality?.ok || qualityIssues.length > 0) && (
        <Card className="border-amber-300/25 bg-amber-300/[0.06]">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-300" aria-hidden />
            <div>
              <h3 className="font-semibold text-amber-100">Photo quality could affect this result</h3>
              <ul className="mt-1.5 list-disc space-y-1 pl-4 text-sm text-amber-50/90">
                {qualityIssues.length ? qualityIssues.map((q) => <li key={q}>{q}</li>) : <li>The photo may be blurry, too dark or low contrast.</li>}
              </ul>
              <p className="mt-2 text-xs text-amber-100/80">Try retaking it in good, even light with the spot in focus and filling the frame.</p>
            </div>
          </div>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h3 className="mb-4 flex items-center gap-2 font-semibold">
            <Sparkles className="h-4 w-4 text-accent-cyan" aria-hidden /> Visual features
          </h3>
          <FeatureBars features={scan.features} />
        </Card>
        <div className="space-y-4">
          <Card>
            <h3 className="mb-3 flex items-center gap-2 font-semibold">
              <Eye className="h-4 w-4 text-accent-cyan" aria-hidden /> Observations
            </h3>
            {observations.length ? (
              <ul className="space-y-2">
                {observations.map((o, i) => (
                  <motion.li key={o} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 + i * 0.05 }} className="flex gap-2 text-sm text-ink">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-cyan" aria-hidden />
                    {o}
                  </motion.li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-ink-muted">No specific observations for this photo.</p>
            )}
          </Card>
          <Card>
            <h3 className="mb-3 flex items-center gap-2 font-semibold">
              <ListChecks className="h-4 w-4 text-accent-teal" aria-hidden /> Recommendations
            </h3>
            {recommendations.length ? (
              <ul className="space-y-2">
                {recommendations.map((r) => (
                  <li key={r} className="flex gap-2 text-sm text-ink">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-teal" aria-hidden />
                    {r}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-ink-muted">Keep tracking this spot and re-scan if you notice changes.</p>
            )}
          </Card>
          {symptoms.length > 0 && (
            <Card>
              <h3 className="mb-2 font-semibold">Symptoms you reported</h3>
              <div className="flex flex-wrap gap-2">
                {symptoms.map((k) => (
                  <span key={k} className="chip">
                    {SYMPTOM_LABELS[k]}
                  </span>
                ))}
              </div>
              {scan.symptoms?.notes && <p className="mt-2 text-sm text-ink-muted">{scan.symptoms.notes}</p>}
            </Card>
          )}
        </div>
      </div>

      <div className="grid gap-2 sm:grid-cols-3">
        <Link to={`/care?scan_id=${scan.id}`} className={buttonClasses('primary', 'lg', true)}>
          <CalendarHeart className="h-5 w-5" aria-hidden /> Find a dermatologist
        </Link>
        <Link to={`/track/${scan.lesion_id}`} className={buttonClasses('glass', 'lg', true)}>
          <LineChart className="h-5 w-5" aria-hidden /> Track this spot
        </Link>
        <Link to={`/assistant?scan_id=${scan.id}`} className={buttonClasses('glass', 'lg', true)}>
          <Bot className="h-5 w-5" aria-hidden /> Ask about this scan
        </Link>
      </div>

      <p className="flex items-center justify-center gap-1.5 text-center text-xs text-ink-faint">
        <Cpu className="h-3.5 w-3.5" aria-hidden />
        Analysis engine: {scan.model?.name ?? 'unknown'}
        {scan.model?.version ? ` v${scan.model.version}` : ''} ({scan.model?.kind === 'vit' ? 'vision transformer' : 'visual heuristics'})
      </p>
      <Disclaimer variant="inline" />
    </div>
  );
}
