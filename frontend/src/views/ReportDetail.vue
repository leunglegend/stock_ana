<template>
  <div class="report-detail-page">
    <!-- 返回按钮 + 标题 -->
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" text @click="goBack">
          返回列表
        </el-button>
        <div class="title-group">
          <h2 class="page-title">{{ report?.report_date || '复盘报告' }}</h2>
          <p class="page-subtitle">
            <el-tag
              v-if="report"
              :type="statusTagType(report.status)"
              size="small"
              effect="light"
            >
              {{ statusText(report.status) }}
            </el-tag>
            <span v-if="report" class="sub-info">
              覆盖 {{ report.stock_count || 0 }} 只股票
            </span>
            <span v-if="report?.completed_at" class="sub-info">
              完成于 {{ formatTime(report.completed_at) }}
            </span>
          </p>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrapper">
      <el-icon class="is-loading" :size="48" color="#8b5cf6"><Loading /></el-icon>
      <p>加载报告详情中...</p>
    </div>

    <!-- 错误状态 -->
    <el-card v-else-if="error" class="error-card">
      <el-result icon="error" title="加载失败" sub-title="报告数据加载失败，请稍后重试">
        <template #extra>
          <el-button type="primary" @click="loadReport">重新加载</el-button>
        </template>
      </el-result>
    </el-card>

    <!-- 生成中状态 -->
    <el-card v-else-if="report.status !== 'completed'" class="generating-card">
      <el-result
        :icon="report.status === 'failed' ? 'warning' : 'info'"
        :title="report.status === 'failed' ? '生成失败' : '生成中'"
        :sub-title="report.status === 'failed' ? '报告生成失败，请稍后重试或重新生成' : 'AI 正在努力生成报告，请稍候...'"
      >
        <template #extra v-if="report.status === 'generating'">
          <el-icon class="is-loading" :size="32" color="#8b5cf6"><Loading /></el-icon>
        </template>
      </el-result>
    </el-card>

    <!-- 报告内容 -->
    <div v-else class="report-content">
      <!-- 市场总览卡片 -->
      <el-card class="section-card market-card card-shadow" v-if="report.market_summary">
        <template #header>
          <div class="card-title">
            <div class="title-icon market-icon">
              <el-icon color="#fff" :size="18"><DataLine /></el-icon>
            </div>
            <span>市场总览</span>
          </div>
        </template>
        <div class="market-summary">
          <p v-for="(para, idx) in summaryParagraphs" :key="idx">{{ para }}</p>
        </div>
      </el-card>

      <!-- 关注重点卡片 -->
      <el-card class="section-card highlights-card card-shadow" v-if="report.highlights && report.highlights.length > 0">
        <template #header>
          <div class="card-title">
            <div class="title-icon highlights-icon">
              <el-icon color="#fff" :size="18"><Star /></el-icon>
            </div>
            <span>关注重点</span>
          </div>
        </template>
        <div class="highlights-list">
          <div
            v-for="(item, idx) in report.highlights"
            :key="idx"
            class="highlight-item"
          >
            <div class="highlight-rank">{{ idx + 1 }}</div>
            <div class="highlight-content">
              <div class="highlight-stock">
                <span class="stock-name">{{ item.stock_name }}</span>
                <span class="stock-code">{{ item.stock_code }}</span>
              </div>
              <div class="highlight-reason">{{ item.reason }}</div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 个股分析列表 -->
      <el-card class="section-card stocks-card card-shadow" v-if="report.stock_reports && report.stock_reports.length > 0">
        <template #header>
          <div class="card-title">
            <div class="title-icon stocks-icon">
              <el-icon color="#fff" :size="18"><TrendCharts /></el-icon>
            </div>
            <span>个股分析</span>
            <span class="stock-count">共 {{ report.stock_reports.length }} 只</span>
          </div>
        </template>
        <el-collapse class="stock-collapse">
          <el-collapse-item
            v-for="stock in report.stock_reports"
            :key="stock.id"
            :name="stock.id"
          >
            <template #title>
              <div class="stock-item-header">
                <div class="stock-info">
                  <span class="stock-name">{{ stock.stock_name }}</span>
                  <span class="stock-code">{{ stock.stock_code }}</span>
                  <!-- 评分徽章 -->
                  <span
                    v-if="extractStockScore(stock)"
                    class="score-badge"
                    :style="{
                      background: getRatingStyle(extractStockScore(stock).rating).bg,
                      color: getRatingStyle(extractStockScore(stock).rating).color,
                      borderColor: getRatingStyle(extractStockScore(stock).rating).border
                    }"
                  >
                    <span class="badge-score">{{ extractStockScore(stock).score }}</span>
                    <span class="badge-rating">{{ extractStockScore(stock).rating }}</span>
                  </span>
                </div>
                <div class="stock-meta">
                  <span
                    class="change-pct"
                    :class="stock.change_pct > 0 ? 'up' : stock.change_pct < 0 ? 'down' : ''"
                  >
                    {{ stock.change_pct > 0 ? '+' : '' }}{{ stock.change_pct?.toFixed(2) }}%
                  </span>
                  <span class="close-price">{{ stock.close_price?.toFixed(2) }}</span>
                </div>
              </div>
              <div class="stock-summary">{{ stock.summary || stock.analysis_text?.substring(0, 60) + '...' }}</div>
            </template>
            <div class="stock-analysis-content">
              <div v-if="stock.analysis_text" class="analysis-text" v-html="renderMarkdown(cleanAnalysisText(stock.analysis_text))"></div>
              <el-empty v-else description="暂无分析内容" :image-size="50" />
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-card>

      <!-- 风险提示卡片 -->
      <el-card class="section-card risk-card card-shadow" v-if="report.risk_notes">
        <template #header>
          <div class="card-title">
            <div class="title-icon risk-icon">
              <el-icon color="#fff" :size="18"><Warning /></el-icon>
            </div>
            <span>风险提示</span>
          </div>
        </template>
        <div class="risk-notes">
          <p v-for="(para, idx) in riskParagraphs" :key="idx">{{ para }}</p>
        </div>
      </el-card>

      <!-- 底部声明 -->
      <div class="footer-disclaimer">
        <el-icon color="#f59e0b" :size="16"><Warning /></el-icon>
        <span>本报告由 AI 自动生成，仅供学习参考，不构成任何投资建议。投资有风险，入市需谨慎。</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, Loading, DataLine, Star, TrendCharts, Warning,
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import { reportApi } from '@/api/report'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref(false)
const report = ref(null)

const summaryParagraphs = computed(() => {
  if (!report.value?.market_summary) return []
  return report.value.market_summary.split('\n').filter(p => p.trim())
})

const riskParagraphs = computed(() => {
  if (!report.value?.risk_notes) return []
  return report.value.risk_notes.split('\n').filter(p => p.trim())
})

async function loadReport() {
  loading.value = true
  error.value = false
  try {
    const data = await reportApi.getDetail(route.params.id)
    report.value = data
  } catch (e) {
    error.value = true
    ElMessage.error('加载报告详情失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/reports')
}

function statusText(status) {
  const map = {
    pending: '待生成',
    generating: '生成中',
    completed: '已完成',
    failed: '生成失败',
  }
  return map[status] || status
}

function statusTagType(status) {
  const map = {
    pending: 'info',
    generating: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return map[status] || 'info'
}

function formatTime(dateStr) {
  if (!dateStr) return '--'
  const date = new Date(dateStr)
  const y = date.getFullYear()
  const m = (date.getMonth() + 1).toString().padStart(2, '0')
  const d = date.getDate().toString().padStart(2, '0')
  const h = date.getHours().toString().padStart(2, '0')
  const min = date.getMinutes().toString().padStart(2, '0')
  return `${y}-${m}-${d} ${h}:${min}`
}

function renderMarkdown(text) {
  if (!text) return ''
  try {
    return marked.parse(text)
  } catch (e) {
    return text.replace(/\n/g, '<br>')
  }
}

// 从分析文本中提取评分数据
function extractStockScore(stock) {
  if (!stock?.analysis_text) return null
  const text = stock.analysis_text
  const match = text.match(/```json\s*([\s\S]*?)\s*```/)
  if (!match) return null
  try {
    const data = JSON.parse(match[1].trim())
    if (typeof data.score === 'number' && data.score >= 0 && data.score <= 100) {
      return data
    }
    return null
  } catch (e) {
    return null
  }
}

// 去除 analysis_text 中的 JSON 代码块，用于显示正文
function cleanAnalysisText(text) {
  if (!text) return ''
  return text.replace(/```json\s*[\s\S]*?```\s*/, '').trim()
}

// 评级颜色配置
function getRatingStyle(rating) {
  const map = {
    '强烈买入': { color: '#dc2626', bg: '#fef2f2', border: '#fecaca' },
    '买入': { color: '#ef4444', bg: '#fef2f2', border: '#fecaca' },
    '观望': { color: '#d97706', bg: '#fffbeb', border: '#fde68a' },
    '减仓': { color: '#059669', bg: '#ecfdf5', border: '#a7f3d0' },
    '卖出': { color: '#10b981', bg: '#ecfdf5', border: '#a7f3d0' },
  }
  return map[rating] || map['观望']
}

onMounted(() => {
  loadReport()
})
</script>

<style scoped>
.report-detail-page {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-group {
  flex: 1;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 6px 0;
}

.page-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.sub-info {
  color: #9ca3af;
}

/* 加载状态 */
.loading-wrapper {
  text-align: center;
  padding: 80px 0;
  color: #6b7280;
}

.loading-wrapper p {
  margin-top: 12px;
}

.error-card, .generating-card {
  border-radius: 12px;
}

/* 报告内容区域 */
.report-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-card {
  border-radius: 12px;
  overflow: hidden;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.title-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.market-icon {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.highlights-icon {
  background: linear-gradient(135deg, #f59e0b, #ef4444);
}

.stocks-icon {
  background: linear-gradient(135deg, #10b981, #0ea5e9);
}

.risk-icon {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

.stock-count {
  font-size: 13px;
  font-weight: 400;
  color: #9ca3af;
  margin-left: 8px;
}

/* 市场总览 */
.market-summary {
  font-size: 15px;
  line-height: 2;
  color: #4b5563;
}

.market-summary p {
  margin: 0 0 12px 0;
  text-indent: 2em;
}

.market-summary p:last-child {
  margin-bottom: 0;
}

/* 关注重点 */
.highlights-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.highlight-item {
  display: flex;
  gap: 14px;
  padding: 14px 16px;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border-radius: 10px;
  border: 1px solid #fde68a;
}

.highlight-rank {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  color: white;
  font-size: 14px;
  font-weight: 700;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.highlight-content {
  flex: 1;
  min-width: 0;
}

.highlight-stock {
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.highlight-stock .stock-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.highlight-stock .stock-code {
  font-size: 12px;
  color: #9ca3af;
}

.highlight-reason {
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
}

/* 个股分析折叠面板 */
.stock-collapse {
  border: none;
}

.stock-collapse :deep(.el-collapse-item) {
  border-bottom: 1px solid #f0f2f5;
}

.stock-collapse :deep(.el-collapse-item:last-child) {
  border-bottom: none;
}

.stock-collapse :deep(.el-collapse-item__header) {
  padding: 12px 0;
  height: auto;
  line-height: 1.5;
  flex-wrap: wrap;
  gap: 4px;
}

.stock-collapse :deep(.el-collapse-item__wrap) {
  border-bottom: none;
}

.stock-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: calc(100% - 24px);
}

.stock-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stock-info .stock-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.stock-info .stock-code {
  font-size: 12px;
  color: #9ca3af;
}

.score-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border: 1px solid;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.4;
}
.badge-score {
  font-size: 13px;
  font-weight: 700;
}
.badge-rating {
  font-size: 11px;
  opacity: 0.9;
}

.stock-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.change-pct {
  font-size: 15px;
  font-weight: 600;
}

.change-pct.up { color: #ef4444; }
.change-pct.down { color: #10b981; }

.close-price {
  font-size: 13px;
  color: #6b7280;
}

.stock-summary {
  width: 100%;
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
  padding-left: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stock-analysis-content {
  padding: 8px 0 16px;
}

.analysis-text {
  font-size: 14px;
  line-height: 1.9;
  color: #4b5563;
}

.analysis-text :deep(h1),
.analysis-text :deep(h2),
.analysis-text :deep(h3) {
  color: #1f2937;
  margin-top: 16px;
  margin-bottom: 8px;
}

.analysis-text :deep(h1) { font-size: 18px; }
.analysis-text :deep(h2) { font-size: 16px; }
.analysis-text :deep(h3) { font-size: 15px; }

.analysis-text :deep(p) {
  margin: 8px 0;
}

.analysis-text :deep(ul),
.analysis-text :deep(ol) {
  padding-left: 24px;
  margin: 8px 0;
}

.analysis-text :deep(li) {
  margin: 4px 0;
}

.analysis-text :deep(strong) {
  color: #1f2937;
  font-weight: 600;
}

/* 风险提示 */
.risk-notes {
  font-size: 14px;
  line-height: 2;
  color: #92400e;
  background: #fffbeb;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid #f59e0b;
}

.risk-notes p {
  margin: 0 0 8px 0;
}

.risk-notes p:last-child {
  margin-bottom: 0;
}

/* 底部声明 */
.footer-disclaimer {
  margin-top: 12px;
  padding: 14px 20px;
  background: #fafafa;
  border-radius: 12px;
  font-size: 12.5px;
  color: #9ca3af;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  line-height: 1.6;
}

.footer-disclaimer .el-icon {
  flex-shrink: 0;
  margin-top: 1px;
}
</style>
