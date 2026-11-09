import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Flag, Send, ShieldAlert, Trash2 } from 'lucide-react';
import { Disclaimer } from '@/components/Disclaimer';
import { Avatar, Badge, Button, Card, ErrorState, Modal, PageHeader, Skeleton, Textarea, useToast } from '@/components/ui';
import { useAuth } from '@/features/auth/AuthContext';
import { useAsync } from '@/hooks/useAsync';
import { api, type ApiError } from '@/lib/api';
import { formatDateTime, relativeTime } from '@/lib/format';
import { validateLength } from '@/lib/validation';
import { AnonymousToggle } from './CreatePostSheet';
import { ReactionBar } from './ReactionBar';
import { ReportDialog } from './ReportDialog';
import { TOPIC_LABEL, privacyMessage } from './topics';

export default function PostDetailPage() {
  const { id } = useParams();
  const postId = Number(id);
  const nav = useNavigate();
  const toast = useToast();
  const { isModerator } = useAuth();
  const q = useAsync(() => api.community.post(postId), [postId]);
  const [comment, setComment] = useState('');
  const [anon, setAnon] = useState(false);
  const [busy, setBusy] = useState(false);
  const [commentError, setCommentError] = useState<string | null>(null);
  const [report, setReport] = useState<{ type: 'post' | 'comment'; id: number } | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<{ type: 'post' | 'comment'; id: number } | null>(null);

  const p = q.data;

  const submitComment = async () => {
    const err = validateLength(comment, 1, 2000, 'Comment');
    if (err) return setCommentError(err);
    setBusy(true);
    setCommentError(null);
    try {
      const c = await api.community.comment(postId, { body: comment.trim(), anonymous: anon });
      q.setData((d) => (d ? { ...d, comments: [...d.comments, c], comment_count: d.comment_count + 1 } : d));
      setComment('');
    } catch (e) {
      const ae = e as ApiError;
      setCommentError(privacyMessage(ae.status, ae.message));
    } finally {
      setBusy(false);
    }
  };

  const doDelete = async () => {
    if (!confirmDelete) return;
    try {
      if (confirmDelete.type === 'post') {
        await api.community.deletePost(confirmDelete.id);
        toast.success('Post deleted.');
        nav('/community', { replace: true });
      } else {
        await api.community.deleteComment(confirmDelete.id);
        q.setData((d) => (d ? { ...d, comments: d.comments.filter((c) => c.id !== confirmDelete.id), comment_count: Math.max(0, d.comment_count - 1) } : d));
        toast.success('Comment deleted.');
      }
    } catch (e) {
      toast.error((e as ApiError).message);
    } finally {
      setConfirmDelete(null);
    }
  };

  if (q.error) return <ErrorState className="mx-auto max-w-xl" message={q.error.message} onRetry={q.reload} />;
  if (!p)
    return (
      <div className="mx-auto max-w-3xl space-y-3" role="status" aria-label="Loading post">
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-40" />
      </div>
    );

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <PageHeader back="/community" eyebrow={TOPIC_LABEL[p.topic]} title={p.title} />
      <Card className="space-y-4">
        <div className="flex items-center gap-3">
          <Avatar name={p.author.display_name} size={40} />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-white">{p.author.display_name}</p>
            <p className="text-xs text-ink-faint">{formatDateTime(p.created_at)}</p>
          </div>
          {p.status === 'removed' && <Badge tone="rose">Removed</Badge>}
        </div>
        <p className="whitespace-pre-line text-[15px] leading-relaxed text-ink">{p.body}</p>
        <ReactionBar postId={p.id} initial={{ reactions: p.reactions, my_reactions: p.my_reactions }} />
        <div className="flex gap-2 border-t border-white/5 pt-3">
          {!p.is_mine && (
            <Button size="sm" variant="ghost" onClick={() => setReport({ type: 'post', id: p.id })} leftIcon={<Flag className="h-4 w-4" aria-hidden />}>
              Report
            </Button>
          )}
          {(p.is_mine || isModerator) && (
            <Button size="sm" variant="ghost" className="text-rose-200" onClick={() => setConfirmDelete({ type: 'post', id: p.id })} leftIcon={<Trash2 className="h-4 w-4" aria-hidden />}>
              Delete
            </Button>
          )}
        </div>
      </Card>

      <section aria-labelledby="comments-h" className="space-y-3">
        <h2 id="comments-h" className="text-lg font-semibold">
          Comments ({p.comments.length})
        </h2>
        {p.comments.length === 0 && <p className="text-sm text-ink-muted">No comments yet. Offer some encouragement.</p>}
        <ul className="space-y-2">
          {p.comments.map((c) => (
            <li key={c.id}>
              <Card className="py-3">
                <div className="flex items-start gap-3">
                  <Avatar name={c.author.display_name} size={32} />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm">
                      <span className="font-medium text-white">{c.author.display_name}</span> <span className="text-xs text-ink-faint">· {relativeTime(c.created_at)}</span>
                    </p>
                    <p className="mt-1 whitespace-pre-line text-sm text-ink">{c.body}</p>
                  </div>
                  <div className="flex shrink-0">
                    {!c.is_mine && (
                      <Button size="icon" variant="ghost" onClick={() => setReport({ type: 'comment', id: c.id })} aria-label="Report comment">
                        <Flag className="h-4 w-4" />
                      </Button>
                    )}
                    {(c.is_mine || isModerator) && (
                      <Button size="icon" variant="ghost" onClick={() => setConfirmDelete({ type: 'comment', id: c.id })} aria-label="Delete comment">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            </li>
          ))}
        </ul>
        <Card className="space-y-3">
          {commentError && (
            <p role="alert" className="flex gap-2 rounded-xl border border-amber-300/30 bg-amber-300/10 px-3 py-2 text-sm text-amber-50">
              <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" aria-hidden /> {commentError}
            </p>
          )}
          <Textarea label="Add a comment" maxLength={2000} value={comment} onChange={(e) => setComment(e.target.value)} className="min-h-[90px]" placeholder="Be kind and supportive." />
          <AnonymousToggle value={anon} onChange={setAnon} />
          <div className="flex justify-end">
            <Button onClick={submitComment} loading={busy} leftIcon={<Send className="h-4 w-4" aria-hidden />}>
              Comment
            </Button>
          </div>
        </Card>
      </section>
      <Disclaimer variant="compact" />

      <ReportDialog target={report} onClose={() => setReport(null)} />
      <Modal
        open={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        size="sm"
        title={`Delete this ${confirmDelete?.type ?? ''}?`}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setConfirmDelete(null)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={doDelete}>
              Delete
            </Button>
          </div>
        }
      >
        <p className="text-sm text-ink-muted">This cannot be undone.</p>
      </Modal>
    </div>
  );
}
