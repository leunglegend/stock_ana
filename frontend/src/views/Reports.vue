<template>
  <div class="reports-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">复盘报告</h2>
        <p class="page-subtitle">AI 每日生成专业复盘，涵盖市场行情与自选股分析</p>
      </div>
      <div class="header-actions">
        <el-button
          type="primary"
          :icon="MagicStick"
          :loading="generating"
          @click="handleGenerate"
        >
          手动生成今日报告
        </el-button>
      </div>
    </div>

    <!-- 报告列表 -->
    <div class="reports-list" v-loading="loading">
      <el-empty
        v-if="!loading && reports.length === 0"
        description="暂无复盘报告，点击上方按钮生成第一份"
      >
        <el-button type="primary" @click="handleGenerate" :loading="generating">
          生成今日报告
        </el-button>
      </el-empty>

      <el-card
        v-for="report in reports"
        :key="report.id"
        class="report-card card-shadow"
        @click="goToDetail(report)"
      >
        <div class="report-card-header">
          <div class="report-date">
            <el-icon :size="18" color="#8b5cf6"><Calendar /></el-icon>
            <span class="date-text">{{ report.report_date }}</span>
          </div>
          <el-tag
            :type="statusTagType(report.status)"
            effect="light"
            size="small"
            class="status-tag"
          >
            {{ statusText(report.status) }}
          </el-tag>
        </div>

        <div class="report-stats">
          <div class="stat-item">
            <el-icon :size="16" color="#6b7280"><TrendCharts /></el-icon>
            <span>覆盖 {{ report.stock_count || 0 }} 只股票</span>
          </div>
        </div>

        <div class="report-summary" v-if="report.market_summary">
          <div class="summary-label">市场总览</div>
          <div class="summary-text">{{ truncateText(report.market_summary, 80) }}</div>
        </div>

        <div class="report-footer">
          <span class="create-time">
            <el-icon :size="14" color="#9ca3af"><Clock /></el-icon>
            生成于 {{ formatTime(report.created_at) }}
          </span>
          <el-button type="primary" link>
            查看详情
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="total > pageSize">
      <el-pagination
        background
        layout="prev, pager, next, total"
        :total="total"
        :current-page="page"
        :page-size="pageSize"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  MagicStick, Calendar, TrendCharts, Clock, ArrowRight,
} from '@element-plus/icons-vue'
import { reportApi } from '@/api/report'

const router = useRouter()

const loading = ref(false)
const generating = ref(false)
const reports = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

async function loadReports() {
  loading.value = true
  try {
    const data = await reportApi.getList({ page: page.value, page_size: pageSize.value })
    reports.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    ElMessage.error('加载报告列表失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function handleGenerate() {
  if (generating.value) return
  generating.value = true
  try {
    const data = await reportApi.generateToday()
    ElMessage.success(data.message || '报告生成任务已提交，请稍后查看')
    // 刷新列表
    page.value = 1
    setTimeout(loadReports, 1500)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '生成失败，请稍后重试')
    console.error(e)
  } finally {
    generating.value = false
  }
}

function goToDetail(report) {
  if (report.status === 'completed') {
    router.push(`/reports/${report.id}`)
  }
}

function handlePageChange(p) {
  page.value = p
  loadReports()
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

function truncateText(text, maxLen) {
  if (!text) return ''
  if (text.length <= maxLen) return text
  return text.substring(0, maxLen) + '...'
}

function formatTime(dateStr) {
  if (!dateStr) return '--'
  const date = new Date(dateStr)
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${month}-${day} ${hours}:${minutes}`
}

onMounted(() => {
  loadReports()
})
</script>

<style scoped>
.reports-page {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 4px 0;
}

.page-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.reports-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.report-card {
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.report-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.report-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.report-date {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-text {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.status-tag {
  font-size: 12px;
}

.report-stats {
  margin-bottom: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #6b7280;
}

.report-summary {
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 12px;
}

.summary-label {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 4px;
}

.summary-text {
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
}

.report-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid #f0f2f5;
}

.create-time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #9ca3af;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
