<template>
  <main class="report-detail-page workbench-page">
    <header class="report-detail-page__header workbench-page__header">
      <el-button :icon="ArrowLeft" text @click="router.push('/reports')">返回列表</el-button>
      <div>
        <h1 data-page-title tabindex="-1">{{ report?.report_date || '复盘报告' }}</h1>
        <p v-if="report">
          {{ statusText(report.status) }} · 覆盖 {{ report.stock_count || 0 }} 只股票 ·
          {{ formatTime(report.completed_at) }}
        </p>
      </div>
    </header>
    <StatusState v-if="loading" state="loading" />
    <StatusState
      v-else-if="error"
      state="error"
      description="报告详情暂时无法加载。"
      @retry="loadReport"
    />
    <StatusState v-else-if="!report" state="empty" />
    <StatusState
      v-else-if="report.status !== 'completed'"
      :state="report.status === 'failed' ? 'error' : 'loading'"
      :title="report.status === 'failed' ? '报告生成失败' : '报告生成中'"
      :description="report.status === 'failed' ? '该历史报告未成功生成。' : '完成后即可阅读。'"
    >
      <template v-if="report.status === 'failed'" #action><span /></template>
    </StatusState>
    <div v-else class="report-detail-page__reader workbench-grid workbench-grid--reader">
      <ReportOutline :items="outline" />
      <article class="report-detail-page__article">
        <div class="report-detail-page__summary">
          <section v-if="report.market_summary" id="conclusion" class="report-detail-page__summary-section">
          <h2>今日结论</h2>
          <div class="markdown" v-html="renderSafeMarkdown(report.market_summary)"></div>
          </section>
          <section v-if="report.risk_notes" id="risks" class="report-detail-page__summary-section risk">
          <h2>风险提示</h2>
          <div class="markdown" v-html="renderSafeMarkdown(report.risk_notes)"></div>
          </section>
          <section v-if="report.highlights?.length" id="highlights" class="report-detail-page__summary-section">
          <h2>关联股票</h2>
          <ol class="highlights">
            <li
              v-for="item in report.highlights"
              :key="`${item.stock_code}-${item.reason}`"
            >
              <button type="button" class="report-detail-page__stock-link" @click="openStock(item.stock_code)">{{ item.stock_name }} <span>{{ item.stock_code }}</span></button>
              <p>{{ item.reason }}</p>
            </li>
          </ol>
          </section>
        </div>

        <section v-if="report.stock_reports?.length" id="stocks" class="report-detail-page__body">
          <h2>个股分析</h2>
          <details v-for="stock in report.stock_reports" :key="stock.id">
            <summary>
              <span>
                <strong>{{ stock.stock_name }}</strong>
                <small>{{ stock.stock_code }}</small>
              </span>
              <span
                class="quote"
                :class="stock.change_pct > 0 ? 'text-up' : stock.change_pct < 0 ? 'text-down' : 'text-neutral'"
              >
                {{ signed(stock.change_pct) }} · {{ number(stock.close_price) }}
              </span>
            </summary>

            <div class="stock-body">
              <span v-if="score(stock)" class="score">
                评分 {{ score(stock).score }}
                <template v-if="score(stock).rating"> · {{ score(stock).rating }}</template>
              </span>
              <div
                class="markdown"
                v-html="renderSafeMarkdown(stripScoreBlock(stock.analysis_text))"
              ></div>
            </div>
          </details>
        </section>
      </article>
    </div>
  </main>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { reportApi } from '@/api/report'
import StatusState from '@/components/base/StatusState.vue'
import ReportOutline from '@/components/reports/ReportOutline.vue'
import {
  parseScoreBlock,
  renderSafeMarkdown,
  stripScoreBlock,
} from '@/utils/markdown'

const route = useRoute()
const router = useRouter()
const report = ref(null)
const loading = ref(true)
const error = ref(false)
let detailRequestId = 0

const outline = computed(() => [
  report.value?.market_summary && { id: 'conclusion', label: '今日结论' },
  report.value?.risk_notes && { id: 'risks', label: '风险提示' },
  report.value?.highlights?.length && { id: 'highlights', label: '关联股票' },
  report.value?.stock_reports?.length && { id: 'stocks', label: '个股分析' },
].filter(Boolean))

async function loadReport() {
  const requestId = ++detailRequestId
  loading.value = true
  error.value = false

  try {
    const nextReport = await reportApi.getDetail(route.params.id)
    if (requestId !== detailRequestId) return
    report.value = nextReport
  } catch {
    if (requestId !== detailRequestId) return
    error.value = true
  } finally {
    if (requestId !== detailRequestId) return
    loading.value = false
  }
}

const statusText = (value) => ({
  pending: '待生成',
  generating: '生成中',
  completed: '已完成',
  failed: '生成失败',
})[value] || value

const number = (value) => Number.isFinite(Number(value)) ? Number(value).toFixed(2) : '--'

const signed = (value) => Number.isFinite(Number(value))
  ? `${Number(value) > 0 ? '+' : ''}${Number(value).toFixed(2)}%`
  : '--'

const score = (stock) => parseScoreBlock(stock?.analysis_text)

function openStock(code) {
  if (code) router.push(`/stock/${code}`)
}

function formatTime(value) {
  return value
    ? new Intl.DateTimeFormat('zh-CN', {
      dateStyle: 'medium',
      timeStyle: 'short',
      hour12: false,
    }).format(new Date(value))
    : '--'
}

watch(() => route.params.id, loadReport, { immediate: true })
</script>

<style scoped>
.report-detail-page {
  gap: var(--spacing-3);
}
.report-detail-page__header {
  align-items: center;
  justify-content: flex-start;
  gap: var(--spacing-3);
}
.report-detail-page__article {
  min-width: 0;
  width: min(760px, 100%);
  max-width: 760px;
  margin: 0 auto;
}
.report-detail-page__reader {
  grid-template-columns: 180px minmax(0, 1fr);
  background: var(--surface-primary);
  border: 1px solid var(--border-default);
}
.report-detail-page__article section {
  scroll-margin-top: 84px;
  border-bottom: 1px solid var(--border-subtle);
}

.report-detail-page__summary { border-top: 1px solid var(--border-subtle); }
.report-detail-page__summary-section { padding: var(--spacing-3) 0; margin: 0; }
.report-detail-page__body { padding-top: var(--spacing-4); margin-top: var(--spacing-4); }
h2 {
  margin: 0 0 var(--spacing-2);
  font-size: var(--font-size-xl);
  letter-spacing: 0;
}
.markdown {
  max-width: 68ch;
  overflow-wrap: anywhere;
  line-height: 1.8;
}
.markdown :deep(pre) {
  max-width: 100%;
  padding: var(--spacing-4);
  overflow-x: auto;
  background: var(--surface-secondary);
  border-radius: var(--radius-sm);
}
.highlights {
  display: grid;
  gap: var(--spacing-2);
  padding-left: 24px;
  margin: 0;
}
.highlights span,
small {
  color: var(--text-tertiary);
  font-weight: 400;
}
.highlights p {
  margin: var(--spacing-1) 0 0;
}
.report-detail-page__stock-link {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--text-link);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}
details {
  border-top: 1px solid var(--border-subtle);
}
summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
  min-height: 56px;
  cursor: pointer;
}
summary > span:first-child {
  display: inline-flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}
.quote {
  flex: 0 0 auto;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.stock-body {
  padding: var(--spacing-1) 0 var(--spacing-5);
}
.score {
  display: inline-block;
  padding: 3px 7px;
  margin-bottom: var(--spacing-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
}

.risk { padding-left: var(--spacing-3); border-left: 2px solid var(--color-warning); }

@media (max-width: 767px) {
  .report-detail-page__reader { grid-template-columns: minmax(0, 1fr); }
  .report-detail-page__article { width: 100%; padding-inline: var(--spacing-3); }
  .report-detail-page__header {
    align-items: start;
  }

  .report-detail-page__header :deep(.el-button) {
    min-height: 44px;
    touch-action: manipulation;
  }

  summary {
    align-items: flex-start;
    flex-direction: column;
    justify-content: center;
    padding-block: var(--spacing-3);
  }
}
</style>
