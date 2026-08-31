<template>
  <section :class="['section-panel', `section-panel--${variant}`]">
    <header v-if="$slots.header" class="section-panel__header">
      <slot name="header" />
    </header>

    <div class="section-panel__body">
      <slot />
    </div>

    <footer v-if="$slots.footer" class="section-panel__footer">
      <slot name="footer" />
    </footer>
  </section>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'standard',
    validator: (value) => ['standard', 'flush', 'overlay'].includes(value),
  },
})
</script>

<style scoped>
.section-panel {
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--surface-panel);
  border: 1px solid var(--border-default);
  border-radius: 0;
  box-shadow: none;
  overflow: hidden;
}

.section-panel__header,
.section-panel__footer {
  padding: var(--spacing-2) var(--panel-padding-inline);
}

.section-panel__header {
  min-height: var(--table-head-height);
  border-bottom: 1px solid var(--border-subtle);
}

.section-panel__body {
  flex: 1;
  min-width: 0;
  padding: var(--panel-padding-block) var(--panel-padding-inline);
}

.section-panel__footer {
  border-top: 1px solid var(--border-subtle);
  background-color: var(--surface-panel-muted);
}

.section-panel--flush > .section-panel__body {
  padding: 0;
}

.section-panel--overlay {
  border-radius: var(--radius-overlay);
  box-shadow: var(--shadow-overlay);
}

@media (max-width: 767px) {
  .section-panel__header,
  .section-panel__footer {
    padding-inline: var(--spacing-3);
  }
}
</style>
