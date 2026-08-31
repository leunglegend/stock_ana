<template>
  <section class="signal-center" aria-label="自选待处理">
    <header class="signal-center__head">
      <div>
        <h2>待处理</h2>
        <span>{{ scanMeta }}</span>
      </div>
      <el-button link type="primary" :loading="scanning" :disabled="stockCount === 0" @click="$emit('scan')">
        {{ results.length ? '重新扫描' : '扫描' }}
      </el-button>
    </header>

    <div class="signal-center__stats" aria-label="信号扫描汇总">
      <span><b>{{ summary.strong }}</b>偏强</span>
      <span><b>{{ summary.attention }}</b>关注</span>
      <span><b>{{ summary.neutral }}</b>中性</span>
      <span><b>{{ summary.error }}</b>失败</span>
    </div>

    <div v-if="scanning" class="signal-center__progress" aria-live="polite">
      <el-progress :percentage="progress" :stroke-width="4" :show-text="false" />
      <span>{{ completed }} / {{ stockCount }}</span>
    </div>

    <div v-else-if="visibleResults.length" class="signal-center__todos" role="list">
      <article v-for="(item, index) in visibleResults" :key="item.code" class="signal-center__todo" role="listitem">
        <div class="signal-center__todo-top">
          <strong>{{ String(index + 1).padStart(2, '0') }} {{ item.name }}</strong>
          <span :class="movementClass(item.code)">{{ changeLabel(item.code) }}</span>
        </div>
        <p>{{ itemDetail(item) }}</p>
      </article>
    </div>

    <p v-else class="signal-center__empty">{{ stockCount ? '尚未扫描当前分组' : '当前分组没有可扫描股票' }}</p>

    <footer v-if="results.length" class="signal-center__footer">
      <span>另有 {{ hiddenCount }} 只已完成扫描</span>
    </footer>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { formatFetchTime, formatPercent } from '@/utils/format'

const props = defineProps({
  results: { type: Array, default: () => [] },
  summary: { type: Object, required: true },
  scanning: { type: Boolean, default: false },
  completed: { type: Number, default: 0 },
  progress: { type: Number, default: 0 },
  stockCount: { type: Number, default: 0 },
  lastScannedAt: { type: [Number, Date, String], default: null },
  quoteRows: { type: Array, default: () => [] },
})

defineEmits(['scan'])

const priority = { attention: 0, strong: 1, neutral: 2, loading: 3, error: 4 }
const quoteMap = computed(() => new Map(props.quoteRows.map((row) => [row.code, row])))
const orderedResults = computed(() => props.results.slice().sort((left, right) => resultPriority(left) - resultPriority(right)))
const visibleResults = computed(() => orderedResults.value.slice(0, 3))
const hiddenCount = computed(() => Math.max(orderedResults.value.length - visibleResults.value.length, 0))
const scanMeta = computed(() => props.lastScannedAt ? '扫描于 ' + formatFetchTime(props.lastScannedAt) : '扫描当前分组')

function resultPriority(item) {
  return item.status === 'success' ? priority[item.analysis?.status] : priority[item.status]
}

function changeLabel(code) {
  const change = quoteMap.value.get(code)?.changePct
  return change == null ? '--' : formatPercent(change)
}

function movementClass(code) {
  const change = quoteMap.value.get(code)?.changePct
  if (change > 0) return 'is-up'
  if (change < 0) return 'is-down'
  return ''
}

function itemDetail(item) {
  if (item.status === 'error') return 'K 线读取失败，需要重新确认技术状态。'
  if (item.status === 'loading') return '正在读取 K 线数据。'
  return item.analysis?.signals?.[0]?.detail || item.analysis?.note || '当前没有额外技术信号。'
}
</script>

<style scoped>
.signal-center { display: flex; flex-direction: column; min-height: 100%; background: var(--surface-panel); }
.signal-center__head { display: flex; align-items: center; justify-content: space-between; min-height: 40px; padding: 0 var(--spacing-3); border-bottom: 1px solid var(--border-subtle); }
.signal-center__head h2 { margin: 0; color: var(--text-primary); font-size: var(--font-size-base); }
.signal-center__head span { margin-left: var(--spacing-2); color: var(--text-tertiary); font-size: var(--font-size-xs); }
.signal-center__stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); min-height: 40px; border-bottom: 1px solid var(--border-subtle); }
.signal-center__stats span { display: grid; place-items: center; gap: 2px; border-right: 1px solid var(--border-subtle); color: var(--text-tertiary); font-size: var(--font-size-xs); }
.signal-center__stats span:last-child { border-right: 0; }
.signal-center__stats b { color: var(--text-primary); font-family: var(--font-family-mono); font-size: var(--font-size-base); }
.signal-center__progress { display: flex; align-items: center; gap: var(--spacing-2); padding: var(--spacing-3); color: var(--text-tertiary); font-family: var(--font-family-mono); font-size: var(--font-size-xs); }
.signal-center__progress :deep(.el-progress) { flex: 1; }
.signal-center__todos { display: grid; }
.signal-center__todo { min-height: 66px; padding: var(--spacing-2) var(--spacing-3); border-bottom: 1px solid var(--border-subtle); }
.signal-center__todo-top { display: flex; align-items: center; justify-content: space-between; gap: var(--spacing-2); font-family: var(--font-family-mono); font-size: var(--font-size-xs); }
.signal-center__todo strong { overflow: hidden; color: var(--text-primary); font-family: var(--font-family-base); font-size: var(--font-size-sm); text-overflow: ellipsis; white-space: nowrap; }
.signal-center__todo p { margin: 4px 0 0; color: var(--text-secondary); font-size: var(--font-size-xs); line-height: 1.45; }
.signal-center__empty { margin: 0; padding: var(--spacing-4) var(--spacing-3); color: var(--text-tertiary); font-size: var(--font-size-sm); text-align: center; }
.signal-center__footer { display: flex; align-items: center; min-height: 40px; padding: 0 var(--spacing-3); margin-top: auto; border-top: 1px solid var(--border-subtle); color: var(--text-tertiary); font-size: var(--font-size-xs); }
.is-up { color: var(--text-positive); }
.is-down { color: var(--text-negative); }
@media (max-width: 767px) {
  .signal-center__head { min-height: 44px; }
  .signal-center__todo { min-height: 68px; }
}
</style>
