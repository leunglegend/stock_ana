<template>
  <SectionPanel variant="flush">
    <template #header>
      <div class="board-ranking__header">
        <div>
          <span class="board-ranking__context-label">{{ resolvedTitle }}</span>
          <h3 class="board-ranking__title">板块信号索引</h3>
        </div>
        <div class="board-ranking__meta">
          <span class="board-ranking__meta-count">{{ boards.length }} 个板块</span>
          <span v-if="refreshing" class="board-ranking__meta-status">更新中</span>
        </div>
      </div>
    </template>

    <StatusState
      v-if="loading && !hasBoards"
      state="loading"
      title="正在加载板块榜单"
      description="行业榜和概念榜独立请求，稍后即可查看。"
      :min-height="320"
    />

    <StatusState
      v-else-if="error && !hasBoards"
      state="error"
      title="板块榜单加载失败"
      description="当前无法读取该类型板块列表，可单独重试。"
      :min-height="320"
      @retry="$emit('retry')"
    />

    <StatusState
      v-else-if="!hasBoards"
      state="empty"
      title="暂无可展示板块"
      description="可切换板块类型，或放宽筛选条件后再查看。"
      :min-height="320"
    />

    <div v-else class="board-ranking__body">
      <div v-if="error" class="board-ranking__notice" role="status" aria-live="polite">
        <span>榜单更新失败，当前保留上次成功的数据。</span>
        <el-button link type="primary" @click="$emit('retry')">重试</el-button>
      </div>

      <div class="board-ranking__list" role="list" :aria-label="resolvedTitle">
        <button
          v-for="(board, index) in visibleBoards"
          :key="board.name"
          class="board-ranking__row"
          :class="{ 'is-active': board.name === selectedName }"
          type="button"
          :aria-pressed="board.name === selectedName"
          :aria-label="`查看${board.name}板块`"
          @click="$emit('select', board)"
        >
          <span class="board-ranking__rank">{{ formatRank(pageOffset + index + 1) }}</span>

          <div class="board-ranking__content">
            <div class="board-ranking__topline">
              <div class="board-ranking__headline">
                <p class="board-ranking__name">{{ board.name }}</p>
                <p class="board-ranking__leader">
                  领涨 {{ board.leading_stock || '--' }} · {{ formatLeadingChange(board.leading_change) }}
                </p>
              </div>
              <PercentageDisplay :value="board.change_pct" size="sm" />
            </div>

            <dl class="board-ranking__facts">
              <div class="board-ranking__fact">
                <dt>上涨 / 下跌</dt>
                <dd class="tabular-nums">{{ formatCount(board.rise_count) }} / {{ formatCount(board.fall_count) }}</dd>
              </div>
              <div class="board-ranking__fact">
                <dt>成交额</dt>
                <dd class="tabular-nums">{{ formatTurnover(board.total_turnover) }}</dd>
              </div>
              <div class="board-ranking__fact">
                <dt>换手率</dt>
                <dd class="tabular-nums">{{ formatTurnoverRate(board.turnover_rate) }}</dd>
              </div>
            </dl>
          </div>
        </button>
      </div>
    </div>

    <template v-if="hasBoards" #footer>
      <div class="board-ranking__footer">
        <span>共 {{ resolvedTotal }} 个板块</span>
        <span v-if="compact" class="board-ranking__page-state">第 {{ page }} / {{ pageCount }} 页</span>
        <el-pagination
          v-if="resolvedTotal > pageSize"
          :current-page="page"
          :page-size="pageSize"
          :total="resolvedTotal"
          :pager-count="5"
          background
          :layout="compact ? 'prev, next' : 'prev, pager, next'"
          size="small"
          @update:current-page="$emit('page-change', $event)"
        />
      </div>
    </template>
  </SectionPanel>
</template>

<script setup>
import { computed } from 'vue'

import PercentageDisplay from '@/components/base/PercentageDisplay.vue'
import SectionPanel from '@/components/base/SectionPanel.vue'
import StatusState from '@/components/base/StatusState.vue'
import { formatPercent, formatYi, safeNumber } from '@/utils/format'
import { paginateRows } from '@/utils/opportunityRadar'

const props = defineProps({
  title: { type: String, default: '' },
  type: { type: String, default: 'industry' },
  boards: { type: Array, default: () => [] },
  activeBoards: { type: Array, default: () => [] },
  selectedName: { type: String, default: '' },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 10 },
  total: { type: Number, default: 0 },
  compact: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  error: { type: [Boolean, String], default: false },
  refreshing: { type: Boolean, default: false },
})

defineEmits(['select', 'retry', 'page-change'])

const hasBoards = computed(() => props.boards.length > 0)
const resolvedTitle = computed(() => props.title || (props.type === 'concept' ? '概念涨幅榜' : '行业涨幅榜'))
const resolvedTotal = computed(() => props.total || props.boards.length || props.activeBoards.length)
const pageCount = computed(() => Math.max(1, Math.ceil(resolvedTotal.value / props.pageSize)))
const pageOffset = computed(() => (props.page - 1) * props.pageSize)
const visibleBoards = computed(() => paginateRows(props.boards, props.page, props.pageSize))

function formatRank(value) { return value.toString().padStart(2, '0') }

function formatLeadingChange(value) {
  const number = safeNumber(value)
  return number == null ? '--' : formatPercent(number, 2, true)
}

function formatCount(value) { const number = safeNumber(value); return number == null ? '--' : `${number}` }
function formatTurnover(value) {
  const number = safeNumber(value)
  return number == null ? '--' : formatYi(number)
}
function formatTurnoverRate(value) {
  const number = safeNumber(value)
  return number == null ? '--' : formatPercent(number, 2, false)
}
</script>

<style scoped>
.board-ranking__header,.board-ranking__topline,.board-ranking__footer{display:flex;align-items:center;justify-content:space-between;gap:var(--spacing-3)}
.board-ranking__leader,.board-ranking__meta,.board-ranking__fact dt,.board-ranking__notice,.board-ranking__footer,.board-ranking__context-label{color:var(--text-tertiary);font-size:var(--font-size-sm);line-height:var(--line-height-normal)}
.board-ranking__title,.board-ranking__name{margin:0;color:var(--text-primary)}
.board-ranking__meta{display:flex;align-items:center;gap:var(--spacing-2);text-align:right}
.board-ranking__body,.board-ranking__list,.board-ranking__content,.board-ranking__headline{display:grid;gap:var(--spacing-1);min-width:0}
.board-ranking__notice{display:flex;align-items:center;justify-content:space-between;gap:var(--spacing-3);padding:var(--spacing-2) var(--spacing-3);border-bottom:1px solid var(--border-subtle);background:var(--surface-info)}
.board-ranking__row{display:grid;grid-template-columns:auto minmax(0,1fr);gap:var(--spacing-2);width:100%;padding:var(--spacing-2) var(--spacing-3);border:0;border-bottom:1px solid var(--border-subtle);background:transparent;cursor:pointer;text-align:left;transition:background-color var(--transition-fast),border-color var(--transition-fast)}
.board-ranking__row:hover{background:var(--state-hover)}
.board-ranking__row.is-active{background:var(--state-selected);box-shadow:inset 2px 0 0 var(--color-primary-500)}
.board-ranking__row:last-child{border-bottom:0}
.board-ranking__rank{display:inline-grid;place-items:center;min-width:34px;min-height:34px;padding-inline:var(--spacing-2);border-radius:var(--radius-pill);background:var(--surface-panel-muted);color:var(--text-secondary);font-family:var(--font-family-mono);font-size:var(--font-size-sm);font-weight:600}
.board-ranking__name{margin:0;font-size:var(--font-size-base);font-weight:600}
.board-ranking__leader,.board-ranking__facts{margin:0}
.board-ranking__facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--spacing-1) var(--spacing-2);margin-top:var(--spacing-1)}
.board-ranking__fact:last-child{display:none}
.board-ranking__fact{min-width:0}
.board-ranking__fact dd{margin:4px 0 0;color:var(--text-secondary);font-size:var(--font-size-sm);line-height:var(--line-height-normal)}
@media (max-width:767px){.board-ranking__header,.board-ranking__topline,.board-ranking__notice,.board-ranking__footer{display:grid;grid-template-columns:minmax(0,1fr)}.board-ranking__rank{min-width:44px;min-height:44px}.board-ranking__facts{grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--spacing-2) var(--spacing-3)}}
</style>
