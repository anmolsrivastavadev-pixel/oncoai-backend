import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

afterEach(() => cleanup());

if (!window.matchMedia) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }),
  });
}

if (!('IntersectionObserver' in window)) {
  class IO {
    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords() {
      return [];
    }
  }
  // @ts-expect-error test shim
  window.IntersectionObserver = IO;
}

if (!('ResizeObserver' in window)) {
  class RO {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  // @ts-expect-error test shim
  window.ResizeObserver = RO;
}

if (!URL.createObjectURL) URL.createObjectURL = vi.fn(() => 'blob:mock');
if (!URL.revokeObjectURL) URL.revokeObjectURL = vi.fn();
Element.prototype.scrollIntoView = Element.prototype.scrollIntoView || vi.fn();
