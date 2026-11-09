import { motion, useReducedMotion } from 'framer-motion';
import { clamp } from '@/lib/format';
import type { ScanFeatures } from '@/types/api';

export const FEATURE_INFO: { key: keyof Pick<ScanFeatures, 'asymmetry' | 'border_irregularity' | 'color_variation' | 'diameter_relative'>; label: string; explain: string }[] = [
  { key: 'asymmetry', label: 'Asymmetry', explain: 'How different the two halves of the spot look. Higher means less symmetrical.' },
  { key: 'border_irregularity', label: 'Border irregularity', explain: 'How uneven, notched or blurred the edge of the spot appears.' },
  { key: 'color_variation', label: 'Colour variation', explain: 'How much the shades within the spot differ from each other.' },
  { key: 'diameter_relative', label: 'Relative size', explain: 'How much of the photo the spot fills. It depends on camera distance, so it is not a real-world measurement.' },
];

function barColor(v: number) {
  if (v >= 66) return 'from-rose-400 to-rose-300';
  if (v >= 40) return 'from-amber-400 to-amber-300';
  return 'from-accent-cyan to-accent-teal';
}

export function FeatureBars({ features }: { features: ScanFeatures }) {
  const reduce = useReducedMotion();
  return (
    <ul className="space-y-4">
      {FEATURE_INFO.map((f, i) => {
        const v = clamp(Math.round(features[f.key] ?? 0));
        return (
          <li key={f.key}>
            <div className="mb-1.5 flex items-baseline justify-between gap-3">
              <span className="text-sm font-medium text-white">{f.label}</span>
              <span className="font-display text-sm font-semibold text-ink" aria-label={`${f.label} ${v} out of 100`}>
                {v}
                <span className="text-ink-faint">/100</span>
              </span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-white/[0.07]" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={v} aria-label={f.label}>
              <motion.div
                className={`h-full rounded-full bg-gradient-to-r ${barColor(v)}`}
                initial={{ width: reduce ? `${v}%` : 0 }}
                animate={{ width: `${v}%` }}
                transition={{ duration: reduce ? 0 : 0.8, delay: reduce ? 0 : 0.1 + i * 0.08, ease: 'easeOut' }}
              />
            </div>
            <p className="mt-1.5 text-xs leading-relaxed text-ink-muted">
              {f.explain}
              {f.key === 'color_variation' && features.color_count ? ` About ${features.color_count} distinct shade${features.color_count === 1 ? '' : 's'} detected.` : ''}
            </p>
          </li>
        );
      })}
    </ul>
  );
}
