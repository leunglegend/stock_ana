<template>
  <div v-if="!supportStore.snoozed" class="support-entry">
    <button
      type="button"
      class="support-btn"
      :class="{ 'support-btn--liked': supportStore.liked }"
      :aria-pressed="supportStore.liked"
      :title="supportStore.liked ? SUPPORT_COPY.entryTitleLiked : SUPPORT_COPY.entryTitleIdle"
      @click="handleToggle"
    >
      <svg
        class="support-btn__thumb"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3z" />
        <path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
      </svg>
      <span v-if="isDesktop" class="support-btn__label">
        {{ supportStore.liked ? SUPPORT_COPY.labelLiked : SUPPORT_COPY.labelIdle }}
      </span>
    </button>

    <button
      v-if="panelOpen"
      type="button"
      class="support-confirm__scrim"
      tabindex="-1"
      aria-hidden="true"
      @click="closePanel"
    ></button>

    <div v-if="panelOpen" class="support-confirm" role="dialog" aria-label="点赞确认卡">
      <p class="support-confirm__head">{{ SUPPORT_COPY.confirmHead }}</p>
      <p class="support-confirm__sub">{{ SUPPORT_COPY.confirmSub }}</p>
      <p class="support-confirm__note">{{ SUPPORT_COPY.confirmLocalNote }}</p>

      <template v-if="bigInvite">
        <p class="support-confirm__invite-text">{{ SUPPORT_COPY.inviteLead }}</p>
        <div class="support-confirm__actions">
          <el-button type="primary" size="small" @click="openTip">
            {{ SUPPORT_COPY.inviteAction }}
          </el-button>
          <el-button text size="small" @click="closePanel">
            {{ SUPPORT_COPY.inviteDecline }}
          </el-button>
        </div>
      </template>
      <button v-else-if="showGhostInvite" type="button" class="support-confirm__ghost" @click="openTip">
        {{ SUPPORT_COPY.inviteGhost }}
      </button>

      <div class="support-confirm__links">
        <button v-if="supportStore.liked" type="button" @click="revoke">
          {{ SUPPORT_COPY.revokeAction }}
        </button>
        <button v-if="!supportStore.suppressed" type="button" @click="suppress">
          {{ SUPPORT_COPY.suppressAction }}
        </button>
        <button type="button" @click="snooze">
          {{ SUPPORT_COPY.snoozeAction }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, ref } from 'vue'
import { useResponsive } from '@/composables/useResponsive'
import { useSupportStore } from '@/store/support'
import { SUPPORT_COPY } from '../support/supportCopy'
import { useSupportUi } from '../support/useSupportUi'

const supportStore = useSupportStore()
const ui = useSupportUi()
const { isDesktop } = useResponsive()

const panelOpen = ref(false)
const bigInvite = ref(false)        // 刚点亮且拿到自动配额 → 大号「顺带增资?」
const showGhostInvite = ref(false)  // 手动进卡 / 配额耗尽 → 小号幽灵入口

function onKeydown(e) {
  if (e.key === 'Escape') closePanel()
}
function removeKeydown() {
  window.removeEventListener('keydown', onKeydown)
}
function closePanel() {
  panelOpen.value = false
  bigInvite.value = false
  showGhostInvite.value = false
  removeKeydown()
}
async function openPanel() {
  panelOpen.value = true
  await nextTick()
  window.addEventListener('keydown', onKeydown)
}

function handleToggle() {
  if (panelOpen.value) {
    closePanel()
    return
  }
  if (supportStore.liked) {
    // 手动点开已点亮:只给幽灵小入口,不消耗自动配额
    bigInvite.value = false
    showGhostInvite.value = !supportStore.suppressed
    openPanel()
    return
  }
  const becameLiked = supportStore.likeIt()
  if (!becameLiked) return
  bigInvite.value = supportStore.takeAutoInvite()
  showGhostInvite.value = !bigInvite.value && !supportStore.suppressed
  openPanel()
}

function revoke() {
  supportStore.unlikeIt()
  closePanel()
}
function suppress() {
  supportStore.suppressInvites()
  closePanel()
}
function snooze() {
  supportStore.snoozeDays(30)
  closePanel()
}
function openTip() {
  closePanel()
  ui.open()
}

onBeforeUnmount(removeKeydown)
</script>

<style scoped>
.support-entry {
  position: relative;
  display: inline-flex;
}

.support-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-1);
  height: 44px;
  padding: 0 var(--spacing-1);
  border: 0;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius-md);
  transition:
    background var(--transition-fast),
    color var(--transition-fast);
}

.support-btn:hover {
  background: var(--surface-panel-muted);
}

.support-btn--liked {
  color: var(--color-support);
}

.support-btn--liked .support-btn__thumb {
  fill: currentColor;
}

.support-btn__thumb {
  width: 20px;
  height: 20px;
  flex: 0 0 auto;
}

.support-btn__label {
  font-size: var(--font-size-xs);
  line-height: 1;
  color: inherit;
  white-space: nowrap;
}

.support-btn:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 1px;
  border-radius: var(--radius-md);
}

.support-confirm {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: var(--z-dropdown);
  box-sizing: border-box;
  width: min(340px, calc(100vw - 16px));
  display: grid;
  gap: var(--spacing-2);
  padding: var(--spacing-3);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-overlay);
  text-align: left;
}

.support-confirm__scrim {
  position: fixed;
  inset: 0;
  z-index: calc(var(--z-dropdown) - 1);
  background: transparent;
  border: 0;
  cursor: default;
}

.support-confirm__head {
  margin: 0;
  font-size: var(--font-size-base);
  font-weight: 600;
  line-height: var(--line-height-tight);
  color: var(--text-primary);
}

.support-confirm__sub {
  margin: 0;
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
  color: var(--text-secondary);
}

.support-confirm__note {
  margin: 0;
  font-size: var(--font-size-xs);
  line-height: var(--line-height-normal);
  color: var(--text-tertiary);
}

.support-confirm__invite-text {
  margin: var(--spacing-1) 0 0;
  padding-top: var(--spacing-2);
  border-top: 1px solid var(--border-subtle);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
  color: var(--text-secondary);
}

.support-confirm__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.support-confirm__ghost {
  margin-top: var(--spacing-1);
  padding: var(--spacing-1) 0;
  appearance: none;
  border: 0;
  background: none;
  font: inherit;
  font-size: var(--font-size-sm);
  color: var(--text-link);
  cursor: pointer;
  text-align: left;
}

.support-confirm__ghost:hover {
  text-decoration: underline;
  text-underline-offset: 2px;
}

.support-confirm__links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-1) var(--spacing-4);
  margin-top: var(--spacing-1);
  padding-top: var(--spacing-2);
  border-top: 1px dashed var(--border-subtle);
}

.support-confirm__links button {
  padding: 0;
  appearance: none;
  border: 0;
  background: none;
  font: inherit;
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  cursor: pointer;
}

.support-confirm__links button:hover {
  color: var(--text-link);
}

.support-confirm__ghost:focus-visible,
.support-confirm__links button:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
  border-radius: var(--radius-xs);
}
</style>
