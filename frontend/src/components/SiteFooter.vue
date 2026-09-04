<template>
  <footer class="site-footer">
    <div class="site-footer__disclaimer">
      <span class="site-footer__name">{{ SUPPORT_COPY.footerSiteName }}</span>
      <span class="site-footer__muted">{{ SUPPORT_COPY.footerDisclaimer }}</span>
    </div>

    <button
      type="button"
      class="site-footer__tip"
      :aria-label="SUPPORT_COPY.footerTipAria"
      @click="ui.open()"
    >
      {{ SUPPORT_COPY.footerTipEntry }}
    </button>

    <TipSupportDialog v-model:visible="ui.visible" />
  </footer>
</template>

<script setup>
import { SUPPORT_COPY } from './support/supportCopy'
import { useSupportUi } from './support/useSupportUi'
import TipSupportDialog from './support/TipSupportDialog.vue'

const ui = useSupportUi()
</script>

<style scoped>
.site-footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-1) var(--spacing-4);
  flex: 0 0 auto;
  padding: var(--spacing-2) var(--spacing-4) var(--spacing-3);
  border-top: 1px solid var(--border-subtle);
  font-size: var(--font-size-xs);
  line-height: var(--line-height-normal);
  color: var(--text-tertiary);
}

.site-footer__disclaimer {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  min-width: 0;
}

.site-footer__name {
  color: var(--text-secondary);
  font-weight: 500;
  white-space: nowrap;
}

.site-footer__tip {
  appearance: none;
  border: 0;
  background: transparent;
  padding: var(--spacing-1) 0;
  font: inherit;
  color: var(--text-tertiary);
  white-space: nowrap;
  cursor: pointer;
  transition: color var(--transition-fast);
}

.site-footer__tip:hover {
  color: var(--text-link);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.site-footer__tip:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
  border-radius: var(--radius-xs);
}

@media (min-width: 768px) and (max-width: 1023px) {
  .site-footer {
    padding-inline: var(--spacing-3);
  }
}

@media (max-width: 767px) {
  .site-footer {
    padding-inline: var(--spacing-2);
  }
}
</style>
