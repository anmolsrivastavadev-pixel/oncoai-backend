import { ShieldCheck } from 'lucide-react';
import { Card } from '@/components/ui';

export function GuidelinesCard() {
  return (
    <Card>
      <h2 className="mb-2 flex items-center gap-2 text-base font-semibold">
        <ShieldCheck className="h-4 w-4 text-accent-teal" aria-hidden /> Community guidelines
      </h2>
      <ul className="list-disc space-y-1.5 pl-5 text-sm text-ink-muted">
        <li>Be kind. Everyone here is navigating something personal.</li>
        <li>Share experiences, not diagnoses or treatment advice.</li>
        <li>Protect privacy — phone numbers and emails are blocked automatically.</li>
        <li>Post anonymously whenever you like.</li>
        <li>Report anything harmful; moderators review every report.</li>
      </ul>
    </Card>
  );
}
