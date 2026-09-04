import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { loadSupportLocal, saveSupportLocal } from '../utils/supportPersistence'
import {
  DEFAULT_SUPPORT,
  canAutoShowInvite,
  isSnoozed,
  like,
  recordAutoInviteShown,
  setInviteSuppressed,
  setSnoozed,
  unlike,
} from '../utils/supportState'

export const useSupportStore = defineStore('support', () => {
  const state = ref(loadSupportLocal())

  const liked = computed(() => state.value.liked)
  const suppressed = computed(() => state.value.suppressInvite)
  const snoozed = computed(() => isSnoozed(state.value))

  function persist(next) {
    state.value = next
    saveSupportLocal(next)
  }

  function likeIt() {
    const next = like(state.value)
    if (next === state.value) return false
    persist(next)
    return true
  }

  function unlikeIt() {
    const next = unlike(state.value)
    if (next !== state.value) persist(next)
  }

  function takeAutoInvite() {
    if (!canAutoShowInvite(state.value)) return false
    persist(recordAutoInviteShown(state.value))
    return true
  }

  function suppressInvites() {
    persist(setInviteSuppressed(state.value))
  }

  function snoozeDays(days = 30) {
    persist(setSnoozed(state.value, Date.now() + days * 24 * 60 * 60 * 1000))
  }

  return {
    state,
    liked,
    suppressed,
    snoozed,
    likeIt,
    unlikeIt,
    takeAutoInvite,
    suppressInvites,
    snoozeDays,
  }
})
