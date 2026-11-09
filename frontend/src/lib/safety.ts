/**
 * Words that must never be rendered as a result/diagnosis in the scan UI.
 * The API never returns them; this list is used by tests (and the defensive
 * `scrubDiagnosticTerms` below) to guarantee the UI never adds any.
 */
export const FORBIDDEN_DIAGNOSTIC_TERMS = [
  'melanoma',
  'carcinoma',
  'basal cell',
  'squamous',
  'malignant',
  'benign',
  'cancer',
  'cancerous',
  'nevus',
  'naevus',
  'keratosis',
  'dermatofibroma',
  'diagnosis:',
  'diagnosed',
  'tumor',
  'tumour',
] as const;

const RE = new RegExp(`\\b(${FORBIDDEN_DIAGNOSTIC_TERMS.map((t) => t.replace(/[.*+?^${}()|[\]\\:]/g, '\\$&')).join('|')})`, 'i');

export function containsDiagnosticTerm(text: string): boolean {
  return RE.test(text);
}

/**
 * Defensive filter for server-provided observation/recommendation strings
 * shown on the scan result. If a string ever contained a disease name it is
 * dropped rather than shown.
 */
export function scrubDiagnosticTerms(lines: string[]): string[] {
  return lines.filter((l) => !containsDiagnosticTerm(l));
}
