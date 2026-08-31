import { marked } from 'marked'

const ALLOWED_TAGS = new Set(['p', 'br', 'strong', 'em', 'del', 'code', 'pre', 'blockquote', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'hr'])
const SAFE_PROTOCOLS = new Set(['http:', 'https:'])

function escapeHtml(value = '') {
  return String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char])
}

function safeHref(value = '') {
  try { return SAFE_PROTOCOLS.has(new URL(value, 'https://local.invalid').protocol) ? value : '' } catch { return '' }
}

const renderer = new marked.Renderer()
renderer.html = ({ text }) => escapeHtml(text)
renderer.link = ({ href, title, tokens }) => {
  const label = renderer.parser.parseInline(tokens)
  const safe = safeHref(href)
  if (!safe) return label
  const titleAttr = title ? ` title="${escapeHtml(title)}"` : ''
  return `<a href="${escapeHtml(safe)}"${titleAttr} target="_blank" rel="noopener noreferrer">${label}</a>`
}

function sanitizeWithDom(html) {
  const parsed = new DOMParser().parseFromString(`<body>${html}</body>`, 'text/html')
  for (const element of [...parsed.body.querySelectorAll('*')]) {
    const tag = element.tagName.toLowerCase()
    if (!ALLOWED_TAGS.has(tag)) { element.replaceWith(parsed.createTextNode(element.outerHTML)); continue }
    for (const attribute of [...element.attributes]) {
      const name = attribute.name.toLowerCase()
      const allowed = tag === 'a' && ['href', 'title', 'target', 'rel'].includes(name)
      if (!allowed || (name === 'href' && !safeHref(attribute.value))) element.removeAttribute(attribute.name)
    }
  }
  return parsed.body.innerHTML
}

export function renderSafeMarkdown(text) {
  if (!text) return ''
  const html = marked.parse(String(text), { renderer, async: false })
  return typeof DOMParser === 'undefined' ? html : sanitizeWithDom(html)
}

export const stripScoreBlock = (text) => String(text || '').replace(/```json\s*[\s\S]*?```\s*/i, '').trim()
export function parseScoreBlock(text) {
  const match = String(text || '').match(/```json\s*([\s\S]*?)\s*```/i)
  if (!match) return null
  try { const value = JSON.parse(match[1]); return Number.isFinite(value.score) && value.score >= 0 && value.score <= 100 ? value : null } catch { return null }
}
