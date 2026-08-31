<template>
  <el-card class="stock-info-card card-shadow" v-loading="loading">
    <template #header>
      <div class="card-header">
        <el-icon><InfoFilled /></el-icon>
        <span>股票行情</span>
      </div>
    </template>

    <div v-if="stockInfo" class="stock-info">
      <!-- 主价格区 -->
      <div class="price-section">
        <div class="stock-name">
          <h2>{{ stockInfo.name }}</h2>
          <span class="stock-code">{{ stockInfo.code }}</span>
        </div>
        <div class="price-main" :class="priceClass">
          <span class="price">{{ formatPrice(stockInfo.price) }}</span>
          <span class="change">
            <span>{{ stockInfo.change_pct >= 0 ? '+' : '' }}{{ stockInfo.change_pct.toFixed(2) }}%</span>
            <span class="change-amount">
              {{ stockInfo.change_amount >= 0 ? '+' : '' }}{{ stockInfo.change_amount.toFixed(2) }}
            </span>
          </span>
        </div>
      </div>

      <!-- 详细数据网格 -->
      <el-divider />
      <el-row :gutter="16" class="data-grid">
        <el-col :span="8">
          <div class="data-item">
            <span class="label">今开</span>
            <span class="value">{{ formatPrice(stockInfo.open) }}</span>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="data-item">
            <span class="label">昨收</span>
            <span class="value">{{ formatPrice(stockInfo.pre_close) }}</span>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="data-item">
            <span class="label">成交量</span>
            <span class="value">{{ formatVolume(stockInfo.volume) }}</span>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="data-item">
            <span class="label">最高</span>
            <span class="value text-up">{{ formatPrice(stockInfo.high) }}</span>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="data-item">
            <span class="label">最低</span>
            <span class="value text-down">{{ formatPrice(stockInfo.low) }}</span>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="data-item">
            <span class="label">成交额</span>
            <span class="value">{{ formatAmount(stockInfo.amount) }}</span>
          </div>
        </el-col>
      </el-row>
    </div>

    <div v-else class="empty-state">
      <el-empty description="暂无数据" :image-size="80" />
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'

const props = defineProps({
  stockInfo: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const priceClass = computed(() => {
  if (!props.stockInfo) return ''
  if (props.stockInfo.change_pct > 0) return 'price-up'
  if (props.stockInfo.change_pct < 0) return 'price-down'
  return 'price-neutral'
})

function formatPrice(price) {
  if (price == null) return '--'
  return Number(price).toFixed(2)
}

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
</script>

<style scoped>
.stock-info-card {
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
  color: var(--text-primary);
}

.stock-info {
  padding: 4px 0;
}

.price-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.stock-name {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.stock-name h2 {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
}

.stock-code {
  font-size: 16px;
  color: var(--text-tertiary);
  font-weight: 400;
}

.price-main {
  text-align: right;
}

.price-main .price {
  font-size: 36px;
  font-weight: 700;
  line-height: 1.1;
}

.price-main .change {
  display: flex;
  align-items: baseline;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 4px;
  font-size: 16px;
  font-weight: 600;
}

.change-amount {
  font-size: 14px;
  font-weight: 500;
}

.price-up {
  color: var(--text-positive);
}

.price-down {
  color: var(--text-negative);
}

.price-neutral {
  color: var(--text-secondary);
}

.data-grid {
  margin-top: 8px;
}

.data-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 0;
}

.data-item .label {
  font-size: 13px;
  color: var(--text-tertiary);
}

.data-item .value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.empty-state {
  padding: 40px 0;
}
</style>
