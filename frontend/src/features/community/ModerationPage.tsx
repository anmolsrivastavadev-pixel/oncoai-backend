import { useState } from 'react';
import { Check, ShieldCheck, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Badge, Button, Card, EmptyState, ErrorState, ListSkeleton, PageHeader, useToast } from '@/components/ui';
import { useAsync } from '@/hooks/useAsync';
import { api, type ApiError } from '@/lib/api';
import { formatDateTime } from '@/lib/format';
import type { ModerationAction, ModerationReport } from '@/types/api';

function targetOf(r: ModerationReport) {
  const type = r.target_type ?? (r.comment_id || r.comment ? 'comment' : 'post');
  const postId = r.post_id ?? r.post?.id ?? r.comment?.post_id ?? null;
  const preview = r.content_preview ?? r.comment?.body ?? r.post?.title ?? r.post?.body ?? null;
  return { type, postId, preview };
}

export default function ModerationPage() {
  const toast = useToast();
  const q = useAsync(() => api.community.reports('open'), []);
  const [busy, setBusy] = useState<number | null>(null);

  const resolve = async (r: ModerationReport, action: ModerationAction) => {
    setBusy(r.id);
    try {
      await api.community.resolveReport(r.id, action);
      q.setData((d) => d?.filter((x) => x.id !== r.id));
      toast.success(action === 'dismiss' ? 'Report dismissed.' : 'Content removed.');
    } catch (e) {
      toast.error((e as ApiError).message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader eyebrow="Moderation" title="Open reports" subtitle="Review reported posts and comments." />
      {q.loading ? (
        <ListSkeleton rows={3} />
      ) : q.error ? (
        <ErrorState message={q.error.message} onRetry={q.reload} />
      ) : !q.data?.length ? (
        <EmptyState icon={ShieldCheck} title="All clear" description="There are no open reports right now." />
      ) : (
        <ul className="space-y-3">
          {q.data.map((r) => {
            const t = targetOf(r);
            return (
              <li key={r.id}>
                <Card className="space-y-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone="amber">{t.type}</Badge>
                    <span className="text-xs text-ink-faint">Report #{r.id}{r.created_at ? ` · ${formatDateTime(r.created_at)}` : ''}</span>
                  </div>
                  <p className="text-sm text-white">
                    <span className="text-ink-faint">Reason: </span>
                    {r.reason}
                  </p>
                  {t.preview && <blockquote className="rounded-xl border-l-2 border-accent-cyan/50 bg-white/[0.03] px-3 py-2 text-sm text-ink-muted">{t.preview}</blockquote>}
                  <div className="flex flex-wrap gap-2">
                    {t.postId && (
                      <Link to={`/community/${t.postId}`} className="chip">
                        View post
                      </Link>
                    )}
                    <Button size="sm" variant="glass" loading={busy === r.id} onClick={() => resolve(r, 'dismiss')} leftIcon={<Check className="h-4 w-4" aria-hidden />}>
                      Dismiss
                    </Button>
                    <Button size="sm" variant="danger" loading={busy === r.id} onClick={() => resolve(r, 'remove_content')} leftIcon={<Trash2 className="h-4 w-4" aria-hidden />}>
                      Remove content
                    </Button>
                  </div>
                </Card>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
