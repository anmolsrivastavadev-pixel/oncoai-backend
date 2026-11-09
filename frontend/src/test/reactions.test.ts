import { describe, expect, it } from 'vitest';
import { reactionReducer, type ReactionState } from '@/lib/reactions';

const base: ReactionState = { reactions: { support: 2, hug: 0, strength: 1, relate: 0 }, my_reactions: ['support'] };

describe('reactionReducer', () => {
  it('toggles off an existing reaction', () => {
    const s = reactionReducer(base, { type: 'toggle', kind: 'support' });
    expect(s.reactions.support).toBe(1);
    expect(s.my_reactions).toEqual([]);
  });
  it('toggles on a new reaction', () => {
    const s = reactionReducer(base, { type: 'toggle', kind: 'hug' });
    expect(s.reactions.hug).toBe(1);
    expect(s.my_reactions).toContain('hug');
  });
  it('never goes negative', () => {
    const s = reactionReducer({ reactions: { support: 0, hug: 0, strength: 0, relate: 0 }, my_reactions: ['relate'] }, { type: 'toggle', kind: 'relate' });
    expect(s.reactions.relate).toBe(0);
  });
  it('syncs to server state and rolls back', () => {
    const optimistic = reactionReducer(base, { type: 'toggle', kind: 'hug' });
    const synced = reactionReducer(optimistic, { type: 'sync', result: { reactions: { support: 5, hug: 1, strength: 1, relate: 0 }, my_reactions: ['support', 'hug'] } });
    expect(synced.reactions.support).toBe(5);
    expect(reactionReducer(optimistic, { type: 'rollback', previous: base })).toBe(base);
  });
  it('does not mutate input state', () => {
    const copy = JSON.parse(JSON.stringify(base));
    reactionReducer(base, { type: 'toggle', kind: 'strength' });
    expect(base).toEqual(copy);
  });
});
