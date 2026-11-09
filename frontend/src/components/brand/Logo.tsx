import clsx from 'clsx';
import { useId } from 'react';

/**
 * Original OncoAI mark: an open scanning ring around a stylised cell
 * (nucleus + membrane) with an orbiting "signal" dot. Cyan → teal gradient.
 */
export function LogoMark({ size = 36, className, title = 'OncoAI' }: { size?: number; className?: string; title?: string }) {
  const id = useId().replace(/:/g, '');
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" role="img" aria-label={title} className={className}>
      <defs>
        <linearGradient id={`g-${id}`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#22D3EE" />
          <stop offset="1" stopColor="#2DD4BF" />
        </linearGradient>
        <radialGradient id={`c-${id}`} cx="0.4" cy="0.35" r="0.7">
          <stop offset="0" stopColor="#67E8F9" />
          <stop offset="1" stopColor="#14B8A6" />
        </radialGradient>
      </defs>
      <circle
        cx="32"
        cy="32"
        r="24"
        fill="none"
        stroke={`url(#g-${id})`}
        strokeWidth="4"
        strokeLinecap="round"
        strokeDasharray="112 39"
        transform="rotate(-50 32 32)"
      />
      <circle cx="32" cy="32" r="15" fill="none" stroke={`url(#g-${id})`} strokeOpacity="0.45" strokeWidth="1.5" />
      <path d="M22 32a10 10 0 0 1 20 0" fill="none" stroke="#22D3EE" strokeOpacity="0.6" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="32" cy="33" r="7.5" fill={`url(#c-${id})`} />
      <circle cx="34.5" cy="30.5" r="2.4" fill="#050B1A" fillOpacity="0.85" />
      <circle cx="51" cy="15" r="3.2" fill="#2DD4BF" />
    </svg>
  );
}

export function Logo({ className, size = 34, showText = true }: { className?: string; size?: number; showText?: boolean }) {
  return (
    <span className={clsx('inline-flex items-center gap-2.5', className)}>
      <LogoMark size={size} />
      {showText && (
        <span className="font-display text-xl font-bold tracking-tight text-white">
          Onco<span className="text-gradient">AI</span>
        </span>
      )}
    </span>
  );
}
