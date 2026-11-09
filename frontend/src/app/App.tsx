import { MotionConfig } from 'framer-motion';
import { useEffect } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { ErrorBoundary, ToastProvider } from '@/components/ui';
import { ChatProvider } from '@/features/assistant/ChatContext';
import { AuthProvider } from '@/features/auth/AuthContext';
import { initNativeChrome } from '@/lib/native';
import { AppRoutes } from './routes';

export function App() {
  useEffect(() => {
    void initNativeChrome();
  }, []);
  return (
    <MotionConfig reducedMotion="user">
      <ErrorBoundary>
        <ToastProvider>
          <AuthProvider>
            <ChatProvider>
              <BrowserRouter>
                <AppRoutes />
              </BrowserRouter>
            </ChatProvider>
          </AuthProvider>
        </ToastProvider>
      </ErrorBoundary>
    </MotionConfig>
  );
}
