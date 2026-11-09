/// <reference types="vitest" />
import { defineConfig, loadEnv, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

/**
 * Injects the API origin into the CSP meta tag in index.html so that
 * connect-src / img-src allow exactly 'self' + VITE_API_URL.
 */
function cspPlugin(apiUrl: string): Plugin {
  let origin = '';
  try {
    origin = new URL(apiUrl).origin;
  } catch {
    origin = '';
  }
  return {
    name: 'oncoai-csp',
    transformIndexHtml(html) {
      return html.replace(/__API_ORIGIN__/g, origin);
    },
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');
  const apiUrl = env.VITE_API_URL || 'http://localhost:8000';
  return {
    plugins: [react(), cspPlugin(apiUrl)],
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    build: {
      target: 'es2020',
      sourcemap: false,
      chunkSizeWarningLimit: 700,
      rollupOptions: {
        output: {
          manualChunks: {
            react: ['react', 'react-dom', 'react-router-dom'],
            motion: ['framer-motion'],
            charts: ['recharts'],
          },
        },
      },
    },
    server: { port: 5173 },
    preview: { port: 4173 },
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
      css: false,
      include: ['src/**/*.test.{ts,tsx}'],
    },
  };
});
