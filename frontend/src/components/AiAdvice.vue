<template>
  <section class="ai-advice-card">
    <header class="ai-advice-card__header">
      <h2 class="ai-advice-card__title">AI 分析</h2>
        <el-button
          type="primary"
          plain
          :icon="RefreshRight"
          :loading="isLoading"
          :disabled="!code || isLoading"
          @click="$emit('start-analyze')"
        >
          {{ actionLabel }}
        </el-button>
    </header>

    <div v-if="viewState === 'idle'" class="ai-advice-card__placeholder">
      <el-icon :size="32" class="ai-advice-card__placeholder-icon"><MagicStick /></el-icon>
      <p class="ai-advice-card__placeholder-title">尚未开始 AI 分析</p>
      <el-button type="primary" :icon="MagicStick" :disabled="!code" @click="$emit('start-analyze')">开始分析</el-button>
    </div>

    <StatusState
      v-else-if="viewState === 'loading'"
      state="loading"
      title="正在生成 AI 分析"
      :min-height="260"
    />

    <StatusState
      v-else-if="viewState === 'error'"
      state="error"
      title="AI 分析失败"
      :description="errorMessage || '当前未拿到可展示的分析结果，可重新尝试。'"
      :min-height="260"
      @retry="$emit('start-analyze')"
    />

    <StatusState
      v-else-if="viewState === 'empty'"
      state="empty"
      title="暂无 AI 分析结果"
      :min-height="260"
    >
      <template #action>
        <el-button type="primary" plain @click="$emit('start-analyze')">重新分析</el-button>
      </template>
    </StatusState>

    <div v-else class="ai-advice-card__body" :aria-live="isLoading ? 'polite' : 'off'">
      <div v-if="isLoading" class="ai-advice-card__notice">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>AI 正在继续生成分析内容，以下为当前已返回的部分。</span>
      </div>

      <div v-else-if="state === 'error' && errorMessage" class="ai-advice-card__notice ai-advice-card__notice--error" role="alert">
        <el-icon><WarningFilled /></el-icon>
        <span>{{ errorMessage }}</span>
        <el-button link @click="$emit('start-analyze')">重试</el-button>
      </div>

      <section v-if="scoreData" class="ai-advice-card__score-panel" aria-label="AI 评分摘要">
        <div class="ai-advice-card__score-main">
          <span class="ai-advice-card__score-label">综合评分</span>
          <div class="ai-advice-card__score-row">
            <span class="ai-advice-card__score-value">{{ scoreData.score }}</span>
            <span class="ai-advice-card__score-total">/100</span>
          </div>
          <span v-if="scoreData.rating" class="ai-advice-card__score-rating">{{ scoreData.rating }}</span>
        </div>

        <div class="ai-advice-card__score-side">
          <p v-if="scoreData.action_advice" class="ai-advice-card__action">{{ scoreData.action_advice }}</p>

          <ul v-if="keyPoints.length" class="ai-advice-card__points">
            <li v-for="point in keyPoints" :key="point">{{ point }}</li>
          </ul>
        </div>

        <dl v-if="dimensionEntries.length" class="ai-advice-card__dimensions">
          <div v-for="item in dimensionEntries" :key="item.key" class="ai-advice-card__dimension">
            <dt>{{ item.label }}</dt>
            <dd>
              <span class="ai-advice-card__dimension-track" aria-hidden="true">
                <span class="ai-advice-card__dimension-fill" :style="{ width: `${item.score}%` }"></span>
              </span>
              <span class="ai-advice-card__dimension-value">{{ item.score }}</span>
            </dd>
          </div>
        </dl>
      </section>

      <article v-if="renderedAdvice" class="ai-advice-card__markdown" v-html="renderedAdvice"></article>
      <p v-else class="ai-advice-card__body-empty">当前仅返回评分字段，尚未返回分析正文。</p>
    </div>

  </section>
</template>

<script setup>
import { computed } from 'vue'
import { Loading, MagicStick, RefreshRight, WarningFilled } from '@element-plus/icons-vue'

import StatusState from '@/components/base/StatusState.vue'
import { parseScoreBlock, renderSafeMarkdown, stripScoreBlock } from '@/utils/markdown'

const props = defineProps({
  code: { type: String, default: '' },
  advice: { type: String, default: '' },
  state: {
    type: String,
    default: 'idle',
    validator: (value) => ['idle', 'loading', 'success', 'empty', 'error'].includes(value),
  },
  errorMessage: { type: String, default: '' },
})

defineEmits(['start-analyze'])

const dimensionLabels = { technical: '技术面', fundamental: '基本面', sentiment: '情绪面', risk: '风险控制' }

const isLoading = computed(() => props.state === 'loading')
const adviceBody = computed(() => stripScoreBlock(props.advice))
const renderedAdvice = computed(() => renderSafeMarkdown(adviceBody.value))
const scoreData = computed(() => parseScoreBlock(props.advice))
const hasReport = computed(() => Boolean(scoreData.value || adviceBody.value.trim()))
const actionLabel = computed(() => (hasReport.value ? '重新分析' : '开始分析'))

const viewState = computed(() => {
  if (hasReport.value) return 'report'
  return props.state === 'success' ? 'empty' : props.state
})

const keyPoints = computed(() =>
  Array.isArray(scoreData.value?.key_points) ? scoreData.value.key_points.filter((item) => typeof item === 'string' && item.trim()) : []
)

const dimensionEntries = computed(() =>
  Object.entries(dimensionLabels)
    .map(([key, label]) => ({ key, label, score: normalizeScore(scoreData.value?.dimensions?.[key]) }))
    .filter((item) => item.score !== null)
)

function normalizeScore(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return null
  return Math.max(0, Math.min(100, Math.round(numeric)))
}
</script>

<style scoped>
.ai-advice-card{height:100%;padding:var(--spacing-3)}
.ai-advice-card__header,.ai-advice-card__score-panel,.ai-advice-card__placeholder,.ai-advice-card__body,.ai-advice-card__score-main,.ai-advice-card__score-side,.ai-advice-card__dimensions{display:grid;gap:var(--spacing-4)}
.ai-advice-card__header{grid-template-columns:minmax(0,1fr) auto;align-items:center;padding-bottom:var(--spacing-3);border-bottom:1px solid var(--border-subtle)}
.ai-advice-card__body-empty,.ai-advice-card__dimension dt,.ai-advice-card__score-label,.ai-advice-card__score-total{color:var(--text-tertiary);font-size:var(--font-size-sm)}
.ai-advice-card__points,.ai-advice-card__dimensions{margin:0;padding:0}
.ai-advice-card__title,.ai-advice-card__placeholder-title{margin:0;color:var(--text-primary);font-size:var(--font-size-lg)}
.ai-advice-card__placeholder{min-height:260px;place-content:center;justify-items:center;padding:var(--spacing-4) 0;border-bottom:1px dashed var(--border-ai);text-align:center}
.ai-advice-card__placeholder-icon,.ai-advice-card__score-value{color:var(--text-ai)}
.ai-advice-card__notice,.ai-advice-card__action{display:flex;align-items:center;gap:var(--spacing-2);padding:var(--spacing-3) 0;border-bottom:1px solid var(--border-ai);color:var(--text-secondary);line-height:var(--line-height-normal)}
.ai-advice-card__notice--error{border-color:var(--border-positive);color:var(--text-primary);justify-content:space-between;flex-wrap:wrap}
.ai-advice-card__score-panel{padding:var(--spacing-3) 0;border-top:1px solid var(--border-subtle)}
.ai-advice-card__score-main,.ai-advice-card__score-side{gap:var(--spacing-2)}
.ai-advice-card__score-label,.ai-advice-card__score-total,.ai-advice-card__score-rating,.ai-advice-card__dimension-value{font-variant-numeric:tabular-nums}
.ai-advice-card__score-row{display:flex;align-items:end;gap:var(--spacing-2)}
.ai-advice-card__score-value{font-size:var(--font-size-5xl);font-weight:700;line-height:1}
.ai-advice-card__score-rating{color:var(--text-primary);font-size:var(--font-size-base);font-weight:600}
.ai-advice-card__action{margin:0}
.ai-advice-card__points{display:grid;gap:var(--spacing-2);padding-left:var(--spacing-4);color:var(--text-secondary)}
.ai-advice-card__dimensions{gap:var(--spacing-3)}
.ai-advice-card__dimension dd{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:var(--spacing-3);margin:6px 0 0}
.ai-advice-card__dimension-track{height:8px;overflow:hidden;background:var(--state-selected)}
.ai-advice-card__dimension-fill{display:block;height:100%;background:var(--color-primary-500)}
.ai-advice-card__dimension-value{min-width:32px;color:var(--text-primary);font-size:var(--font-size-sm);text-align:right}
.ai-advice-card__markdown{color:var(--text-primary);line-height:var(--line-height-relaxed)}
.ai-advice-card__markdown :deep(*){overflow-wrap:anywhere}
.ai-advice-card__markdown :deep(h1),.ai-advice-card__markdown :deep(h2),.ai-advice-card__markdown :deep(h3){margin:var(--spacing-5) 0 var(--spacing-3);color:var(--text-primary);line-height:var(--line-height-tight)}
.ai-advice-card__markdown :deep(p),.ai-advice-card__markdown :deep(ul),.ai-advice-card__markdown :deep(ol),.ai-advice-card__markdown :deep(blockquote),.ai-advice-card__markdown :deep(pre){margin:0 0 var(--spacing-3)}
.ai-advice-card__markdown :deep(ul),.ai-advice-card__markdown :deep(ol){padding-left:1.25rem}
.ai-advice-card__markdown :deep(blockquote){padding-left:var(--spacing-4);border-left:3px solid var(--border-ai);color:var(--text-secondary)}
.ai-advice-card__markdown :deep(code),.ai-advice-card__markdown :deep(pre){font-family:var(--font-family-mono)}
.ai-advice-card__markdown :deep(pre){padding:var(--spacing-3) 0;border-left:2px solid var(--border-subtle);background:transparent}
.ai-advice-card__markdown :deep(a){color:var(--text-link)}
@media (min-width:768px){.ai-advice-card__score-panel{grid-template-columns:180px minmax(0,1fr)}.ai-advice-card__dimensions{grid-column:1/-1;grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:767px){.ai-advice-card__header{grid-template-columns:1fr}.ai-advice-card__notice--error{align-items:start}}
@media (prefers-reduced-motion:reduce){.is-loading{animation:none}}
</style>
