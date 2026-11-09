import { motion, useReducedMotion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowRight, Bot, CalendarHeart, Camera, LineChart, ScanLine, Sparkles, Users, type LucideIcon } from 'lucide-react';
import { Logo } from '@/components/brand/Logo';
import { Disclaimer } from '@/components/Disclaimer';
import { buttonClasses } from '@/components/ui';
import { useAuth } from '@/features/auth/AuthContext';
import { TAGLINE } from '@/lib/constants';
import { ScanVisual } from './ScanVisual';

const FEATURES: { icon: LucideIcon; title: string; text: string }[] = [
  { icon: ScanLine, title: 'AI-assisted visual analysis', text: 'Measures visual patterns like symmetry, border regularity and colour variation, then explains them in plain language.' },
  { icon: LineChart, title: 'Track spots over time', text: 'Build a private timeline for each spot and compare any two photos side by side to see what changed.' },
  { icon: CalendarHeart, title: 'Dermatologist booking', text: 'Find a dermatologist, pick a time that suits you and bring your scan history to the appointment.' },
  { icon: Users, title: 'Supportive community', text: 'Share experiences and encouragement — anonymously if you prefer — in a moderated, privacy-first space.' },
  { icon: Bot, title: 'Educational assistant', text: 'Ask questions about skin health, sun safety and what to expect at a visit. It never diagnoses.' },
];

const STEPS = [
  { icon: Camera, title: 'Snap a clear photo', text: 'Good light, in focus, the spot filling the frame.' },
  { icon: Sparkles, title: 'Get an awareness summary', text: 'See a concern level and the visual features behind it.' },
  { icon: LineChart, title: 'Track & stay informed', text: 'Re-scan regularly, set reminders and talk to a professional.' },
];

const ABCDE = [
  { k: 'A', t: 'Asymmetry', d: 'One half looks unlike the other.' },
  { k: 'B', t: 'Border', d: 'Edges that are irregular, ragged or blurred.' },
  { k: 'C', t: 'Colour', d: 'Several shades or uneven colour.' },
  { k: 'D', t: 'Diameter', d: 'Larger than a pencil eraser (~6 mm).' },
  { k: 'E', t: 'Evolving', d: 'Changes in size, shape or colour over time.' },
];

function Reveal({ children, delay = 0, className }: { children: React.ReactNode; delay?: number; className?: string }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={reduce ? { opacity: 1 } : { opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.5, delay }}
    >
      {children}
    </motion.div>
  );
}

export default function LandingPage() {
  const { status } = useAuth();
  const authed = status === 'authenticated';
  return (
    <div className="min-h-[100dvh] overflow-x-hidden">
      <header className="sticky top-0 z-30 border-b border-white/5 bg-navy-950/70 backdrop-blur-xl" style={{ paddingTop: 'var(--safe-top)' }}>
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-safe sm:px-6">
          <Link to="/" aria-label="OncoAI home">
            <Logo />
          </Link>
          <nav className="flex items-center gap-1 sm:gap-2" aria-label="Account">
            {authed ? (
              <Link to="/dashboard" className={buttonClasses('primary', 'sm')}>
                Open app
              </Link>
            ) : (
              <>
                <Link to="/login" className={buttonClasses('ghost', 'sm')}>
                  Sign in
                </Link>
                <Link to="/signup" className={buttonClasses('primary', 'sm')}>
                  Get started
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <main>
        {/* HERO */}
        <section className="relative mx-auto grid max-w-6xl items-center gap-10 px-safe pb-12 pt-10 sm:px-6 lg:grid-cols-[1.1fr_1fr] lg:pb-20 lg:pt-16">
          <div>
            <motion.p initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="inline-flex items-center gap-2 rounded-full border border-accent-cyan/30 bg-accent-cyan/10 px-3 py-1 text-xs font-semibold text-cyan-100">
              <Sparkles className="h-3.5 w-3.5" aria-hidden /> AI-assisted skin health awareness
            </motion.p>
            <motion.h1 initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="mt-5 text-[2.6rem] font-bold leading-[1.05] sm:text-6xl">
              <span className="text-gradient">{TAGLINE.split(' ')[0]}</span> {TAGLINE.split(' ').slice(1, 2).join(' ')}
              <br />
              {TAGLINE.split(' ').slice(2).join(' ')}
            </motion.h1>
            <motion.p initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="mt-5 max-w-xl text-base leading-relaxed text-ink-muted sm:text-lg">
              OncoAI helps you photograph skin spots, understand their visual features, follow changes over time and connect with dermatologists — all in one calm, private place.
            </motion.p>
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="mt-7 flex flex-col gap-3 sm:flex-row">
              <Link to={authed ? '/scan' : '/signup'} className={buttonClasses('primary', 'lg')}>
                {authed ? 'Start a scan' : 'Get started'} <ArrowRight className="h-5 w-5" aria-hidden />
              </Link>
              {!authed && (
                <Link to="/login" className={buttonClasses('glass', 'lg')}>
                  Sign in
                </Link>
              )}
            </motion.div>
            <Disclaimer variant="banner" className="mt-7 max-w-xl" />
          </div>
          <ScanVisual />
        </section>

        {/* FEATURES */}
        <section className="mx-auto max-w-6xl px-safe py-12 sm:px-6" aria-labelledby="features-h">
          <Reveal>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent-cyan">Features</p>
            <h2 id="features-h" className="mt-2 text-3xl font-bold sm:text-4xl">
              Everything you need to stay informed
            </h2>
          </Reveal>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f, i) => (
              <Reveal key={f.title} delay={i * 0.05}>
                <div className="glass h-full p-5 transition hover:border-accent-cyan/30">
                  <div className="mb-4 grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-accent-cyan/20 to-accent-teal/10 text-accent-cyan">
                    <f.icon className="h-5 w-5" aria-hidden />
                  </div>
                  <h3 className="text-lg font-semibold">{f.title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-ink-muted">{f.text}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        {/* HOW IT WORKS */}
        <section className="mx-auto max-w-6xl px-safe py-12 sm:px-6" aria-labelledby="how-h">
          <Reveal>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent-cyan">How it works</p>
            <h2 id="how-h" className="mt-2 text-3xl font-bold sm:text-4xl">
              Three simple steps
            </h2>
          </Reveal>
          <ol className="mt-8 grid gap-4 md:grid-cols-3">
            {STEPS.map((s, i) => (
              <Reveal key={s.title} delay={i * 0.08}>
                <li className="glass relative h-full p-5">
                  <span className="absolute right-4 top-3 font-display text-5xl font-bold text-white/5">{i + 1}</span>
                  <s.icon className="h-6 w-6 text-accent-teal" aria-hidden />
                  <h3 className="mt-3 text-lg font-semibold">{s.title}</h3>
                  <p className="mt-1 text-sm text-ink-muted">{s.text}</p>
                </li>
              </Reveal>
            ))}
          </ol>
        </section>

        {/* ABCDE */}
        <section className="mx-auto max-w-6xl px-safe py-12 sm:px-6" aria-labelledby="abcde-h">
          <Reveal className="glass overflow-hidden p-6 sm:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent-cyan">Learn</p>
            <h2 id="abcde-h" className="mt-2 text-2xl font-bold sm:text-3xl">
              The ABCDE guide to looking at spots
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-ink-muted">A widely used educational checklist for noticing visual changes worth showing to a dermatologist.</p>
            <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-5">
              {ABCDE.map((a) => (
                <div key={a.k} className="rounded-xl border border-white/10 bg-navy-950/40 p-4">
                  <span className="font-display text-3xl font-bold text-gradient">{a.k}</span>
                  <p className="mt-1 text-sm font-semibold text-white">{a.t}</p>
                  <p className="mt-0.5 text-xs leading-snug text-ink-muted">{a.d}</p>
                </div>
              ))}
            </div>
          </Reveal>
        </section>

        {/* CTA */}
        <section className="mx-auto max-w-6xl px-safe pb-16 pt-6 sm:px-6">
          <Reveal className="relative overflow-hidden rounded-3xl border border-accent-cyan/20 bg-gradient-to-br from-accent-cyan/15 via-navy-900 to-accent-teal/10 p-8 text-center shadow-glow">
            <h2 className="text-2xl font-bold sm:text-3xl">Start building your skin timeline</h2>
            <p className="mx-auto mt-2 max-w-lg text-sm text-ink-muted">Free, private and designed to help you have better conversations with your dermatologist.</p>
            <Link to={authed ? '/scan' : '/signup'} className={buttonClasses('primary', 'lg') + ' mt-6'}>
              {authed ? 'Start a scan' : 'Create free account'} <ArrowRight className="h-5 w-5" aria-hidden />
            </Link>
          </Reveal>
        </section>
      </main>

      <footer className="border-t border-white/10 bg-navy-950/60" style={{ paddingBottom: 'calc(var(--safe-bottom) + 24px)' }}>
        <div className="mx-auto max-w-6xl space-y-5 px-safe pt-8 sm:px-6">
          <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
            <Logo size={28} />
            <p className="text-sm text-ink-faint">{TAGLINE}</p>
          </div>
          <Disclaimer variant="inline" />
          <p className="text-xs text-ink-faint">© {new Date().getFullYear()} OncoAI. For education and awareness only. In an emergency, contact your local emergency services.</p>
        </div>
      </footer>
    </div>
  );
}
