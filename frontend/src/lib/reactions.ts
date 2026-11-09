import type { ReactionCounts, ReactionKind, ReactionResult } from '@/types/api';

export interface ReactionState {
  reactions: ReactionCounts;
  my_reactions: ReactionKind[];
}

export type ReactionAction =
  | { type: 'toggle'; kind: ReactionKind }
  | { type: 'sync'; result: ReactionResult }
  | { type: 'rollback'; previous: ReactionState };

/** Optimistic reaction toggle reducer. Counts never go below zero. */
export function reactionReducer(state: ReactionState, action: ReactionAction): ReactionState {
  switch (action.type) {
    case 'toggle': {
      const has = state.my_reactions.includes(action.kind);
      const count = state.reactions[action.kind] ?? 0;
      return {
        reactions: { ...state.reactions, [action.kind]: Math.max(0, count + (has ? -1 : 1)) },
        my_reactions: has ? state.my_reactions.filter((k) => k !== action.kind) : [...state.my_reactions, action.kind],
      };
    }
    case 'sync':
      return { reactions: { ...action.result.reactions }, my_reactions: [...action.result.my_reactions] };
    case 'rollback':
      return action.previous;
    default:
      return state;
  }
}

export const REACTION_LABEL: Record<ReactionKind, string> = {
  support: 'Support',
  hug: 'Hug',
  strength: 'Strength',
  relate: 'Relate',
};
