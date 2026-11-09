import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import { HandHeart, Heart, Users, Zap, type LucideIcon } from 'lucide-react';
import { useReducer, useRef } from 'react';
import { useToast } from '@/components/ui';
import { api, type ApiError } from '@/lib/api';
import { hapticTap } from '@/lib/native';
import { REACTION_LABEL, reactionReducer, type ReactionState } from '@/lib/reactions';
import { REACTION_KINDS, type ReactionKind } from '@/types/api';

const ICONS: Record<ReactionKind, LucideIcon> = { support: Heart, hug: HandHeart, strength: Zap, relate: Users };

export function ReactionBar({ postId, initial, compact }: { postId: number; initial: ReactionState; compact?: boolean }) {
  const [state, dispatch] = useReducer(reactionReducer, initial);
  const toast = useToast();
  const stateRef = useRef(state);
  stateRef.current = state;

  const toggle = async (kind: ReactionKind) => {
    const previous = stateRef.current;
    dispatch({ type: 'toggle', kind });
    void hapticTap();
    try {
      const result = await api.community.react(postId, kind);
      dispatch({ type: 'sync', result });
    } catch (e) {
      dispatch({ type: 'rollback', previous });
      toast.error((e as ApiError).message);
    }
  };

  return (
    <div className="flex flex-wrap gap-1.5" role="group" aria-label="Reactions">
      {REACTION_KINDS.map((k) => {
        const Icon = ICONS[k];
        const on = state.my_reactions.includes(k);
        const n = state.reactions[k] ?? 0;
        return (
          <motion.button
            key={k}
            type="button"
            whileTap={{ scale: 0.9 }}
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              void toggle(k);
            }}
            aria-pressed={on}
            aria-label={`${REACTION_LABEL[k]} (${n})`}
            className={clsx(
              'inline-flex min-h-[40px] items-center gap-1.5 rounded-full border px-3 text-sm transition',
              on ? 'border-accent-cyan/60 bg-accent-cyan/15 text-white' : 'border-white/10 bg-white/[0.03] text-ink-muted hover:text-white',
            )}
          >
            <Icon className={clsx('h-4 w-4', on && 'fill-accent-cyan/40 text-accent-cyan')} aria-hidden />
            {!compact && <span className="hidden sm:inline">{REACTION_LABEL[k]}</span>}
            <span className="relative inline-block min-w-[1ch] overflow-hidden tabular-nums" aria-hidden>
              <AnimatePresence mode="popLayout" initial={false}>
                <motion.span key={n} initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -10, opacity: 0 }} className="inline-block">
                  {n}
                </motion.span>
              </AnimatePresence>
            </span>
          </motion.button>
        );
      })}
    </div>
  );
}
