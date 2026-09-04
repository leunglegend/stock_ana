export const DEFAULT_SUPPORT = {
  version: 1,
  liked: false,
  likedAt: null,
  inviteAutoShown: 0,
  lastInviteAt: null,
  suppressInvite: false,
  snoozedUntil: null,
}

const AUTO_INVITE_LIMIT = 3

export function like(state, now = Date.now()) {
  if (state.liked) return state
  return { ...state, liked: true, likedAt: now }
}

export function unlike(state) {
  if (!state.liked) return state
  return { ...state, liked: false, likedAt: null }
}

function sameLocalDay(a, b) {
  return a.getFullYear() === b.getFullYear()
    && a.getMonth() === b.getMonth()
    && a.getDate() === b.getDate()
}

export function canAutoShowInvite(state, now = Date.now()) {
  if (state.suppressInvite) return false
  if (state.inviteAutoShown >= AUTO_INVITE_LIMIT) return false
  if (state.lastInviteAt && sameLocalDay(new Date(state.lastInviteAt), new Date(now))) return false
  return true
}

export function recordAutoInviteShown(state, now = Date.now()) {
  return { ...state, inviteAutoShown: state.inviteAutoShown + 1, lastInviteAt: now }
}

export function setInviteSuppressed(state) {
  if (state.suppressInvite) return state
  return { ...state, suppressInvite: true }
}

export function setSnoozed(state, untilTs) {
  return { ...state, snoozedUntil: untilTs }
}

export function isSnoozed(state, now = Date.now()) {
  return !!(state.snoozedUntil && state.snoozedUntil > now)
}
