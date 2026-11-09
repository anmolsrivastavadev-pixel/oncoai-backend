import type { BodyLocation, ConcernLevel } from '@/types/api';

export const CONCERN_LABEL: Record<ConcernLevel, string> = {
  low: 'Low concern',
  moderate: 'Moderate concern',
  higher: 'Higher concern',
};

export function formatDate(iso: string | null | undefined, opts: Intl.DateTimeFormatOptions = { dateStyle: 'medium' }) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return new Intl.DateTimeFormat(undefined, opts).format(d);
}

export function formatDateTime(iso: string | null | undefined) {
  return formatDate(iso, { dateStyle: 'medium', timeStyle: 'short' });
}

export function relativeTime(iso: string, now: Date = new Date()): string {
  const d = new Date(iso);
  const diff = (d.getTime() - now.getTime()) / 1000;
  const abs = Math.abs(diff);
  const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' });
  if (abs < 60) return rtf.format(Math.round(diff), 'second');
  if (abs < 3600) return rtf.format(Math.round(diff / 60), 'minute');
  if (abs < 86400) return rtf.format(Math.round(diff / 3600), 'hour');
  if (abs < 86400 * 30) return rtf.format(Math.round(diff / 86400), 'day');
  if (abs < 86400 * 365) return rtf.format(Math.round(diff / (86400 * 30)), 'month');
  return rtf.format(Math.round(diff / (86400 * 365)), 'year');
}

/** Local YYYY-MM-DD for a Date. */
export function toYMD(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function nextDays(n: number, from: Date = new Date()): Date[] {
  const out: Date[] = [];
  for (let i = 0; i < n; i++) {
    const d = new Date(from.getFullYear(), from.getMonth(), from.getDate() + i);
    out.push(d);
  }
  return out;
}

export function initials(name: string): string {
  return (
    name
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((p) => p[0]?.toUpperCase() ?? '')
      .join('') || '?'
  );
}

export const BODY_LOCATION_LABEL: Record<BodyLocation, string> = {
  head_neck: 'Head & neck',
  face: 'Face',
  scalp: 'Scalp',
  chest: 'Chest',
  abdomen: 'Abdomen',
  back: 'Back',
  upper_arm_left: 'Upper arm (left)',
  upper_arm_right: 'Upper arm (right)',
  forearm_left: 'Forearm (left)',
  forearm_right: 'Forearm (right)',
  hand_left: 'Hand (left)',
  hand_right: 'Hand (right)',
  thigh_left: 'Thigh (left)',
  thigh_right: 'Thigh (right)',
  lower_leg_left: 'Lower leg (left)',
  lower_leg_right: 'Lower leg (right)',
  foot_left: 'Foot (left)',
  foot_right: 'Foot (right)',
  other: 'Other',
};

export const BODY_LOCATION_GROUPS: { title: string; items: BodyLocation[] }[] = [
  { title: 'Head', items: ['head_neck', 'face', 'scalp'] },
  { title: 'Torso', items: ['chest', 'abdomen', 'back'] },
  { title: 'Arms', items: ['upper_arm_left', 'upper_arm_right', 'forearm_left', 'forearm_right', 'hand_left', 'hand_right'] },
  { title: 'Legs', items: ['thigh_left', 'thigh_right', 'lower_leg_left', 'lower_leg_right', 'foot_left', 'foot_right'] },
  { title: 'Other', items: ['other'] },
];

export function clamp(n: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, n));
}
