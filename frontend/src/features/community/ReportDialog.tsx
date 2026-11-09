import { useState } from 'react';
import clsx from 'clsx';
import { Button, Modal, Textarea, useToast } from '@/components/ui';
import { api, type ApiError } from '@/lib/api';

const REASONS = ['Shares personal contact info', 'Harassment or hate', 'Medical misinformation', 'Spam or advertising', 'Other'];

export function ReportDialog({ target, onClose }: { target: { type: 'post' | 'comment'; id: number } | null; onClose: () => void }) {
  const toast = useToast();
  const [reason, setReason] = useState('');
  const [detail, setDetail] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!target || !reason) return;
    const full = reason === 'Other' || detail.trim() ? `${reason}${detail.trim() ? `: ${detail.trim()}` : ''}` : reason;
    setBusy(true);
    try {
      if (target.type === 'post') await api.community.reportPost(target.id, full);
      else await api.community.reportComment(target.id, full);
      toast.success('Thanks — our moderators will review this.');
      setReason('');
      setDetail('');
      onClose();
    } catch (e) {
      toast.error((e as ApiError).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      open={!!target}
      onClose={onClose}
      size="sm"
      title={`Report ${target?.type ?? ''}`}
      description="Reports are anonymous to the author."
      footer={
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="danger" disabled={!reason} loading={busy} onClick={submit}>
            Submit report
          </Button>
        </div>
      }
    >
      <div role="radiogroup" aria-label="Reason" className="space-y-2">
        {REASONS.map((r) => (
          <button key={r} type="button" role="radio" aria-checked={reason === r} onClick={() => setReason(r)} className={clsx('chip w-full justify-start rounded-xl', reason === r && 'chip-active')}>
            {r}
          </button>
        ))}
      </div>
      <Textarea label="Details (optional)" className="mt-3 min-h-[80px]" maxLength={500} value={detail} onChange={(e) => setDetail(e.target.value)} />
    </Modal>
  );
}
