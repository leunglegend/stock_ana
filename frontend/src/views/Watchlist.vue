<template>
  <div class="watchlist-page workbench-page">
    <header class="watchlist-page__header workbench-page__header">
      <div>
        <h1 data-page-title class="watchlist-page__title">我的自选</h1>
        <p class="watchlist-page__subtitle">{{ activeGroupName }} · {{ activeStocks.length }} 只<template v-if="errorCount"> · {{ errorCount }} 只行情待重试</template></p>
      </div>
      <div class="watchlist-page__header-actions">
        <el-button :icon="Refresh" :loading="quotesLoading" aria-label="刷新当前分组行情" @click="refreshQuotes">刷新</el-button>
        <el-button v-if="!cloudStateLocked" type="primary" @click="showAddDialog = true">添加股票</el-button>
      </div>
    </header>
    <StatusState v-if="cloudError" state="error" title="云端自选股暂时不可用" :description="cloudError">
      <template #action><el-button type="primary" @click="retryEnterCloudMode">重试连接云端</el-button></template>
    </StatusState>
    <StatusState
      v-else-if="showCloudLoadingState"
      state="loading"
      title="正在连接云端自选股"
      description="连接成功后会展示云端的最新自选股数据。"
    />
    <template v-else>
      <section class="watchlist-page__toolbar" aria-label="自选研究工具">
        <div class="watchlist-page__toolbar-top">
          <GroupTabs :groups="groups" :active-id="activeGroupId" @change="store.setActiveGroup($event)"
            @create="handleCreateGroup" @rename="handleRenameGroup" @remove="handleRemoveGroup" />
        </div>
        <WatchlistFilters v-model:keyword="keyword" v-model:movement="movementFilter" v-model:sort-by="sortBy"
          v-model:only-cost="onlyCost" :total="filteredRows.length" :updated-at="lastUpdatedAt"
          :loading="quotesLoading" @clear="clearFilters" />
      </section>
      <StatusState v-if="activeStocks.length === 0" state="empty" title="当前分组还没有股票" description="添加股票后，这里会按真实接口逐行补齐行情。">
        <template #action><el-button type="primary" @click="showAddDialog = true">添加股票</el-button></template>
      </StatusState>
      <StatusState v-else-if="filteredRows.length === 0" state="empty" title="没有匹配结果" description="请调整筛选条件，或清空筛选后重试。">
        <template #action><el-button type="primary" plain @click="clearFilters">清空筛选</el-button></template>
      </StatusState>
      <section v-else class="watchlist-page__workspace">
        <div class="watchlist-page__queue">
          <WatchlistMobileList v-if="isMobile" :rows="paginatedRows" @open="openDetail" @edit="openEditDialog"
            @remove="handleRemoveStock" @retry="retryQuote" />
          <WatchlistTable v-else :rows="paginatedRows" :loading="quotesLoading" :signals="signalResults"
            @open="openDetail" @edit="openEditDialog" @remove="handleRemoveStock" @retry="retryQuote" />
          <div v-if="filteredRows.length > pageSize" class="watchlist-page__pagination-row">
            <span class="watchlist-page__range">第 {{ (currentPage - 1) * pageSize + 1 }}–{{ Math.min(currentPage * pageSize, filteredRows.length) }} 项，共 {{ filteredRows.length }} 项</span>
            <el-pagination class="watchlist-page__pagination" background :size="isMobile ? 'default' : 'small'" :layout="paginationLayout"
              :total="filteredRows.length" :page-size="pageSize" :current-page="currentPage"
              @current-change="currentPage = $event" />
            <span v-if="isMobile" class="watchlist-page__page-status" aria-live="polite">第 {{ currentPage }} / {{ pageCount }} 页</span>
          </div>
        </div>
        <aside class="watchlist-page__inspector">
          <WatchlistSignalCenter :results="signalResults" :summary="signalSummary" :scanning="signalsScanning"
            :completed="signalsCompleted" :progress="signalProgress" :stock-count="activeStocks.length"
            :last-scanned-at="lastSignalScanAt" :quote-rows="quoteRows" @scan="scanSignals" />
        </aside>
      </section>

      <WatchlistAddDialog
        v-model:visible="showAddDialog"
        :groups="groups"
        :default-group-id="activeGroupId"
        :submitting="adding"
        @submit="handleAddStock"
      />

      <WatchlistEditDialog
        v-model:visible="showEditDialog"
        :row="editingRow"
        :submitting="editing"
        @submit="handleEditStock"
        @update:visible="handleEditDialogVisible"
      />
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { ElMessageBox } from 'element-plus/es/components/message-box/index.mjs'
import { Refresh } from '@element-plus/icons-vue'
import StatusState from '@/components/base/StatusState.vue'
import GroupTabs from '@/components/watchlist/GroupTabs.vue'
import WatchlistAddDialog from '@/components/watchlist/WatchlistAddDialog.vue'
import WatchlistEditDialog from '@/components/watchlist/WatchlistEditDialog.vue'
import WatchlistFilters from '@/components/watchlist/WatchlistFilters.vue'
import WatchlistMobileList from '@/components/watchlist/WatchlistMobileList.vue'
import WatchlistSignalCenter from '@/components/watchlist/WatchlistSignalCenter.vue'
import WatchlistTable from '@/components/watchlist/WatchlistTable.vue'
import { useWatchlistRows } from '@/components/watchlist/useWatchlistRows'
import { useWatchlistSignals } from '@/components/watchlist/useWatchlistSignals'
import { useResponsive } from '@/composables/useResponsive'
import { useWatchlistStore } from '@/store'

const router = useRouter()
const store = useWatchlistStore()
const { isMobile } = useResponsive()

const showAddDialog = ref(false)
const showEditDialog = ref(false)
const adding = ref(false)
const editing = ref(false)
const editingRow = ref(null)
const currentPage = ref(1)
const pageSize = 10
const paginationLayout = computed(() => isMobile.value ? 'prev, next' : 'total, prev, pager, next')

const groups = computed(() => store.groups)
const activeGroupId = computed(() => store.activeGroup)
const activeGroup = computed(() => groups.value.find((group) => group.id === activeGroupId.value) || groups.value[0] || null)
const activeGroupName = computed(() => activeGroup.value?.name || '我的自选')
const activeStocks = computed(() => activeGroup.value?.stocks || [])
const cloudError = computed(() => store.cloudError)
const showCloudLoadingState = computed(() => store.cloudMode && store.loading && !cloudError.value && activeStocks.value.length === 0)
const cloudStateLocked = computed(() => Boolean(cloudError.value) || showCloudLoadingState.value)

const {
  quoteRows,
  keyword,
  movementFilter,
  sortBy,
  onlyCost,
  filteredRows,
  quotesLoading,
  errorCount,
  lastUpdatedAt,
  retryQuote,
  refreshQuotes,
  patchRow,
  clearFilters,
} = useWatchlistRows(activeGroupId, activeStocks)

const paginatedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredRows.value.slice(start, start + pageSize)
})
const pageCount = computed(() => Math.max(1, Math.ceil(filteredRows.value.length / pageSize)))

watch([activeGroupId, keyword, movementFilter, sortBy, onlyCost], () => {
  currentPage.value = 1
})

watch(() => filteredRows.value.length, (count) => {
  const lastPage = Math.max(1, Math.ceil(count / pageSize))
  if (currentPage.value > lastPage) currentPage.value = lastPage
})

const {
  results: signalResults,
  scanning: signalsScanning,
  completed: signalsCompleted,
  lastScannedAt: lastSignalScanAt,
  summary: signalSummary,
  progress: signalProgress,
  scan: scanSignals,
} = useWatchlistSignals(activeGroupId, activeStocks, quoteRows)

async function retryEnterCloudMode() {
  if (store.loading) return
  await store._enterCloudMode()
}

async function handleCreateGroup() {
  try {
    const { value } = await ElMessageBox.prompt('请输入分组名称', '新建分组', { inputPattern: /\S+/, inputErrorMessage: '分组名称不能为空' })
    const name = value.trim()
    const nextId = await store.addGroup(name)
    if (!nextId) return
    store.setActiveGroup(String(nextId))
    ElMessage.success(`已创建分组「${name}」`)
  } catch {}
}

async function handleRenameGroup(groupId) {
  const group = groups.value.find((item) => item.id === groupId)
  if (!group) return
  try {
    const { value } = await ElMessageBox.prompt('请输入新的分组名称', '重命名分组', {
      inputValue: group.name,
      inputPattern: /\S+/,
      inputErrorMessage: '分组名称不能为空',
    })
    if (await store.renameGroup(groupId, value.trim())) ElMessage.success('分组已重命名')
  } catch {}
}

async function handleRemoveGroup(groupId) {
  const group = groups.value.find((item) => item.id === groupId)
  if (!group || groups.value.length <= 1) return
  try {
    await ElMessageBox.confirm(`确定删除分组「${group.name}」吗？其中股票会一并移出当前分组。`, '删除分组', { type: 'warning' })
    if (await store.removeGroup(groupId)) ElMessage.success('分组已删除')
  } catch {}
}

async function handleAddStock(payload) {
  if (adding.value) return
  adding.value = true
  try {
    const result = await store.addStockToGroup(payload.groupId, {
      code: payload.stock.code,
      name: payload.stock.name,
      cost: payload.cost,
      remark: payload.remark,
    })
    if (result.success) {
      ElMessage.success(`已将「${payload.stock.name}」加入「${result.groupName}」`)
      showAddDialog.value = false
      return
    }
    if (result.reason === 'duplicate') return void ElMessage.warning(`「${payload.stock.name}」已在「${result.groupName}」中`)
    ElMessage.error('加入自选失败')
  } finally {
    adding.value = false
  }
}

function openEditDialog(row) {
  editingRow.value = { ...row }
  showEditDialog.value = true
}

function handleEditDialogVisible(visible) {
  showEditDialog.value = visible
  if (!visible) editingRow.value = null
}

async function handleEditStock(payload) {
  if (!editingRow.value || editing.value) return
  editing.value = true
  try {
    const result = await store.updateStock(payload.code, { cost: payload.cost, remark: payload.remark }, activeGroupId.value)
    if (!result?.success) return
    patchRow(payload.code, { cost: payload.cost, remark: payload.remark })
    ElMessage.success('已更新成本与备注')
    handleEditDialogVisible(false)
  } finally {
    editing.value = false
  }
}

async function handleRemoveStock(row) {
  try {
    await ElMessageBox.confirm(`确定移除「${row.name} (${row.code})」吗？`, '移除股票', { type: 'warning' })
    await store.removeStock(row.code, activeGroupId.value)
    if (!activeStocks.value.some((item) => item.code === row.code)) ElMessage.success('已移除自选')
  } catch {}
}

function openDetail(code) {
  router.push(`/stock/${code}`)
}
</script>

<style scoped>
.watchlist-page { gap: var(--spacing-3); }
.watchlist-page__title { margin: 0; color: var(--text-primary); font-size: var(--font-size-2xl); }
.watchlist-page__subtitle { margin: 4px 0 0; color: var(--text-secondary); line-height: 1.4; }
.watchlist-page__header-actions { display: flex; align-items: center; gap: var(--spacing-2); }
.watchlist-page__toolbar { display: grid; gap: var(--spacing-2); padding: var(--spacing-2) var(--spacing-3); border: 1px solid var(--border-default); border-radius: var(--radius-panel); background: var(--surface-panel); }
.watchlist-page__toolbar-top { display: flex; align-items: center; min-width: 0; }
.watchlist-page__workspace { display: grid; grid-template-columns: minmax(0, 1fr) 320px; min-width: 0; border: 1px solid var(--border-default); border-radius: var(--radius-panel); background: var(--surface-panel); overflow: hidden; }
.watchlist-page__queue { min-width: 0; }
.watchlist-page__inspector { min-width: 0; border-left: 1px solid var(--border-default); }
.watchlist-page__pagination-row { display: flex; align-items: center; justify-content: space-between; gap: var(--spacing-3); min-height: 40px; padding: 0 var(--spacing-3); border-top: 1px solid var(--border-subtle); color: var(--text-tertiary); font-size: var(--font-size-xs); }
@media (max-width: 767px) {
  .watchlist-page__header { align-items: stretch; }
  .watchlist-page__header-actions { width: 100%; }
  .watchlist-page__header-actions :deep(.el-button) { flex: 1; min-height: 44px; }
  .watchlist-page__toolbar { padding: var(--spacing-3); }
  .watchlist-page__workspace { grid-template-columns: minmax(0, 1fr); }
  .watchlist-page__inspector { border-top: 1px solid var(--border-default); border-left: 0; }
  .watchlist-page__pagination-row { justify-content: center; }
  .watchlist-page__range { display: none; }
  .watchlist-page__page-status { color: var(--text-secondary); font-size: var(--font-size-sm); white-space: nowrap; }
  .watchlist-page__pagination :deep(.btn-prev),
  .watchlist-page__pagination :deep(.btn-next) {
    min-width: 44px;
    min-height: 44px;
  }
}
</style>
