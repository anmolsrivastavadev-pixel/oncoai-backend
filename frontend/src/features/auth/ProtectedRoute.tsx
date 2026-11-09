import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { PageSkeleton } from '@/components/ui';

export function ProtectedRoute({ roles }: { roles?: ('user' | 'moderator' | 'admin')[] }) {
  const { status, user } = useAuth();
  const loc = useLocation();
  if (status === 'loading') return <PageSkeleton />;
  if (status !== 'authenticated' || !user) {
    return <Navigate to="/login" replace state={{ from: loc.pathname + loc.search }} />;
  }
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}

/** Redirect authenticated users away from login/signup. */
export function GuestOnly({ children }: { children: JSX.Element }) {
  const { status } = useAuth();
  if (status === 'loading') return <PageSkeleton />;
  if (status === 'authenticated') return <Navigate to="/dashboard" replace />;
  return children;
}
