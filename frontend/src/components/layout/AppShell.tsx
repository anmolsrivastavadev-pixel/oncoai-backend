import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import { Suspense } from 'react';
import { Link, NavLink, useLocation, useOutlet } from 'react-router-dom';
import { Bot, UserRound } from 'lucide-react';
import { Logo } from '@/components/brand/Logo';
import { Disclaimer } from '@/components/Disclaimer';
import { Avatar, ErrorBoundary, PageSkeleton } from '@/components/ui';
import { useAuth } from '@/features/auth/AuthContext';
import { ASSISTANT_NAV, MODERATION_NAV, PRIMARY_NAV, isActive, type NavItem } from './nav';
import { OfflineBanner } from './OfflineBanner';
import { PageTransition } from './PageTransition';

function SidebarLink({ item }: { item: NavItem }) {
  const { pathname } = useLocation();
  const active = isActive(pathname, item);
  const Icon = item.icon;
  return (
    <NavLink
      to={item.to}
      aria-current={active ? 'page' : undefined}
      className={clsx(
        'group relative flex min-h-[44px] items-center gap-3 rounded-xl px-3 text-[15px] font-medium transition',
        active ? 'bg-accent-cyan/10 text-white' : 'text-ink-muted hover:bg-white/5 hover:text-white',
      )}
    >
      {active && <motion.span layoutId="sidebar-active" className="absolute inset-y-2 left-0 w-1 rounded-full bg-accent-cyan shadow-glow-sm" />}
      <Icon className={clsx('h-5 w-5', active ? 'text-accent-cyan' : 'text-ink-faint group-hover:text-ink')} aria-hidden />
      {item.label}
    </NavLink>
  );
}

function Sidebar() {
  const { user, isModerator } = useAuth();
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-white/10 bg-navy-950/70 px-4 py-6 backdrop-blur-xl lg:flex">
      <Link to="/dashboard" className="mb-8 px-2" aria-label="OncoAI dashboard">
        <Logo />
      </Link>
      <nav aria-label="Main" className="flex flex-1 flex-col gap-1">
        {PRIMARY_NAV.map((i) => (
          <SidebarLink key={i.to} item={i} />
        ))}
        <div className="my-3 h-px bg-white/10" />
        <SidebarLink item={ASSISTANT_NAV} />
        {isModerator && <SidebarLink item={MODERATION_NAV} />}
      </nav>
      {user && (
        <Link to="/profile" className="glass flex items-center gap-3 p-3 hover:bg-white/10">
          <Avatar name={user.full_name || user.email} size={36} />
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-white">{user.full_name}</p>
            <p className="truncate text-xs text-ink-faint">View profile</p>
          </div>
        </Link>
      )}
    </aside>
  );
}

function BottomNav() {
  const { pathname } = useLocation();
  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-white/10 bg-navy-950/95 backdrop-blur-xl lg:hidden"
      style={{ paddingBottom: 'var(--safe-bottom)' }}
    >
      <ul className="mx-auto flex h-16 max-w-xl items-stretch justify-around px-1">
        {PRIMARY_NAV.map((item) => {
          const active = isActive(pathname, item);
          const Icon = item.icon;
          const isScan = item.to === '/scan';
          return (
            <li key={item.to} className="flex-1">
              <NavLink
                to={item.to}
                aria-current={active ? 'page' : undefined}
                className={clsx('relative flex h-full min-w-[44px] flex-col items-center justify-center gap-0.5 text-[11px] font-medium', active ? 'text-white' : 'text-ink-faint')}
              >
                {isScan ? (
                  <span
                    className={clsx(
                      '-mt-5 grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-accent-cyan to-accent-teal text-navy-950 shadow-glow',
                      active && 'ring-2 ring-white/60',
                    )}
                  >
                    <Icon className="h-6 w-6" aria-hidden />
                  </span>
                ) : (
                  <Icon className={clsx('h-[22px] w-[22px]', active && 'text-accent-cyan')} aria-hidden />
                )}
                <span>{item.label}</span>
                {active && !isScan && <motion.span layoutId="bottom-active" className="absolute top-0 h-0.5 w-8 rounded-full bg-accent-cyan" />}
              </NavLink>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

function MobileTopBar() {
  const { user, isModerator } = useAuth();
  return (
    <header className="sticky top-0 z-30 border-b border-white/5 bg-navy-950/75 backdrop-blur-xl lg:hidden" style={{ paddingTop: 'var(--safe-top)' }}>
      <div className="flex h-14 items-center justify-between px-safe">
        <Link to="/dashboard" aria-label="OncoAI dashboard">
          <Logo size={28} />
        </Link>
        <div className="flex items-center gap-1">
          {isModerator && (
            <Link to="/moderation" className="grid h-11 w-11 place-items-center rounded-xl text-ink-muted hover:text-white" aria-label="Moderation">
              <MODERATION_NAV.icon className="h-5 w-5" />
            </Link>
          )}
          <Link to="/profile" className="grid h-11 w-11 place-items-center rounded-xl" aria-label="Profile">
            {user ? <Avatar name={user.full_name || user.email} size={32} /> : <UserRound className="h-5 w-5" />}
          </Link>
        </div>
      </div>
    </header>
  );
}

function AssistantFab() {
  const { pathname } = useLocation();
  if (pathname.startsWith('/assistant')) return null;
  return (
    <Link
      to="/assistant"
      aria-label="Open AI assistant"
      className="fixed right-4 z-40 grid h-14 w-14 place-items-center rounded-full border border-accent-cyan/40 bg-navy-900/90 text-accent-cyan shadow-glow backdrop-blur-xl transition hover:scale-105 lg:bottom-8 lg:right-8"
      style={{ bottom: 'calc(var(--bottom-nav-h) + var(--safe-bottom) + 16px)' }}
    >
      <span className="absolute inset-0 animate-pulse-ring rounded-full border border-accent-cyan/40" aria-hidden />
      <Bot className="h-6 w-6" />
    </Link>
  );
}

export function AppShell() {
  const location = useLocation();
  const outlet = useOutlet();
  return (
    <div className="min-h-[100dvh]">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-[80] focus:rounded-lg focus:bg-navy-900 focus:px-3 focus:py-2">
        Skip to content
      </a>
      <Sidebar />
      <div className="lg:pl-64">
        <MobileTopBar />
        <div className="hidden lg:block" style={{ paddingTop: 'var(--safe-top)' }} />
        <OfflineBanner />
        <main id="main" className="px-safe pb-nav pt-5 sm:px-6 lg:px-10 lg:pt-8">
          <ErrorBoundary key={location.pathname}>
            <Suspense fallback={<PageSkeleton />}>
              <AnimatePresence mode="wait" initial={false}>
                <PageTransition key={location.pathname}>{outlet}</PageTransition>
              </AnimatePresence>
            </Suspense>
          </ErrorBoundary>
          <footer className="mx-auto mt-10 max-w-5xl border-t border-white/5 pt-5">
            <Disclaimer variant="compact" className="text-center" />
          </footer>
        </main>
      </div>
      <BottomNav />
      <AssistantFab />
    </div>
  );
}
