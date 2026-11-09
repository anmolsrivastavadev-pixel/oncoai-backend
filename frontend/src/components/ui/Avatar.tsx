import clsx from 'clsx';
import { initials } from '@/lib/format';

const palette = ['from-cyan-400 to-teal-400', 'from-sky-400 to-cyan-300', 'from-teal-400 to-emerald-300', 'from-indigo-400 to-sky-300'];

export function Avatar({ name, size = 40, className }: { name: string; size?: number; className?: string }) {
  const idx = [...name].reduce((a, c) => a + c.charCodeAt(0), 0) % palette.length;
  return (
    <span
      aria-hidden
      style={{ width: size, height: size, fontSize: size * 0.38 }}
      className={clsx('inline-grid shrink-0 place-items-center rounded-full bg-gradient-to-br font-display font-semibold text-navy-950', palette[idx], className)}
    >
      {initials(name)}
    </span>
  );
}
