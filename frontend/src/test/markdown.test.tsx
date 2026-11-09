import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MarkdownLite, parseBlocks, safeHref } from '@/lib/markdown';

describe('MarkdownLite', () => {
  it('renders bullets and bold as elements', () => {
    const { container } = render(<MarkdownLite text={'Key points:\n- **Asymmetry** matters\n- Borders'} />);
    expect(container.querySelectorAll('li')).toHaveLength(2);
    expect(container.querySelector('strong')?.textContent).toBe('Asymmetry');
  });
  it('never renders raw HTML', () => {
    const { container } = render(<MarkdownLite text={'<img src=x onerror=alert(1)> <script>bad()</script>'} />);
    expect(container.querySelector('img')).toBeNull();
    expect(container.querySelector('script')).toBeNull();
    expect(screen.getByText(/<img src=x/)).toBeInTheDocument();
  });
  it('parses numbered lists', () => {
    expect(parseBlocks('1. one\n2. two')).toEqual([{ type: 'ol', items: ['one', 'two'] }]);
  });
  it('only allows http(s) links', () => {
    expect(safeHref('javascript:alert(1)')).toBeNull();
    expect(safeHref('https://example.org/a')).toBe('https://example.org/a');
  });
});
