import { motion, useReducedMotion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { LogoMark } from '@/components/brand/Logo';

const PHASES = ['Uploading photo securely…', 'Checking photo quality…', 'Measuring symmetry and borders…', 'Analysing colour patterns…', 'Preparing your summary…'];

export function AnalyzingState({ progress, previewUrl }: { progress: number; previewUrl?: string }) {
  const reduce = useReducedMotion();
  const [phase, setPhase] = useState(0);
  useEffect(() => {
    if (progress < 100) {
      setPhase(0);
      return;
    }
    const t = setInterval(() => setPhase((p) => Math.min(PHASES.length - 1, p + 1)), 900);
    return () => clearInterval(t);
  }, [progress]);

  return (
    <div className="glass flex flex-col items-center px-6 py-10 text-center" role="status" aria-live="polite">
      <div className="relative mb-6 h-48 w-48 overflow-hidden rounded-full border border-accent-cyan/30 shadow-glow">
        {previewUrl ? <img src={previewUrl} alt="" className="h-full w-full object-cover opacity-70" /> : <div className="h-full w-full bg-navy-900" />}
        <motion.div
          className="absolute inset-x-0 h-16 bg-gradient-to-b from-transparent via-accent-cyan/50 to-transparent"
          initial={{ top: '-20%' }}
          animate={reduce ? { top: '40%' } : { top: ['-20%', '100%', '-20%'] }}
          transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
        />
        <div className="absolute inset-0 rounded-full ring-1 ring-inset ring-white/10" />
      </div>
      <LogoMark size={28} />
      <p className="mt-3 font-display text-lg font-semibold text-white">{progress < 100 ? `Uploading… ${progress}%` : 'Analysing visual patterns'}</p>
      <p className="mt-1 text-sm text-ink-muted">{PHASES[phase]}</p>
      <div className="mt-5 h-2 w-full max-w-xs overflow-hidden rounded-full bg-white/10" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress} aria-label="Upload progress">
        <motion.div className="h-full rounded-full bg-gradient-to-r from-accent-cyan to-accent-teal" animate={{ width: `${progress}%` }} transition={{ ease: 'easeOut' }} />
      </div>
    </div>
  );
}
