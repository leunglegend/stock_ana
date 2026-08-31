<template>
  <section class="watchlist-mobile">
    <div class="watchlist-mobile__list" role="list">
      <article v-for="row in rows" :key="row.code" class="watchlist-mobile__row" role="listitem">
        <button class="watchlist-mobile__primary" type="button" @click="$emit('open', row.code)">
          <span class="watchlist-mobile__identity">
            <strong>{{ row.name }}</strong>
            <small>{{ row.code }}</small>
          </span>
          <span class="watchlist-mobile__quote">
            <template v-if="row.quoteStatus === 'success'">
              <span class="watchlist-mobile__price">{{ formatPrice(row.price) }}</span>
              <span :class="movementClass(row.changePct)">{{ formatPercent(row.changePct) }}</span>
            </template>
            <span v-else class="watchlist-mobile__muted">{{ quoteStateLabel(row) }}</span>
          </span>
          <span class="watchlist-mobile__return" :class="movementClass(row.costReturn)">
            {{ row.costReturn != null ? formatPercent(row.costReturn * 100) : '--' }}
          </span>
        </button>
        <el-dropdown trigger="click" @command="handleCommand($event, row)">
          <el-button text circle aria-label="更多操作"><el-icon><MoreFilled /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="open">查看详情</el-dropdown-item>
              <el-dropdown-item command="edit">编辑成本与备注</el-dropdown-item>
              <el-dropdown-item v-if="row.quoteStatus === 'error'" command="retry">重试行情</el-dropdown-item>
              <el-dropdown-item command="remove" divided>移除自选</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </article>
    </div>
  </section>
</template>

<script setup>
import { MoreFilled } from '@element-plus/icons-vue'
import { formatPercent, formatPrice } from '@/utils/format'

defineProps({
  rows: { type: Array, default: () => [] },
  signals: { type: Array, default: () => [] },
})

const emit = defineEmits(['open', 'edit', 'remove', 'retry'])

function quoteStateLabel(row) {
  return row.quoteStatus === 'loading' ? '加载中' : row.quoteStatus === 'error' ? '失败，重试' : '--'
}

function movementClass(value) {
  if (value > 0) return 'is-up'
  if (value < 0) return 'is-down'
  return ''
}

function handleCommand(command, row) {
  emit(command, command === 'retry' || command === 'open' ? row.code : row)
}
</script>

<style scoped>
.watchlist-mobile { min-width: 0; background: var(--surface-panel); }
.watchlist-mobile__list { display: grid; }
.watchlist-mobile__row { display: grid; grid-template-columns: minmax(0, 1fr) 44px; align-items: center; min-height: 68px; max-height: 76px; border-bottom: 1px solid var(--border-subtle); }
.watchlist-mobile__row:last-child { border-bottom: 0; }
.watchlist-mobile__primary { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; align-items: center; gap: var(--spacing-2); min-width: 0; padding: var(--spacing-2) var(--spacing-3); border: 0; background: transparent; color: var(--text-primary); text-align: left; }
.watchlist-mobile__identity { display: grid; min-width: 0; gap: 2px; }
.watchlist-mobile__identity strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: var(--font-size-sm); }
.watchlist-mobile__identity small, .watchlist-mobile__muted { color: var(--text-tertiary); font-family: var(--font-family-mono); font-size: var(--font-size-xs); }
.watchlist-mobile__quote, .watchlist-mobile__return { display: grid; justify-items: end; font-family: var(--font-family-mono); font-size: var(--font-size-xs); font-variant-numeric: tabular-nums; white-space: nowrap; }
.watchlist-mobile__price { color: var(--text-primary); font-size: var(--font-size-sm); font-weight: 600; }
.watchlist-mobile__return { min-width: 56px; }
.is-up { color: var(--text-positive); }
.is-down { color: var(--text-negative); }
</style>
