import type * as T from '@/types/api';
import { API_URL } from './env';
import { TokenStore, kvStore } from './storage';

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;
  /** Field → message map for 422 validation errors (FastAPI `loc` arrays). */
  readonly fieldErrors: Record<string, string>;

  constructor(status: number, message: string, detail?: unknown, fieldErrors: Record<string, string> = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
    this.fieldErrors = fieldErrors;
  }

  get isNetwork() {
    return this.status === 0;
  }
}

interface FastApiValidationItem {
  loc?: (string | number)[];
  msg?: string;
}

const STATUS_FALLBACK: Record<number, string> = {
  400: 'The request could not be processed.',
  401: 'Your session has expired. Please sign in again.',
  403: 'You do not have permission to do that.',
  404: 'We could not find what you were looking for.',
  409: 'That conflicts with existing data. Please try another option.',
  413: 'The file is too large.',
  422: 'Some of the information provided is invalid.',
  429: 'Too many attempts. Please wait a moment and try again.',
  500: 'Something went wrong on our side. Please try again.',
  503: 'The service is temporarily unavailable. Please try again soon.',
};

/** Turn any FastAPI error payload into a friendly ApiError. */
export function normalizeError(status: number, payload: unknown): ApiError {
  const fallback = STATUS_FALLBACK[status] ?? `Request failed (${status}).`;
  if (payload && typeof payload === 'object' && 'detail' in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === 'string' && detail.trim()) {
      return new ApiError(status, detail, detail);
    }
    if (Array.isArray(detail)) {
      const fieldErrors: Record<string, string> = {};
      const messages: string[] = [];
      for (const item of detail as FastApiValidationItem[]) {
        const msg = (item?.msg ?? '').replace(/^Value error, /, '');
        const loc = (item?.loc ?? []).filter((p) => p !== 'body' && p !== 'query');
        const field = loc.length ? String(loc[loc.length - 1]) : '';
        if (field && msg && !fieldErrors[field]) fieldErrors[field] = msg;
        if (msg) messages.push(field ? `${field.replace(/_/g, ' ')}: ${msg}` : msg);
      }
      return new ApiError(status, messages[0] ?? fallback, detail, fieldErrors);
    }
  }
  return new ApiError(status, fallback, payload);
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

type Query = Record<string, string | number | boolean | undefined | null>;

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';
  body?: unknown;
  query?: Query;
  /** Attach the bearer token (default true). */
  auth?: boolean;
  signal?: AbortSignal;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percent: number;
}

export interface ApiClientConfig {
  baseUrl: string;
  tokens: TokenStore;
  fetchImpl?: typeof fetch;
  /** Factory for XMLHttpRequest (overridable in tests). */
  xhrFactory?: () => XMLHttpRequest;
}

export function buildQuery(query?: Query): string {
  if (!query) return '';
  const params = new URLSearchParams();
  for (const [k, v] of Object.entries(query)) {
    if (v === undefined || v === null || v === '') continue;
    params.append(k, String(v));
  }
  const s = params.toString();
  return s ? `?${s}` : '';
}

export class ApiClient {
  readonly baseUrl: string;
  readonly origin: string;
  readonly tokens: TokenStore;
  private readonly fetchImpl: typeof fetch;
  private readonly xhrFactory: () => XMLHttpRequest;
  private refreshing: Promise<boolean> | null = null;
  private logoutListeners = new Set<() => void>();
  private tokenListeners = new Set<(user: T.User) => void>();

  constructor(cfg: ApiClientConfig) {
    this.baseUrl = cfg.baseUrl.replace(/\/+$/, '');
    this.origin = safeOrigin(this.baseUrl);
    this.tokens = cfg.tokens;
    this.fetchImpl = cfg.fetchImpl ?? ((...args) => fetch(...args));
    this.xhrFactory = cfg.xhrFactory ?? (() => new XMLHttpRequest());
  }

  /** Subscribe to forced logouts (refresh failed). Returns an unsubscribe fn. */
  onLogout(fn: () => void): () => void {
    this.logoutListeners.add(fn);
    return () => this.logoutListeners.delete(fn);
  }

  /** Subscribe to user updates delivered with fresh token pairs. */
  onUserRefreshed(fn: (user: T.User) => void): () => void {
    this.tokenListeners.add(fn);
    return () => this.tokenListeners.delete(fn);
  }

  /** Resolve a server-provided path (e.g. `/api/v1/scans/1/image`) to an absolute URL. */
  resolveUrl(pathOrUrl: string): string {
    if (/^https?:\/\//i.test(pathOrUrl)) return pathOrUrl;
    if (pathOrUrl.startsWith('/api/')) return `${this.origin}${pathOrUrl}`;
    const p = pathOrUrl.startsWith('/') ? pathOrUrl : `/${pathOrUrl}`;
    return `${this.baseUrl}/api/v1${p}`;
  }

  /** Bearer tokens are only ever sent to the configured API origin. */
  private canAttachToken(url: string): boolean {
    return safeOrigin(url) === this.origin;
  }

  private authHeader(url: string): Record<string, string> {
    const t = this.tokens.get();
    return t && this.canAttachToken(url) ? { Authorization: `Bearer ${t.access}` } : {};
  }

  async setSession(pair: T.TokenPair): Promise<void> {
    await this.tokens.set({ access: pair.access_token, refresh: pair.refresh_token });
  }

  async clearSession(): Promise<void> {
    await this.tokens.clear();
  }

  private async forceLogout() {
    await this.tokens.clear();
    this.logoutListeners.forEach((fn) => fn());
  }

  /**
   * Exchange the refresh token for a new pair. Concurrent callers share one
   * in-flight refresh. Resolves true on success.
   */
  refresh(): Promise<boolean> {
    if (this.refreshing) return this.refreshing;
    const current = this.tokens.get();
    if (!current?.refresh) return Promise.resolve(false);
    this.refreshing = (async () => {
      try {
        const res = await this.fetchImpl(`${this.baseUrl}/api/v1/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify({ refresh_token: current.refresh }),
        });
        if (!res.ok) return false;
        const pair = (await res.json()) as T.TokenPair;
        await this.setSession(pair);
        if (pair.user) this.tokenListeners.forEach((fn) => fn(pair.user));
        return true;
      } catch {
        return false;
      } finally {
        this.refreshing = null;
      }
    })();
    return this.refreshing;
  }

  /** Core JSON request with refresh-on-401 (once) and error normalisation. */
  async request<R>(path: string, opts: RequestOptions = {}): Promise<R> {
    const { method = 'GET', body, query, auth = true, signal } = opts;
    const url = `${this.baseUrl}/api/v1${path}${buildQuery(query)}`;

    const send = () =>
      this.fetchImpl(url, {
        method,
        signal,
        headers: {
          Accept: 'application/json',
          ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
          ...(auth ? this.authHeader(url) : {}),
        },
        body: body !== undefined ? JSON.stringify(body) : undefined,
      });

    let res: Response;
    try {
      res = await send();
      if (res.status === 401 && auth && this.tokens.get()) {
        const ok = await this.refresh();
        if (!ok) {
          await this.forceLogout();
          throw normalizeError(401, await safeJson(res));
        }
        res = await send();
        if (res.status === 401) {
          await this.forceLogout();
          throw normalizeError(401, await safeJson(res));
        }
      }
    } catch (err) {
      if (err instanceof ApiError) throw err;
      if ((err as Error)?.name === 'AbortError') throw err;
      throw new ApiError(0, 'Network error — please check your connection and try again.');
    }

    if (!res.ok) throw normalizeError(res.status, await safeJson(res));
    if (res.status === 204) return undefined as R;
    const text = await res.text();
    return (text ? JSON.parse(text) : undefined) as R;
  }

  /** Fetch a binary resource (e.g. scan image) with auth, refreshing once on 401. */
  async fetchBlob(pathOrUrl: string, signal?: AbortSignal): Promise<Blob> {
    const url = this.resolveUrl(pathOrUrl);
    const send = () => this.fetchImpl(url, { headers: this.authHeader(url), signal });
    let res: Response;
    try {
      res = await send();
      if (res.status === 401 && this.tokens.get() && this.canAttachToken(url)) {
        if (await this.refresh()) res = await send();
      }
    } catch (err) {
      if ((err as Error)?.name === 'AbortError') throw err;
      throw new ApiError(0, 'Network error while loading image.');
    }
    if (!res.ok) throw normalizeError(res.status, await safeJson(res));
    return res.blob();
  }

  /** Multipart upload via XHR so we can report progress. Refreshes once on 401. */
  async upload<R>(path: string, form: () => FormData, onProgress?: (p: UploadProgress) => void): Promise<R> {
    const url = `${this.baseUrl}/api/v1${path}`;
    const attempt = () =>
      new Promise<{ status: number; body: string }>((resolve, reject) => {
        const xhr = this.xhrFactory();
        xhr.open('POST', url);
        xhr.setRequestHeader('Accept', 'application/json');
        const h = this.authHeader(url);
        if (h.Authorization) xhr.setRequestHeader('Authorization', h.Authorization);
        xhr.upload.onprogress = (e: ProgressEvent) => {
          if (!onProgress || !e.lengthComputable) return;
          onProgress({ loaded: e.loaded, total: e.total, percent: Math.round((e.loaded / e.total) * 100) });
        };
        xhr.onload = () => resolve({ status: xhr.status, body: xhr.responseText });
        xhr.onerror = () => reject(new ApiError(0, 'Network error during upload. Please try again.'));
        xhr.ontimeout = () => reject(new ApiError(0, 'The upload timed out. Please try again.'));
        xhr.send(form());
      });

    let r = await attempt();
    if (r.status === 401 && this.tokens.get()) {
      if (!(await this.refresh())) {
        await this.forceLogout();
        throw normalizeError(401, parseMaybe(r.body));
      }
      r = await attempt();
    }
    if (r.status < 200 || r.status >= 300) throw normalizeError(r.status, parseMaybe(r.body));
    return parseMaybe(r.body) as R;
  }

  // -------------------------------------------------------------------------
  // Typed endpoints (docs/API_CONTRACT.md)
  // -------------------------------------------------------------------------

  /** `GET /api/v1/health` (contract: "all routes under /api/v1"). */
  health = () => this.request<T.Health>('/health', { auth: false });

  auth = {
    register: (body: T.RegisterBody) => this.request<T.TokenPair>('/auth/register', { method: 'POST', body, auth: false }),
    login: (body: T.LoginBody) => this.request<T.TokenPair>('/auth/login', { method: 'POST', body, auth: false }),
  };

  users = {
    me: () => this.request<T.User>('/users/me'),
    update: (body: T.UpdateMeBody) => this.request<T.User>('/users/me', { method: 'PATCH', body }),
    changePassword: (body: T.ChangePasswordBody) => this.request<void>('/users/me/password', { method: 'POST', body }),
    remove: () => this.request<void>('/users/me', { method: 'DELETE' }),
  };

  lesions = {
    list: () => this.request<T.Paginated<T.Lesion>>('/lesions/'),
    create: (body: T.CreateLesionBody) => this.request<T.Lesion>('/lesions/', { method: 'POST', body }),
    get: (id: number) => this.request<T.LesionDetail>(`/lesions/${id}`),
    update: (id: number, body: T.UpdateLesionBody) => this.request<T.Lesion>(`/lesions/${id}`, { method: 'PATCH', body }),
    remove: (id: number) => this.request<void>(`/lesions/${id}`, { method: 'DELETE' }),
  };

  scans = {
    create: (input: T.CreateScanInput, onProgress?: (p: UploadProgress) => void) =>
      this.upload<T.Scan>(
        '/scans/',
        () => {
          const fd = new FormData();
          fd.append('image', input.image, input.filename ?? defaultFilename(input.image.type));
          if (input.lesion_id !== undefined) fd.append('lesion_id', String(input.lesion_id));
          if (input.symptoms) fd.append('symptoms', JSON.stringify(input.symptoms));
          return fd;
        },
        onProgress,
      ),
    list: (q: { lesion_id?: number; limit?: number; offset?: number } = {}) =>
      this.request<T.Paginated<T.ScanSummary>>('/scans/', { query: q }),
    get: (id: number) => this.request<T.Scan>(`/scans/${id}`),
    remove: (id: number) => this.request<void>(`/scans/${id}`, { method: 'DELETE' }),
    imagePath: (id: number, thumb = false) => `/api/v1/scans/${id}/image${thumb ? '?variant=thumb' : ''}`,
  };

  tracking = {
    compare: (a: number, b: number) => this.request<T.Comparison>('/tracking/compare', { query: { a, b } }),
    dashboard: () => this.request<T.Dashboard>('/tracking/dashboard'),
    symptoms: () => this.request<T.ItemsOnly<T.SymptomLog>>('/tracking/symptoms'),
    logSymptoms: (body: T.CreateSymptomLogBody) =>
      this.request<T.SymptomLog>('/tracking/symptoms', { method: 'POST', body }),
  };

  dermatologists = {
    search: (q: T.DermatologistQuery = {}) =>
      this.request<T.Paginated<T.Dermatologist>>('/dermatologists', { query: { ...q } }),
    get: (id: number) => this.request<T.Dermatologist>(`/dermatologists/${id}`),
    availability: (id: number, date: T.YMD) =>
      this.request<T.Availability>(`/dermatologists/${id}/availability`, { query: { date } }),
  };

  appointments = {
    list: (status: 'upcoming' | 'past' | 'all' = 'upcoming') =>
      this.request<T.Paginated<T.Appointment>>('/appointments', { query: { status } }),
    create: (body: T.CreateAppointmentBody) => this.request<T.Appointment>('/appointments', { method: 'POST', body }),
    update: (id: number, body: T.UpdateAppointmentBody) =>
      this.request<T.Appointment>(`/appointments/${id}`, { method: 'PATCH', body }),
    cancel: (id: number) => this.request<T.Appointment>(`/appointments/${id}/cancel`, { method: 'POST' }),
  };

  reminders = {
    list: () => this.request<T.ItemsOnly<T.Reminder>>('/reminders/'),
    create: (body: T.CreateReminderBody) => this.request<T.Reminder>('/reminders/', { method: 'POST', body }),
    update: (id: number, body: T.UpdateReminderBody) =>
      this.request<T.Reminder>(`/reminders/${id}`, { method: 'PATCH', body }),
    remove: (id: number) => this.request<void>(`/reminders/${id}`, { method: 'DELETE' }),
  };

  community = {
    posts: (q: { topic?: T.PostTopic; limit?: number; offset?: number } = {}) =>
      this.request<T.Paginated<T.Post>>('/community/posts', { query: q }),
    createPost: (body: T.CreatePostBody) => this.request<T.Post>('/community/posts', { method: 'POST', body }),
    post: (id: number) => this.request<T.PostDetail>(`/community/posts/${id}`),
    deletePost: (id: number) => this.request<void>(`/community/posts/${id}`, { method: 'DELETE' }),
    comment: (postId: number, body: T.CreateCommentBody) =>
      this.request<T.Comment>(`/community/posts/${postId}/comments`, { method: 'POST', body }),
    deleteComment: (id: number) => this.request<void>(`/community/comments/${id}`, { method: 'DELETE' }),
    react: (postId: number, kind: T.ReactionKind) =>
      this.request<T.ReactionResult>(`/community/posts/${postId}/reactions`, { method: 'POST', body: { kind } }),
    reportPost: (id: number, reason: string) =>
      this.request<T.ReportResult>(`/community/posts/${id}/report`, { method: 'POST', body: { reason } }),
    reportComment: (id: number, reason: string) =>
      this.request<T.ReportResult>(`/community/comments/${id}/report`, { method: 'POST', body: { reason } }),
    reports: (status = 'open') =>
      this.request<T.ItemsOnly<T.ModerationReport> | T.ModerationReport[]>('/community/moderation/reports', {
        query: { status },
      }).then((r) => (Array.isArray(r) ? r : (r?.items ?? []))),
    resolveReport: (id: number, action: T.ModerationAction) =>
      this.request<unknown>(`/community/moderation/reports/${id}/resolve`, { method: 'POST', body: { action } }),
  };

  assistant = {
    chat: (body: T.ChatRequest) => this.request<T.ChatResponse>('/assistant/chat', { method: 'POST', body }),
    topics: () => this.request<T.ItemsOnly<T.AssistantTopic>>('/assistant/topics'),
  };
}

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

function safeOrigin(url: string): string {
  try {
    return new URL(url).origin;
  } catch {
    return '';
  }
}

async function safeJson(res: Response): Promise<unknown> {
  try {
    const text = await res.text();
    return text ? JSON.parse(text) : null;
  } catch {
    return null;
  }
}

function parseMaybe(text: string): unknown {
  try {
    return text ? JSON.parse(text) : null;
  } catch {
    return null;
  }
}

function defaultFilename(mime: string): string {
  const ext = mime === 'image/png' ? 'png' : mime === 'image/webp' ? 'webp' : 'jpg';
  return `scan.${ext}`;
}

/** App-wide singleton. */
export const api = new ApiClient({ baseUrl: API_URL, tokens: new TokenStore(kvStore()) });
