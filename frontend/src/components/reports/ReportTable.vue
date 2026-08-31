<template>
  <section class="report-table" aria-label="复盘报告列表">
    <table class="report-table__table">
      <thead>
        <tr>
          <th>日期</th><th>状态</th><th class="report-table__numeric">重点股票</th><th>今日结论 / 风险</th><th class="report-table__numeric report-table__time">完成时间</th><th aria-label="查看详情"></th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="report in reports"
          :key="report.id"
          class="report-table__row"
          :class="{ 'is-openable': report.status === 'completed' }"
          :tabindex="report.status === 'completed' ? 0 : undefined"
          @click="open(report)"
          @keydown.enter.prevent="open(report)"
          @keydown.space.prevent="open(report)"
        >
          <td class="report-table__date">{{ report.report_date }}</td>
          <td><span class="report-table__status" :data-status="report.status">{{ statusText(report.status) }}</span></td>
          <td class="report-table__numeric">{{ report.stock_count || '--' }}</td>
          <td class="report-table__summary">
            <strong>{{ report.market_summary || statusHint(report.status) }}</strong>
            <small class="report-table__risk">{{ report.risk_notes ? `风险：${report.risk_notes}` : statusRisk(report.status) }}</small>
          </td>
          <td class="report-table__numeric report-table__time">{{ formatTime(report.completed_at || report.created_at) }}</td>
          <td class="report-table__open"><el-icon v-if="report.status === 'completed'"><ArrowRight /></el-icon></td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup>
import { ArrowRight } from '@element-plus/icons-vue'

defineProps({ reports: { type: Array, default: () => [] } })
const emit = defineEmits(['open'])

const statusText = (value) => ({ pending: '待生成', generating: '生成中', completed: '已完成', failed: '生成失败' })[value] || value
const statusHint = (value) => ({ pending: '等待生成', generating: '正在汇总盘面与自选信号', failed: '报告生成失败' })[value] || '--'
const statusRisk = (value) => value === 'completed' ? '详情查看风险' : value === 'failed' ? '请重新生成或稍后重试' : '--'

function open(report) {
  if (report.status === 'completed') emit('open', report)
}

function formatTime(value) {
  return value ? new Intl.DateTimeFormat('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(value)) : '--'
}
</script>

<style scoped>
.report-table { min-width: 0; background: var(--surface-primary); }
.report-table__table { width: 100%; border-collapse: collapse; font-size: var(--font-size-sm); }
.report-table th { height: 32px; padding: 0 var(--spacing-3); border-bottom: 1px solid var(--border-subtle); color: var(--text-secondary); font-size: var(--font-size-xs); font-weight: 500; text-align: left; white-space: nowrap; }
.report-table__row { height: 44px; border-bottom: 1px solid var(--border-subtle); outline: 0; }
.report-table__row.is-openable { cursor: pointer; }
.report-table__row.is-openable:hover, .report-table__row.is-openable:focus-visible { background: var(--surface-secondary); }
.report-table td { box-sizing: border-box; height: 44px; padding: 2px var(--spacing-3); vertical-align: middle; }
.report-table__date, .report-table__numeric { font-family: var(--font-family-mono); font-variant-numeric: tabular-nums; white-space: nowrap; }
.report-table__numeric { text-align: right; }
.report-table__status { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }
.report-table__status::before { width: 6px; height: 6px; content: ''; border-radius: 50%; background: var(--text-tertiary); }
.report-table__status[data-status='completed']::before { background: var(--color-success); }
.report-table__status[data-status='generating']::before, .report-table__status[data-status='pending']::before { background: var(--color-warning); }
.report-table__status[data-status='failed']::before { background: var(--color-up); }
.report-table__summary { min-width: 0; }
.report-table__summary strong, .report-table__risk { display: block; overflow: hidden; line-height: 1.15; text-overflow: ellipsis; white-space: nowrap; }
.report-table__summary strong { font-weight: 500; }
.report-table__risk { margin-top: 1px; color: var(--text-secondary); font-size: var(--font-size-xs); }
.report-table__open { width: 28px; color: var(--text-tertiary); text-align: right; }

@media (max-width: 767px) {
  .report-table__table, .report-table__table tbody { display: block; }
  .report-table thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
  .report-table__row { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 4px var(--spacing-2); min-width: 0; height: auto; padding: var(--spacing-2) var(--spacing-3); }
  .report-table td { display: flex; align-items: center; min-width: 0; height: auto; padding: 0; }
  .report-table__date { grid-column: 1; font-weight: 600; }
  .report-table__numeric:not(.report-table__time) { grid-column: 2; grid-row: 1; }
  .report-table__summary { grid-column: 1 / -1; grid-row: 2; }
  .report-table__time { display: none; }
  .report-table__open { grid-column: 3; grid-row: 1; }
}
</style>
