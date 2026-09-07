<template>
  <section class="market-ai__band" :aria-busy="loading">
    <span class="market-ai__label">{{ label }}</span>
    <p v-if="text" class="market-ai__text">{{ text }}</p>
    <p v-else-if="error" class="market-ai__placeholder">AI 点评暂时不可用，可稍后重试。</p>
    <p v-else class="market-ai__placeholder">需要时再触发 AI 点评。</p>
    <el-button link type="primary" :disabled="loading" @click="$emit('refresh')">
      {{ loading ? '生成中' : '展开研究' }}
    </el-button>
  </section>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    default: '',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: Boolean,
    default: false,
  },
  label: {
    type: String,
    default: 'AI 盘面结论', // 向后兼容默认
  },
})

defineEmits(['refresh'])
</script>

<style scoped>
.market-ai__band {
  display: grid;
  grid-template-columns: 108px minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--spacing-3);
  min-height: 56px;
  padding: var(--spacing-2) var(--spacing-3);
  border-block: 1px solid var(--border-subtle);
  background: var(--surface-panel-muted);
}

.market-ai__label { font-size: var(--font-size-sm); font-weight: 600; }
.market-ai__text,
.market-ai__placeholder {
  margin: 0;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 767px) {
  .market-ai__band { grid-template-columns: minmax(0, 1fr) auto; }
  .market-ai__label { display: none; }
}
</style>
