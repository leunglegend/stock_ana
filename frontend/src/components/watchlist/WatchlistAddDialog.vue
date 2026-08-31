<template>
  <el-dialog
    :model-value="visible"
    title="添加自选"
    width="720px"
    :close-on-click-modal="!submitting"
    @update:model-value="$emit('update:visible', $event)"
  >
    <div class="watchlist-add">
      <div class="watchlist-add__field">
        <label class="watchlist-add__label">目标分组</label>
        <el-select v-model="selectedGroupId" aria-label="选择目标分组">
          <el-option v-for="group in groups" :key="group.id" :label="group.name" :value="group.id" />
        </el-select>
        <p class="watchlist-add__hint">同一股票仅在同一分组内禁止重复，不同分组允许重复。</p>
      </div>

      <div class="watchlist-add__field">
        <label class="watchlist-add__label">搜索股票</label>
        <StockSearch @select="handleSelectStock" />
      </div>

      <section v-if="selectedStock" class="watchlist-add__preview" aria-label="股票预览">
        <div class="watchlist-add__preview-header">
          <StockName :name="selectedStock.name" :code="selectedStock.code" />
          <TagBadge v-if="duplicateInGroup" type="warning">该分组已存在</TagBadge>
        </div>

        <StatusState v-if="quoteState === 'loading'" state="loading" title="行情加载中" description="正在读取真实接口行情。" :min-height="140" />
        <StatusState v-else-if="quoteState === 'error'" state="error" title="行情加载失败" description="预览未拿到数据，可直接重试。" :min-height="140" @retry="loadQuotePreview" />
        <template v-else-if="quoteState === 'success'">
          <PriceDisplay :price="quote.price" :change="quote.change_amount" :change-percent="quote.change_pct" size="md" />
          <dl class="watchlist-add__facts">
            <div><dt>开盘</dt><dd>{{ formatPrice(quote.open) }}</dd></div>
            <div><dt>最高</dt><dd>{{ formatPrice(quote.high) }}</dd></div>
            <div><dt>最低</dt><dd>{{ formatPrice(quote.low) }}</dd></div>
            <div><dt>昨收</dt><dd>{{ formatPrice(quote.pre_close) }}</dd></div>
          </dl>
        </template>
      </section>

      <el-form label-position="top">
        <el-form-item label="成本价（可选）">
          <el-input-number v-model="cost" :min="0" :precision="2" :step="0.01" style="width: 100%" />
          <div class="watchlist-add__hint">成本为 0 表示暂不计算每股盈亏与成本收益率。</div>
        </el-form-item>
        <el-form-item label="备注（可选）">
          <el-input v-model="remark" type="textarea" :rows="3" maxlength="80" show-word-limit placeholder="例如：财报窗口、趋势观察、买点提醒" />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <el-button :disabled="submitting" @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="submitting" :disabled="!canSubmit" @click="submitForm">确认添加</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { getStockInfo } from '@/api/stock'
import PriceDisplay from '@/components/base/PriceDisplay.vue'
import StatusState from '@/components/base/StatusState.vue'
import StockName from '@/components/base/StockName.vue'
import TagBadge from '@/components/base/TagBadge.vue'
import StockSearch from '@/components/StockSearch.vue'
import { formatPrice, safeNumber } from '@/utils/format'

const props = defineProps({
  visible: { type: Boolean, default: false },
  submitting: { type: Boolean, default: false },
  defaultGroupId: { type: String, default: '' },
  groups: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:visible', 'submit'])
const selectedGroupId = ref('')
const selectedStock = ref(null)
const quote = ref(null)
const quoteState = ref('idle')
const cost = ref(0)
const remark = ref('')
let quoteRequestId = 0

const duplicateInGroup = computed(() => {
  if (!selectedStock.value || !selectedGroupId.value) return false
  const group = props.groups.find((item) => item.id === selectedGroupId.value)
  return Boolean(group?.stocks?.some((stock) => stock.code === selectedStock.value.code))
})

const canSubmit = computed(() => Boolean(selectedStock.value && selectedGroupId.value && !duplicateInGroup.value))

watch(() => props.visible, (visible) => {
  if (!visible) return
  quoteRequestId += 1
  selectedGroupId.value = props.defaultGroupId || props.groups[0]?.id || ''
  selectedStock.value = null
  quote.value = null
  quoteState.value = 'idle'
  cost.value = 0
  remark.value = ''
})

async function handleSelectStock(stock) {
  selectedStock.value = stock
  await loadQuotePreview()
}

async function loadQuotePreview() {
  if (!selectedStock.value?.code) return
  const requestId = ++quoteRequestId
  quoteState.value = 'loading'
  try {
    const data = await getStockInfo(selectedStock.value.code)
    if (requestId !== quoteRequestId || !selectedStock.value) return
    quote.value = data
    quoteState.value = 'success'
  } catch {
    if (requestId !== quoteRequestId) return
    quote.value = null
    quoteState.value = 'error'
  }
}

function submitForm() {
  if (!canSubmit.value || !selectedStock.value) return
  emit('submit', {
    groupId: selectedGroupId.value,
    stock: { code: selectedStock.value.code, name: selectedStock.value.name },
    cost: safeNumber(cost.value, 0) ?? 0,
    remark: remark.value.trim(),
  })
}
</script>

<style scoped>
.watchlist-add { display: grid; gap: var(--spacing-4); }
.watchlist-add__field { display: grid; gap: var(--spacing-2); }
.watchlist-add__label { color: var(--text-secondary); font-size: var(--font-size-sm); font-weight: 500; }
.watchlist-add__hint { margin: 0; color: var(--text-tertiary); font-size: var(--font-size-xs); line-height: 1.5; }
.watchlist-add__preview {
  display: grid; gap: var(--spacing-4); padding: var(--spacing-4); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md); background: var(--surface-panel-muted);
}
.watchlist-add__preview-header { display: flex; align-items: center; justify-content: space-between; gap: var(--spacing-3); flex-wrap: wrap; }
.watchlist-add__facts {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--spacing-3); margin: 0;
  font-family: var(--font-family-mono); font-variant-numeric: tabular-nums;
}
.watchlist-add__facts div { display: grid; gap: 4px; }
.watchlist-add__facts dt { color: var(--text-tertiary); font-size: var(--font-size-xs); }
.watchlist-add__facts dd { margin: 0; color: var(--text-primary); }
@media (max-width: 767px) {
  .watchlist-add__facts { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
:deep(.el-dialog) { width: min(720px, calc(100vw - 24px)); }
:deep(.el-dialog__footer .el-button) { min-height: 44px; }
</style>
