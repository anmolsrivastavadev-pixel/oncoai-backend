import { Area, AreaChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { CONCERN_COLOR } from '@/components/ui';
import { CONCERN_LABEL } from '@/lib/format';
import type { ConcernLevel, Dashboard } from '@/types/api';

/** Categorical series palette (validated for the dark chart surface). Fixed order, never cycled. */
export const SERIES_COLORS = ['#0891B2', '#8B5CF6', '#EA580C', '#DB2777', '#4F46E5'];
const MAX_SERIES = SERIES_COLORS.length;

const axis = { stroke: 'rgba(255,255,255,0.12)', tick: { fill: '#A9B8D0', fontSize: 11 }, tickLine: false };
const tooltipStyle = {
  contentStyle: { background: '#0A1630', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 12, color: '#E6EEF9', fontSize: 12 },
  labelStyle: { color: '#A9B8D0' },
  itemStyle: { color: '#E6EEF9' },
};

const shortDate = (d: string) => {
  const dt = new Date(d.length === 10 ? `${d}T00:00:00` : d);
  return Number.isNaN(dt.getTime()) ? d : dt.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
};

export function ConcernDonut({ breakdown }: { breakdown: Dashboard['concern_breakdown'] }) {
  const levels: ConcernLevel[] = ['low', 'moderate', 'higher'];
  const data = levels.map((l) => ({ level: l, name: CONCERN_LABEL[l], value: breakdown[l] ?? 0 }));
  const total = data.reduce((a, d) => a + d.value, 0);
  return (
    <div className="flex items-center gap-4">
      <div className="relative h-36 w-36 shrink-0" role="img" aria-label={`Concern breakdown: ${data.map((d) => `${d.value} ${d.name}`).join(', ')}`}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={total ? data : [{ name: 'none', value: 1, level: 'none' }]} dataKey="value" innerRadius={46} outerRadius={64} paddingAngle={total ? 3 : 0} stroke="#0A1630" strokeWidth={2} isAnimationActive>
              {(total ? data : [{ level: 'none' }]).map((d) => (
                <Cell key={d.level} fill={d.level === 'none' ? 'rgba(255,255,255,0.08)' : CONCERN_COLOR[d.level as ConcernLevel]} />
              ))}
            </Pie>
            {total > 0 && <Tooltip {...tooltipStyle} />}
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
          <div>
            <div className="font-display text-2xl font-bold text-white">{total}</div>
            <div className="text-[10px] uppercase tracking-wider text-ink-faint">spots</div>
          </div>
        </div>
      </div>
      <ul className="space-y-2 text-sm">
        {data.map((d) => (
          <li key={d.level} className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: CONCERN_COLOR[d.level] }} aria-hidden />
            <span className="text-ink-muted">{d.name}</span>
            <span className="ml-auto pl-3 font-semibold text-white">{d.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ScansOverTime({ data }: { data: Dashboard['scans_over_time'] }) {
  return (
    <div className="h-48" role="img" aria-label="Scans over the last 90 days">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
          <defs>
            <linearGradient id="area-cyan" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#22D3EE" stopOpacity={0.45} />
              <stop offset="1" stopColor="#22D3EE" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="date" tickFormatter={shortDate} minTickGap={24} {...axis} />
          <YAxis allowDecimals={false} {...axis} width={40} />
          <Tooltip {...tooltipStyle} labelFormatter={(l: string) => shortDate(l)} formatter={(v: number) => [v, 'Scans']} cursor={{ stroke: 'rgba(34,211,238,0.4)' }} />
          <Area type="monotone" dataKey="count" stroke="#22D3EE" strokeWidth={2} fill="url(#area-cyan)" activeDot={{ r: 5, stroke: '#0A1630', strokeWidth: 2 }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Pivot [{date, lesion_id, lesion_label, concern_score}] into wide rows for a multi-line chart. */
export function pivotTrend(points: Dashboard['score_trend']) {
  const lesions = new Map<number, string>();
  const rows = new Map<string, Record<string, number | string>>();
  for (const p of points) {
    if (!lesions.has(p.lesion_id)) lesions.set(p.lesion_id, p.lesion_label);
    const key = p.date.slice(0, 10);
    const row = rows.get(key) ?? { date: key };
    row[`l${p.lesion_id}`] = p.concern_score;
    rows.set(key, row);
  }
  const series = [...lesions.entries()].slice(0, MAX_SERIES).map(([id, label], i) => ({ key: `l${id}`, label, color: SERIES_COLORS[i]! }));
  return { rows: [...rows.values()].sort((a, b) => String(a.date).localeCompare(String(b.date))), series };
}

export function ScoreTrend({ points }: { points: Dashboard['score_trend'] }) {
  const { rows, series } = pivotTrend(points);
  return (
    <div className="h-56" role="img" aria-label="Concern score trend per spot">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="date" tickFormatter={shortDate} minTickGap={24} {...axis} />
          <YAxis domain={[0, 100]} {...axis} width={40} />
          <Tooltip {...tooltipStyle} labelFormatter={(l: string) => shortDate(l)} />
          {series.length > 1 && <Legend wrapperStyle={{ fontSize: 12, color: '#A9B8D0' }} iconType="circle" iconSize={8} />}
          {series.map((s) => (
            <Line key={s.key} type="monotone" dataKey={s.key} name={s.label} stroke={s.color} strokeWidth={2} dot={{ r: 4, strokeWidth: 2, stroke: '#0A1630', fill: s.color }} activeDot={{ r: 6 }} connectNulls />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
