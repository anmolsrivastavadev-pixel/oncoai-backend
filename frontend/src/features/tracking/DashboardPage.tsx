import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Bell, CalendarClock, CalendarHeart, ChevronRight, LineChart, ScanLine, Sparkles } from 'lucide-react';
import { Disclaimer } from '@/components/Disclaimer';
import { Card, ConcernBadge, EmptyState, ErrorState, Skeleton, buttonClasses } from '@/components/ui';
import { useAuth } from '@/features/auth/AuthContext';
import { ScanImage } from '@/features/scan/ScanResultView';
import { useAsync } from '@/hooks/useAsync';
import { api } from '@/lib/api';
import { formatDate, formatDateTime, relativeTime } from '@/lib/format';
import { ConcernDonut, ScansOverTime, ScoreTrend } from './charts';

function Stat({ label, value, icon: Icon, to }: { label: string; value: number; icon: typeof ScanLine; to: string }) {
  return (
    <Link to={to} className="glass group flex items-center gap-3 p-4 transition hover:border-accent-cyan/30">
      <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-accent-cyan/10 text-accent-cyan">
        <Icon className="h-5 w-5" aria-hidden />
      </span>
      <div className="min-w-0">
        <p className="font-display text-2xl font-bold leading-none text-white">{value}</p>
        <p className="mt-1 truncate text-xs text-ink-muted">{label}</p>
      </div>
    </Link>
  );
}

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
}

export default function DashboardPage() {
  const { user } = useAuth();
  const q = useAsync(() => api.tracking.dashboard(), []);
  const d = q.data;
  const first = user?.full_name?.split(' ')[0];

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm text-ink-muted">{greeting()}{first ? `, ${first}` : ''}</p>
          <h1 className="text-2xl font-bold sm:text-3xl">Your skin dashboard</h1>
        </div>
        <Link to="/scan" className={buttonClasses('primary', 'md')}>
          <ScanLine className="h-5 w-5" aria-hidden /> New scan
        </Link>
      </header>
      <Disclaimer variant="inline" />

      {q.error ? (
        <ErrorState message={q.error.message} onRetry={q.reload} />
      ) : !d ? (
        <div className="space-y-4" role="status" aria-label="Loading dashboard">
          <div className="grid grid-cols-3 gap-3">
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <Skeleton className="h-56" />
            <Skeleton className="h-56" />
          </div>
        </div>
      ) : (
        <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.05 } } }} className="space-y-4">
          <div className="grid grid-cols-1 gap-3 min-[420px]:grid-cols-3">
            <Stat label="Tracked spots" value={d.totals.lesions} icon={LineChart} to="/track" />
            <Stat label="Total scans" value={d.totals.scans} icon={ScanLine} to="/track" />
            <Stat label="Upcoming visits" value={d.totals.upcoming_appointments} icon={CalendarHeart} to="/care" />
          </div>

          {d.totals.scans === 0 && (
            <EmptyState
              icon={Sparkles}
              title="Start with your first scan"
              description="Photograph a spot you'd like to keep an eye on. Your timeline and charts will appear here."
              action={
                <Link to="/scan" className={buttonClasses('primary')}>
                  <ScanLine className="h-5 w-5" aria-hidden /> Start a scan
                </Link>
              }
            />
          )}

          <div className="grid gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-1">
              <h2 className="mb-3 text-base font-semibold">Concern breakdown</h2>
              <ConcernDonut breakdown={d.concern_breakdown} />
              <p className="mt-3 text-xs text-ink-faint">Based on each spot's latest scan.</p>
            </Card>
            <Card className="lg:col-span-2">
              <h2 className="mb-2 text-base font-semibold">Scans over time</h2>
              <p className="mb-2 text-xs text-ink-faint">Last 90 days</p>
              {d.scans_over_time.length ? <ScansOverTime data={d.scans_over_time} /> : <p className="py-10 text-center text-sm text-ink-muted">No scans in the last 90 days.</p>}
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <h2 className="mb-2 text-base font-semibold">Concern score trend</h2>
              <p className="mb-2 text-xs text-ink-faint">Per tracked spot · 0–100 visual score</p>
              {d.score_trend.length ? <ScoreTrend points={d.score_trend} /> : <p className="py-10 text-center text-sm text-ink-muted">Scan a spot more than once to see its trend.</p>}
            </Card>
            <div className="space-y-4">
              <Card>
                <h2 className="mb-3 flex items-center gap-2 text-base font-semibold">
                  <CalendarClock className="h-4 w-4 text-accent-cyan" aria-hidden /> Next appointment
                </h2>
                {d.next_appointment ? (
                  <Link to="/care?tab=appointments" className="block rounded-xl border border-white/10 bg-white/[0.03] p-3 hover:border-accent-cyan/30">
                    <p className="font-semibold text-white">{d.next_appointment.dermatologist.name}</p>
                    <p className="text-sm text-ink-muted">{d.next_appointment.dermatologist.clinic_name}</p>
                    <p className="mt-1 text-sm text-accent-cyan">{formatDateTime(d.next_appointment.scheduled_at)}</p>
                  </Link>
                ) : (
                  <div className="text-sm text-ink-muted">
                    No upcoming visits.{' '}
                    <Link to="/care" className="font-medium text-accent-cyan hover:underline">
                      Find a dermatologist
                    </Link>
                  </div>
                )}
              </Card>
              <Card>
                <h2 className="mb-3 flex items-center gap-2 text-base font-semibold">
                  <Bell className="h-4 w-4 text-accent-cyan" aria-hidden /> Reminders
                </h2>
                {d.reminders.length ? (
                  <ul className="space-y-2">
                    {d.reminders.map((r) => (
                      <li key={r.id} className="flex items-center justify-between gap-2 text-sm">
                        <span className="truncate text-ink">{r.title}</span>
                        <span className={`shrink-0 text-xs ${new Date(r.due_at) < new Date() ? 'text-amber-300' : 'text-ink-faint'}`}>{relativeTime(r.due_at)}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-ink-muted">No reminders due.</p>
                )}
                <Link to="/care?tab=reminders" className="mt-3 inline-flex min-h-[44px] items-center text-sm font-medium text-accent-cyan hover:underline">
                  Manage reminders <ChevronRight className="h-4 w-4" aria-hidden />
                </Link>
              </Card>
            </div>
          </div>

          {d.recent_scans.length > 0 && (
            <Card>
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-base font-semibold">Recent scans</h2>
                <Link to="/track" className="inline-flex min-h-[44px] items-center text-sm font-medium text-accent-cyan hover:underline">
                  View all <ChevronRight className="h-4 w-4" aria-hidden />
                </Link>
              </div>
              <ul className="divide-y divide-white/5">
                {d.recent_scans.map((s) => (
                  <li key={s.id}>
                    <Link to={`/scan/${s.id}`} className="flex items-center gap-3 py-3 hover:opacity-90">
                      <ScanImage url={s.thumbnail_url} alt="" className="h-12 w-12 shrink-0 rounded-xl" />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-white">{s.headline}</p>
                        <p className="text-xs text-ink-faint">{formatDate(s.created_at)} · score {Math.round(s.concern_score)}</p>
                      </div>
                      <ConcernBadge level={s.concern_level} size="sm" />
                    </Link>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </motion.div>
      )}
    </div>
  );
}
