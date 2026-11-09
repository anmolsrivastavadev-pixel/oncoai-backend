/**
 * Types mirroring docs/API_CONTRACT.md (v1). Keep in sync with the contract.
 */

export type ISODate = string; // ISO-8601 UTC timestamp
export type YMD = string; // YYYY-MM-DD

export interface Paginated<T> {
  items: T[];
  total: number;
}

export interface ItemsOnly<T> {
  items: T[];
}

// ---------- Health ----------
export interface Health {
  status: string;
  db: string;
  model: { loaded: boolean; name: string; kind: ModelKind };
}

// ---------- Auth / users ----------
export type Role = 'user' | 'moderator' | 'admin';
export type SkinType = 'I' | 'II' | 'III' | 'IV' | 'V' | 'VI';

export interface User {
  id: number;
  email: string;
  full_name: string;
  date_of_birth: YMD | null;
  skin_type: SkinType | null;
  location: string | null;
  bio: string | null;
  role: Role;
  created_at: ISODate;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  user: User;
}

export interface RegisterBody {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginBody {
  email: string;
  password: string;
}

export interface UpdateMeBody {
  full_name?: string;
  date_of_birth?: YMD | null;
  skin_type?: SkinType | null;
  location?: string | null;
  bio?: string | null;
}

export interface ChangePasswordBody {
  current_password: string;
  new_password: string;
}

// ---------- Lesions ----------
export const BODY_LOCATIONS = [
  'head_neck',
  'face',
  'scalp',
  'chest',
  'abdomen',
  'back',
  'upper_arm_left',
  'upper_arm_right',
  'forearm_left',
  'forearm_right',
  'hand_left',
  'hand_right',
  'thigh_left',
  'thigh_right',
  'lower_leg_left',
  'lower_leg_right',
  'foot_left',
  'foot_right',
  'other',
] as const;
export type BodyLocation = (typeof BODY_LOCATIONS)[number];

export type ConcernLevel = 'low' | 'moderate' | 'higher';

export interface Lesion {
  id: number;
  label: string;
  body_location: BodyLocation;
  notes: string | null;
  created_at: ISODate;
  scan_count: number;
  latest_concern: ConcernLevel | null;
  latest_scan_at: ISODate | null;
  thumbnail_url: string | null;
}

export interface LesionDetail extends Lesion {
  scans: ScanSummary[];
}

export interface CreateLesionBody {
  label: string;
  body_location: BodyLocation;
  notes?: string;
}

export type UpdateLesionBody = Partial<CreateLesionBody>;

// ---------- Scans ----------
export interface Symptoms {
  itching: boolean;
  bleeding: boolean;
  pain: boolean;
  changed_size: boolean;
  changed_color: boolean;
  changed_shape: boolean;
  new_spot: boolean;
  notes?: string;
}

export type ModelKind = 'vit' | 'heuristic';

export interface ScanSummary {
  id: number;
  lesion_id: number;
  created_at: ISODate;
  concern_level: ConcernLevel;
  concern_score: number;
  thumbnail_url: string;
  headline: string;
}

export interface ScanQuality {
  ok: boolean;
  blur_score: number;
  brightness: number;
  contrast: number;
  issues: string[];
}

export interface ScanFeatures {
  asymmetry: number;
  border_irregularity: number;
  color_variation: number;
  diameter_px: number;
  diameter_relative: number;
  color_count: number;
}

export interface Scan extends ScanSummary {
  image_url: string;
  quality: ScanQuality;
  features: ScanFeatures;
  observations: string[];
  recommendations: string[];
  symptoms: Symptoms | null;
  model: { name: string; kind: ModelKind; version: string };
  disclaimer: string;
}

export interface CreateScanInput {
  image: Blob;
  filename?: string;
  lesion_id?: number;
  symptoms?: Symptoms;
}

// ---------- Tracking ----------
export interface ScanDeltas {
  asymmetry: number;
  border_irregularity: number;
  color_variation: number;
  diameter_relative: number;
  concern_score: number;
}

export interface Comparison {
  a: Scan;
  b: Scan;
  deltas: ScanDeltas;
  summary: string;
}

export interface Dashboard {
  totals: { lesions: number; scans: number; upcoming_appointments: number };
  concern_breakdown: { low: number; moderate: number; higher: number };
  scans_over_time: { date: YMD; count: number }[];
  score_trend: { date: string; lesion_id: number; lesion_label: string; concern_score: number }[];
  recent_scans: ScanSummary[];
  next_appointment: Appointment | null;
  reminders: Reminder[];
}

export interface SymptomLog extends Symptoms {
  id: number;
  lesion_id: number | null;
  created_at: ISODate;
}

export type CreateSymptomLogBody = Symptoms & { lesion_id?: number };

// ---------- Dermatologists & appointments ----------
export interface Dermatologist {
  id: number;
  name: string;
  title: string;
  specialty: string;
  clinic_name: string;
  city: string;
  address: string;
  phone: string;
  rating: number;
  review_count: number;
  languages: string[];
  accepts_new_patients: boolean;
  bio: string;
  is_sample: boolean;
}

export interface DermatologistQuery {
  q?: string;
  city?: string;
  specialty?: string;
  limit?: number;
  offset?: number;
}

export interface Availability {
  date: YMD;
  slots: string[];
}

export type AppointmentStatus = 'booked' | 'cancelled' | 'completed';

export interface Appointment {
  id: number;
  dermatologist: Dermatologist;
  scheduled_at: ISODate;
  reason: string;
  status: AppointmentStatus;
  scan_id: number | null;
  created_at: ISODate;
}

export interface CreateAppointmentBody {
  dermatologist_id: number;
  date: YMD;
  time: string; // HH:MM
  reason: string;
  scan_id?: number;
}

export interface UpdateAppointmentBody {
  date?: YMD;
  time?: string;
  reason?: string;
}

// ---------- Reminders ----------
export type ReminderKind = 'rescan' | 'appointment' | 'self_check' | 'custom';

export interface Reminder {
  id: number;
  title: string;
  kind: ReminderKind;
  due_at: ISODate;
  done: boolean;
  lesion_id: number | null;
  appointment_id: number | null;
  repeat_days: number | null;
}

export interface CreateReminderBody {
  title: string;
  kind: ReminderKind;
  due_at: ISODate;
  lesion_id?: number;
  appointment_id?: number;
  repeat_days?: number;
}

export interface UpdateReminderBody {
  title?: string;
  due_at?: ISODate;
  done?: boolean;
}

// ---------- Community ----------
export const POST_TOPICS = ['support', 'awareness', 'prevention', 'stories', 'questions'] as const;
export type PostTopic = (typeof POST_TOPICS)[number];

export const REACTION_KINDS = ['support', 'hug', 'strength', 'relate'] as const;
export type ReactionKind = (typeof REACTION_KINDS)[number];
export type ReactionCounts = Record<ReactionKind, number>;

export interface Author {
  id: number | null;
  display_name: string;
}

export interface Post {
  id: number;
  title: string;
  body: string;
  topic: PostTopic;
  author: Author;
  created_at: ISODate;
  comment_count: number;
  reactions: ReactionCounts;
  my_reactions: ReactionKind[];
  is_mine: boolean;
  status: 'visible' | 'removed';
}

export interface Comment {
  id: number;
  post_id: number;
  body: string;
  author: Author;
  created_at: ISODate;
  is_mine: boolean;
}

export interface PostDetail extends Post {
  comments: Comment[];
}

export interface CreatePostBody {
  title: string;
  body: string;
  topic: PostTopic;
  anonymous?: boolean;
}

export interface CreateCommentBody {
  body: string;
  anonymous?: boolean;
}

export interface ReactionResult {
  reactions: ReactionCounts;
  my_reactions: ReactionKind[];
}

export interface ReportResult {
  id: number;
  status: 'open';
}

/**
 * The contract does not define the moderation report shape. We accept the
 * fields below defensively (all optional except id/status) — see README.
 */
export interface ModerationReport {
  id: number;
  status: string;
  reason: string;
  created_at?: ISODate;
  target_type?: 'post' | 'comment' | string;
  post_id?: number | null;
  comment_id?: number | null;
  content_preview?: string | null;
  post?: Partial<Post> | null;
  comment?: Partial<Comment> | null;
}

export type ModerationAction = 'dismiss' | 'remove_content';

// ---------- Assistant ----------
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  context?: { scan_id?: number };
}

export interface ChatResponse {
  reply: string;
  sources: { title: string; url: string }[];
  suggestions: string[];
  provider: 'claude' | 'knowledge_base';
  disclaimer: string;
  safety: { redirected: boolean; reason: string | null };
}

export interface AssistantTopic {
  id: string | number;
  title: string;
  summary: string;
}
