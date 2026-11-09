import { AnimatePresence, motion } from 'framer-motion';
import { WifiOff } from 'lucide-react';
import { useOnline } from '@/hooks/useOnline';

export function OfflineBanner() {
  const online = useOnline();
  return (
    <AnimatePresence>
      {!online && (
        <motion.div
          role="status"
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="overflow-hidden bg-amber-400/15 text-amber-100"
        >
          <div className="flex items-center justify-center gap-2 px-4 py-2 text-sm">
            <WifiOff className="h-4 w-4" aria-hidden /> You're offline. Some features are unavailable until you reconnect.
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
