import clsx from 'clsx';
import type { HTMLAttributes } from 'react';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padded?: boolean;
  glow?: boolean;
  interactive?: boolean;
}

export function Card({ className, padded = true, glow, interactive, ...rest }: CardProps) {
  return (
    <div
      className={clsx(
        'glass',
        padded && 'p-4 sm:p-5',
        glow && 'shadow-glow',
        interactive && 'transition hover:border-accent-cyan/30 hover:bg-white/[0.07]',
        className,
      )}
      {...rest}
    />
  );
}

export const GlassCard = Card;

export function CardTitle({ className, ...rest }: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={clsx('text-base font-semibold text-white', className)} {...rest} />;
}
