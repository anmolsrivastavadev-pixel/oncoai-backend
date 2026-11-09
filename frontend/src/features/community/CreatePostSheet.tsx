import clsx from 'clsx';
import { useState } from 'react';
import { EyeOff, ShieldAlert } from 'lucide-react';
import { Button, Input, Modal, Textarea } from '@/components/ui';
import { api, type ApiError } from '@/lib/api';
import { containsContactInfo, validateLength } from '@/lib/validation';
import { POST_TOPICS, type Post, type PostTopic } from '@/types/api';
import { TOPIC_LABEL, privacyMessage } from './topics';

export function AnonymousToggle({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={value}
      onClick={() => onChange(!value)}
      className="flex min-h-[44px] w-full items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/[0.03] px-3.5 text-left"
    >
      <span className="flex items-center gap-2 text-sm text-ink">
        <EyeOff className="h-4 w-4 text-ink-faint" aria-hidden /> Post anonymously
      </span>
      <span className={clsx('relative h-6 w-11 rounded-full transition', value ? 'bg-accent-cyan' : 'bg-white/15')}>
        <span className={clsx('absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all', value ? 'left-[22px]' : 'left-0.5')} />
      </span>
    </button>
  );
}

export function CreatePostSheet({ open, onClose, onCreated, defaultTopic }: { open: boolean; onClose: () => void; onCreated: (p: Post) => void; defaultTopic?: PostTopic }) {
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [topic, setTopic] = useState<PostTopic>(defaultTopic ?? 'support');
  const [anonymous, setAnonymous] = useState(false);
  const [errors, setErrors] = useState<{ title?: string | null; body?: string | null }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const warn = containsContactInfo(`${title} ${body}`);

  const submit = async () => {
    const errs = { title: validateLength(title, 3, 150, 'Title'), body: validateLength(body, 1, 5000, 'Post') };
    setErrors(errs);
    if (errs.title || errs.body) return;
    setBusy(true);
    setFormError(null);
    try {
      const p = await api.community.createPost({ title: title.trim(), body: body.trim(), topic, anonymous });
      onCreated(p);
      setTitle('');
      setBody('');
      setAnonymous(false);
      onClose();
    } catch (e) {
      const ae = e as ApiError;
      if (ae.fieldErrors.title || ae.fieldErrors.body) setErrors({ title: ae.fieldErrors.title, body: ae.fieldErrors.body });
      setFormError(privacyMessage(ae.status, ae.message));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Share with the community"
      description="Support, stories and questions — please don't share personal contact details."
      footer={
        <Button block size="lg" onClick={submit} loading={busy}>
          Publish post
        </Button>
      }
    >
      <div className="space-y-4">
        {formError && (
          <div role="alert" className="flex gap-2 rounded-xl border border-amber-300/30 bg-amber-300/10 px-3 py-2.5 text-sm text-amber-50">
            <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" aria-hidden />
            {formError}
          </div>
        )}
        <div>
          <p className="mb-2 text-sm font-medium text-ink">Topic</p>
          <div role="radiogroup" aria-label="Topic" className="flex flex-wrap gap-2">
            {POST_TOPICS.map((t) => (
              <button key={t} type="button" role="radio" aria-checked={topic === t} onClick={() => setTopic(t)} className={clsx('chip', topic === t && 'chip-active')}>
                {TOPIC_LABEL[t]}
              </button>
            ))}
          </div>
        </div>
        <Input label="Title" maxLength={150} value={title} onChange={(e) => setTitle(e.target.value)} error={errors.title} hint={`${title.length}/150`} />
        <Textarea label="Your post" maxLength={5000} value={body} onChange={(e) => setBody(e.target.value)} error={errors.body} hint={`${body.length}/5000`} className="min-h-[140px]" />
        {warn && <p className="text-xs text-amber-200">It looks like this includes a phone number or email. Posts with contact details are blocked to protect your privacy.</p>}
        <AnonymousToggle value={anonymous} onChange={setAnonymous} />
      </div>
    </Modal>
  );
}
