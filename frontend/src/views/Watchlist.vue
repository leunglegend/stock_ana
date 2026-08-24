<template>
  <div class="watchlist-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">我的自选股</h2>
        <p class="page-subtitle">共 {{ activeStocks.length }} 只股票 · {{ activeGroupName }}</p>
      </div>
      <div class="header-actions">
        <el-select v-model="activeGroup" @change="onGroupChange" style="width: 140px; margin-right: 12px;">
          <el-option
            v-for="group in groups"
            :key="group.id"
            :label="group.name"
            :value="group.id"
          />
        </el-select>
        <el-button type="primary" :icon="Plus" @click="showAddDialog = true">
          添加股票
        </el-button>
        <el-dropdown @command="handleGroupCommand">
          <el-button :icon="MoreFilled" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="add-group">新建分组</el-dropdown-item>
              <el-dropdown-item command="rename-group" :disabled="groups.length <= 1">重命名分组</el-dropdown-item>
              <el-dropdown-item command="delete-group" :disabled="groups.length <= 1">删除分组</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 盈亏总览卡片 -->
    <el-card v-if="activeStocks.length > 0" class="summary-card card-shadow">
      <el-row :gutter="24">
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">总市值</div>
            <div class="summary-value">¥{{ totalValue.toFixed(2) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">总成本</div>
            <div class="summary-value">¥{{ totalCost.toFixed(2) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">总盈亏</div>
            <div class="summary-value" :class="{ up: totalProfit > 0, down: totalProfit < 0 }">
              {{ totalProfit > 0 ? '+' : '' }}¥{{ totalProfit.toFixed(2) }}
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <div class="summary-label">收益率</div>
            <div class="summary-value" :class="{ up: totalProfitRate > 0, down: totalProfitRate < 0 }">
              {{ totalProfitRate > 0 ? '+' : '' }}{{ totalProfitRate.toFixed(2) }}%
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 股票列表 -->
    <el-card class="list-card card-shadow">
      <el-table
        :data="stockListData"
        v-loading="loading"
        style="width: 100%"
        :row-class-name="tableRowClassName"
      >
        <el-table-column prop="name" label="股票名称" width="150">
          <template #default="{ row }">
            <div class="stock-name-cell">
              <span class="star-btn" @click.stop="toggleWatch(row)">
                <el-icon :size="16" color="#f59e0b"><StarFilled /></el-icon>
              </span>
              <span class="name">{{ row.name }}</span>
              <span class="code">{{ row.code }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="price" label="最新价" width="120" align="right">
          <template #default="{ row }">
            <span class="price" :class="priceClass(row)">
              {{ row.price ? row.price.toFixed(2) : '--' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="change_pct" label="涨跌幅" width="120" align="right">
          <template #default="{ row }">
            <span :class="priceClass(row)">
              {{ row.change_pct > 0 ? '+' : '' }}{{ row.change_pct?.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="cost" label="成本价" width="120" align="right">
          <template #default="{ row }">
            <span v-if="row.cost">{{ row.cost.toFixed(2) }}</span>
            <el-button v-else type="primary" link size="small" @click="editCost(row)">
              设置成本
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="盈亏" width="140" align="right">
          <template #default="{ row }">
            <div v-if="row.cost && row.price">
              <span :class="profitClass(row)">
                {{ row.profit > 0 ? '+' : '' }}{{ row.profit?.toFixed(2) }}
              </span>
              <span class="profit-rate" :class="profitClass(row)">
                ({{ row.profitRate > 0 ? '+' : '' }}{{ row.profitRate?.toFixed(2) }}%)
              </span>
            </div>
            <span v-else class="text-muted">--</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="goToDetail(row)">
              分析
            </el-button>
            <el-button type="primary" link size="small" @click="editCost(row)">
              成本
            </el-button>
            <el-button type="danger" link size="small" @click="removeStock(row)">
              移除
            </el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="暂无自选股，点击「添加股票」开始关注">
            <el-button type="primary" @click="showAddDialog = true">添加股票</el-button>
          </el-empty>
        </template>
      </el-table>
    </el-card>

    <!-- 添加股票对话框 -->
    <el-dialog v-model="showAddDialog" title="添加自选股" width="500px">
      <el-form label-position="top">
        <el-form-item label="搜索股票">
          <StockSearch @select="onStockSelect" />
        </el-form-item>
        <el-form-item v-if="selectedStock" label="股票信息">
          <div class="selected-stock">
            <span class="name">{{ selectedStock.name }}</span>
            <span class="code">{{ selectedStock.code }}</span>
            <el-tag type="success" size="small" v-if="isWatched(selectedStock.code)">已关注</el-tag>
          </div>
        </el-form-item>
        <el-form-item v-if="selectedStock" label="成本价（可选）">
          <el-input-number
            v-model="costPrice"
            :precision="2"
            :step="0.01"
            :min="0"
            placeholder="输入成本价"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!selectedStock || isWatched(selectedStock?.code)" @click="confirmAdd">
          添加
        </el-button>
      </template>
    </el-dialog>

    <!-- 设置成本对话框 -->
    <el-dialog v-model="showCostDialog" title="设置成本价" width="400px">
      <el-form label-position="top">
        <el-form-item label="股票">
          <span>{{ currentStock?.name }}（{{ currentStock?.code }}）</span>
        </el-form-item>
        <el-form-item label="成本价">
          <el-input-number
            v-model="costPrice"
            :precision="2"
            :step="0.01"
            :min="0"
            placeholder="输入成本价"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCostDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmCost">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, MoreFilled, StarFilled,
} from '@element-plus/icons-vue'
import { useWatchlistStore } from '../store'
import StockSearch from '../components/StockSearch.vue'
import { getStockInfo } from '../api/stock'

const router = useRouter()
const store = useWatchlistStore()

const loading = ref(false)
const showAddDialog = ref(false)
const showCostDialog = ref(false)
const selectedStock = ref(null)
const currentStock = ref(null)
const costPrice = ref(0)
const stockListData = ref([])

const activeGroup = computed({
  get: () => store.activeGroup,
  set: (val) => store.setActiveGroup(val),
})

const groups = computed(() => store.groupNames)
const activeStocks = computed(() => store.activeStocks)

const activeGroupName = computed(() => {
  const g = groups.value.find(g => g.id === activeGroup.value)
  return g ? g.name : ''
})

// 计算持仓盈亏
const totalCost = computed(() => {
  return stockListData.value.reduce((sum, s) => {
    return sum + (s.cost && s.shares ? s.cost * s.shares : 0)
  }, 0)
})

const totalValue = computed(() => {
  return stockListData.value.reduce((sum, s) => {
    return sum + (s.price && s.shares ? s.price * s.shares : 0)
  }, 0)
})

const totalProfit = computed(() => totalValue.value - totalCost.value)
const totalProfitRate = computed(() => {
  if (totalCost.value === 0) return 0
  return (totalProfit.value / totalCost.value) * 100
})

function priceClass(row) {
  if (!row.change_pct) return ''
  return row.change_pct > 0 ? 'up' : row.change_pct < 0 ? 'down' : ''
}

function profitClass(row) {
  if (!row.profit) return ''
  return row.profit > 0 ? 'up' : (row.profit < 0 ? 'down' : '')
}

function tableRowClassName({ row }) {
  return profitClass(row) ? `row-${profitClass(row)}` : ''
}

// 加载股票实时行情
async function loadStockPrices() {
  if (activeStocks.value.length === 0) {
    stockListData.value = []
    return
  }

  loading.value = true
  try {
    // 逐个获取行情（避免并发太高）
    const results = []
    for (const stock of activeStocks.value) {
      try {
        const info = await getStockInfo(stock.code)
        results.push({
          ...stock,
          price: info.price,
          change_pct: info.change_pct,
          change_amount: info.change_amount,
          profit: stock.cost ? info.price - stock.cost : 0,
          profitRate: stock.cost ? ((info.price - stock.cost) / stock.cost) * 100 : 0,
          shares: 100, // 默认100股，后续可改
        })
      } catch (e) {
        results.push({ ...stock, price: 0, change_pct: 0, profit: 0, profitRate: 0, shares: 100 })
      }
    }
    stockListData.value = results
  } catch (e) {
    ElMessage.error('加载行情失败')
  } finally {
    loading.value = false
  }
}

function onStockSelect(stock) {
  selectedStock.value = stock
  costPrice.value = 0
}

function isWatched(code) {
  return store.isWatched(code)
}

async function confirmAdd() {
  if (!selectedStock.value) return
  const success = await store.addStock({
    code: selectedStock.value.code,
    name: selectedStock.value.name,
    cost: costPrice.value || 0,
  })
  if (success) {
    ElMessage.success('添加成功')
    showAddDialog.value = false
    selectedStock.value = null
    loadStockPrices()
  } else {
    ElMessage.warning('该股票已在自选列表中')
  }
}

async function toggleWatch(row) {
  await store.removeStock(row.code)
  loadStockPrices()
  ElMessage.success('已移除自选')
}

function removeStock(row) {
  ElMessageBox.confirm(`确定要移除「${row.name}」吗？`, '提示', {
    type: 'warning',
  }).then(async () => {
    await store.removeStock(row.code)
    loadStockPrices()
    ElMessage.success('移除成功')
  }).catch(() => {})
}

function editCost(row) {
  currentStock.value = row
  costPrice.value = row.cost || 0
  showCostDialog.value = true
}

async function confirmCost() {
  if (!currentStock.value) return
  await store.updateCost(currentStock.value.code, costPrice.value)
  loadStockPrices()
  showCostDialog.value = false
  ElMessage.success('成本价已更新')
}

function goToDetail(row) {
  router.push(`/stock/${row.code}`)
}

function onGroupChange() {
  loadStockPrices()
}

function handleGroupCommand(cmd) {
  if (cmd === 'add-group') {
    ElMessageBox.prompt('请输入分组名称', '新建分组', {
      inputPattern: /\S+/,
      inputErrorMessage: '分组名称不能为空',
    }).then(async ({ value }) => {
      const id = await store.addGroup(value)
      if (id) {
        ElMessage.success('创建成功')
      }
    }).catch(() => {})
  } else if (cmd === 'delete-group') {
    ElMessageBox.confirm(`确定删除「${activeGroupName.value}」分组吗？`, '提示', {
      type: 'warning',
    }).then(async () => {
      const ok = await store.removeGroup(activeGroup.value)
      if (ok) {
        loadStockPrices()
        ElMessage.success('删除成功')
      }
    }).catch(() => {})
  } else if (cmd === 'rename-group') {
    // 预留
    ElMessage.info('暂未开放，敬请期待')
  }
}

watch(() => store.activeGroup, () => {
  loadStockPrices()
})

onMounted(() => {
  loadStockPrices()
})
</script>

<style scoped>
.watchlist-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 20px;
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
}

/* 盈亏总览 */
.summary-card {
  margin-bottom: 20px;
  border-radius: 12px;
}
.summary-item {
  text-align: center;
  padding: 8px 0;
}
.summary-label {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}
.summary-value {
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
}
.summary-value.up { color: #ef4444; }
.summary-value.down { color: #10b981; }

/* 股票列表 */
.list-card {
  border-radius: 12px;
}

.stock-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.star-btn {
  cursor: pointer;
  line-height: 1;
}
.stock-name-cell .name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}
.stock-name-cell .code {
  font-size: 12px;
  color: #9ca3af;
  margin-left: 4px;
}

.price {
  font-size: 15px;
  font-weight: 600;
}
.price.up, .up { color: #ef4444; }
.price.down, .down { color: #10b981; }

.profit-rate {
  margin-left: 4px;
  font-size: 12px;
}

.text-muted {
  color: #9ca3af;
}

.selected-stock {
  display: flex;
  align-items: center;
  gap: 8px;
}
.selected-stock .name {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}
.selected-stock .code {
  font-size: 13px;
  color: #6b7280;
}

/* 行背景色（涨跌颜色淡背景） */
:deep(.el-table__row.row-up) {
  background-color: rgba(239, 68, 68, 0.03);
}
:deep(.el-table__row.row-down) {
  background-color: rgba(16, 185, 129, 0.03);
}
</style>
