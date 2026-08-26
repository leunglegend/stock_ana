<template>
  <div class="board-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">板块监控</h2>
        <p class="page-subtitle">实时追踪行业与概念板块动向，把握市场热点</p>
      </div>
    </div>

    <!-- Tab 切换 -->
    <el-tabs v-model="activeTab" class="board-tabs" @tab-change="onTabChange">
      <el-tab-pane label="行业板块" name="industry">
        <div class="board-grid">
          <div
            v-for="(board, idx) in industryBoards"
            :key="board.name"
            class="board-card card-shadow"
            :class="{ up: board.change_pct > 0, down: board.change_pct < 0 }"
            @click="showBoardDetail(board.name, 'industry')"
          >
            <div class="board-header">
              <span class="rank" :class="'rank-' + (idx + 1)">{{ idx + 1 }}</span>
              <span class="name">{{ board.name }}</span>
            </div>
            <div class="board-change">
              <span class="change-pct">
                {{ board.change_pct > 0 ? '+' : '' }}{{ board.change_pct?.toFixed(2) }}%
              </span>
            </div>
            <div class="board-footer">
              <span class="leader">领涨：{{ board.leading_stock || '--' }}</span>
              <span class="stock-count">{{ board.stock_count }} 只</span>
            </div>
          </div>
          <el-empty v-if="!loading.industry && industryBoards.length === 0" description="暂无数据" />
        </div>
      </el-tab-pane>

      <el-tab-pane label="概念板块" name="concept">
        <div class="board-grid">
          <div
            v-for="(board, idx) in conceptBoards"
            :key="board.name"
            class="board-card card-shadow"
            :class="{ up: board.change_pct > 0, down: board.change_pct < 0 }"
            @click="showBoardDetail(board.name, 'concept')"
          >
            <div class="board-header">
              <span class="rank" :class="'rank-' + (idx + 1)">{{ idx + 1 }}</span>
              <span class="name">{{ board.name }}</span>
            </div>
            <div class="board-change">
              <span class="change-pct">
                {{ board.change_pct > 0 ? '+' : '' }}{{ board.change_pct?.toFixed(2) }}%
              </span>
            </div>
            <div class="board-footer">
              <span class="leader">领涨：{{ board.leading_stock || '--' }}</span>
              <span class="stock-count">{{ board.stock_count }} 只</span>
            </div>
          </div>
          <el-empty v-if="!loading.concept && conceptBoards.length === 0" description="暂无数据" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 板块详情抽屉 -->
    <el-drawer
      v-model="detailVisible"
      :title="currentBoardName"
      direction="rtl"
      size="600px"
    >
      <div v-loading="loading.detail">
        <div class="drawer-header">
          <div class="drawer-change" :class="{ up: boardDetailChange > 0, down: boardDetailChange < 0 }">
            {{ boardDetailChange > 0 ? '+' : '' }}{{ boardDetailChange?.toFixed(2) }}%
          </div>
          <div class="drawer-stats">
            <span>成分股 {{ boardStocks.length }} 只</span>
          </div>
        </div>

        <!-- 加载失败提示 -->
        <div v-if="detailError" class="detail-error">
          <el-empty description="成分股数据加载失败">
            <el-button type="primary" @click="retryLoadDetail">重新加载</el-button>
          </el-empty>
        </div>

        <!-- 空状态 -->
        <div v-else-if="boardStocks.length === 0 && !loading.detail" class="detail-empty">
          <el-empty description="暂无成分股数据" />
        </div>

        <!-- 成分股列表 -->
        <el-table
          v-else
          :data="boardStocks"
          style="width: 100%"
          @row-click="goToStock"
        >
          <el-table-column prop="name" label="名称" width="120">
            <template #default="{ row }">
              <div class="stock-name">
                <span class="name">{{ row.name }}</span>
                <span class="code">{{ row.code }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="price" label="最新价" width="100" align="right">
            <template #default="{ row }">
              <span :class="row.change_pct > 0 ? 'up' : 'down'">
                {{ row.price?.toFixed(2) || '--' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="change_pct" label="涨跌幅" width="100" align="right">
            <template #default="{ row }">
              <span :class="row.change_pct > 0 ? 'up' : (row.change_pct < 0 ? 'down' : '')">
                {{ row.change_pct > 0 ? '+' : '' }}{{ row.change_pct?.toFixed(2) }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="turnover_rate" label="换手率" width="90" align="right">
            <template #default="{ row }">
              {{ row.turnover_rate?.toFixed(2) || '--' }}%
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click.stop="addToWatchlist(row)">
                + 自选
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useWatchlistStore } from '../store'
import { getBoardIndustry, getBoardConcept, getBoardStocks } from '../api/stock'

const router = useRouter()
const store = useWatchlistStore()

const activeTab = ref('industry')
const loading = reactive({
  industry: false,
  concept: false,
  detail: false,
})

const industryBoards = ref([])
const conceptBoards = ref([])

const detailVisible = ref(false)
const currentBoardName = ref('')
const currentBoardType = ref('')
const boardStocks = ref([])
const boardDetailChange = ref(0)
const detailError = ref(false)

async function loadIndustryBoards() {
  loading.industry = true
  try {
    const data = await getBoardIndustry()
    industryBoards.value = data.slice(0, 30)
  } catch (e) {
    console.error('加载行业板块失败:', e)
    industryBoards.value = []
  } finally {
    loading.industry = false
  }
}

async function loadConceptBoards() {
  loading.concept = true
  try {
    const data = await getBoardConcept()
    conceptBoards.value = data.slice(0, 30)
  } catch (e) {
    console.error('加载概念板块失败:', e)
    conceptBoards.value = []
  } finally {
    loading.concept = false
  }
}

function onTabChange(tab) {
  if (tab === 'industry' && industryBoards.value.length === 0) {
    loadIndustryBoards()
  } else if (tab === 'concept' && conceptBoards.value.length === 0) {
    loadConceptBoards()
  }
}

async function showBoardDetail(name, type) {
  currentBoardName.value = name
  currentBoardType.value = type
  detailVisible.value = true
  detailError.value = false
  await loadBoardDetail(name, type)
}

async function loadBoardDetail(name, type) {
  loading.detail = true
  detailError.value = false

  try {
    const data = await getBoardStocks(type, name)
    boardStocks.value = data.slice(0, 50) // 取前50只
    // 计算板块平均涨跌幅
    if (data.length > 0) {
      const avgChange = data.reduce((sum, s) => sum + (s.change_pct || 0), 0) / data.length
      boardDetailChange.value = avgChange
    } else {
      boardDetailChange.value = 0
    }
  } catch (e) {
    boardStocks.value = []
    boardDetailChange.value = 0
    detailError.value = true
  } finally {
    loading.detail = false
  }
}

function retryLoadDetail() {
  loadBoardDetail(currentBoardName.value, currentBoardType.value)
}

function goToStock(row) {
  router.push(`/stock/${row.code}`)
}

function addToWatchlist(row) {
  const success = store.addStock({ code: row.code, name: row.name })
  if (success) {
    ElMessage.success(`已添加「${row.name}」到自选`)
  } else {
    ElMessage.warning('已在自选列表中')
  }
}

onMounted(() => {
  loadIndustryBoards()
})
</script>

<style scoped>
.board-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 16px;
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

.board-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}
.board-tabs :deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 600;
}

/* 板块卡片网格 */
.board-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  min-height: 300px;
}

.board-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px 18px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #f0f0f0;
  position: relative;
  overflow: hidden;
}

.board-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.1);
}

.board-card.up {
  border-top: 3px solid #ef4444;
}
.board-card.down {
  border-top: 3px solid #10b981;
}

.board-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.rank {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: #f3f4f6;
  color: #6b7280;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.rank-1 { background: #fee2e2; color: #dc2626; }
.rank-2 { background: #fed7aa; color: #ea580c; }
.rank-3 { background: #fef3c7; color: #d97706; }

.name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.board-change {
  margin-bottom: 12px;
}
.change-pct {
  font-size: 24px;
  font-weight: 700;
}
.up .change-pct { color: #ef4444; }
.down .change-pct { color: #10b981; }

.board-footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #9ca3af;
  padding-top: 10px;
  border-top: 1px dashed #f0f0f0;
}
.leader {
  max-width: 60%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 抽屉 */
.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}
.detail-error,
.detail-empty {
  padding: 40px 0;
}
.drawer-change {
  font-size: 28px;
  font-weight: 700;
}
.drawer-change.up { color: #ef4444; }
.drawer-change.down { color: #10b981; }
.drawer-stats {
  font-size: 14px;
  color: #6b7280;
}

.stock-name {
  display: flex;
  flex-direction: column;
}
.stock-name .name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}
.stock-name .code {
  font-size: 12px;
  color: #9ca3af;
}

.up { color: #ef4444; }
.down { color: #10b981; }

/* 响应式 */
@media (max-width: 1200px) {
  .board-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 768px) {
  .board-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
