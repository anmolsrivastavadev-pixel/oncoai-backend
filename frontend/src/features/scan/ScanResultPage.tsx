import { useLocation, useParams } from 'react-router-dom';
import { ScanLine } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ErrorState, PageHeader, Skeleton, buttonClasses } from '@/components/ui';
import { useAsync } from '@/hooks/useAsync';
import { api } from '@/lib/api';
import type { Scan } from '@/types/api';
import { ScanResultView } from './ScanResultView';

export default function ScanResultPage() {
  const { id } = useParams();
  const scanId = Number(id);
  const passed = (useLocation().state as { scan?: Scan } | null)?.scan;
  const fresh = passed && passed.id === scanId ? passed : undefined;
  const q = useAsync(() => api.scans.get(scanId), [scanId], !fresh && Number.isFinite(scanId));
  const scan = fresh ?? q.data;

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        back
        eyebrow="Scan result"
        title="Your awareness summary"
        actions={
          <Link to={scan ? `/scan?lesion=${scan.lesion_id}` : '/scan'} className={buttonClasses('glass', 'sm')}>
            <ScanLine className="h-4 w-4" aria-hidden /> Re-scan
          </Link>
        }
      />
      {scan ? (
        <ScanResultView scan={scan} />
      ) : q.error ? (
        <ErrorState message={q.error.message} onRetry={q.reload} />
      ) : (
        <div className="space-y-4" role="status" aria-label="Loading result">
          <Skeleton className="h-16" />
          <Skeleton className="h-48" />
          <Skeleton className="h-64" />
        </div>
      )}
    </div>
  );
}
