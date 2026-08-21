<template>
  <div class="stock-detail-page">
    <!-- 返回按钮 + 股票信息栏 -->
    <div class="detail-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" circle @click="goBack" />
        <div class="stock-title">
          <h1 class="stock-name">{{ stockInfo?.name || '--' }}</h1>
          <span class="stock-code">{{ stockInfo?.code || code }}</span>
          <el-tag
            v-if="isWatched"
            type="warning"
            effect="light"
            size="small"
            @click="removeFromWatchlist"
            class="watch-tag"
          >
            <el-icon><StarFilled /></el-icon>
            已自选
          </el-tag>
          <el-tag
            v-else
            size="small"
            @click="addToWatchlist"
            class="watch-tag add-tag"
          >
            <el-icon><Star /></el-icon>
            加自选
          </el-tag>
        </div>
      </div>
      <div class="header-right" v-if="stockInfo">
        <div class="price-block">
          <span class="price" :class="priceClass">{{ stockInfo.price?.toFixed(2) }}</span>
          <span class="change" :class="priceClass">
            {{ stockInfo.change_pct > 0 ? '+' : '' }}{{ stockInfo.change_pct?.toFixed(2) }}%
            <span class="change-amount">
              {{ stockInfo.change_amount > 0 ? '+' : '' }}{{ stockInfo.change_amount?.toFixed(2) }}
            </span>
          </span>
        </div>
      </div>
    </div>

    <!-- 行情数据栏 -->
    <el-row v-if="stockInfo" class="quote-bar">
      <el-col :span="24">
        <div class="quote-items">
          <div class="quote-item">
            <span class="label">今开</span>
            <span class="value">{{ stockInfo.open?.toFixed(2) }}</span>
          </div>
          <div class="quote-item">
            <span class="label">昨收</span>
            <span class="value">{{ stockInfo.pre_close?.toFixed(2) }}</span>
          </div>
          <div class="quote-item">
            <span class="label text-up">最高</span>
            <span class="value text-up">{{ stockInfo.high?.toFixed(2) }}</span>
          </div>
          <div class="quote-item">
            <span class="label text-down">最低</span>
            <span class="value text-down">{{ stockInfo.low?.toFixed(2) }}</span>
          </div>
          <div class="quote-item">
            <span class="label">成交量</span>
            <span class="value">{{ formatVolume(stockInfo.volume) }}</span>
          </div>
          <div class="quote-item">
            <span class="label">成交额</span>
            <span class="value">{{ formatAmount(stockInfo.amount) }}</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 主体内容 -->
    <div class="detail-body">
      <!-- K线图 -->
      <el-card class="chart-card card-shadow" v-loading="loading.kline">
        <KLineChart
          :kline-data="klineData"
          :loading="loading.kline"
          @period-change="handlePeriodChange"
        />
      </el-card>

      <el-row :gutter="16" class="info-row">
        <el-col :span="12">
          <FinancialCard :financial="financial" :loading="loading.financial" />
        </el-col>
        <el-col :span="12">
          <AiAdvice
            :code="code"
            :analyzing="analyzing"
            :advice="aiAdvice"
            @start-analyze="startAnalyze"
          />
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, Star, StarFilled,
} from '@element-plus/icons-vue'
import { useWatchlistStore } from '../store'

import KLineChart from '../components/KLineChart.vue'
import FinancialCard from '../components/FinancialCard.vue'
import AiAdvice from '../components/AiAdvice.vue'

import { getStockInfo, getKlineData, getFinancialData, analyzeStock } from '../api/stock'

const route = useRoute()
const router = useRouter()
const store = useWatchlistStore()

const code = computed(() => route.params.code)

const stockInfo = ref(null)
const klineData = ref(null)
const financial = ref(null)
const aiAdvice = ref('')
const analyzing = ref(false)
const klinePeriod = ref('daily')

const loading = reactive({
  info: false,
  kline: false,
  financial: false,
})

const isWatched = computed(() => store.isWatched(code.value))

const priceClass = computed(() => {
  if (!stockInfo.value) return ''
  if (stockInfo.value.change_pct > 0) return 'up'
  if (stockInfo.value.change_pct < 0) return 'down'
  return ''
})

function formatVolume(vol) {
  if (!vol) return '--'
  if (vol >= 10000) return (vol / 10000).toFixed(2) + '万手'
  return vol + '手'
}

function formatAmount(amount) {
  if (!amount) return '--'
  if (amount >= 100000000) return (amount / 100000000).toFixed(2) + '亿'
  if (amount >= 10000) return (amount / 10000).toFixed(2) + '万'
  return amount + '元'
}

function goBack() {
  router.back()
}

async function loadAllData() {
  const tasks = [loadStockInfo(), loadKlineData(), loadFinancialData()]
  await Promise.all(tasks)
}

async function loadStockInfo() {
  loading.info = true
  try {
    stockInfo.value = await getStockInfo(code.value)
  } catch (e) {
    ElMessage.error('获取股票信息失败')
  } finally {
    loading.info = false
  }
}

async function loadKlineData() {
  loading.kline = true
  try {
    klineData.value = await getKlineData(code.value, klinePeriod.value)
  } catch (e) {
    ElMessage.error('获取K线数据失败')
  } finally {
    loading.kline = false
  }
}

async function loadFinancialData() {
  loading.financial = true
  try {
    financial.value = await getFinancialData(code.value)
  } catch (e) {
    // 财务数据失败不弹窗，静默处理
  } finally {
    loading.financial = false
  }
}

function handlePeriodChange(period) {
  klinePeriod.value = period
  loadKlineData()
}

let sseSource = null

function startAnalyze() {
  if (!code.value || analyzing.value) return
  analyzing.value = true
  aiAdvice.value = ''

  if (sseSource) sseSource.close()

  sseSource = analyzeStock(
    code.value,
    (data) => { aiAdvice.value += data },
    () => { analyzing.value = false },
    () => {
      analyzing.value = false
      if (!aiAdvice.value) ElMessage.error('AI 分析失败，请稍后重试')
    }
  )
}

function addToWatchlist() {
  if (!stockInfo.value) return
  const success = store.addStock({
    code: stockInfo.value.code,
    name: stockInfo.value.name,
  })
  if (success) {
    ElMessage.success('已添加到自选')
  } else {
    ElMessage.warning('已在自选列表中')
  }
}

function removeFromWatchlist() {
  store.removeStock(code.value)
  ElMessage.success('已移出自选')
}

watch(code, () => {
  if (code.value) {
    aiAdvice.value = ''
    loadAllData()
  }
})

onMounted(() => {
  if (code.value) {
    loadAllData()
  }
})
</script>

<style scoped>
.stock-detail-page {
  max-width: 1400px;
  margin: 0 auto;
}

/* 头部 */
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.stock-title {
  display: flex;
  align-items: center;
  gap: 12px;
}
.stock-name {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}
.stock-code {
  font-size: 16px;
  color: #6b7280;
}
.watch-tag {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.add-tag {
  background: #fff;
  border-color: #d1d5db;
  color: #6b7280;
}

.header-right {
  text-align: right;
}
.price-block {
  display: flex;
  align-items: baseline;
  gap: 16px;
}
.price {
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
}
.price.up { color: #ef4444; }
.price.down { color: #10b981; }

.change {
  font-size: 18px;
  font-weight: 600;
}
.change.up { color: #ef4444; }
.change.down { color: #10b981; }
.change-amount {
  font-size: 14px;
  margin-left: 8px;
}

/* 行情栏 */
.quote-bar {
  margin-bottom: 20px;
}
.quote-items {
  display: flex;
  gap: 40px;
  padding: 12px 0;
}
.quote-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.quote-item .label {
  font-size: 12px;
  color: #6b7280;
}
.quote-item .value {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.text-up { color: #ef4444 !important; }
.text-down { color: #10b981 !important; }

/* 主体内容 */
.detail-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chart-card {
  border-radius: 12px;
}

.info-row {
  margin: 0 !important;
}
</style>
