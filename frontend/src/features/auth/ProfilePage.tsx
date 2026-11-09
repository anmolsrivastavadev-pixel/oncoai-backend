import clsx from 'clsx';
import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { KeyRound, LogOut, Save, ShieldCheck, Trash2 } from 'lucide-react';
import { Avatar, Badge, Button, Card, Input, Modal, PageHeader, Textarea, useToast } from '@/components/ui';
import { Disclaimer } from '@/components/Disclaimer';
import { api, type ApiError } from '@/lib/api';
import { formatDate } from '@/lib/format';
import { validatePassword } from '@/lib/validation';
import type { SkinType, UpdateMeBody } from '@/types/api';
import { useAuth } from './AuthContext';
import { PasswordInput } from './PasswordInput';
import { PasswordStrengthMeter } from './PasswordStrength';

export const FITZPATRICK: { type: SkinType; swatch: string; title: string; text: string }[] = [
  { type: 'I', swatch: '#F6E3D4', title: 'Type I', text: 'Very fair. Always burns, never tans.' },
  { type: 'II', swatch: '#EBCBB1', title: 'Type II', text: 'Fair. Usually burns, tans minimally.' },
  { type: 'III', swatch: '#D6A985', title: 'Type III', text: 'Medium. Sometimes burns, tans gradually.' },
  { type: 'IV', swatch: '#B07B55', title: 'Type IV', text: 'Olive. Rarely burns, tans easily.' },
  { type: 'V', swatch: '#7E5236', title: 'Type V', text: 'Brown. Very rarely burns, tans darkly.' },
  { type: 'VI', swatch: '#4A2F20', title: 'Type VI', text: 'Deeply pigmented. Almost never burns.' },
];

export function SkinTypePicker({ value, onChange }: { value: SkinType | null; onChange: (v: SkinType | null) => void }) {
  return (
    <fieldset>
      <legend className="mb-1 text-sm font-medium text-ink">Fitzpatrick skin type</legend>
      <p className="mb-3 text-xs text-ink-faint">A common scale describing how skin reacts to sun. Optional, and only used to personalise educational content.</p>
      <div role="radiogroup" className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {FITZPATRICK.map((f) => {
          const active = value === f.type;
          return (
            <button
              key={f.type}
              type="button"
              role="radio"
              aria-checked={active}
              onClick={() => onChange(active ? null : f.type)}
              className={clsx(
                'flex min-h-[64px] items-start gap-3 rounded-xl border p-3 text-left transition',
                active ? 'border-accent-cyan/70 bg-accent-cyan/10 shadow-glow-sm' : 'border-white/10 bg-white/[0.03] hover:border-white/20',
              )}
            >
              <span className="mt-0.5 h-7 w-7 shrink-0 rounded-full border border-white/20" style={{ background: f.swatch }} aria-hidden />
              <span>
                <span className="block text-sm font-semibold text-white">{f.title}</span>
                <span className="block text-xs leading-snug text-ink-muted">{f.text}</span>
              </span>
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}

export default function ProfilePage() {
  const { user, setUser, logout } = useAuth();
  const toast = useToast();
  const nav = useNavigate();
  const [form, setForm] = useState({ full_name: '', date_of_birth: '', skin_type: null as SkinType | null, location: '', bio: '' });
  const [saving, setSaving] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [pw, setPw] = useState({ current: '', next: '' });
  const [pwError, setPwError] = useState<string | null>(null);
  const [pwBusy, setPwBusy] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!user) return;
    setForm({
      full_name: user.full_name ?? '',
      date_of_birth: user.date_of_birth ?? '',
      skin_type: user.skin_type,
      location: user.location ?? '',
      bio: user.bio ?? '',
    });
  }, [user]);

  if (!user) return null;

  const save = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.full_name.trim()) {
      setFieldErrors({ full_name: 'Name is required.' });
      return;
    }
    setSaving(true);
    setFieldErrors({});
    const body: UpdateMeBody = {
      full_name: form.full_name.trim(),
      date_of_birth: form.date_of_birth || null,
      skin_type: form.skin_type,
      location: form.location.trim() || null,
      bio: form.bio.trim() || null,
    };
    try {
      const u = await api.users.update(body);
      setUser(u);
      toast.success('Profile saved.');
    } catch (err) {
      const e2 = err as ApiError;
      setFieldErrors(e2.fieldErrors ?? {});
      toast.error(e2.message);
    } finally {
      setSaving(false);
    }
  };

  const changePassword = async (e: FormEvent) => {
    e.preventDefault();
    const err = validatePassword(pw.next);
    if (!pw.current) return setPwError('Enter your current password.');
    if (err) return setPwError(err);
    setPwError(null);
    setPwBusy(true);
    try {
      await api.users.changePassword({ current_password: pw.current, new_password: pw.next });
      setPw({ current: '', next: '' });
      toast.success('Password updated.');
    } catch (e2) {
      const ae = e2 as ApiError;
      setPwError(ae.status === 400 || ae.status === 401 || ae.status === 403 ? 'Current password is incorrect.' : ae.message);
    } finally {
      setPwBusy(false);
    }
  };

  const deleteAccount = async () => {
    setDeleting(true);
    try {
      await api.users.remove();
      await logout();
      toast.info('Your account and all data were deleted.');
      nav('/', { replace: true });
    } catch (e2) {
      toast.error((e2 as ApiError).message);
      setDeleting(false);
    }
  };

  const doLogout = async () => {
    await logout();
    nav('/', { replace: true });
  };

  const today = new Date().toISOString().slice(0, 10);

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title="Profile" subtitle="Manage your account and preferences." />
      <Card className="mb-4 flex items-center gap-4">
        <Avatar name={user.full_name || user.email} size={56} />
        <div className="min-w-0 flex-1">
          <p className="truncate font-display text-lg font-semibold text-white">{user.full_name}</p>
          <p className="truncate text-sm text-ink-muted">{user.email}</p>
          <p className="mt-0.5 text-xs text-ink-faint">Member since {formatDate(user.created_at)}</p>
        </div>
        {user.role !== 'user' && (
          <Badge tone="violet">
            <ShieldCheck className="h-3.5 w-3.5" aria-hidden /> {user.role}
          </Badge>
        )}
      </Card>

      <Card className="mb-4">
        <form onSubmit={save} className="space-y-4" noValidate>
          <h2 className="text-lg font-semibold">Personal details</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="Full name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} error={fieldErrors.full_name} autoComplete="name" />
            <Input
              label="Date of birth"
              type="date"
              max={today}
              value={form.date_of_birth}
              onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })}
              error={fieldErrors.date_of_birth}
            />
            <Input
              label="Location"
              placeholder="City, country"
              value={form.location}
              onChange={(e) => setForm({ ...form, location: e.target.value })}
              error={fieldErrors.location}
              wrapClassName="sm:col-span-2"
            />
          </div>
          <SkinTypePicker value={form.skin_type} onChange={(skin_type) => setForm({ ...form, skin_type })} />
          <Textarea label="Bio" maxLength={500} value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })} hint={`${form.bio.length}/500`} error={fieldErrors.bio} />
          <div className="flex justify-end">
            <Button type="submit" loading={saving} leftIcon={<Save className="h-4 w-4" aria-hidden />}>
              Save changes
            </Button>
          </div>
        </form>
      </Card>

      <Card className="mb-4">
        <form onSubmit={changePassword} className="space-y-4" noValidate>
          <h2 className="text-lg font-semibold">Change password</h2>
          {pwError && (
            <p role="alert" className="rounded-xl border border-rose-300/30 bg-rose-400/10 px-3 py-2 text-sm text-rose-100">
              {pwError}
            </p>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            <PasswordInput label="Current password" autoComplete="current-password" value={pw.current} onChange={(e) => setPw({ ...pw, current: e.target.value })} />
            <div className="space-y-2">
              <PasswordInput label="New password" autoComplete="new-password" value={pw.next} onChange={(e) => setPw({ ...pw, next: e.target.value })} />
              <PasswordStrengthMeter password={pw.next} />
            </div>
          </div>
          <div className="flex justify-end">
            <Button type="submit" variant="glass" loading={pwBusy} leftIcon={<KeyRound className="h-4 w-4" aria-hidden />}>
              Update password
            </Button>
          </div>
        </form>
      </Card>

      <Card className="mb-4 space-y-3">
        <h2 className="text-lg font-semibold">Account</h2>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Button variant="glass" onClick={doLogout} leftIcon={<LogOut className="h-4 w-4" aria-hidden />}>
            Log out
          </Button>
          <Button variant="danger" onClick={() => setDeleteOpen(true)} leftIcon={<Trash2 className="h-4 w-4" aria-hidden />}>
            Delete account
          </Button>
        </div>
      </Card>
      <Disclaimer variant="inline" />

      <Modal
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        title="Delete your account?"
        description="This permanently deletes your profile, tracked spots, scans, images, appointments and posts. This cannot be undone."
        size="sm"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setDeleteOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" disabled={confirmText !== 'DELETE'} loading={deleting} onClick={deleteAccount}>
              Delete forever
            </Button>
          </div>
        }
      >
        <Input label='Type "DELETE" to confirm' value={confirmText} onChange={(e) => setConfirmText(e.target.value)} autoCapitalize="characters" />
      </Modal>
    </div>
  );
}
