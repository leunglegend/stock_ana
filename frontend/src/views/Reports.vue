<template>
  <main class="reports-page workbench-page">
    <header class="reports-page__header workbench-page__header">
      <div>
        <div class="reports-page__title-line">
          <h1 data-page-title tabindex="-1">复盘报告</h1>
          <span v-if="total" class="reports-page__total">共 {{ total }} 份</span>
        </div>
      </div>

      <el-button
        type="primary"
        :icon="Refresh"
        :loading="generating"
        @click="generate"
      >
        生成今日报告
      </el-button>
    </header>

    <p v-if="pollMessage" class="reports-page__poll-note" aria-live="polite">
      {{ pollMessage }}
    </p>

    <section class="reports-page__toolbar" aria-label="报告列表控制">
      <div class="reports-page__toolbar-left">
        <el-select v-model="statusFilter" size="small" aria-label="报告状态筛选">
          <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="daysFilter" size="small" aria-label="报告日期范围">
          <el-option v-for="item in daysOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <span class="reports-page__result-count">共 {{ total }} 份</span>
      </div>
      <el-pagination
        v-if="total > pageSize && !isMobile"
        class="reports-page__pagination reports-page__pagination--top"
        size="small"
        :layout="paginationLayout"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="changePage"
      />
    </section>

    <section class="reports-page__workspace" aria-label="报告列表">
      <StatusState v-if="loading" state="loading" />
      <StatusState
        v-else-if="error"
        state="error"
        description="报告列表暂时无法加载。"
        @retry="loadReports"
      />
      <StatusState
        v-else-if="!reports.length"
        state="empty"
        title="暂无复盘报告"
      >
        <template #action>
          <el-button type="primary" @click="generate">生成今日报告</el-button>
        </template>
      </StatusState>
      <ReportTable v-else :reports="reports" @open="openReport" />
    </section>

    <div v-if="total > pageSize" class="reports-page__feedback">
      <el-pagination
        class="reports-page__pagination"
        size="small"
        :layout="paginationLayout"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="changePage"
      />
      <span v-if="isMobile" class="reports-page__page-status" aria-live="polite">第 {{ page }} / {{ pageCount }} 页</span>
    </div>
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { reportApi } from '@/api/report'
import StatusState from '@/components/base/StatusState.vue'
import ReportTable from '@/components/reports/ReportTable.vue'
import { useResponsive } from '@/composables/useResponsive'

const router = useRouter()
const { isMobile } = useResponsive()
const reports = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(true)
const error = ref(false)
const generating = ref(false)
const pollMessage = ref('')
const statusFilter = ref('all')
const daysFilter = ref('30')
const statusOptions = [
  { label: '全部状态', value: 'all' }, { label: '已完成', value: 'completed' },
  { label: '生成中', value: 'generating' }, { label: '生成失败', value: 'failed' }, { label: '待生成', value: 'pending' },
]
const daysOptions = [
  { label: '最近 7 天', value: '7' }, { label: '最近 30 天', value: '30' },
  { label: '最近 90 天', value: '90' }, { label: '全部时间', value: 'all' },
]
const paginationLayout = computed(() => isMobile.value ? 'prev, next' : 'prev, pager, next')
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

let pollTimer = null
let pollStartedAt = 0
let pollingId = null
let listRequestId = 0

async function loadReports() {
  const requestId = ++listRequestId
  loading.value = true
  error.value = false

  try {
    const data = await reportApi.getList({
      page: page.value,
      page_size: pageSize,
      status: statusFilter.value,
      days: daysFilter.value,
    })
    if (requestId !== listRequestId) return
    reports.value = data.items || []
    total.value = data.total || 0
  } catch {
    if (requestId !== listRequestId) return
    error.value = true
  } finally {
    if (requestId !== listRequestId) return
    loading.value = false
  }
}

function stopPolling(message = '') {
  clearTimeout(pollTimer)
  pollTimer = null
  pollingId = null
  pollMessage.value = message
}

async function pollReport() {
  if (!pollingId || Date.now() - pollStartedAt >= 120000) {
    return stopPolling('生成时间较长，可稍后手动刷新列表。')
  }

  try {
    const item = await reportApi.getDetail(pollingId)

    if (['completed', 'failed'].includes(item.status)) {
      stopPolling(item.status === 'completed' ? '今日报告已完成。' : '今日报告生成失败。')
      await loadReports()
      return
    }
  } catch {
    pollMessage.value = '状态查询暂时失败，正在重试。'
  }

  pollTimer = setTimeout(pollReport, 5000)
}

async function generate() {
  if (generating.value || pollingId) return

  generating.value = true

  try {
    const data = await reportApi.generateToday()
    pollingId = data.report_id
    pollStartedAt = Date.now()
    pollMessage.value = data.message || '报告生成中。'
    page.value = 1
    await loadReports()
    pollReport()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '生成失败，请稍后重试')
  } finally {
    generating.value = false
  }
}

function openReport(report) {
  if (report.status === 'completed') {
    router.push(`/reports/${report.id}`)
  }
}

function changePage(value) {
  page.value = value
  loadReports()
}

watch([statusFilter, daysFilter], () => {
  page.value = 1
  loadReports()
})

onMounted(loadReports)
onBeforeUnmount(() => stopPolling())
</script>

<style scoped>
.reports-page {
  gap: var(--spacing-3);
}

.reports-page__header {
  gap: var(--spacing-3);
}

.reports-page__title-line { display: flex; align-items: baseline; gap: var(--spacing-2); }
.reports-page__total, .reports-page__toolbar { color: var(--text-secondary); font-size: var(--font-size-sm); }
.reports-page__toolbar { display: flex; align-items: center; justify-content: space-between; min-height: 40px; padding: 0 var(--spacing-2); border-bottom: 1px solid var(--border-subtle); background: var(--surface-primary); }
.reports-page__toolbar-left { display: flex; align-items: center; gap: var(--spacing-2); min-width: 0; }
.reports-page__toolbar :deep(.el-select) { width: 112px; }
.reports-page__result-count { font-variant-numeric: tabular-nums; white-space: nowrap; }

.reports-page__workspace {
  display: grid;
  min-width: 0;
  min-block-size: 220px;
  background: var(--surface-primary);
  border: 1px solid var(--border-default);
}

.reports-page__workspace :deep(.report-row) {
  min-height: 52px;
}

.reports-page__feedback {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
  min-block-size: 48px;
}

.reports-page__pagination {
  justify-content: center;
  min-height: 32px;
}
.reports-page__pagination--top { margin-left: auto; }

.reports-page__poll-note {
  margin: 0;
  padding: var(--spacing-2) var(--spacing-3);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
  text-align: center;
  background: var(--surface-secondary);
  border-left: 2px solid var(--color-primary);
}

@media (max-width: 767px) {
  .reports-page__header :deep(.el-button) {
    width: 100%;
    min-height: 44px;
  }

  .reports-page__workspace :deep(.report-row) {
    min-height: 64px;
  }

  .reports-page__toolbar { align-items: flex-start; flex-direction: column; padding: var(--spacing-2); }
  .reports-page__toolbar-left { width: 100%; }
  .reports-page__toolbar :deep(.el-select) { flex: 1; width: auto; }

  .reports-page__pagination :deep(.btn-prev),
  .reports-page__pagination :deep(.btn-next) {
    min-width: 44px;
    min-height: 44px;
  }

  .reports-page__page-status {
    color: var(--text-secondary);
    font-size: var(--font-size-sm);
    white-space: nowrap;
  }
}
</style>
