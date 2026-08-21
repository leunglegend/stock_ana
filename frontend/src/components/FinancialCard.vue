<template>
  <el-card class="financial-card card-shadow" v-loading="loading">
    <template #header>
      <div class="card-header">
        <el-icon><DataAnalysis /></el-icon>
        <span>财务指标</span>
        <span v-if="financial?.report_date" class="report-date">
          {{ financial.report_date }}
        </span>
      </div>
    </template>

    <div v-if="financial" class="financial-grid">
      <div class="fin-item">
        <div class="fin-label">市盈率 (PE)</div>
        <div class="fin-value" :class="peClass">
          {{ formatValue(financial.pe) }}
          <span v-if="financial.pe" class="unit">倍</span>
        </div>
        <div class="fin-tip">{{ getPeTip(financial.pe) }}</div>
      </div>

      <div class="fin-item">
        <div class="fin-label">市净率 (PB)</div>
        <div class="fin-value">
          {{ formatValue(financial.pb) }}
          <span v-if="financial.pb" class="unit">倍</span>
        </div>
      </div>

      <div class="fin-item">
        <div class="fin-label">总市值</div>
        <div class="fin-value">
          {{ formatMv(financial.total_mv) }}
        </div>
      </div>

      <div class="fin-item">
        <div class="fin-label">净资产收益率 (ROE)</div>
        <div class="fin-value" :class="roeClass">
          {{ formatValue(financial.roe) }}
          <span v-if="financial.roe" class="unit">%</span>
        </div>
      </div>

      <div class="fin-item">
        <div class="fin-label">净利润</div>
        <div class="fin-value">
          {{ formatYi(financial.net_profit) }}
        </div>
      </div>

      <div class="fin-item">
        <div class="fin-label">营业收入</div>
        <div class="fin-value">
          {{ formatYi(financial.revenue) }}
        </div>
      </div>

      <div class="fin-item">
        <div class="fin-label">毛利率</div>
        <div class="fin-value">
          {{ formatValue(financial.gross_margin) }}
          <span v-if="financial.gross_margin" class="unit">%</span>
        </div>
      </div>

      <div class="fin-item">
        <div class="fin-label">净利率</div>
        <div class="fin-value">
          {{ formatValue(financial.net_margin) }}
          <span v-if="financial.net_margin" class="unit">%</span>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <el-empty description="暂无数据" :image-size="60" />
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { DataAnalysis } from '@element-plus/icons-vue'

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

const peClass = computed(() => {
  const pe = props.financial?.pe
  if (!pe) return ''
  if (pe < 0) return 'text-down'
  if (pe < 20) return 'text-up'
  if (pe > 50) return 'text-down'
  return ''
})

const roeClass = computed(() => {
  const roe = props.financial?.roe
  if (!roe) return ''
  if (roe > 15) return 'text-up'
  if (roe < 5) return 'text-down'
  return ''
})

function formatValue(val) {
  if (val == null || val === '' || isNaN(val)) return '--'
  return Number(val).toFixed(2)
}

function formatYi(val) {
  if (val == null || val === '' || isNaN(val)) return '--'
  return Number(val).toFixed(2) + '亿'
}

function formatMv(val) {
  if (val == null || val === '' || isNaN(val)) return '--'
  if (val >= 10000) return (val / 10000).toFixed(2) + '万亿'
  return Number(val).toFixed(2) + '亿'
}

function getPeTip(pe) {
  if (!pe) return ''
  if (pe < 0) return '亏损'
  if (pe < 15) return '低估'
  if (pe < 30) return '合理'
  if (pe < 50) return '偏高'
  return '高估'
}
</script>

<style scoped>
.financial-card {
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
  color: #1f2937;
}

.report-date {
  margin-left: auto;
  font-size: 12px;
  font-weight: 400;
  color: #9ca3af;
}

.financial-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.fin-item {
  background: #f9fafb;
  border-radius: 8px;
  padding: 12px 14px;
  transition: background 0.2s;
}

.fin-item:hover {
  background: #f3f4f6;
}

.fin-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}

.fin-value {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.2;
}

.fin-value .unit {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  margin-left: 2px;
}

.fin-tip {
  font-size: 11px;
  margin-top: 4px;
  color: #9ca3af;
}

.empty-state {
  padding: 40px 0;
}
</style>
