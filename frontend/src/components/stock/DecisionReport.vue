<template>
  <section class="decision-report" aria-label="AI 决策报告">
    <header class="decision-report__header">
      <div><h2>决策报告</h2><p>基于当前行情、日 K 线与财务字段生成</p></div>
      <el-button type="primary" plain :loading="state === 'loading'" :disabled="state === 'loading'" @click="$emit('retry')">{{ state === 'success' ? '重新生成' : '生成报告' }}</el-button>
    </header>
    <StatusState v-if="state === 'idle' || state === 'loading'" :state="state === 'idle' ? 'empty' : 'loading'" :title="state === 'idle' ? '等待生成决策报告' : '正在生成决策报告'" :description="state === 'idle' ? '进入页面后将自动生成。' : '正在整理行情、技术信号和财务数据。'" :min-height="260" />
    <StatusState v-else-if="state === 'error'" state="error" title="决策报告生成失败" :description="errorMessage || '当前未拿到可展示的报告。'" :min-height="260" @retry="$emit('retry')" />
    <StatusState v-else-if="state === 'empty' || !report" state="empty" title="暂无决策报告" :min-height="260" @retry="$emit('retry')" />
    <div v-else class="decision-report__body">
      <section class="decision-report__conclusion"><span class="eyebrow">综合结论</span><div class="decision-report__score"><strong>{{ report.conclusion?.score ?? '--' }}</strong><span>/100</span><b>{{ report.conclusion?.label || '观望' }}</b></div><p>{{ report.conclusion?.rationale || '暂无结论理由。' }}</p></section>
      <section class="decision-report__section"><h3>趋势与技术信号</h3><dl><div><dt>趋势</dt><dd>{{ report.trend?.label || '暂无数据' }}</dd></div><div><dt>阶段</dt><dd>{{ report.trend?.phase || '暂无数据' }}</dd></div></dl><ul v-if="report.signals?.length"><li v-for="signal in report.signals" :key="`${signal.code}-${signal.detail}`">{{ signal.label }}<small>{{ signal.detail }}</small></li></ul><p v-else class="muted">暂无显著规则信号。</p></section>
      <section class="decision-report__section"><h3>关键价位</h3><dl class="levels"><div v-for="item in levelEntries" :key="item.key"><dt>{{ item.label }}</dt><dd>{{ formatLevel(item.value) }}</dd></div></dl></section>
      <section class="decision-report__section"><h3>风险与催化</h3><ul><li v-for="risk in report.risks || []" :key="`risk-${risk}`">风险：{{ risk }}</li><li v-for="item in report.catalysts || []" :key="`catalyst-${item}`">催化：{{ item }}</li></ul><p v-if="!report.risks?.length && !report.catalysts?.length" class="muted">暂无额外信息。</p></section>
      <section class="decision-report__section"><h3>数据限制</h3><p class="muted">{{ report.sentiment?.summary || '当前未接入新闻与情绪数据。' }}</p><p class="muted">{{ report.latest_developments?.summary || '当前未接入公告与最新动态数据。' }}</p><ul v-if="report.data_quality?.warnings?.length"><li v-for="warning in report.data_quality.warnings" :key="warning">{{ warning }}</li></ul></section>
      <section v-if="report.checklist?.length" class="decision-report__section"><h3>操作检查清单</h3><ul><li v-for="item in report.checklist" :key="item">{{ item }}</li></ul></section>
      <article v-if="renderedMarkdown" class="decision-report__markdown" v-html="renderedMarkdown" />
      <footer>生成于 {{ formatTime(report.generated_at) }} · 仅供参考，不构成投资建议</footer>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import StatusState from '@/components/base/StatusState.vue'
import { renderSafeMarkdown } from '@/utils/markdown'

const props = defineProps({ report: { type: Object, default: null }, state: { type: String, default: 'idle' }, errorMessage: { type: String, default: '' } })
defineEmits(['retry'])
const levelEntries = computed(() => [
  { key: 'support', label: '支撑', value: props.report?.levels?.support },
  { key: 'resistance', label: '压力', value: props.report?.levels?.resistance },
  { key: 'entry_low', label: '入场下沿', value: props.report?.levels?.entry_low },
  { key: 'entry_high', label: '入场上沿', value: props.report?.levels?.entry_high },
  { key: 'stop_loss', label: '止损', value: props.report?.levels?.stop_loss },
  { key: 'target_price', label: '目标', value: props.report?.levels?.target_price },
].filter(item => item.value !== null && item.value !== undefined))
const renderedMarkdown = computed(() => renderSafeMarkdown(props.report?.analysis_markdown || ''))
const formatLevel = value => Number.isFinite(Number(value)) ? `${Number(value).toFixed(2)} 元` : '暂无数据'
const formatTime = value => value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '--'
</script>

<style scoped>
.decision-report{padding:var(--spacing-3)}.decision-report__header{display:flex;justify-content:space-between;gap:var(--spacing-3);align-items:center;padding-bottom:var(--spacing-3);border-bottom:1px solid var(--border-subtle)}h2,h3,p{margin:0}.decision-report__header h2{font-size:var(--font-size-lg)}.decision-report__header p,.muted,dt,footer{color:var(--text-tertiary);font-size:var(--font-size-xs)}.decision-report__body,.decision-report__section{display:grid;gap:var(--spacing-3)}.decision-report__body{padding-top:var(--spacing-3)}.decision-report__section{padding:var(--spacing-3) 0;border-top:1px solid var(--border-subtle)}.decision-report__section h3{font-size:var(--font-size-base)}.eyebrow{color:var(--text-tertiary);font-size:var(--font-size-xs)}.decision-report__score{display:flex;align-items:baseline;gap:var(--spacing-2)}.decision-report__score strong{color:var(--text-ai);font-size:var(--font-size-5xl)}.decision-report__score b{color:var(--text-primary)}.decision-report__conclusion p{color:var(--text-secondary);line-height:var(--line-height-normal)}dl{display:grid;gap:var(--spacing-2);margin:0}dl div{display:flex;justify-content:space-between;gap:var(--spacing-3)}dt,dd{margin:0}dd{font-family:var(--font-family-mono);color:var(--text-primary)}ul{display:grid;gap:var(--spacing-2);padding-left:1.2rem;margin:0}li{color:var(--text-secondary)}li small{display:block;color:var(--text-tertiary);margin-top:2px}.decision-report__markdown{color:var(--text-primary);line-height:var(--line-height-relaxed)}.decision-report__markdown :deep(p),.decision-report__markdown :deep(ul),.decision-report__markdown :deep(h2),.decision-report__markdown :deep(h3){margin:0 0 var(--spacing-3)}footer{padding-top:var(--spacing-3);border-top:1px solid var(--border-subtle)}
</style>
