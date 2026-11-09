import { Fragment, type ReactNode } from 'react';

/**
 * Markdown-lite renderer producing React elements only (never raw HTML).
 * Supports: paragraphs, "- " / "* " / "1. " lists, **bold**, *italic*.
 * Anything else is rendered as literal text, so it is XSS-safe by construction.
 */
export function renderInline(text: string, keyPrefix = 'i'): ReactNode[] {
  const out: ReactNode[] = [];
  const re = /(\*\*[^*]+\*\*|\*[^*\s][^*]*\*)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith('**')) out.push(<strong key={`${keyPrefix}-${i++}`}>{tok.slice(2, -2)}</strong>);
    else out.push(<em key={`${keyPrefix}-${i++}`}>{tok.slice(1, -1)}</em>);
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

type Block = { type: 'p'; lines: string[] } | { type: 'ul' | 'ol'; items: string[] };

export function parseBlocks(text: string): Block[] {
  const blocks: Block[] = [];
  let cur: Block | null = null;
  for (const raw of text.replace(/\r\n/g, '\n').split('\n')) {
    const line = raw.trim();
    const ul = /^[-*•]\s+(.*)$/.exec(line);
    const ol = /^\d+[.)]\s+(.*)$/.exec(line);
    if (!line) {
      cur = null;
      continue;
    }
    if (ul || ol) {
      const type = ul ? 'ul' : 'ol';
      const content = (ul ?? ol)![1] ?? '';
      if (!cur || cur.type !== type) {
        cur = { type, items: [] };
        blocks.push(cur);
      }
      (cur as { items: string[] }).items.push(content);
    } else {
      if (!cur || cur.type !== 'p') {
        cur = { type: 'p', lines: [] };
        blocks.push(cur);
      }
      cur.lines.push(line);
    }
  }
  return blocks;
}

export function MarkdownLite({ text, className }: { text: string; className?: string }) {
  const blocks = parseBlocks(text);
  return (
    <div className={className}>
      {blocks.map((b, bi) => {
        if (b.type === 'p')
          return (
            <p key={bi} className="mb-2 last:mb-0">
              {b.lines.map((l, li) => (
                <Fragment key={li}>
                  {li > 0 && <br />}
                  {renderInline(l, `${bi}-${li}`)}
                </Fragment>
              ))}
            </p>
          );
        const List = b.type === 'ul' ? 'ul' : 'ol';
        return (
          <List key={bi} className={`mb-2 last:mb-0 space-y-1 pl-5 ${b.type === 'ul' ? 'list-disc' : 'list-decimal'}`}>
            {b.items.map((it, ii) => (
              <li key={ii}>{renderInline(it, `${bi}-${ii}`)}</li>
            ))}
          </List>
        );
      })}
    </div>
  );
}

/** Only allow http(s) links from the server to be rendered as anchors. */
export function safeHref(url: string): string | null {
  try {
    const u = new URL(url);
    return u.protocol === 'https:' || u.protocol === 'http:' ? u.toString() : null;
  } catch {
    return null;
  }
}
