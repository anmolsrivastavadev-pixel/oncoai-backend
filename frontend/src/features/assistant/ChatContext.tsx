import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from 'react';
import { api, type ApiError } from '@/lib/api';
import type { ChatResponse } from '@/types/api';

export interface UiMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatResponse['sources'];
  safety?: ChatResponse['safety'];
  error?: boolean;
}

interface ChatCtx {
  messages: UiMessage[];
  suggestions: string[];
  sending: boolean;
  send: (text: string, scanId?: number) => Promise<void>;
  clear: () => void;
}

const Ctx = createContext<ChatCtx | null>(null);

export const DEFAULT_SUGGESTIONS = ['What is the ABCDE rule?', 'How do I do a skin self-exam?', 'What happens at a dermatologist visit?', 'How can I protect my skin from UV?'];

/** Chat history lives in memory only (per app session) — never persisted to storage. */
export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>(DEFAULT_SUGGESTIONS);
  const [sending, setSending] = useState(false);
  const seq = useRef(0);
  const ref = useRef(messages);
  ref.current = messages;

  const send = useCallback(async (text: string, scanId?: number) => {
    const content = text.trim();
    if (!content) return;
    const userMsg: UiMessage = { id: ++seq.current, role: 'user', content };
    const history = [...ref.current.filter((m) => !m.error), userMsg];
    setMessages((m) => [...m, userMsg]);
    setSending(true);
    try {
      const res = await api.assistant.chat({
        messages: history.slice(-20).map((m) => ({ role: m.role, content: m.content })),
        context: scanId ? { scan_id: scanId } : undefined,
      });
      setMessages((m) => [...m, { id: ++seq.current, role: 'assistant', content: res.reply, sources: res.sources, safety: res.safety }]);
      if (res.suggestions?.length) setSuggestions(res.suggestions);
    } catch (e) {
      setMessages((m) => [...m, { id: ++seq.current, role: 'assistant', content: (e as ApiError).message || 'Sorry, I could not reply right now.', error: true }]);
    } finally {
      setSending(false);
    }
  }, []);

  const clear = useCallback(() => {
    setMessages([]);
    setSuggestions(DEFAULT_SUGGESTIONS);
  }, []);

  const value = useMemo(() => ({ messages, suggestions, sending, send, clear }), [messages, suggestions, sending, send, clear]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useChat() {
  const c = useContext(Ctx);
  if (!c) throw new Error('useChat must be used inside <ChatProvider>');
  return c;
}
