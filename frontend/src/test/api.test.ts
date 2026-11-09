import { describe, expect, it, vi } from 'vitest';
import { ApiClient, ApiError, buildQuery, normalizeError } from '@/lib/api';
import { TokenStore, memoryStore } from '@/lib/storage';
import { jsonResponse, tokenPair, user } from './fixtures';

const BASE = 'http://api.test';

async function makeClient(fetchImpl: typeof fetch, tokens: { access: string; refresh: string } | null = { access: 'old', refresh: 'r1' }) {
  const store = new TokenStore(memoryStore());
  if (tokens) await store.set(tokens);
  return new ApiClient({ baseUrl: BASE, tokens: store, fetchImpl });
}

const authOf = (init?: RequestInit) => (init?.headers as Record<string, string> | undefined)?.Authorization;

describe('ApiClient', () => {
  it('attaches the bearer token and parses JSON', async () => {
    const f = vi.fn(async () => jsonResponse(200, user));
    const c = await makeClient(f as unknown as typeof fetch);
    const me = await c.users.me();
    expect(me.email).toBe(user.email);
    const [url, init] = f.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${BASE}/api/v1/users/me`);
    expect(authOf(init)).toBe('Bearer old');
  });

  it('refreshes once on 401 and retries with the new token', async () => {
    const f = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/auth/refresh')) return jsonResponse(200, tokenPair('new', 'r2'));
      return authOf(init) === 'Bearer new' ? jsonResponse(200, user) : jsonResponse(401, { detail: 'expired' });
    });
    const c = await makeClient(f as unknown as typeof fetch);
    const me = await c.users.me();
    expect(me.id).toBe(1);
    expect(f).toHaveBeenCalledTimes(3);
    expect(c.tokens.get()).toEqual({ access: 'new', refresh: 'r2' });
    const refreshBody = JSON.parse((f.mock.calls[1]![1] as RequestInit).body as string);
    expect(refreshBody).toEqual({ refresh_token: 'r1' });
  });

  it('logs out when refresh fails', async () => {
    const f = vi.fn(async (url: string) => (url.endsWith('/auth/refresh') ? jsonResponse(401, { detail: 'bad refresh' }) : jsonResponse(401, { detail: 'expired' })));
    const c = await makeClient(f as unknown as typeof fetch);
    const onLogout = vi.fn();
    c.onLogout(onLogout);
    await expect(c.users.me()).rejects.toMatchObject({ status: 401 });
    expect(onLogout).toHaveBeenCalledOnce();
    expect(c.tokens.get()).toBeNull();
  });

  it('does not loop: a second 401 after refresh logs out', async () => {
    const f = vi.fn(async (url: string) => (url.endsWith('/auth/refresh') ? jsonResponse(200, tokenPair('new', 'r2')) : jsonResponse(401, { detail: 'nope' })));
    const c = await makeClient(f as unknown as typeof fetch);
    await expect(c.users.me()).rejects.toBeInstanceOf(ApiError);
    expect(f.mock.calls.filter((x) => String(x[0]).endsWith('/auth/refresh'))).toHaveLength(1);
    expect(c.tokens.get()).toBeNull();
  });

  it('shares a single refresh between concurrent 401s', async () => {
    let refreshes = 0;
    const f = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/auth/refresh')) {
        refreshes++;
        await new Promise((r) => setTimeout(r, 5));
        return jsonResponse(200, tokenPair('new', 'r2'));
      }
      return authOf(init) === 'Bearer new' ? jsonResponse(200, { items: [], total: 0 }) : jsonResponse(401, { detail: 'expired' });
    });
    const c = await makeClient(f as unknown as typeof fetch);
    await Promise.all([c.lesions.list(), c.reminders.list(), c.appointments.list()]);
    expect(refreshes).toBe(1);
  });

  it('does not attempt refresh for unauthenticated login failures', async () => {
    const f = vi.fn(async () => jsonResponse(401, { detail: 'Incorrect email or password' }));
    const c = await makeClient(f as unknown as typeof fetch, null);
    await expect(c.auth.login({ email: 'a@b.co', password: 'x' })).rejects.toMatchObject({ status: 401, message: 'Incorrect email or password' });
    expect(f).toHaveBeenCalledTimes(1);
  });

  it('returns undefined for 204', async () => {
    const f = vi.fn(async () => new Response(null, { status: 204 }));
    const c = await makeClient(f as unknown as typeof fetch);
    await expect(c.lesions.remove(3)).resolves.toBeUndefined();
    expect((f.mock.calls[0] as unknown as [string, RequestInit])[1].method).toBe('DELETE');
  });

  it('normalises network failures to status 0', async () => {
    const f = vi.fn(async () => {
      throw new TypeError('Failed to fetch');
    });
    const c = await makeClient(f as unknown as typeof fetch);
    await expect(c.users.me()).rejects.toMatchObject({ status: 0, isNetwork: true });
  });

  it('builds query strings skipping empty values', () => {
    expect(buildQuery({ q: 'ana', city: '', specialty: undefined, limit: 20 })).toBe('?q=ana&limit=20');
    expect(buildQuery({})).toBe('');
  });

  it('never sends the token to a foreign origin', async () => {
    const f = vi.fn(async () => new Response(new Blob(['x'])));
    const c = await makeClient(f as unknown as typeof fetch);
    await c.fetchBlob('https://evil.example/img.png');
    expect(authOf((f.mock.calls[0] as unknown as [string, RequestInit])[1])).toBeUndefined();
    await c.fetchBlob('/api/v1/scans/1/image');
    const [url, init] = f.mock.calls[1] as unknown as [string, RequestInit];
    expect(url).toBe(`${BASE}/api/v1/scans/1/image`);
    expect(authOf(init)).toBe('Bearer old');
  });

  it('uses contract paths and bodies for key endpoints', async () => {
    const f = vi.fn(async () => jsonResponse(200, {}));
    const c = await makeClient(f as unknown as typeof fetch);
    await c.tracking.compare(1, 2);
    await c.community.react(9, 'hug');
    await c.appointments.cancel(4);
    const calls = f.mock.calls as unknown as [string, RequestInit][];
    const urls = calls.map((x) => String(x[0]));
    expect(urls).toEqual([`${BASE}/api/v1/tracking/compare?a=1&b=2`, `${BASE}/api/v1/community/posts/9/reactions`, `${BASE}/api/v1/appointments/4/cancel`]);
    expect(JSON.parse(calls[1]![1].body as string)).toEqual({ kind: 'hug' });
  });
});

describe('normalizeError', () => {
  it('uses string detail', () => {
    expect(normalizeError(409, { detail: 'Slot taken' }).message).toBe('Slot taken');
  });
  it('maps FastAPI 422 arrays to field errors', () => {
    const e = normalizeError(422, { detail: [{ loc: ['body', 'password'], msg: 'Value error, too short', type: 'value_error' }] });
    expect(e.fieldErrors).toEqual({ password: 'too short' });
    expect(e.message).toContain('password');
  });
  it('falls back to a friendly message', () => {
    expect(normalizeError(429, null).message).toMatch(/too many/i);
  });
});

describe('upload', () => {
  it('sends multipart via XHR with progress and parses result', async () => {
    const progress = vi.fn();
    const sent: { headers: Record<string, string>; body?: FormData } = { headers: {} };
    class FakeXHR {
      status = 0;
      responseText = '';
      upload: { onprogress: ((e: ProgressEvent) => void) | null } = { onprogress: null };
      onload: (() => void) | null = null;
      onerror: (() => void) | null = null;
      ontimeout: (() => void) | null = null;
      open() {}
      setRequestHeader(k: string, v: string) {
        sent.headers[k] = v;
      }
      send(body: FormData) {
        sent.body = body;
        this.upload.onprogress?.({ lengthComputable: true, loaded: 50, total: 100 } as ProgressEvent);
        this.status = 201;
        this.responseText = JSON.stringify({ id: 99 });
        this.onload?.();
      }
    }
    const store = new TokenStore(memoryStore());
    await store.set({ access: 'tok', refresh: 'r' });
    const c = new ApiClient({ baseUrl: BASE, tokens: store, fetchImpl: vi.fn() as unknown as typeof fetch, xhrFactory: () => new FakeXHR() as unknown as XMLHttpRequest });
    const res = await c.scans.create({ image: new Blob(['img'], { type: 'image/jpeg' }), lesion_id: 7, symptoms: { itching: true, bleeding: false, pain: false, changed_size: false, changed_color: false, changed_shape: false, new_spot: false } }, progress);
    expect(res).toEqual({ id: 99 });
    expect(progress).toHaveBeenCalledWith({ loaded: 50, total: 100, percent: 50 });
    expect(sent.headers.Authorization).toBe('Bearer tok');
    expect(sent.body?.get('lesion_id')).toBe('7');
    expect(JSON.parse(String(sent.body?.get('symptoms'))).itching).toBe(true);
    expect(sent.body?.get('image')).toBeInstanceOf(Blob);
  });
});
