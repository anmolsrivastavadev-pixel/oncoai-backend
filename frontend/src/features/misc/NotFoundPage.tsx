import { Link } from 'react-router-dom';
import { Compass } from 'lucide-react';
import { LogoMark } from '@/components/brand/Logo';
import { Disclaimer } from '@/components/Disclaimer';
import { buttonClasses } from '@/components/ui';

export default function NotFoundPage() {
  return (
    <div className="grid min-h-[100dvh] place-items-center px-safe pt-safe">
      <div className="max-w-md text-center">
        <LogoMark size={64} className="mx-auto" />
        <p className="mt-6 font-display text-6xl font-bold text-gradient">404</p>
        <h1 className="mt-2 text-2xl font-bold">This page drifted out of frame</h1>
        <p className="mt-2 text-sm text-ink-muted">The page you're looking for doesn't exist or has moved.</p>
        <Link to="/" className={buttonClasses('primary', 'lg') + ' mt-6'}>
          <Compass className="h-5 w-5" aria-hidden /> Back to home
        </Link>
        <Disclaimer variant="compact" className="mt-8" />
      </div>
    </div>
  );
}
