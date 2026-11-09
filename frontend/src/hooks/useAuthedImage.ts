import { useEffect, useState } from 'react';
import { api as defaultApi, type ApiClient } from '@/lib/api';

export interface AuthedImageState {
  src: string | null;
  loading: boolean;
  error: boolean;
}

/**
 * Images are only served by authenticated endpoints, so <img src> cannot be
 * used directly. Fetch with the Authorization header and expose an object URL,
 * revoked on change/unmount.
 */
export function useAuthedImage(url: string | null | undefined, client: ApiClient = defaultApi): AuthedImageState {
  const [state, setState] = useState<AuthedImageState>({ src: null, loading: !!url, error: false });

  useEffect(() => {
    if (!url) {
      setState({ src: null, loading: false, error: false });
      return;
    }
    const ctrl = new AbortController();
    let objectUrl: string | null = null;
    let alive = true;
    setState({ src: null, loading: true, error: false });
    client
      .fetchBlob(url, ctrl.signal)
      .then((blob) => {
        if (!alive) return;
        objectUrl = URL.createObjectURL(blob);
        setState({ src: objectUrl, loading: false, error: false });
      })
      .catch(() => {
        if (alive) setState({ src: null, loading: false, error: true });
      });
    return () => {
      alive = false;
      ctrl.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [url, client]);

  return state;
}
