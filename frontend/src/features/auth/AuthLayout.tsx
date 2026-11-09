import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Logo } from '@/components/brand/Logo';
import { Disclaimer } from '@/components/Disclaimer';
import { TAGLINE } from '@/lib/constants';

export function AuthLayout({ title, subtitle, children, footer }: { title: string; subtitle: string; children: ReactNode; footer: ReactNode }) {
  return (
    <div className="flex min-h-[100dvh] flex-col px-safe pt-safe">
      <div className="mx-auto flex w-full max-w-md flex-1 flex-col pb-8 pt-6 sm:pt-12">
        <Link to="/" className="mb-8 self-start rounded-xl" aria-label="OncoAI home">
          <Logo />
        </Link>
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="glass p-5 sm:p-7">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent-cyan">{TAGLINE}</p>
          <h1 className="mt-2 text-2xl font-bold">{title}</h1>
          <p className="mt-1 text-sm text-ink-muted">{subtitle}</p>
          <div className="mt-6">{children}</div>
        </motion.div>
        <div className="mt-5 text-center text-sm text-ink-muted">{footer}</div>
        <Disclaimer variant="banner" className="mt-6" />
      </div>
    </div>
  );
}
