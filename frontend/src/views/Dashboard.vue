<template>
  <div class="dashboard-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">市场概览</h2>
        <p class="page-subtitle">A股市场全景数据</p>
      </div>
      <button class="search-entry" @click="showSearch = true">
        <el-icon :size="16" color="#6b7280"><Search /></el-icon>
        <span>搜索股票</span>
        <kbd>/</kbd>
      </button>
    </div>

    <!-- 中央时间组件 -->
    <DateTimeHero />

    <!-- 全局搜索弹窗 -->
    <GlobalSearch v-model="showSearch" />

    <!-- 三大指数卡片 -->
    <el-row :gutter="16" class="index-row">
      <el-col :span="8">
        <div class="index-card" :class="{ up: shIndex.change_pct > 0, down: shIndex.change_pct < 0 }">
          <div class="index-name">上证指数</div>
          <div class="index-price" v-loading="loading.index">{{ shIndex.price || '--' }}</div>
          <div class="index-change">
            <span>{{ shIndex.change_pct > 0 ? '+' : '' }}{{ shIndex.change_pct }}%</span>
            <span>{{ shIndex.change_pct > 0 ? '+' : '' }}{{ shIndex.change_amount }}</span>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="index-card" :class="{ up: szIndex.change_pct > 0, down: szIndex.change_pct < 0 }">
          <div class="index-name">深证成指</div>
          <div class="index-price" v-loading="loading.index">{{ szIndex.price || '--' }}</div>
          <div class="index-change">
            <span>{{ szIndex.change_pct > 0 ? '+' : '' }}{{ szIndex.change_pct }}%</span>
            <span>{{ szIndex.change_pct > 0 ? '+' : '' }}{{ szIndex.change_amount }}</span>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="index-card" :class="{ up: cybIndex.change_pct > 0, down: cybIndex.change_pct < 0 }">
          <div class="index-name">创业板指</div>
          <div class="index-price" v-loading="loading.index">{{ cybIndex.price || '--' }}</div>
          <div class="index-change">
            <span>{{ cybIndex.change_pct > 0 ? '+' : '' }}{{ cybIndex.change_pct }}%</span>
            <span>{{ cybIndex.change_pct > 0 ? '+' : '' }}{{ cybIndex.change_amount }}</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 市场统计 + 热门板块 -->
    <el-row :gutter="16" class="data-row">
      <!-- 涨跌统计 -->
      <el-col :span="10">
        <el-card class="stats-card card-shadow">
          <template #header>
            <div class="card-header">
              <el-icon color="#f59e0b"><DataLine /></el-icon>
              <span>市场情绪</span>
            </div>
          </template>
          <div class="market-stats">
            <div class="stat-row">
              <div class="stat-item rise">
                <div class="stat-value">{{ marketStats.rise }}</div>
                <div class="stat-label">上涨家数</div>
              </div>
              <div class="stat-item flat">
                <div class="stat-value">{{ marketStats.flat }}</div>
                <div class="stat-label">平盘家数</div>
              </div>
              <div class="stat-item fall">
                <div class="stat-value">{{ marketStats.fall }}</div>
                <div class="stat-label">下跌家数</div>
              </div>
            </div>
            <div class="stat-row">
              <div class="stat-item limit-up">
                <div class="stat-value">{{ marketStats.limitUp }}</div>
                <div class="stat-label">涨停</div>
              </div>
              <div class="stat-item limit-down">
                <div class="stat-value">{{ marketStats.limitDown }}</div>
                <div class="stat-label">跌停</div>
              </div>
              <div class="stat-item amount">
                <div class="stat-value">{{ marketStats.amount }}亿</div>
                <div class="stat-label">成交额</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 热门板块 -->
      <el-col :span="14">
        <el-card class="board-card card-shadow">
          <template #header>
            <div class="card-header">
              <el-icon color="#8b5cf6"><TrendCharts /></el-icon>
              <span>热门板块</span>
              <el-button type="primary" link @click="$router.push('/board')">
                查看全部 →
              </el-button>
            </div>
          </template>
          <div v-loading="loading.board" class="board-list" :class="{ 'is-refreshing': isRefreshing }">
            <div
              v-for="(item, idx) in topBoards"
              :key="item.name"
              class="board-item"
              @click="goToBoard(item.name, 'industry')"
            >
              <span class="board-rank" :class="'rank-' + (idx + 1)">{{ idx + 1 }}</span>
              <span class="board-name">{{ item.name }}</span>
              <span class="board-stock">领涨: {{ item.leading_stock || '--' }}</span>
              <span
                class="board-change"
                :class="{ up: item.change_pct > 0, down: item.change_pct < 0 }"
              >
                {{ item.change_pct > 0 ? '+' : '' }}{{ item.change_pct }}%
              </span>
            </div>
            <el-empty v-if="!loading.board && topBoards.length === 0" description="暂无数据" :image-size="60" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- AI 一句话点评 -->
    <el-card class="ai-card card-shadow">
      <div class="ai-header">
        <div class="ai-icon">
          <el-icon color="#fff" :size="20"><MagicStick /></el-icon>
        </div>
        <div class="ai-title">
          <span>AI 市场点评</span>
          <el-tag type="primary" effect="dark" size="small" v-if="loading.ai">
            <el-icon class="is-loading"><Loading /></el-icon>
            生成中
          </el-tag>
        </div>
        <el-button size="small" type="primary" link @click="generateAiSummary" :disabled="loading.ai">
          重新生成
        </el-button>
      </div>
      <div class="ai-content" v-loading="loading.ai">
        <p v-if="aiSummary">{{ aiSummary }}</p>
        <p v-else class="ai-placeholder">点击「重新生成」，AI 将为您解读今日市场概况</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  DataLine, TrendCharts, MagicStick, Loading, Search,
} from '@element-plus/icons-vue'

import DateTimeHero from '../components/DateTimeHero.vue'
import GlobalSearch from '../components/GlobalSearch.vue'
import { getMarketSummary, getBoardIndustry, getMarketAiSummary } from '../api/stock.js'

const router = useRouter()
const showSearch = ref(false)

const loading = reactive({
  index: false,
  board: false,
  ai: false,
})

// 指数数据
const shIndex = reactive({ price: 0, change_pct: 0, change_amount: 0 })
const szIndex = reactive({ price: 0, change_pct: 0, change_amount: 0 })
const cybIndex = reactive({ price: 0, change_pct: 0, change_amount: 0 })

// 市场统计
const marketStats = reactive({
  rise: 0, fall: 0, flat: 0, limitUp: 0, limitDown: 0, amount: '--',
})

// 热门板块
const topBoards = ref([])

// AI 点评
const aiSummary = ref('')

// 自动刷新状态（静默刷新时的轻微视觉提示）
const isRefreshing = ref(false)

async function loadMarketData() {
  loading.index = true
  try {
    const data = await getMarketSummary()
    shIndex.price = data.sh_index?.toFixed(2) || '--'
    shIndex.change_pct = data.sh_change_pct?.toFixed(2) || '0'
    shIndex.change_amount = data.sh_change_amount?.toFixed(2) || '0'
    szIndex.price = data.sz_index?.toFixed(2) || '--'
    szIndex.change_pct = data.sz_change_pct?.toFixed(2) || '0'
    szIndex.change_amount = data.sz_change_amount?.toFixed(2) || '0'
    cybIndex.price = data.cyb_index?.toFixed(2) || '--'
    cybIndex.change_pct = data.cyb_change_pct?.toFixed(2) || '0'
    cybIndex.change_amount = data.cyb_change_amount?.toFixed(2) || '0'

    marketStats.rise = data.rise_count || 0
    marketStats.fall = data.fall_count || 0
    marketStats.flat = data.flat_count || 0
    marketStats.limitUp = data.limit_up_count || 0
    marketStats.limitDown = data.limit_down_count || 0
    marketStats.amount = data.total_amount ? data.total_amount.toFixed(0) : '--'
  } catch (e) {
    console.error('加载市场数据失败:', e)
  } finally {
    loading.index = false
  }
}

async function loadTopBoards() {
  loading.board = true
  try {
    const data = await getBoardIndustry()
    topBoards.value = data.slice(0, 6)
  } catch (e) {
    console.error('加载板块数据失败:', e)
    topBoards.value = []
  } finally {
    loading.board = false
  }
}

let aiSummarySse = null

function generateAiSummary() {
  if (loading.ai) return
  loading.ai = true
  aiSummary.value = ''

  // 关闭之前的连接
  if (aiSummarySse) {
    aiSummarySse.close()
    aiSummarySse = null
  }

  aiSummarySse = getMarketAiSummary(
    (data) => {
      // 过滤掉状态提示消息（带 emoji 的那种）
      if (data.startsWith('🤖') || data.startsWith('❌') || data.startsWith('📊')) {
        return
      }
      aiSummary.value += data
    },
    () => {
      loading.ai = false
      aiSummarySse = null
    },
    () => {
      loading.ai = false
      aiSummarySse = null
      if (!aiSummary.value) {
        ElMessage.error('AI 点评生成失败，请稍后重试')
      }
    }
  )
}

function goToStock(code) {
  router.push(`/stock/${code}`)
}

function goToBoard(name, type) {
  router.push({ path: '/board', query: { name, type } })
}

// 自动刷新定时器
let refreshTimer = null
const REFRESH_INTERVAL = 30000 // 30 秒

function startAutoRefresh() {
  if (refreshTimer) return
  refreshTimer = setInterval(() => {
    // 静默刷新：短暂的透明度变化提示正在刷新，不显示 loading
    isRefreshing.value = true
    Promise.all([
      loadMarketData().catch(() => {}),
      loadTopBoards().catch(() => {})
    ]).finally(() => {
      setTimeout(() => {
        isRefreshing.value = false
      }, 200)
    })
  }, REFRESH_INTERVAL)
}

function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  loadMarketData()
  loadTopBoards()
  // 页面加载后自动生成 AI 市场点评
  generateAiSummary()
  // 启动自动刷新（30秒）
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
  // 关闭 SSE 连接
  if (aiSummarySse) {
    aiSummarySse.close()
    aiSummarySse = null
  }
})
</script>

<style scoped>
.dashboard-page {
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面标题 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

/* 搜索入口按钮 */
.search-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #6b7280;
  transition: all 0.2s;
  font-family: inherit;
}

.search-entry:hover {
  border-color: #8b5cf6;
  color: #8b5cf6;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.15);
}

.search-entry kbd {
  padding: 1px 6px;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 12px;
  font-family: ui-monospace, monospace;
  border: 1px solid #e5e7eb;
  color: #9ca3af;
}

.search-entry:hover kbd {
  background: #f5f3ff;
  border-color: #ddd6fe;
  color: #8b5cf6;
}

/* 指数卡片 */
.index-row {
  margin-bottom: 20px;
}
.index-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s;
}
.index-card:hover {
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  transform: translateY(-2px);
}
.index-card.up { border-top: 3px solid #ef4444; }
.index-card.down { border-top: 3px solid #10b981; }

.index-name {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 8px;
}
.index-price {
  font-size: 32px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.2;
  margin-bottom: 8px;
  transition: color 0.3s ease;
}
.up .index-price { color: #ef4444; }
.down .index-price { color: #10b981; }

.index-change {
  display: flex;
  gap: 16px;
  font-size: 14px;
  font-weight: 600;
  transition: color 0.3s ease;
}
.up .index-change { color: #ef4444; }
.down .index-change { color: #10b981; }

/* 数据行 */
.data-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}
.card-header .el-button {
  margin-left: auto;
}

/* 市场情绪 */
.market-stats {
  padding: 8px 0;
}
.stat-row {
  display: flex;
  justify-content: space-around;
  margin-bottom: 16px;
}
.stat-row:last-child {
  margin-bottom: 0;
  padding-top: 16px;
  border-top: 1px dashed #e5e7eb;
}
.stat-item {
  text-align: center;
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 4px;
}
.stat-label {
  font-size: 12px;
  color: #6b7280;
}
.stat-item.rise .stat-value { color: #ef4444; }
.stat-item.fall .stat-value { color: #10b981; }
.stat-item.flat .stat-value { color: #6b7280; }
.stat-item.limit-up .stat-value { color: #dc2626; }
.stat-item.limit-down .stat-value { color: #059669; }
.stat-item.amount .stat-value { color: #7c3aed; font-size: 20px; }

/* 热门板块 */
.board-list {
  min-height: 240px;
}
.board-item {
  display: flex;
  align-items: center;
  padding: 12px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s, opacity 0.3s ease;
  gap: 12px;
}
.board-list.is-refreshing .board-item {
  opacity: 0.85;
}
.board-item:hover {
  background: #f5f3ff;
}
.board-rank {
  width: 24px;
  height: 24px;
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

.board-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.board-stock {
  font-size: 13px;
  color: #6b7280;
  flex-shrink: 0;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.board-change {
  font-size: 16px;
  font-weight: 700;
  flex-shrink: 0;
  min-width: 80px;
  text-align: right;
}
.board-change.up { color: #ef4444; }
.board-change.down { color: #10b981; }

/* AI 点评卡片 */
.ai-card {
  background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
  border: 1px solid #ddd6fe;
  border-radius: 12px;
  margin-bottom: 20px;
}
.ai-card :deep(.el-card__body) {
  padding: 0;
}
.ai-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px 0;
}
.ai-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ai-title {
  font-size: 16px;
  font-weight: 600;
  color: #4c1d95;
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}
.ai-content {
  padding: 16px 20px 20px;
}
.ai-content p {
  font-size: 15px;
  line-height: 2;
  color: #4b5563;
  margin: 0;
  text-indent: 2em;
  text-align: justify;
}
.ai-placeholder {
  color: #9ca3af !important;
  text-indent: 0 !important;
  text-align: center !important;
}
</style>
