<template>
  <div
    class="status-state"
    :class="`status-state--${state}`"
    :style="containerStyle"
    :aria-live="ariaLive"
    :role="state === 'error' ? 'alert' : 'status'"
  >
    <div class="status-state__inner">
      <div class="status-state__icon">
        <el-icon :size="26" :class="{ 'is-loading': state === 'loading' }">
          <component :is="iconName" />
        </el-icon>
      </div>

      <p class="status-state__title">{{ resolvedTitle }}</p>
      <p class="status-state__description">{{ resolvedDescription }}</p>

      <div class="status-state__action">
        <slot name="action">
          <el-button v-if="state === 'error'" type="primary" plain @click="$emit('retry')">
            重试
          </el-button>
        </slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  state: {
    type: String,
    required: true,
    validator: (value) => ['loading', 'empty', 'error'].includes(value),
  },
  title: {
    type: String,
    default: '',
  },
  description: {
    type: String,
    default: '',
  },
  minHeight: {
    type: [Number, String],
    default: 180,
  },
})

defineEmits(['retry'])

const fallbackTitle = {
  loading: '加载中',
  empty: '暂无数据',
  error: '加载失败',
}

const fallbackDescription = {
  loading: '正在获取最新内容，请稍候。',
  empty: '当前没有可展示的数据。',
  error: '请求未完成，可以稍后重试。',
}

const iconName = computed(() => {
  if (props.state === 'loading') return 'Loading'
  return props.state === 'empty' ? 'DocumentRemove' : 'WarningFilled'
})

const resolvedTitle = computed(() => props.title || fallbackTitle[props.state])
const resolvedDescription = computed(() => props.description || fallbackDescription[props.state])
const ariaLive = computed(() => (props.state === 'error' ? 'assertive' : 'polite'))
const containerStyle = computed(() => ({
  minHeight: typeof props.minHeight === 'number' ? `${props.minHeight}px` : props.minHeight,
}))
</script>

<style scoped>
.status-state {
  display: grid;
  place-items: center;
  width: 100%;
  padding: var(--spacing-6);
  border-radius: var(--radius-md);
  background: var(--color-gray-50);
}

.status-state__inner {
  display: grid;
  justify-items: center;
  gap: var(--spacing-3);
  max-width: 320px;
  text-align: center;
}

.status-state__icon {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background-color: var(--surface-canvas);
  color: var(--color-info-dark);
  box-shadow: inset 0 0 0 1px var(--border-default);
}

.status-state--empty .status-state__icon {
  color: var(--color-gray-500);
}

.status-state--error .status-state__icon {
  color: var(--color-up-dark);
}

.status-state__title {
  color: var(--color-gray-800);
  font-size: var(--font-size-lg);
  font-weight: 600;
  line-height: var(--line-height-tight);
}

.status-state__description {
  color: var(--color-gray-500);
  font-size: var(--font-size-base);
  line-height: var(--line-height-relaxed);
}

.status-state__action {
  min-height: 32px;
}

@media (prefers-reduced-motion: reduce) {
  .is-loading {
    animation: none;
  }
}
</style>
