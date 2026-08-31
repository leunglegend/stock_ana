export const DEFAULT_THEME = 'ocean'
export const THEME_CHANGE_EVENT = 'app-theme-change'
export const THEME_STORAGE_KEY = 'stock-analyzer-theme'

export const THEMES = Object.freeze([
  { key: 'ocean', name: '深海蓝 × 金色', colors: ['#172a3d', '#d9a441', '#f4f6f8'] },
  { key: 'jade', name: '墨绿 × 琥珀', colors: ['#133f3a', '#e7a43b', '#edf4f1'] },
  { key: 'charcoal', name: '炭黑 × 朱砂', colors: ['#262b33', '#b8583e', '#f5f3ef'] },
])

const themeKeys = new Set(THEMES.map(({ key }) => key))

export function resolveTheme(value) {
  return themeKeys.has(value) ? value : DEFAULT_THEME
}

export function loadTheme(storage = globalThis.localStorage) {
  try {
    return resolveTheme(storage?.getItem(THEME_STORAGE_KEY))
  } catch {
    return DEFAULT_THEME
  }
}

export function applyTheme(theme, options = {}) {
  const resolved = resolveTheme(theme)
  const root = options.root ?? globalThis.document?.documentElement
  const storage = options.storage ?? globalThis.localStorage
  const dispatch = options.dispatch ?? globalThis.dispatchEvent?.bind(globalThis)
  const createEvent = options.createEvent ?? ((type, detail) => new CustomEvent(type, { detail }))

  if (root) root.dataset.theme = resolved
  try {
    storage?.setItem(THEME_STORAGE_KEY, resolved)
  } catch {}
  dispatch?.(createEvent(THEME_CHANGE_EVENT, { theme: resolved }))
  return resolved
}

export function initializeTheme(options = {}) {
  const theme = loadTheme(options.storage ?? globalThis.localStorage)
  return applyTheme(theme, options)
}
