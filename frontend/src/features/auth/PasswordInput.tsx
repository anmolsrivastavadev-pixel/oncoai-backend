import { Eye, EyeOff } from 'lucide-react';
import { forwardRef, useState } from 'react';
import { Input, type InputProps } from '@/components/ui';

export const PasswordInput = forwardRef<HTMLInputElement, Omit<InputProps, 'type' | 'right'>>(function PasswordInput(props, ref) {
  const [show, setShow] = useState(false);
  return (
    <Input
      ref={ref}
      {...props}
      type={show ? 'text' : 'password'}
      right={
        <button
          type="button"
          onClick={() => setShow((s) => !s)}
          className="grid h-11 w-11 place-items-center rounded-lg text-ink-faint hover:text-white"
          aria-label={show ? 'Hide password' : 'Show password'}
          aria-pressed={show}
        >
          {show ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
        </button>
      }
    />
  );
});
