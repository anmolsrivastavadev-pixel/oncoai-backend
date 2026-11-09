import type { Dashboard, Post, Scan, User } from '@/types/api';

export const user: User = {
  id: 1,
  email: 'alex@example.com',
  full_name: 'Alex Rivera',
  date_of_birth: null,
  skin_type: 'III',
  location: 'Lisbon',
  bio: null,
  role: 'user',
  created_at: '2026-01-01T00:00:00Z',
};

export const tokenPair = (access = 'acc-1', refresh = 'ref-1') => ({ access_token: access, refresh_token: refresh, token_type: 'bearer' as const, user });

export const scan = (over: Partial<Scan> = {}): Scan => ({
  id: 42,
  lesion_id: 7,
  created_at: '2026-11-01T10:00:00Z',
  concern_level: 'moderate',
  concern_score: 54,
  thumbnail_url: '/api/v1/scans/42/image?variant=thumb',
  headline: 'Some irregular visual patterns detected.',
  image_url: '/api/v1/scans/42/image',
  quality: { ok: true, blur_score: 120, brightness: 0.55, contrast: 0.4, issues: [] },
  features: { asymmetry: 61, border_irregularity: 48, color_variation: 33, diameter_px: 210, diameter_relative: 22, color_count: 3 },
  observations: ['Irregular visual patterns detected.', 'Colour appears fairly uniform.'],
  recommendations: ['Consider professional dermatologist evaluation.', 'Re-scan in 4 weeks to track changes.'],
  symptoms: null,
  model: { name: 'oncoai-heuristic', kind: 'heuristic', version: '1.0' },
  disclaimer: 'OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or treatment advice.',
  ...over,
});

export const post = (over: Partial<Post> = {}): Post => ({
  id: 5,
  title: 'Getting my first check-up',
  body: 'I was nervous but it went fine.',
  topic: 'stories',
  author: { id: 2, display_name: 'Sam' },
  created_at: '2026-11-05T10:00:00Z',
  comment_count: 2,
  reactions: { support: 3, hug: 1, strength: 0, relate: 2 },
  my_reactions: ['support'],
  is_mine: false,
  status: 'visible',
  ...over,
});

export const dashboard: Dashboard = {
  totals: { lesions: 3, scans: 8, upcoming_appointments: 1 },
  concern_breakdown: { low: 2, moderate: 1, higher: 0 },
  scans_over_time: [
    { date: '2026-10-01', count: 2 },
    { date: '2026-10-15', count: 3 },
  ],
  score_trend: [
    { date: '2026-10-01', lesion_id: 7, lesion_label: 'Shoulder', concern_score: 40 },
    { date: '2026-10-15', lesion_id: 7, lesion_label: 'Shoulder', concern_score: 45 },
    { date: '2026-10-15', lesion_id: 8, lesion_label: 'Back', concern_score: 20 },
  ],
  recent_scans: [],
  next_appointment: null,
  reminders: [],
};

export const jsonResponse = (status: number, body: unknown) =>
  new Response(body === undefined ? null : JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
