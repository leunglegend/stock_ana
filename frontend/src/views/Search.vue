<template>
  <div class="search-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">搜索个股</h2>
        <p class="page-subtitle">输入股票代码或名称，快速找到你关注的股票</p>
      </div>
    </div>

    <!-- 搜索框 -->
    <div class="search-box card-shadow">
      <el-input
        v-model="keyword"
        size="large"
        placeholder="输入股票代码或名称，如 600519 或 贵州茅台"
        :prefix-icon="Search"
        clearable
        @input="handleInput"
        @keyup.enter="doSearch"
        @clear="handleClear"
      />
      <el-button
        type="primary"
        size="large"
        :loading="loading"
        @click="doSearch"
        style="margin-left: 12px"
      >
        搜索
      </el-button>
    </div>

    <!-- 搜索结果 -->
    <div v-if="keyword" class="search-result-card card-shadow">
      <div v-loading="loading" class="result-content">
        <div v-if="results.length > 0" class="result-header">
          <span>找到 {{ results.length }} 只相关股票</span>
        </div>

        <el-table
          v-if="results.length > 0"
          :data="results"
          style="width: 100%"
          @row-click="goToDetail"
          :row-class-name="tableRowClassName"
          class="result-table"
          :header-cell-style="{ background: '#f9fafb', color: '#6b7280', fontWeight: 500 }"
        >
          <el-table-column prop="name" label="股票名称" width="180">
            <template #default="{ row }">
              <div class="stock-name-cell">
                <span class="name">{{ row.name }}</span>
                <span class="code">{{ row.code }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="price" label="最新价" width="120" align="right">
            <template #default="{ row }">
              <span :class="row.change_pct > 0 ? 'up' : (row.change_pct < 0 ? 'down' : '')">
                {{ row.price?.toFixed(2) || '--' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="change_pct" label="涨跌幅" width="120" align="right">
            <template #default="{ row }">
              <span :class="row.change_pct > 0 ? 'up' : (row.change_pct < 0 ? 'down' : '')">
                {{ row.change_pct > 0 ? '+' : '' }}{{ row.change_pct?.toFixed(2) }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" align="center" fixed="right">
            <template #default="{ row }">
              <el-button
                type="primary"
                link
                size="small"
                @click.stop="goToDetail(row)"
              >
                查看详情
              </el-button>
              <el-button
                :type="isWatched(row.code) ? 'success' : 'primary'"
                link
                size="small"
                @click.stop="toggleWatch(row)"
              >
                {{ isWatched(row.code) ? '已自选' : '+ 自选' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-else-if="!loading" description="未找到匹配的股票" />
      </div>
    </div>

    <!-- 空状态提示（未搜索时） -->
    <div v-else class="empty-hint card-shadow">
      <el-icon :size="48" color="#d1d5db"><Search /></el-icon>
      <p class="hint-title">输入关键词开始搜索</p>
      <p class="hint-desc">支持股票代码、股票名称模糊搜索</p>
      <div class="hot-stocks">
        <span class="hot-label">热门搜索：</span>
        <el-button
          v-for="stock in hotStocks"
          :key="stock.code"
          type="primary"
          link
          size="small"
          @click="quickSearch(stock.name)"
        >
          {{ stock.name }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { searchStock, getStockInfo } from '../api/stock'
import { useWatchlistStore } from '../store'

const router = useRouter()
const store = useWatchlistStore()

const keyword = ref('')
const results = ref([])
const loading = ref(false)

let searchTimer = null

// 热门搜索
const hotStocks = [
  { code: '600519', name: '贵州茅台' },
  { code: '000858', name: '五粮液' },
  { code: '000001', name: '平安银行' },
  { code: '601318', name: '中国平安' },
  { code: '300750', name: '宁德时代' },
]

function handleInput(val) {
  if (!val) {
    results.value = []
    return
  }
  // 防抖
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    doSearch()
  }, 300)
}

function handleClear() {
  results.value = []
}

async function doSearch() {
  const q = keyword.value.trim()
  if (!q) {
    results.value = []
    return
  }

  loading.value = true
  try {
    const list = await searchStock(q)
    // 逐个获取实时行情
    const withPrice = []
    for (const item of list.slice(0, 20)) {
      try {
        const info = await getStockInfo(item.code)
        withPrice.push({
          ...item,
          price: info.price,
          change_pct: info.change_pct,
        })
      } catch (e) {
        withPrice.push({
          ...item,
          price: null,
          change_pct: 0,
        })
      }
    }
    results.value = withPrice
  } catch (e) {
    console.error('搜索失败:', e)
    results.value = []
  } finally {
    loading.value = false
  }
}

function quickSearch(name) {
  keyword.value = name
  doSearch()
}

function goToDetail(row) {
  router.push(`/stock/${row.code}`)
}

function isWatched(code) {
  return store.isWatched(code)
}

async function toggleWatch(row) {
  if (isWatched(row.code)) {
    await store.removeStock(row.code)
    ElMessage.success(`已移除「${row.name}」`)
  } else {
    const success = await store.addStock({
      code: row.code,
      name: row.name,
    })
    if (success) {
      ElMessage.success(`已添加「${row.name}」到自选`)
    } else {
      ElMessage.warning('已在自选列表中')
    }
  }
}

function tableRowClassName({ row }) {
  if (!row.change_pct) return ''
  return row.change_pct > 0 ? 'row-up' : row.change_pct < 0 ? 'row-down' : ''
}
</script>

<style scoped>
.search-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
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

/* 搜索框 */
.search-box {
  display: flex;
  align-items: center;
  background: #fff;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 20px;
}

.search-box :deep(.el-input) {
  flex: 1;
}

/* 搜索结果 */
.search-result-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
}

.result-content {
  padding: 8px 16px 16px;
}

.result-header {
  font-size: 14px;
  color: #6b7280;
  padding: 12px 4px;
  border-bottom: 1px solid #f3f4f6;
  margin-bottom: 4px;
}

.result-table {
  margin-top: 8px;
}

.stock-name-cell {
  display: flex;
  flex-direction: column;
}

.stock-name-cell .name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.stock-name-cell .code {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 2px;
}

.up { color: #ef4444; }
.down { color: #10b981; }

/* 行背景色 */
:deep(.el-table__row.row-up:hover) {
  background-color: rgba(239, 68, 68, 0.04);
}
:deep(.el-table__row.row-down:hover) {
  background-color: rgba(16, 185, 129, 0.04);
}

/* 空状态 */
.empty-hint {
  background: #fff;
  border-radius: 12px;
  padding: 60px 40px;
  text-align: center;
}

.hint-title {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  margin: 16px 0 8px;
}

.hint-desc {
  font-size: 14px;
  color: #9ca3af;
  margin: 0 0 20px;
}

.hot-stocks {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 4px;
}

.hot-label {
  font-size: 13px;
  color: #9ca3af;
  margin-right: 4px;
}

.card-shadow {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
}
</style>
