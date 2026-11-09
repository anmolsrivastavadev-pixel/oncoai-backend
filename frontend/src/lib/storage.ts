import { Preferences } from '@capacitor/preferences';
import { isNative } from './platform';

/**
 * Small async key/value store: Capacitor Preferences on device
 * (Android SharedPreferences), localStorage on the web.
 */
export interface KeyValueStore {
  get(key: string): Promise<string | null>;
  set(key: string, value: string): Promise<void>;
  remove(key: string): Promise<void>;
}

const webStore: KeyValueStore = {
  async get(key) {
    try {
      return window.localStorage.getItem(key);
    } catch {
      return null;
    }
  },
  async set(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch {
      /* storage unavailable (private mode) — keep in memory only */
    }
  },
  async remove(key) {
    try {
      window.localStorage.removeItem(key);
    } catch {
      /* ignore */
    }
  },
};

const nativeStore: KeyValueStore = {
  async get(key) {
    const { value } = await Preferences.get({ key });
    return value;
  },
  async set(key, value) {
    await Preferences.set({ key, value });
  },
  async remove(key) {
    await Preferences.remove({ key });
  },
};

export const kvStore = (): KeyValueStore => (isNative() ? nativeStore : webStore);

export interface Tokens {
  access: string;
  refresh: string;
}

const ACCESS_KEY = 'oncoai.access_token';
const REFRESH_KEY = 'oncoai.refresh_token';

/** Token store with a synchronous in-memory cache for request headers. */
export class TokenStore {
  private cache: Tokens | null = null;
  constructor(private readonly store: KeyValueStore) {}

  async load(): Promise<Tokens | null> {
    const [access, refresh] = await Promise.all([this.store.get(ACCESS_KEY), this.store.get(REFRESH_KEY)]);
    this.cache = access && refresh ? { access, refresh } : null;
    return this.cache;
  }

  get(): Tokens | null {
    return this.cache;
  }

  async set(tokens: Tokens): Promise<void> {
    this.cache = tokens;
    await Promise.all([this.store.set(ACCESS_KEY, tokens.access), this.store.set(REFRESH_KEY, tokens.refresh)]);
  }

  async clear(): Promise<void> {
    this.cache = null;
    await Promise.all([this.store.remove(ACCESS_KEY), this.store.remove(REFRESH_KEY)]);
  }
}

export const memoryStore = (): KeyValueStore => {
  const m = new Map<string, string>();
  return {
    async get(k) {
      return m.get(k) ?? null;
    },
    async set(k, v) {
      m.set(k, v);
    },
    async remove(k) {
      m.delete(k);
    },
  };
};
