import type { PostTopic } from '@/types/api';

export const TOPIC_LABEL: Record<PostTopic, string> = {
  support: 'Support',
  awareness: 'Awareness',
  prevention: 'Prevention',
  stories: 'Stories',
  questions: 'Questions',
};

export const privacyMessage = (status: number, message: string) =>
  status === 422 && /phone|email|contact|privacy/i.test(message)
    ? 'For your privacy, posts and comments cannot include phone numbers or email addresses. Please remove them and try again.'
    : message;
