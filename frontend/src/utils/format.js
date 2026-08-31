export function safeNumber(value, fallback = null) {
  if (value == null || typeof value === 'boolean') return fallback
  if (typeof value === 'string' && value.trim() === '') return fallback
  const num = Number(value)
  return Number.isFinite(num) ? num : fallback
}

export function isDisplayValueMissing(value) {
  return value == null || (typeof value === 'string' && value.trim() === '')
}

const pad2 = (value) => value.toString().padStart(2, '0')

function formatSigned(value, decimals, suffix = '') {
  const num = safeNumber(value)
  if (num == null) return '--'
  const sign = num > 0 ? '+' : ''
  return `${sign}${num.toFixed(decimals)}${suffix}`
}

function formatLargeNumber(value, smallUnit = '') {
  const num = safeNumber(value)
  if (num == null) return '--'
  const abs = Math.abs(num)
  if (abs >= 100000000) return `${(num / 100000000).toFixed(2)}亿`
  if (abs >= 10000) return `${(num / 10000).toFixed(2)}万`
  return `${num}${smallUnit}`
}

function normalizeTimestampNumber(value) {
  if (!Number.isFinite(value)) return null
  const abs = Math.abs(value)
  if (Number.isInteger(value) && abs >= 100000000 && abs < 10000000000) {
    return value * 1000
  }
  return value
}

function parseDateValue(value) {
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value
  if (typeof value === 'number') {
    const timestamp = normalizeTimestampNumber(value)
    if (timestamp == null) return null
    const date = new Date(timestamp)
    return Number.isNaN(date.getTime()) ? null : date
  }
  if (typeof value !== 'string') return null
  const trimmed = value.trim()
  if (!trimmed) return null
  const dateInput = /^-?\d+$/.test(trimmed)
    ? normalizeTimestampNumber(Number(trimmed))
    : trimmed
  const date = new Date(dateInput)
  return Number.isNaN(date.getTime()) ? null : date
}

function formatDateParts(date) {
  return {
    year: date.getFullYear(),
    month: pad2(date.getMonth() + 1),
    day: pad2(date.getDate()),
    hour: pad2(date.getHours()),
    minute: pad2(date.getMinutes()),
    second: pad2(date.getSeconds()),
  }
}

export function formatPrice(value, decimals = 2) {
  const num = safeNumber(value)
  return num == null ? '--' : num.toFixed(decimals)
}

export function formatChangePct(value) {
  return formatSigned(value, 2, '%')
}

export function formatChangeAmount(value) {
  return formatSigned(value, 2)
}

export function formatVolume(value) {
  return formatLargeNumber(value)
}

export function formatAmount(amount) {
  const num = safeNumber(amount)
  if (num == null) return '--'
  if (num === 0) return '0'
  return formatLargeNumber(num, '元')
}

export function formatYi(value) {
  const num = safeNumber(value)
  return num == null ? '--' : `${num.toFixed(2)}亿`
}

export function formatMv(value) {
  const num = safeNumber(value)
  if (num == null) return '--'
  return Math.abs(num) >= 10000 ? `${(num / 10000).toFixed(2)}万亿` : `${num.toFixed(2)}亿`
}

export function formatPercent(value, decimals = 2, withSign = true) {
  const num = safeNumber(value)
  if (num == null) return '--'
  const sign = withSign && num > 0 ? '+' : ''
  return `${sign}${num.toFixed(decimals)}%`
}

export function formatThousands(value) {
  const num = safeNumber(value)
  return num == null ? '--' : num.toLocaleString('en-US')
}

export function formatDateTime(value) {
  const date = parseDateValue(value)
  if (!date) return '--'
  const { year, month, day, hour, minute } = formatDateParts(date)
  return `${year}-${month}-${day} ${hour}:${minute}`
}

export function formatDateShort(value) {
  const date = parseDateValue(value)
  if (!date) return '--'
  const { month, day } = formatDateParts(date)
  return `${month}-${day}`
}

export function formatDateTimeShort(value) {
  const date = parseDateValue(value)
  if (!date) return '--'
  const { month, day, hour, minute } = formatDateParts(date)
  return `${month}-${day} ${hour}:${minute}`
}

export function formatRelativeTime(value) {
  const date = parseDateValue(value)
  if (!date) return ''
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (date.toDateString() === now.toDateString()) return `今天 ${pad2(date.getHours())}:${pad2(date.getMinutes())}`
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) return `昨天 ${pad2(date.getHours())}:${pad2(date.getMinutes())}`
  if (diff < 7 * 86400000) return `${Math.floor(diff / 86400000)}天前`
  const { year, month, day } = formatDateParts(date)
  return `${year}-${month}-${day}`
}

export function formatFetchTime(value) {
  const date = parseDateValue(value)
  if (!date) return '--'
  const { hour, minute, second } = formatDateParts(date)
  return date.toDateString() === new Date().toDateString()
    ? `${hour}:${minute}:${second}`
    : formatDateTimeShort(date)
}

export function calculateRiseRatio(riseCount, fallCount, flatCount) {
  const rise = safeNumber(riseCount)
  const fall = safeNumber(fallCount)
  const flat = safeNumber(flatCount)
  if (rise == null || fall == null || flat == null) return null
  const total = rise + fall + flat
  if (total === 0) return null
  return Number(((rise / total) * 100).toFixed(2))
}

export const ratingConfig = {
  '强烈买入': { color: '#dc2626', bgColor: '#fef2f2', borderColor: '#fecaca' },
  '买入': { color: '#ef4444', bgColor: '#fef2f2', borderColor: '#fecaca' },
  '观望': { color: '#d97706', bgColor: '#fffbeb', borderColor: '#fde68a' },
  '减仓': { color: '#059669', bgColor: '#ecfdf5', borderColor: '#a7f3d0' },
  '卖出': { color: '#10b981', bgColor: '#ecfdf5', borderColor: '#a7f3d0' },
}

export function getRatingStyle(rating) {
  return ratingConfig[rating] || ratingConfig['观望']
}

export function truncateText(text, maxLen) {
  if (!text) return ''
  return text.length <= maxLen ? text : `${text.substring(0, maxLen)}...`
}

export function extractScoreFromText(text) {
  if (!text) return null
  const match = text.match(/```json\s*([\s\S]*?)\s*```/)
  if (!match) return null
  try {
    const data = JSON.parse(match[1].trim())
    return typeof data.score === 'number' && data.score >= 0 && data.score <= 100 ? data : null
  } catch {
    return null
  }
}

export function cleanJsonBlock(text) {
  if (!text) return ''
  return text.replace(/```json\s*[\s\S]*?```\s*/, '').trim()
}

export function changeClass(value) {
  const num = safeNumber(value)
  if (num == null || num === 0) return ''
  return num > 0 ? 'text-up' : 'text-down'
}

export function changeColor(value) {
  const num = safeNumber(value)
  if (num == null || num === 0) return '#6b7280'
  return num > 0 ? '#ef4444' : '#10b981'
}

export function formatChange(value, decimals = 2) {
  return formatSigned(value, decimals)
}

export function formatDate(value, format = 'YYYY-MM-DD') {
  const date = parseDateValue(value)
  if (!date) return '--'
  const parts = formatDateParts(date)
  return format
    .replace('YYYY', parts.year)
    .replace('MM', parts.month)
    .replace('DD', parts.day)
    .replace('HH', parts.hour)
    .replace('mm', parts.minute)
    .replace('ss', parts.second)
}

export function formatTime(value) {
  const date = parseDateValue(value)
  if (!date) return '--'
  const { hour, minute, second } = formatDateParts(date)
  return `${hour}:${minute}:${second}`
}

export function getRatingType(rating) {
  if (!rating || typeof rating !== 'string') return 'default'
  const normalized = rating.trim().toUpperCase()
  if (normalized.startsWith('A')) return 'success'
  if (normalized.startsWith('B')) return 'info'
  if (normalized.startsWith('C')) return 'warning'
  if (normalized.startsWith('D')) return 'danger'
  return 'default'
}

export function thousandsSeparator(value) {
  return formatThousands(value)
}

export function formatMarketValue(value) {
  return formatMv(value)
}

export function formatPE(value) {
  const num = safeNumber(value)
  if (num == null || num <= 0) return '--'
  return num.toFixed(2)
}
