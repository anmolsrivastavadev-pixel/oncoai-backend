import clsx from 'clsx';
import { useCallback, useEffect, useRef, useState } from 'react';
import { PenSquare, Users } from 'lucide-react';
import { Disclaimer } from '@/components/Disclaimer';
import { Button, EmptyState, ErrorState, ListSkeleton, PageHeader, Spinner, useToast } from '@/components/ui';
import { api, ApiError } from '@/lib/api';
import { POST_TOPICS, type Post, type PostTopic } from '@/types/api';
import { CreatePostSheet } from './CreatePostSheet';
import { GuidelinesCard } from './GuidelinesCard';
import { PostCard } from './PostCard';
import { TOPIC_LABEL } from './topics';

const PAGE = 10;

export default function CommunityPage() {
  const toast = useToast();
  const [topic, setTopic] = useState<PostTopic | ''>('');
  const [items, setItems] = useState<Post[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [more, setMore] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const sentinel = useRef<HTMLDivElement>(null);
  const reqId = useRef(0);

  const load = useCallback(
    async (offset: number) => {
      const id = ++reqId.current;
      if (offset === 0) setLoading(true);
      else setMore(true);
      setError(null);
      try {
        const res = await api.community.posts({ topic: topic || undefined, limit: PAGE, offset });
        if (id !== reqId.current) return;
        setItems((xs) => (offset === 0 ? res.items : [...xs, ...res.items.filter((p) => !xs.some((x) => x.id === p.id))]));
        setTotal(res.total);
      } catch (e) {
        if (id === reqId.current) setError(e instanceof ApiError ? e : new ApiError(0, 'Failed to load posts.'));
      } finally {
        if (id === reqId.current) {
          setLoading(false);
          setMore(false);
        }
      }
    },
    [topic],
  );

  useEffect(() => {
    void load(0);
  }, [load]);

  const hasMore = items.length < total;
  useEffect(() => {
    const el = sentinel.current;
    if (!el || !hasMore || typeof IntersectionObserver === 'undefined') return;
    const io = new IntersectionObserver((entries) => {
      if (entries[0]?.isIntersecting && !more && !loading) void load(items.length);
    });
    io.observe(el);
    return () => io.disconnect();
  }, [hasMore, more, loading, items.length, load]);

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        eyebrow="Community"
        title="You're not alone"
        subtitle="A moderated, privacy-first space for support and shared experiences."
        actions={
          <Button size="sm" onClick={() => setCreateOpen(true)} leftIcon={<PenSquare className="h-4 w-4" aria-hidden />}>
            Post
          </Button>
        }
      />
      <div className="grid gap-5 lg:grid-cols-[1fr_300px]">
        <div className="min-w-0 space-y-4">
          <div role="radiogroup" aria-label="Filter by topic" className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1 no-scrollbar">
            {[{ v: '' as const, l: 'All' }, ...POST_TOPICS.map((t) => ({ v: t, l: TOPIC_LABEL[t] }))].map((c) => (
              <button key={c.v || 'all'} type="button" role="radio" aria-checked={topic === c.v} onClick={() => setTopic(c.v)} className={clsx('chip shrink-0', topic === c.v && 'chip-active')}>
                {c.l}
              </button>
            ))}
          </div>
          {loading ? (
            <ListSkeleton rows={3} />
          ) : error && !items.length ? (
            <ErrorState message={error.message} onRetry={() => load(0)} />
          ) : !items.length ? (
            <EmptyState icon={Users} title="No posts yet" description="Be the first to share in this topic." action={<Button onClick={() => setCreateOpen(true)}>Write a post</Button>} />
          ) : (
            <ul className="space-y-3">
              {items.map((p) => (
                <li key={p.id}>
                  <PostCard post={p} />
                </li>
              ))}
            </ul>
          )}
          <div ref={sentinel} />
          {hasMore && !loading && (
            <div className="flex justify-center">
              {more ? (
                <Spinner />
              ) : (
                <Button variant="glass" onClick={() => load(items.length)}>
                  Load more
                </Button>
              )}
            </div>
          )}
        </div>
        <aside className="space-y-4 lg:sticky lg:top-8 lg:self-start">
          <GuidelinesCard />
          <Disclaimer variant="inline" />
        </aside>
      </div>
      <CreatePostSheet
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        defaultTopic={topic || undefined}
        onCreated={(p) => {
          setItems((xs) => [p, ...xs]);
          setTotal((t) => t + 1);
          toast.success('Your post is live.');
        }}
      />
    </div>
  );
}
