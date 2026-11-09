import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react';
import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from 'react';

export type ToastTone = 'success' | 'error' | 'info';
interface ToastItem {
  id: number;
  tone: ToastTone;
  message: string;
}

interface ToastApi {
  show: (message: string, tone?: ToastTone) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
}

const ToastCtx = createContext<ToastApi | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const seq = useRef(0);
  const dismiss = useCallback((id: number) => setItems((xs) => xs.filter((x) => x.id !== id)), []);
  const show = useCallback(
    (message: string, tone: ToastTone = 'info') => {
      const id = ++seq.current;
      setItems((xs) => [...xs.slice(-2), { id, tone, message }]);
      setTimeout(() => dismiss(id), tone === 'error' ? 6000 : 3800);
    },
    [dismiss],
  );
  const api = useMemo<ToastApi>(
    () => ({ show, success: (m) => show(m, 'success'), error: (m) => show(m, 'error'), info: (m) => show(m, 'info') }),
    [show],
  );
  const icons = { success: CheckCircle2, error: AlertCircle, info: Info };
  return (
    <ToastCtx.Provider value={api}>
      {children}
      <div
        aria-live="polite"
        className="pointer-events-none fixed inset-x-0 top-0 z-[70] flex flex-col items-center gap-2 px-4"
        style={{ paddingTop: 'calc(var(--safe-top) + 12px)' }}
      >
        <AnimatePresence>
          {items.map((t) => {
            const Icon = icons[t.tone];
            return (
              <motion.div
                key={t.id}
                layout
                initial={{ opacity: 0, y: -16, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.97 }}
                role={t.tone === 'error' ? 'alert' : 'status'}
                className={clsx(
                  'glass-strong pointer-events-auto flex w-full max-w-md items-start gap-3 px-4 py-3 text-sm',
                  t.tone === 'success' && 'border-emerald-300/30',
                  t.tone === 'error' && 'border-rose-300/30',
                )}
              >
                <Icon
                  className={clsx('mt-0.5 h-5 w-5 shrink-0', t.tone === 'success' ? 'text-emerald-300' : t.tone === 'error' ? 'text-rose-300' : 'text-accent-cyan')}
                  aria-hidden
                />
                <p className="flex-1 text-ink">{t.message}</p>
                <button type="button" onClick={() => dismiss(t.id)} aria-label="Dismiss notification" className="-m-1 grid h-8 w-8 place-items-center rounded-lg text-ink-faint hover:text-white">
                  <X className="h-4 w-4" />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastCtx.Provider>
  );
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastCtx);
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>');
  return ctx;
}
