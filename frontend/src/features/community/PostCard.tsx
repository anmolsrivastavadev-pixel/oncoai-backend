import { Link } from 'react-router-dom';
import { MessageCircle } from 'lucide-react';
import { Avatar, Badge, Card } from '@/components/ui';
import { relativeTime } from '@/lib/format';
import type { Post } from '@/types/api';
import { ReactionBar } from './ReactionBar';
import { TOPIC_LABEL } from './topics';

export function PostCard({ post }: { post: Post }) {
  return (
    <Card className="space-y-3" interactive>
      <Link to={`/community/${post.id}`} className="block space-y-2">
        <div className="flex items-center gap-2.5">
          <Avatar name={post.author.display_name} size={34} />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-white">
              {post.author.display_name}
              {post.is_mine && <span className="ml-1.5 text-xs text-ink-faint">(you)</span>}
            </p>
            <p className="text-xs text-ink-faint">{relativeTime(post.created_at)}</p>
          </div>
          <Badge tone="cyan">{TOPIC_LABEL[post.topic] ?? post.topic}</Badge>
        </div>
        <h3 className="text-base font-semibold leading-snug text-white">{post.title}</h3>
        <p className="line-clamp-3 whitespace-pre-line text-sm leading-relaxed text-ink-muted">{post.body}</p>
      </Link>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <ReactionBar postId={post.id} initial={{ reactions: post.reactions, my_reactions: post.my_reactions }} compact />
        <Link to={`/community/${post.id}`} className="inline-flex min-h-[40px] items-center gap-1.5 px-1 text-sm text-ink-muted hover:text-white" aria-label={`${post.comment_count} comments`}>
          <MessageCircle className="h-4 w-4" aria-hidden /> {post.comment_count}
        </Link>
      </div>
    </Card>
  );
}
