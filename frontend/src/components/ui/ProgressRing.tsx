import { motion, useReducedMotion } from 'framer-motion';

export function ProgressRing({
  value,
  size = 120,
  stroke = 10,
  color = '#22D3EE',
  label,
  sublabel,
}: {
  value: number;
  size?: number;
  stroke?: number;
  color?: string;
  label?: string;
  sublabel?: string;
}) {
  const reduce = useReducedMotion();
  const v = Math.max(0, Math.min(100, value));
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative inline-grid place-items-center" style={{ width: size, height: size }} role="img" aria-label={`${label ?? 'Score'}: ${Math.round(v)} out of 100`}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="rgba(255,255,255,0.08)" strokeWidth={stroke} fill="none" />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={c}
          initial={{ strokeDashoffset: reduce ? c * (1 - v / 100) : c }}
          animate={{ strokeDashoffset: c * (1 - v / 100) }}
          transition={{ duration: reduce ? 0 : 1.1, ease: 'easeOut' }}
          style={{ filter: `drop-shadow(0 0 6px ${color}88)` }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">
        <div>
          <div className="font-display text-3xl font-bold text-white">{Math.round(v)}</div>
          {sublabel && <div className="text-[11px] uppercase tracking-wider text-ink-faint">{sublabel}</div>}
        </div>
      </div>
    </div>
  );
}
