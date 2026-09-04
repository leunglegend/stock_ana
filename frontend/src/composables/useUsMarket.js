// 美股复盘页数据编排：摘要 + 板块榜（useAsyncSection）+ AI 一句话（SSE）
import { ref } from 'vue'
import { useAsyncSection } from './useAsyncSection'
import { getUsAiSummary, getUsSectors, getUsSummary } from '../api/us'

export function useUsMarket() {
  const summarySection = useAsyncSection(getUsSummary, { initialData: null })
  const sectorsSection = useAsyncSection(getUsSectors, { initialData: [] })

  const aiText = ref('')
  const aiLoading = ref(false)
  const aiError = ref(false)
  let aiSource = null
  let aiRequestId = 0

  function applyAiChunk(requestId, chunk) {
    if (requestId !== aiRequestId) return
    // 丢弃开场/元信息帧；❌ 帧标记出错；其余（含 ⚠️ 未配置兜底）原样追加
    if (chunk.startsWith('📊') || chunk.startsWith('🤖')) return
    if (chunk.startsWith('❌')) return void (aiError.value = true)
    aiText.value += chunk
  }

  async function generateAiSummary() {
    const requestId = ++aiRequestId
    if (aiSource) { aiSource.close(); aiSource = null }
    aiLoading.value = true
    aiError.value = false
    aiText.value = ''
    try {
      aiSource = getUsAiSummary(
        (chunk) => applyAiChunk(requestId, chunk),
        () => { if (requestId === aiRequestId) aiLoading.value = false },
        () => { if (requestId === aiRequestId) { aiLoading.value = false; aiError.value = true } },
      )
    } catch (e) {
      aiLoading.value = false
      aiError.value = true
    }
  }

  function closeAiSource() {
    aiRequestId += 1
    if (aiSource) { aiSource.close(); aiSource = null }
    aiLoading.value = false
  }

  return {
    summarySection, sectorsSection,
    aiText, aiLoading, aiError,
    loadSummary: summarySection.run,
    loadSectors: sectorsSection.run,
    generateAiSummary, closeAiSource,
  }
}
