import clsx from 'clsx';
import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { Spinner } from './Spinner';

export type ButtonVariant = 'primary' | 'glass' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg' | 'icon';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  block?: boolean;
}

const variants: Record<ButtonVariant, string> = {
  primary:
    'bg-gradient-to-r from-accent-cyan to-accent-teal text-navy-950 font-semibold shadow-glow hover:brightness-110 active:brightness-95',
  glass: 'glass text-ink hover:bg-white/10 hover:border-white/20',
  ghost: 'text-ink-muted hover:text-white hover:bg-white/5',
  danger: 'bg-rose-500/15 text-rose-200 border border-rose-400/30 hover:bg-rose-500/25',
};

const sizes: Record<ButtonSize, string> = {
  sm: 'min-h-[40px] px-3.5 text-sm rounded-xl gap-1.5',
  md: 'min-h-[44px] px-5 text-[15px] rounded-xl gap-2',
  lg: 'min-h-[52px] px-6 text-base rounded-2xl gap-2.5',
  icon: 'h-11 w-11 rounded-xl',
};

export const buttonClasses = (variant: ButtonVariant = 'primary', size: ButtonSize = 'md', block = false) =>
  clsx(
    'inline-flex select-none items-center justify-center font-medium transition duration-150 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-navy-950',
    variants[variant],
    sizes[size],
    block && 'w-full',
  );

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', size = 'md', loading, leftIcon, rightIcon, block, className, children, disabled, type = 'button', ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={clsx(buttonClasses(variant, size, block), 'active:scale-[0.98]', className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <Spinner className="h-4 w-4" label="Working" /> : leftIcon}
      {children}
      {!loading && rightIcon}
    </button>
  );
});
