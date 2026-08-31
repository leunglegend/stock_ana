<template>
  <el-dialog
    :model-value="visible"
    title="编辑成本与备注"
    width="560px"
    :close-on-click-modal="!submitting"
    @update:model-value="$emit('update:visible', $event)"
  >
    <div class="watchlist-edit">
      <div v-if="row" class="watchlist-edit__summary">
        <StockName :name="row.name" :code="row.code" />
        <PriceDisplay
          v-if="row.quoteStatus === 'success'"
          :price="row.price"
          :change="row.changeAmount"
          :change-percent="row.changePct"
          size="sm"
        />
        <TagBadge v-else :type="row.quoteStatus === 'error' ? 'warning' : 'info'">
          {{ row.quoteStatus === 'error' ? '行情加载失败' : '行情加载中' }}
        </TagBadge>
      </div>

      <el-form label-position="top">
        <el-form-item label="成本价">
          <el-input-number v-model="cost" :min="0" :precision="2" :step="0.01" style="width: 100%" />
          <div class="watchlist-edit__hint">设为 0 即清除成本，不再计算成本收益率。</div>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="remark" type="textarea" :rows="3" maxlength="80" show-word-limit placeholder="记录交易计划、观察理由或提醒事项" />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <el-button :disabled="submitting" @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submitForm">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import PriceDisplay from '@/components/base/PriceDisplay.vue'
import StockName from '@/components/base/StockName.vue'
import TagBadge from '@/components/base/TagBadge.vue'
import { safeNumber } from '@/utils/format'

const props = defineProps({
  visible: { type: Boolean, default: false },
  submitting: { type: Boolean, default: false },
  row: { type: Object, default: null },
})

const emit = defineEmits(['update:visible', 'submit'])
const cost = ref(0)
const remark = ref('')

watch(() => [props.visible, props.row], () => {
  if (!props.visible || !props.row) return
  cost.value = safeNumber(props.row.cost, 0) ?? 0
  remark.value = props.row.remark || ''
}, { immediate: true })

function submitForm() {
  if (!props.row) return
  emit('submit', {
    code: props.row.code,
    cost: safeNumber(cost.value, 0) ?? 0,
    remark: remark.value.trim(),
  })
}
</script>

<style scoped>
.watchlist-edit { display: grid; gap: var(--spacing-4); }
.watchlist-edit__summary {
  display: flex; align-items: center; justify-content: space-between; gap: var(--spacing-3); flex-wrap: wrap;
  padding: var(--spacing-4); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); background: var(--surface-panel-muted);
}
.watchlist-edit__hint { color: var(--text-tertiary); font-size: var(--font-size-xs); line-height: 1.5; }
:deep(.el-dialog) { width: min(560px, calc(100vw - 24px)); }
:deep(.el-dialog__footer .el-button) { min-height: 44px; }
</style>
