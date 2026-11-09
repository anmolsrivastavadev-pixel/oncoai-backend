import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { Disclaimer } from '@/components/Disclaimer';
import { ConcernBadge } from '@/components/ui';
import { DISCLAIMER } from '@/lib/constants';
import { FORBIDDEN_DIAGNOSTIC_TERMS, containsDiagnosticTerm, scrubDiagnosticTerms } from '@/lib/safety';
import { ScanResultView } from '@/features/scan/ScanResultView';
import { scan } from './fixtures';

vi.mock('@/hooks/useAuthedImage', () => ({ useAuthedImage: () => ({ src: 'blob:mock', loading: false, error: null }) }));

const EXACT = 'OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or treatment advice.';

describe('Disclaimer', () => {
  it('uses the exact mandated wording', () => {
    expect(DISCLAIMER).toBe(EXACT);
  });

  it.each(['banner', 'inline', 'compact'] as const)('renders the full text in the %s variant', (variant) => {
    render(<Disclaimer variant={variant} />);
    expect(screen.getByTestId('disclaimer')).toHaveTextContent(EXACT);
  });
});

describe('ConcernBadge', () => {
  it.each([
    ['low', /low concern/i],
    ['moderate', /moderate concern/i],
    ['higher', /higher concern/i],
  ] as const)('labels %s', (level, label) => {
    render(<ConcernBadge level={level} />);
    expect(screen.getByText(label)).toHaveAttribute('data-level', level);
  });

  it('handles a spot with no scans', () => {
    render(<ConcernBadge level={null} />);
    expect(screen.getByText(/not scanned yet/i)).toBeInTheDocument();
  });
});

describe('safety scrubber', () => {
  it('flags disease names and keeps educational wording', () => {
    expect(containsDiagnosticTerm('This looks like melanoma')).toBe(true);
    expect(containsDiagnosticTerm('Irregular visual patterns detected.')).toBe(false);
    expect(scrubDiagnosticTerms(['Consider professional dermatologist evaluation.', 'Likely basal cell carcinoma'])).toEqual([
      'Consider professional dermatologist evaluation.',
    ]);
  });
});

describe('ScanResultView', () => {
  const renderScan = (s = scan()) =>
    render(
      <MemoryRouter>
        <ScanResultView scan={s} />
      </MemoryRouter>,
    );

  it('shows concern level, headline, guidance and the disclaimer', () => {
    renderScan();
    expect(screen.getAllByText(/moderate concern/i).length).toBeGreaterThan(0);
    expect(screen.getByText('Some irregular visual patterns detected.')).toBeInTheDocument();
    expect(screen.getByText('Consider professional dermatologist evaluation.')).toBeInTheDocument();
    expect(screen.getAllByTestId('disclaimer')[0]).toHaveTextContent(EXACT);
  });

  it.each(['low', 'moderate', 'higher'] as const)('never renders a disease name for a %s result', (level) => {
    const { container } = renderScan(
      scan({
        concern_level: level,
        // Even if a server bug leaked a label, the UI must not show it.
        observations: ['Irregular visual patterns detected.', 'Pattern consistent with melanoma'],
        recommendations: ['Consider professional dermatologist evaluation.', 'Benign nevus, no action'],
      }),
    );
    const text = (container.textContent ?? '').replace(EXACT, '').toLowerCase();
    for (const term of FORBIDDEN_DIAGNOSTIC_TERMS) expect(text).not.toContain(term);
  });

  it('surfaces photo quality issues', () => {
    renderScan(scan({ quality: { ok: false, blur_score: 10, brightness: 0.2, contrast: 0.1, issues: ['The photo looks blurry.'] } }));
    expect(screen.getByText('The photo looks blurry.')).toBeInTheDocument();
  });
});
