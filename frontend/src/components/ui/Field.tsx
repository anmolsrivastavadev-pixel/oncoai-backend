import clsx from 'clsx';
import { forwardRef, useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react';

interface FieldWrapProps {
  id: string;
  label?: ReactNode;
  hint?: ReactNode;
  error?: string | null;
  children: ReactNode;
  className?: string;
}

export function FieldWrap({ id, label, hint, error, children, className }: FieldWrapProps) {
  return (
    <div className={clsx('space-y-1.5', className)}>
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-ink">
          {label}
        </label>
      )}
      {children}
      {error ? (
        <p id={`${id}-err`} role="alert" className="text-xs font-medium text-rose-300">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="text-xs text-ink-faint">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: ReactNode;
  hint?: ReactNode;
  error?: string | null;
  right?: ReactNode;
  wrapClassName?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, hint, error, right, className, id, wrapClassName, ...rest },
  ref,
) {
  const auto = useId();
  const fid = id ?? auto;
  return (
    <FieldWrap id={fid} label={label} hint={hint} error={error} className={wrapClassName}>
      <div className="relative">
        <input
          ref={ref}
          id={fid}
          aria-invalid={!!error || undefined}
          aria-describedby={error ? `${fid}-err` : hint ? `${fid}-hint` : undefined}
          className={clsx('field', right && 'pr-12', error && 'border-rose-400/60', className)}
          {...rest}
        />
        {right && <div className="absolute inset-y-0 right-0 flex items-center pr-1">{right}</div>}
      </div>
    </FieldWrap>
  );
});

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: ReactNode;
  hint?: ReactNode;
  error?: string | null;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  { label, hint, error, className, id, ...rest },
  ref,
) {
  const auto = useId();
  const fid = id ?? auto;
  return (
    <FieldWrap id={fid} label={label} hint={hint} error={error}>
      <textarea
        ref={ref}
        id={fid}
        aria-invalid={!!error || undefined}
        aria-describedby={error ? `${fid}-err` : hint ? `${fid}-hint` : undefined}
        className={clsx('field min-h-[110px] resize-y', error && 'border-rose-400/60', className)}
        {...rest}
      />
    </FieldWrap>
  );
});

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: ReactNode;
  hint?: ReactNode;
  error?: string | null;
  options: { value: string; label: string }[];
  placeholder?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { label, hint, error, className, id, options, placeholder, ...rest },
  ref,
) {
  const auto = useId();
  const fid = id ?? auto;
  return (
    <FieldWrap id={fid} label={label} hint={hint} error={error}>
      <select ref={ref} id={fid} aria-invalid={!!error || undefined} className={clsx('field appearance-none bg-navy-950', className)} {...rest}>
        {placeholder !== undefined && <option value="">{placeholder}</option>}
        {options.map((o) => (
          <option key={o.value} value={o.value} className="bg-navy-900">
            {o.label}
          </option>
        ))}
      </select>
    </FieldWrap>
  );
});
