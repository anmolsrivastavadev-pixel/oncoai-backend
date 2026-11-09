import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useSearchParams } from 'react-router-dom';
import { BookOpen, Bot, ExternalLink, LifeBuoy, RotateCcw, ScanLine, Send, X } from 'lucide-react';
import { LogoMark } from '@/components/brand/Logo';
import { Disclaimer } from '@/components/Disclaimer';
import { Button, Modal, Skeleton } from '@/components/ui';
import { useAsync } from '@/hooks/useAsync';
import { api } from '@/lib/api';
import { MarkdownLite, safeHref } from '@/lib/markdown';
import { useChat, type UiMessage } from './ChatContext';

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2" role="status" aria-label="Assistant is typing">
      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-accent-cyan/30 bg-navy-900">
        <LogoMark size={18} title="" />
      </span>
      <div className="glass flex gap-1 rounded-bl-md px-4 py-3">
        {[0, 1, 2].map((i) => (
          <motion.span key={i} className="h-2 w-2 rounded-full bg-accent-cyan" animate={{ opacity: [0.3, 1, 0.3], y: [0, -3, 0] }} transition={{ duration: 1, repeat: Infinity, delay: i * 0.15 }} />
        ))}
      </div>
    </div>
  );
}

function Bubble({ m }: { m: UiMessage }) {
  const mine = m.role === 'user';
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className={clsx('flex items-end gap-2', mine && 'flex-row-reverse')}>
      {!mine && (
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-accent-cyan/30 bg-navy-900" aria-hidden>
          <LogoMark size={18} title="" />
        </span>
      )}
      <div
        className={clsx(
          'max-w-[85%] px-4 py-3 text-[15px] leading-relaxed sm:max-w-[75%]',
          mine ? 'rounded-2xl rounded-br-md bg-gradient-to-br from-accent-cyan to-accent-teal font-medium text-navy-950' : 'glass rounded-2xl rounded-bl-md text-ink',
          m.error && 'border-rose-300/30 bg-rose-400/10 text-rose-100',
        )}
      >
        <span className="sr-only">{mine ? 'You said:' : 'Assistant said:'}</span>
        {mine ? <p className="whitespace-pre-line">{m.content}</p> : <MarkdownLite text={m.content} />}
        {m.safety?.redirected && (
          <p className="mt-2 flex items-start gap-1.5 rounded-lg bg-amber-300/10 px-2.5 py-1.5 text-xs text-amber-100">
            <LifeBuoy className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden /> If this is urgent, please contact a healthcare professional or local emergency services.
          </p>
        )}
        {!!m.sources?.length && (
          <div className="mt-3 border-t border-white/10 pt-2">
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-ink-faint">Sources</p>
            <ul className="space-y-1">
              {m.sources.map((s) => {
                const href = safeHref(s.url);
                return (
                  <li key={s.url + s.title}>
                    {href ? (
                      <a href={href} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-sm text-accent-cyan hover:underline">
                        {s.title} <ExternalLink className="h-3 w-3" aria-hidden />
                      </a>
                    ) : (
                      <span className="text-sm text-ink-muted">{s.title}</span>
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default function AssistantPage() {
  const { messages, suggestions, sending, send, clear } = useChat();
  const [params, setParams] = useSearchParams();
  const scanId = Number(params.get('scan_id')) || undefined;
  const [text, setText] = useState('');
  const [topicsOpen, setTopicsOpen] = useState(false);
  const topics = useAsync(() => api.assistant.topics(), []);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'end' });
  }, [messages.length, sending]);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    if (!text.trim() || sending) return;
    void send(text, scanId);
    setText('');
  };

  const ask = (q: string) => {
    if (sending) return;
    void send(q, scanId);
  };

  return (
    <div className="mx-auto flex max-w-3xl flex-col">
      <header className="mb-4 flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="grid h-12 w-12 place-items-center rounded-2xl border border-accent-cyan/30 bg-accent-cyan/10 shadow-glow-sm">
            <Bot className="h-6 w-6 text-accent-cyan" aria-hidden />
          </span>
          <div>
            <h1 className="text-2xl font-bold">Skin health assistant</h1>
            <p className="text-sm text-ink-muted">Educational answers. It can't diagnose or recommend treatment.</p>
          </div>
        </div>
        <div className="flex shrink-0 gap-1">
          <Button size="icon" variant="glass" onClick={() => setTopicsOpen(true)} aria-label="Browse topic library">
            <BookOpen className="h-5 w-5" />
          </Button>
          {messages.length > 0 && (
            <Button size="icon" variant="ghost" onClick={clear} aria-label="Clear conversation">
              <RotateCcw className="h-5 w-5" />
            </Button>
          )}
        </div>
      </header>

      <div className="sticky z-20 -mx-1 mb-3 px-1" style={{ top: 'calc(var(--safe-top) + 60px)' }}>
        <Disclaimer variant="inline" className="bg-navy-900/90 backdrop-blur-xl" />
      </div>

      {scanId && (
        <div className="mb-3 flex items-center justify-between gap-2 rounded-xl border border-accent-cyan/30 bg-accent-cyan/10 px-3 py-2 text-sm text-cyan-50">
          <span className="flex items-center gap-2">
            <ScanLine className="h-4 w-4" aria-hidden /> Asking about scan #{scanId}
          </span>
          <button
            type="button"
            className="grid h-9 w-9 place-items-center rounded-lg hover:bg-white/10"
            aria-label="Stop using this scan as context"
            onClick={() => {
              const n = new URLSearchParams(params);
              n.delete('scan_id');
              setParams(n, { replace: true });
            }}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <div className="flex-1 space-y-4" aria-live="polite">
        {messages.length === 0 && (
          <div className="glass p-5">
            <p className="font-display text-lg font-semibold text-white">Hi! How can I help you learn today?</p>
            <p className="mt-1 text-sm text-ink-muted">
              Ask about skin self-checks, sun protection, what your scan features mean or what to expect at a dermatologist visit. For anything about your own health, please talk to a healthcare professional.
            </p>
            {topics.loading ? (
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                <Skeleton className="h-16" />
                <Skeleton className="h-16" />
              </div>
            ) : (
              !!topics.data?.items.length && (
                <div className="mt-4 grid gap-2 sm:grid-cols-2">
                  {topics.data.items.slice(0, 4).map((t) => (
                    <button key={t.id} type="button" onClick={() => ask(`Tell me about: ${t.title}`)} className="rounded-xl border border-white/10 bg-white/[0.03] p-3 text-left transition hover:border-accent-cyan/30">
                      <p className="text-sm font-semibold text-white">{t.title}</p>
                      <p className="mt-0.5 line-clamp-2 text-xs text-ink-muted">{t.summary}</p>
                    </button>
                  ))}
                </div>
              )
            )}
          </div>
        )}
        {messages.map((m) => (
          <Bubble key={m.id} m={m} />
        ))}
        <AnimatePresence>{sending && <TypingIndicator />}</AnimatePresence>
        <div ref={endRef} />
      </div>

      <div className="sticky z-20 mt-4 space-y-2 bg-gradient-to-t from-navy-950 via-navy-950/95 to-transparent pt-4" style={{ bottom: 'calc(var(--bottom-nav-h) + var(--safe-bottom))' }}>
        <div className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1 no-scrollbar" aria-label="Suggested questions">
          {(scanId && messages.length === 0 ? ['What do the features in my scan mean?', 'Should I show this scan to a dermatologist?', ...suggestions] : suggestions).slice(0, 6).map((s) => (
            <button key={s} type="button" onClick={() => ask(s)} disabled={sending} className="chip shrink-0 disabled:opacity-50">
              {s}
            </button>
          ))}
        </div>
        <form onSubmit={submit} className="glass flex items-end gap-2 p-2">
          <label htmlFor="chat-input" className="sr-only">
            Message the assistant
          </label>
          <textarea
            id="chat-input"
            rows={1}
            value={text}
            maxLength={2000}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder="Ask a question…"
            className="max-h-32 min-h-[44px] flex-1 resize-none bg-transparent px-3 py-2.5 text-[15px] text-ink placeholder:text-ink-faint focus:outline-none"
          />
          <Button type="submit" size="icon" disabled={!text.trim()} loading={sending} aria-label="Send message">
            <Send className="h-5 w-5" />
          </Button>
        </form>
      </div>

      <Modal open={topicsOpen} onClose={() => setTopicsOpen(false)} title="Topic library" description="Short educational articles.">
        {topics.error ? (
          <p className="text-sm text-rose-200">{topics.error.message}</p>
        ) : (
          <ul className="space-y-2">
            {(topics.data?.items ?? []).map((t) => (
              <li key={t.id}>
                <button
                  type="button"
                  onClick={() => {
                    setTopicsOpen(false);
                    ask(`Tell me about: ${t.title}`);
                  }}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.03] p-3 text-left hover:border-accent-cyan/30"
                >
                  <p className="font-semibold text-white">{t.title}</p>
                  <p className="mt-0.5 text-sm text-ink-muted">{t.summary}</p>
                </button>
              </li>
            ))}
          </ul>
        )}
      </Modal>
    </div>
  );
}
