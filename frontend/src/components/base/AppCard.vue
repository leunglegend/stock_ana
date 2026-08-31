<template>
  <div
    class="app-card"
    :class="{
      'app-card--hover': hoverEffect,
      'app-card--shadow': shadow
    }"
  >
    <!-- 头部区域：有 header 或 extra 插槽时渲染 -->
    <header v-if="$slots.header || $slots.extra" class="app-card__header">
      <div class="app-card__header-title">
        <slot name="header" />
      </div>
      <div v-if="$slots.extra" class="app-card__header-extra">
        <slot name="extra" />
      </div>
    </header>

    <!-- 主体内容 -->
    <div class="app-card__body">
      <slot />
    </div>

    <!-- 底部区域：有 footer 插槽时渲染 -->
    <footer v-if="$slots.footer" class="app-card__footer">
      <slot name="footer" />
    </footer>
  </div>
</template>

<script setup>
const props = defineProps({
  hoverEffect: {
    type: Boolean,
    default: false
  },
  shadow: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.app-card {
  background: var(--surface-panel);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition:
    background-color var(--transition-fast),
    border-color var(--transition-fast),
    box-shadow var(--transition-normal);
}

.app-card--shadow {
  box-shadow: var(--shadow-card);
}

.app-card--hover:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-sm);
}

.app-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--border-subtle);
}

.app-card__header-title {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--text-primary);
}

.app-card__header-extra {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.app-card__body {
  padding: var(--spacing-5);
}

.app-card__footer {
  padding: var(--spacing-4) var(--spacing-5);
  border-top: 1px solid var(--border-subtle);
  background: var(--surface-panel-muted);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
</style>
