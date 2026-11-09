import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { PageSkeleton } from '@/components/ui';
import { GuestOnly, ProtectedRoute } from '@/features/auth/ProtectedRoute';

const LandingPage = lazy(() => import('@/features/landing/LandingPage'));
const LoginPage = lazy(() => import('@/features/auth/LoginPage'));
const SignupPage = lazy(() => import('@/features/auth/SignupPage'));
const ProfilePage = lazy(() => import('@/features/auth/ProfilePage'));
const DashboardPage = lazy(() => import('@/features/tracking/DashboardPage'));
const TrackPage = lazy(() => import('@/features/tracking/TrackPage'));
const LesionDetailPage = lazy(() => import('@/features/tracking/LesionDetailPage'));
const ComparePage = lazy(() => import('@/features/tracking/ComparePage'));
const ScanPage = lazy(() => import('@/features/scan/ScanPage'));
const ScanResultPage = lazy(() => import('@/features/scan/ScanResultPage'));
const CarePage = lazy(() => import('@/features/care/CarePage'));
const CommunityPage = lazy(() => import('@/features/community/CommunityPage'));
const PostDetailPage = lazy(() => import('@/features/community/PostDetailPage'));
const ModerationPage = lazy(() => import('@/features/community/ModerationPage'));
const AssistantPage = lazy(() => import('@/features/assistant/AssistantPage'));
const NotFoundPage = lazy(() => import('@/features/misc/NotFoundPage'));

export function AppRoutes() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<GuestOnly><LoginPage /></GuestOnly>} />
        <Route path="/signup" element={<GuestOnly><SignupPage /></GuestOnly>} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/scan" element={<ScanPage />} />
            <Route path="/scan/:id" element={<ScanResultPage />} />
            <Route path="/track" element={<TrackPage />} />
            <Route path="/track/:id" element={<LesionDetailPage />} />
            <Route path="/tracking/compare" element={<ComparePage />} />
            <Route path="/care" element={<CarePage />} />
            <Route path="/community" element={<CommunityPage />} />
            <Route path="/community/:id" element={<PostDetailPage />} />
            <Route path="/assistant" element={<AssistantPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Route>
        </Route>
        <Route element={<ProtectedRoute roles={['moderator', 'admin']} />}>
          <Route element={<AppShell />}>
            <Route path="/moderation" element={<ModerationPage />} />
          </Route>
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}
