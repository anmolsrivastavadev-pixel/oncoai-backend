import clsx from 'clsx';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { X } from 'lucide-react';
import { useEffect, useId, useRef, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { useMediaQuery } from '@/hooks/useMediaQuery';

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  description?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  size?: 'sm' | 'md' | 'lg';
  /** Force a bottom sheet even on desktop. Phones always get a sheet. */
  sheet?: boolean;
}

/** Accessible dialog: centered modal on ≥sm, bottom sheet on phones. */
export function Modal({ open, onClose, title, description, children, footer, size = 'md', sheet }: ModalProps) {
  const isDesktop = useMediaQuery('(min-width: 640px)');
  const asSheet = sheet || !isDesktop;
  const reduce = useReducedMotion();
  const titleId = useId();
  const descId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const lastFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) return;
    lastFocus.current = document.activeElement as HTMLElement | null;
    const t = setTimeout(() => {
      const el = panelRef.current?.querySelector<HTMLElement>('[data-autofocus], input, textarea, select, button:not([data-close])');
      (el ?? panelRef.current)?.focus();
    }, 30);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'Tab' && panelRef.current) {
        const f = panelRef.current.querySelectorAll<HTMLElement>('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (!f.length) return;
        const first = f[0]!;
        const last = f[f.length - 1]!;
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener('keydown', onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      clearTimeout(t);
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = prev;
      lastFocus.current?.focus?.();
    };
  }, [open, onClose]);

  const widths = { sm: 'sm:max-w-sm', md: 'sm:max-w-lg', lg: 'sm:max-w-2xl' };

  return createPortal(
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-[60]">
          <motion.div
            className="absolute inset-0 bg-navy-950/70 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            aria-hidden
          />
          <div className={clsx('pointer-events-none absolute inset-0 flex', asSheet ? 'items-end justify-center' : 'items-center justify-center p-4')}>
            <motion.div
              ref={panelRef}
              role="dialog"
              aria-modal="true"
              aria-labelledby={titleId}
              aria-describedby={description ? descId : undefined}
              tabIndex={-1}
              className={clsx(
                'glass-strong pointer-events-auto flex max-h-[92dvh] w-full flex-col overflow-hidden focus:outline-none',
                asSheet ? 'rounded-b-none rounded-t-3xl pb-safe sm:max-w-2xl' : widths[size],
              )}
              initial={reduce ? { opacity: 0 } : asSheet ? { y: '100%' } : { opacity: 0, scale: 0.96, y: 8 }}
              animate={reduce ? { opacity: 1 } : asSheet ? { y: 0 } : { opacity: 1, scale: 1, y: 0 }}
              exit={reduce ? { opacity: 0 } : asSheet ? { y: '100%' } : { opacity: 0, scale: 0.96, y: 8 }}
              transition={{ type: 'spring', damping: 30, stiffness: 320 }}
            >
              {asSheet && <div className="mx-auto mt-2.5 h-1.5 w-10 shrink-0 rounded-full bg-white/20" aria-hidden />}
              <div className="flex items-start justify-between gap-3 px-5 pb-2 pt-4">
                <div className="min-w-0">
                  <h2 id={titleId} className="text-lg font-semibold">
                    {title}
                  </h2>
                  {description && (
                    <p id={descId} className="mt-0.5 text-sm text-ink-muted">
                      {description}
                    </p>
                  )}
                </div>
                <button
                  type="button"
                  data-close
                  onClick={onClose}
                  aria-label="Close dialog"
                  className="-mr-2 -mt-1 grid h-11 w-11 shrink-0 place-items-center rounded-xl text-ink-muted hover:bg-white/5 hover:text-white"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto px-5 pb-5">{children}</div>
              {footer && <div className="border-t border-white/10 px-5 py-3.5">{footer}</div>}
            </motion.div>
          </div>
        </div>
      )}
    </AnimatePresence>,
    document.body,
  );
}

export const Sheet = (props: Omit<ModalProps, 'sheet'>) => <Modal {...props} sheet />;
