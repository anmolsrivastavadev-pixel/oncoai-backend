import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { api as defaultApi, type ApiClient } from '@/lib/api';
import type { LoginBody, RegisterBody, User } from '@/types/api';

export type AuthStatus = 'loading' | 'authenticated' | 'anonymous';

interface AuthCtx {
  status: AuthStatus;
  user: User | null;
  login: (body: LoginBody) => Promise<User>;
  register: (body: RegisterBody) => Promise<User>;
  logout: () => Promise<void>;
  setUser: (u: User) => void;
  isModerator: boolean;
}

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children, client = defaultApi }: { children: ReactNode; client?: ApiClient }) {
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [user, setUserState] = useState<User | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      const tokens = await client.tokens.load();
      if (!tokens) {
        if (alive) setStatus('anonymous');
        return;
      }
      try {
        const me = await client.users.me();
        if (!alive) return;
        setUserState(me);
        setStatus('authenticated');
      } catch {
        if (!alive) return;
        // Offline with tokens: keep anonymous to be safe; tokens remain for retry on reload.
        setStatus('anonymous');
      }
    })();
    const offLogout = client.onLogout(() => {
      setUserState(null);
      setStatus('anonymous');
    });
    const offUser = client.onUserRefreshed((u) => setUserState(u));
    return () => {
      alive = false;
      offLogout();
      offUser();
    };
  }, [client]);

  const login = useCallback(
    async (body: LoginBody) => {
      const pair = await client.auth.login(body);
      await client.setSession(pair);
      setUserState(pair.user);
      setStatus('authenticated');
      return pair.user;
    },
    [client],
  );

  const register = useCallback(
    async (body: RegisterBody) => {
      const pair = await client.auth.register(body);
      await client.setSession(pair);
      setUserState(pair.user);
      setStatus('authenticated');
      return pair.user;
    },
    [client],
  );

  const logout = useCallback(async () => {
    await client.clearSession();
    setUserState(null);
    setStatus('anonymous');
  }, [client]);

  const value = useMemo<AuthCtx>(
    () => ({
      status,
      user,
      login,
      register,
      logout,
      setUser: setUserState,
      isModerator: user?.role === 'moderator' || user?.role === 'admin',
    }),
    [status, user, login, register, logout],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthCtx {
  const c = useContext(Ctx);
  if (!c) throw new Error('useAuth must be used inside <AuthProvider>');
  return c;
}
