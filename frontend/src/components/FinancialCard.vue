<template>
  <section class="financial-card" v-loading="loading">
    <header class="financial-card__header">
      <h2 class="financial-card__title">财务</h2>
        <span v-if="financial?.report_date" class="financial-card__date">{{ financial.report_date }}</span>
    </header>

    <div v-if="financial" class="financial-card__grid">
      <article v-for="item in metrics" :key="item.label" class="financial-card__item">
        <span class="financial-card__label">{{ item.label }}</span>
        <span class="financial-card__value">{{ item.value }}</span>
      </article>
    </div>

    <div v-else class="financial-card__empty">
      <el-empty description="暂无财务数据" :image-size="60" />
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  financial: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

function formatNumber(value, suffix = '') {
  if (value === null || value === undefined || value === '') return '--'
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return '--'
  return `${numeric.toFixed(2)}${suffix}`
}

function formatYi(value) {
  return formatNumber(value, '亿')
}

const metrics = computed(() => {
  if (!props.financial) return []
  return [
    { label: '市盈率 PE', value: formatNumber(props.financial.pe) },
    { label: '市净率 PB', value: formatNumber(props.financial.pb) },
    { label: '总市值', value: formatYi(props.financial.total_mv) },
    { label: '净资产收益率 ROE', value: formatNumber(props.financial.roe, '%') },
    { label: '净利润', value: formatYi(props.financial.net_profit) },
    { label: '营业收入', value: formatYi(props.financial.revenue) },
    { label: '毛利率', value: formatNumber(props.financial.gross_margin, '%') },
    { label: '净利率', value: formatNumber(props.financial.net_margin, '%') },
  ]
})
</script>

<style scoped>
.financial-card {
  height: 100%;
  padding: var(--spacing-3);
}

.financial-card__header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: var(--spacing-3);
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--border-subtle);
}

.financial-card__date {
  margin: 0;
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}

.financial-card__title {
  margin: 0;
  color: var(--text-primary);
  font-size: var(--font-size-lg);
}

.financial-card__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0;
}

.financial-card__item {
  display: grid;
  gap: var(--spacing-1);
  padding: var(--spacing-2);
  border-top: 1px solid var(--border-subtle);
}

.financial-card__label {
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}

.financial-card__value {
  color: var(--text-primary);
  font-size: var(--font-size-xl);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.financial-card__empty {
  padding: var(--spacing-6) 0;
}

@media (max-width: 767px) {
  .financial-card__grid {
    grid-template-columns: 1fr;
  }
}
</style>
