const raw = (import.meta.env.VITE_API_URL as string | undefined) || 'http://localhost:8000';

/** Backend origin, without trailing slash. */
export const API_URL = raw.replace(/\/+$/, '');
/** Prefix for all versioned routes. */
export const API_BASE = `${API_URL}/api/v1`;
