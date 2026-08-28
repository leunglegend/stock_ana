<template>
  <el-card class="ai-advice-card card-shadow">
    <template #header>
      <div class="card-header">
        <div class="header-left">
          <div class="header-icon">
            <el-icon color="#fff" :size="18"><MagicStick /></el-icon>
          </div>
          <span class="header-title">AI 智能分析报告</span>
        </div>
        <div class="header-right">
          <el-tag v-if="analyzing" type="primary" effect="dark" size="small" class="analyzing-tag">
            <el-icon class="is-loading"><Loading /></el-icon>
            生成中
          </el-tag>
          <el-button
            v-else
            type="primary"
            size="small"
            :icon="MagicStick"
            :disabled="!code"
            @click="$emit('start-analyze')"
            class="analyze-btn"
          >
            重新分析
          </el-button>
        </div>
      </div>
    </template>

    <div class="advice-content">
      <!-- 空状态 -->
      <div v-if="!advice && !analyzing" class="empty-state">
        <div class="empty-icon">
          <el-icon :size="56" color="#a78bfa"><MagicStick /></el-icon>
        </div>
        <p class="empty-title">暂无分析报告</p>
        <p class="empty-desc">点击右上角「重新分析」按钮，AI 将为您生成专业的股票投资分析</p>
      </div>

      <!-- 加载中 -->
      <div v-else-if="analyzing && advice.length < 30" class="loading-state">
        <div class="loading-spinner">
          <el-icon class="is-loading" :size="40" color="#8b5cf6"><Loading /></el-icon>
        </div>
        <p class="loading-text">AI 正在深度分析股票数据...</p>
        <p class="loading-sub">整合行情、财务、技术面多维度信息，生成专业投资建议</p>
      </div>

      <!-- 分析结果 -->
      <div v-else class="report-content">
        <!-- 评分仪表盘 -->
        <div v-if="scoreData" class="score-dashboard">
          <div class="score-main" :style="{ borderColor: currentRatingConfig.borderColor, background: currentRatingConfig.bgColor }">
            <div class="score-number">
              <span class="score-value" :style="{ color: currentRatingConfig.color }">{{ scoreData.score }}</span>
              <span class="score-max">/ 100</span>
            </div>
            <div class="score-rating" :style="{ color: currentRatingConfig.color }">
              {{ scoreData.rating }}
            </div>
          </div>

          <!-- 操作建议 -->
          <div v-if="scoreData.action_advice" class="action-advice">
            <span class="advice-icon">💡</span>
            <span>{{ scoreData.action_advice }}</span>
          </div>

          <!-- 核心要点 -->
          <div v-if="scoreData.key_points?.length" class="key-points">
            <div class="key-points-title">核心要点</div>
            <ul>
              <li v-for="(point, idx) in scoreData.key_points" :key="idx">
                {{ point }}
              </li>
            </ul>
          </div>

          <!-- 各维度评分 -->
          <div v-if="scoreData.dimensions" class="dimension-scores">
            <div class="dimension-item" v-for="(label, key) in dimensionLabels" :key="key">
              <div class="dim-label">{{ label }}</div>
              <div class="dim-bar">
                <div
                  class="dim-fill"
                  :style="{
                    width: (scoreData.dimensions[key] || 0) + '%',
                    background: getDimensionColor(scoreData.dimensions[key])
                  }"
                ></div>
              </div>
              <div class="dim-score">{{ scoreData.dimensions[key] || 0 }}</div>
            </div>
          </div>
        </div>
        <div class="report-text">
          <template v-for="(block, idx) in textBlocks" :key="idx">
            <!-- 二级标题 -->
            <div v-if="block.type === 'h2'" class="h2-block">
              <span class="h2-icon">{{ block.icon }}</span>
              <span class="h2-text">{{ block.text }}</span>
              <div class="h2-line"></div>
            </div>
            <!-- 三级标题 -->
            <div v-else-if="block.type === 'h3'" class="h3-block">
              {{ block.text }}
            </div>
            <!-- 列表项 -->
            <div v-else-if="block.type === 'li'" class="li-block">
              <span class="li-dot"></span>
              <span class="li-text" v-html="block.text"></span>
            </div>
            <!-- 有序列表项 -->
            <div v-else-if="block.type === 'olli'" class="li-block">
              <span class="li-num">{{ block.num }}</span>
              <span class="li-text" v-html="block.text"></span>
            </div>
            <!-- 普通段落 -->
            <div v-else-if="block.type === 'p'" class="p-block" v-html="block.text"></div>
            <!-- 空行 -->
            <div v-else-if="block.type === 'empty'" class="empty-line"></div>
          </template>
        </div>

        <!-- 生成中指示器 -->
        <div v-if="analyzing" class="typing-indicator">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="typing-text">AI 正在继续生成</span>
        </div>
      </div>
    </div>

    <!-- 底部声明 -->
    <div class="footer-disclaimer">
      <el-icon color="#f59e0b" :size="16"><Warning /></el-icon>
      <span>本报告由 AI 自动生成，仅供学习参考，不构成任何投资建议。投资有风险，入市需谨慎。</span>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { MagicStick, Loading, Warning } from '@element-plus/icons-vue'

const props = defineProps({
  code: { type: String, default: '' },
  analyzing: { type: Boolean, default: false },
  advice: { type: String, default: '' },
})

defineEmits(['start-analyze'])

// 解析 AI 返回中的评分数据
const scoreData = computed(() => {
  if (!props.advice || props.analyzing) return null

  const text = props.advice
  // 找 ```json ... ``` 代码块
  const match = text.match(/```json\s*([\s\S]*?)\s*```/)
  if (!match) return null

  try {
    const data = JSON.parse(match[1].trim())
    if (typeof data.score === 'number' && data.score >= 0 && data.score <= 100) {
      return data
    }
    return null
  } catch (e) {
    return null
  }
})

// 评级配置
const ratingConfig = {
  '强烈买入': { color: '#dc2626', bgColor: '#fef2f2', borderColor: '#fecaca' },
  '买入': { color: '#ef4444', bgColor: '#fef2f2', borderColor: '#fecaca' },
  '观望': { color: '#d97706', bgColor: '#fffbeb', borderColor: '#fde68a' },
  '减仓': { color: '#059669', bgColor: '#ecfdf5', borderColor: '#a7f3d0' },
  '卖出': { color: '#10b981', bgColor: '#ecfdf5', borderColor: '#a7f3d0' },
}

const currentRatingConfig = computed(() => {
  if (!scoreData.value?.rating) return ratingConfig['观望']
  return ratingConfig[scoreData.value.rating] || ratingConfig['观望']
})

// 维度显示配置
const dimensionLabels = {
  technical: '技术面',
  fundamental: '基本面',
  sentiment: '情绪面',
  risk: '风险防御',
}

function getDimensionColor(score) {
  const s = Number(score) || 0
  if (s >= 70) return '#10b981'
  if (s >= 50) return '#f59e0b'
  return '#ef4444'
}

// 用于显示正文的纯文本（去掉了 JSON 代码块）
const cleanAdviceText = computed(() => {
  if (!props.advice) return ''
  if (!scoreData.value) return props.advice
  // 去掉 ```json ... ``` 代码块
  return props.advice.replace(/```json\s*[\s\S]*?```\s*/, '').trim()
})

// 把文本逐行解析为块级元素
const textBlocks = computed(() => {
  if (!cleanAdviceText.value) return []

  let text = cleanAdviceText.value

  // 找到第一个标题（去掉前面的状态提示）
  const h2Match = text.match(/##\s+.+/)
  if (h2Match && h2Match.index > 0) {
    text = text.substring(h2Match.index)
  }

  const blocks = []
  const lines = text.split('\n')
  let olCounter = 0 // 有序列表计数

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const trimmed = line.trim()

    // 空行
    if (!trimmed) {
      olCounter = 0
      blocks.push({ type: 'empty' })
      continue
    }

    // 二级标题
    const h2Match = line.match(/^\s*##\s+(.+)/)
    if (h2Match) {
      olCounter = 0
      const title = h2Match[1].trim()
      let icon = '📋'
      if (title.includes('公司') || title.includes('概况')) icon = '🏢'
      else if (title.includes('财务')) icon = '💰'
      else if (title.includes('技术') || title.includes('走势')) icon = '📈'
      else if (title.includes('估值')) icon = '⚖️'
      else if (title.includes('建议') || title.includes('投资')) icon = '🎯'
      else if (title.includes('风险')) icon = '⚠️'
      blocks.push({ type: 'h2', text: title, icon })
      continue
    }

    // 三级标题
    const h3Match = line.match(/^\s*###\s+(.+)/)
    if (h3Match) {
      olCounter = 0
      blocks.push({ type: 'h3', text: h3Match[1].trim() })
      continue
    }

    // 无序列表（匹配行首任意空格 + -/*/+/数字. + 空格）
    const ulMatch = line.match(/^\s*[-*+]\s+(.+)/)
    if (ulMatch) {
      olCounter = 0
      const content = formatInline(ulMatch[1].trim())
      blocks.push({ type: 'li', text: content })
      continue
    }

    // 有序列表
    const olMatch = line.match(/^\s*(\d+)\.\s+(.+)/)
    if (olMatch) {
      const num = parseInt(olMatch[1])
      if (num > 0) olCounter = num
      else olCounter++
      const content = formatInline(olMatch[2].trim())
      blocks.push({ type: 'olli', num: olCounter, text: content })
      continue
    }

    // 普通段落（行内格式：加粗等）
    const content = formatInline(trimmed)
    blocks.push({ type: 'p', text: content })
  }

  return blocks
})

// 处理行内格式（加粗）
function formatInline(text) {
  return text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
}
</script>

<style scoped>
.ai-advice-card {
  width: 100%;
  border-radius: 12px;
  border: none;
  overflow: hidden;
}

:deep(.el-card__header) {
  padding: 0;
  border-bottom: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
}

.header-left { display: flex; align-items: center; gap: 12px; }
.header-icon {
  width: 36px; height: 36px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
}
.header-title { font-size: 17px; font-weight: 600; letter-spacing: 0.5px; }
.header-right { display: flex; align-items: center; gap: 10px; }

.analyzing-tag {
  background: rgba(255,255,255,0.2);
  border: none;
  color: white;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.analyze-btn {
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.3);
  color: white;
}
.analyze-btn:hover {
  background: rgba(255,255,255,0.3) !important;
  color: white !important;
  border-color: rgba(255,255,255,0.5) !important;
}

.advice-content { padding: 4px 4px 0 4px; }

/* 空状态 */
.empty-state { padding: 60px 20px; text-align: center; }
.empty-icon {
  width: 100px; height: 100px;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}
.empty-title { font-size: 18px; font-weight: 600; color: #374151; margin: 0 0 8px 0; }
.empty-desc { font-size: 14px; color: #9ca3af; margin: 0; }

/* 加载中 */
.loading-state { padding: 80px 20px; text-align: center; }
.loading-spinner { margin-bottom: 20px; }
.loading-text { font-size: 17px; font-weight: 600; color: #4b5563; margin: 0 0 8px 0; }
.loading-sub { font-size: 13px; color: #9ca3af; margin: 0; }

/* 报告内容 */
.report-content { padding: 8px 16px 16px; }

/* 评分仪表盘 */
.score-dashboard {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}
.score-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-radius: 12px;
  border: 2px solid;
  margin-bottom: 16px;
}
.score-number {
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.score-value {
  font-size: 48px;
  font-weight: 800;
  line-height: 1;
}
.score-max {
  font-size: 16px;
  color: #9ca3af;
  font-weight: 500;
}
.score-rating {
  font-size: 20px;
  font-weight: 700;
  padding: 6px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.6);
}
.action-advice {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 16px;
  background: #f5f3ff;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
}
.advice-icon {
  font-size: 18px;
  line-height: 1.5;
  flex-shrink: 0;
}
.key-points {
  margin-bottom: 16px;
}
.key-points-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}
.key-points ul {
  margin: 0;
  padding-left: 20px;
  color: #4b5563;
  font-size: 14px;
  line-height: 1.8;
}
.key-points li {
  margin-bottom: 4px;
}
.dimension-scores {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 24px;
}
.dimension-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}
.dim-label {
  width: 60px;
  color: #6b7280;
  flex-shrink: 0;
}
.dim-bar {
  flex: 1;
  height: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}
.dim-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}
.dim-score {
  width: 28px;
  text-align: right;
  font-weight: 600;
  color: #374151;
  flex-shrink: 0;
}

.report-text {
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
  color: #374151;
  line-height: 1.9;
}

/* 空行 */
.empty-line { height: 8px; }

/* 二级标题 */
.h2-block {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 24px 0 12px;
}
.h2-icon { font-size: 22px; line-height: 1; }
.h2-text {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
  letter-spacing: 0.5px;
}
.h2-line {
  flex: 1;
  height: 3px;
  margin-left: 12px;
  background: linear-gradient(90deg, #c4b5fd 0%, transparent 100%);
  border-radius: 2px;
}

/* 三级标题 */
.h3-block {
  font-size: 16px;
  font-weight: 600;
  color: #4b5563;
  margin: 18px 0 10px;
  padding-left: 12px;
  border-left: 3px solid #a78bfa;
}

/* 段落 */
.p-block {
  font-size: 15px;
  line-height: 2;
  color: #4b5563;
  margin: 8px 0;
  text-indent: 2em;
  letter-spacing: 0.3px;
}

/* 列表项 */
.li-block {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 15px;
  line-height: 2;
  color: #4b5563;
  margin: 4px 0 4px 4px;
}
.li-dot {
  flex-shrink: 0;
  margin-top: 14px;
  width: 6px;
  height: 6px;
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
  border-radius: 50%;
}
.li-num {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  margin-top: 5px;
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
  color: white;
  font-size: 12px;
  font-weight: 600;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}
.li-text { flex: 1; }

/* 加粗 */
:deep(strong) {
  color: #1f2937;
  font-weight: 700;
  background: linear-gradient(180deg, transparent 60%, #fef3c7 60%);
  padding: 0 2px;
}

/* 打字指示器 */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 16px 0 8px;
  color: #9ca3af;
  font-size: 13px;
}
.typing-indicator .dot {
  width: 6px; height: 6px;
  background: #a78bfa;
  border-radius: 50%;
  animation: typing-bounce 1.4s infinite ease-in-out both;
}
.typing-indicator .dot:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator .dot:nth-child(2) { animation-delay: -0.16s; }
.typing-text { margin-left: 6px; }
@keyframes typing-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

/* 底部声明 */
.footer-disclaimer {
  margin: 16px -20px -20px;
  padding: 14px 20px;
  background: #fafafa;
  border-top: 1px solid #f0f0f0;
  font-size: 12.5px;
  color: #9ca3af;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  line-height: 1.6;
}
.footer-disclaimer .el-icon { flex-shrink: 0; margin-top: 1px; }
</style>
