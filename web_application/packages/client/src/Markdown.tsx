/**
 * Markdown, rendered and then sanitised.
 *
 * Every string this renders came from somewhere else: a position somebody else
 * wrote, a README in a project shared on this server, a file in a workspace.
 * Rendering untrusted markdown is a way to run untrusted script, so the output
 * goes through DOMPurify before it reaches the page, and the allowed set is
 * named rather than inherited.
 *
 * Two things are deliberately not allowed:
 *
 *   **No raw HTML passthrough beyond the sanitiser's set.** `marked` will emit
 *   inline HTML, and a document is not a place to run someone's markup.
 *
 *   **No remote images.** An `<img>` pointing at another host tells that host
 *   who read the document and when. A record you can read without anybody
 *   learning that you read it is worth more than an inline figure, and
 *   material held here is served from here.
 */

import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { useMemo } from 'react'

marked.setOptions({ gfm: true, breaks: false })

const ALLOWED_TAGS = [
  'p', 'br', 'hr',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'strong', 'em', 'del', 'code', 'pre', 'blockquote',
  'ul', 'ol', 'li',
  'table', 'thead', 'tbody', 'tr', 'th', 'td',
  'a', 'img', 'span',
]

/** Only same-origin images. A remote one is a read receipt. */
DOMPurify.addHook('afterSanitizeAttributes', (node) => {
  if (node.tagName === 'IMG') {
    const src = node.getAttribute('src') ?? ''
    if (/^[a-z][a-z0-9+.-]*:/i.test(src) && !src.startsWith('data:image/')) {
      node.removeAttribute('src')
      node.setAttribute('alt', `${node.getAttribute('alt') ?? ''} (remote image not loaded)`.trim())
    }
  }
  if (node.tagName === 'A' && node.hasAttribute('href')) {
    // Links out are fine to follow; they are not fine to leak a referrer to.
    node.setAttribute('rel', 'noreferrer noopener')
    node.setAttribute('target', '_blank')
  }
})

export function Markdown({ source, className = '' }: { source: string; className?: string }) {
  const html = useMemo(() => {
    const rendered = marked.parse(source ?? '', { async: false }) as string
    return DOMPurify.sanitize(rendered, {
      ALLOWED_TAGS,
      ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'colspan', 'rowspan', 'align'],
      ALLOW_DATA_ATTR: false,
    })
  }, [source])

  // The string has been through the sanitiser above; this is the one place in
  // the client allowed to set HTML, and it is the reason that hook exists.
  return <div className={`md ${className}`.trim()} dangerouslySetInnerHTML={{ __html: html }} />
}
