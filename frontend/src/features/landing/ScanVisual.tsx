import { motion, useReducedMotion } from 'framer-motion';

/** Decorative animated "scan" illustration: rings, a stylised cell, a sweeping scan line, data points. */
export function ScanVisual() {
  const reduce = useReducedMotion();
  const spin = reduce ? {} : { rotate: 360 };
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[420px]" aria-hidden>
      <div className="absolute inset-[8%] rounded-full bg-accent-cyan/10 blur-3xl" />
      <svg viewBox="0 0 400 400" className="relative h-full w-full">
        <defs>
          <linearGradient id="sv-g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#22D3EE" />
            <stop offset="1" stopColor="#2DD4BF" />
          </linearGradient>
          <radialGradient id="sv-cell" cx="0.45" cy="0.4" r="0.65">
            <stop offset="0" stopColor="#67E8F9" stopOpacity="0.9" />
            <stop offset="0.6" stopColor="#14B8A6" stopOpacity="0.55" />
            <stop offset="1" stopColor="#0E7490" stopOpacity="0.2" />
          </radialGradient>
          <linearGradient id="sv-line" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#22D3EE" stopOpacity="0" />
            <stop offset="0.5" stopColor="#22D3EE" stopOpacity="0.9" />
            <stop offset="1" stopColor="#22D3EE" stopOpacity="0" />
          </linearGradient>
          <clipPath id="sv-clip">
            <circle cx="200" cy="200" r="120" />
          </clipPath>
        </defs>

        <motion.g style={{ originX: '200px', originY: '200px' }} animate={spin} transition={{ duration: 40, repeat: Infinity, ease: 'linear' }}>
          <circle cx="200" cy="200" r="180" fill="none" stroke="url(#sv-g)" strokeOpacity="0.25" strokeWidth="1" strokeDasharray="2 10" />
        </motion.g>
        <motion.g style={{ originX: '200px', originY: '200px' }} animate={reduce ? {} : { rotate: -360 }} transition={{ duration: 24, repeat: Infinity, ease: 'linear' }}>
          <circle cx="200" cy="200" r="152" fill="none" stroke="url(#sv-g)" strokeWidth="3" strokeLinecap="round" strokeDasharray="220 80 40 80" />
          <circle cx="352" cy="200" r="5" fill="#2DD4BF" />
        </motion.g>
        <circle cx="200" cy="200" r="120" fill="rgba(10,22,48,0.7)" stroke="rgba(255,255,255,0.08)" />

        <g clipPath="url(#sv-clip)">
          {/* grid */}
          {Array.from({ length: 9 }).map((_, i) => (
            <line key={`h${i}`} x1="80" x2="320" y1={80 + i * 30} y2={80 + i * 30} stroke="rgba(34,211,238,0.07)" />
          ))}
          {Array.from({ length: 9 }).map((_, i) => (
            <line key={`v${i}`} y1="80" y2="320" x1={80 + i * 30} x2={80 + i * 30} stroke="rgba(34,211,238,0.07)" />
          ))}
          {/* cell */}
          <motion.path
            d="M200 140c34 0 58 22 60 54 2 34-22 66-58 66-38 0-62-26-62-58 0-36 26-62 60-62z"
            fill="url(#sv-cell)"
            animate={reduce ? {} : { scale: [1, 1.03, 1] }}
            style={{ originX: '200px', originY: '200px' }}
            transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
          />
          <circle cx="210" cy="190" r="14" fill="#050B1A" fillOpacity="0.55" />
          <circle cx="182" cy="222" r="4" fill="#A5F3FC" fillOpacity="0.7" />
          <circle cx="228" cy="226" r="3" fill="#A5F3FC" fillOpacity="0.6" />
          {/* scan line */}
          <motion.rect
            x="80"
            width="240"
            height="60"
            fill="url(#sv-line)"
            initial={{ y: 70 }}
            animate={reduce ? { y: 170 } : { y: [70, 270, 70] }}
            transition={{ duration: 3.6, repeat: Infinity, ease: 'easeInOut' }}
            opacity="0.55"
          />
        </g>

        {/* corner brackets */}
        {[
          'M110 130 v-20 h20',
          'M290 130 v-20 h-20',
          'M110 270 v20 h20',
          'M290 270 v20 h-20',
        ].map((d) => (
          <path key={d} d={d} fill="none" stroke="#22D3EE" strokeWidth="3" strokeLinecap="round" />
        ))}
      </svg>

      {/* floating metric chips */}
      <motion.div
        className="glass absolute left-0 top-[14%] px-3 py-2 text-xs sm:-left-4"
        animate={reduce ? {} : { y: [0, -6, 0] }}
        transition={{ duration: 5, repeat: Infinity }}
      >
        <p className="text-ink-faint">Symmetry</p>
        <p className="font-display text-sm font-semibold text-white">Analysed</p>
      </motion.div>
      <motion.div
        className="glass absolute bottom-[12%] right-0 px-3 py-2 text-xs sm:-right-4"
        animate={reduce ? {} : { y: [0, 6, 0] }}
        transition={{ duration: 6, repeat: Infinity }}
      >
        <p className="text-ink-faint">Tracked over time</p>
        <p className="font-display text-sm font-semibold text-accent-teal">4 scans</p>
      </motion.div>
    </div>
  );
}
